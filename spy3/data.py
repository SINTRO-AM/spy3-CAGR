"""Preisdaten laden (yfinance, dividendenbereinigt) mit lokalem CSV-Cache.

Risk-Off vor SHY-Start (30.07.2002), in dieser Reihenfolge:
  1. Bloomberg US Treasury Total Return Index (LUATTRUU), wenn data/luattruu.csv
     vorliegt (Bloomberg-Export, wird direkt gelesen)
  2. 13-wöchige US-T-Bills (^IRX): Tagesrendite (1 + y/100)^(1/252) - 1
  3. 0 %
"""
from __future__ import annotations

import os
import re

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path(__file__).resolve().parent.parent / "data" / "prices.csv"
# Standardpfad; alternativ per Umgebungsvariable SPY3_TREASURY_FILE überschreiben
TREASURY_FILE = Path(os.environ.get("SPY3_TREASURY_FILE", CACHE.parent / "luattruu.csv"))
TBILL = "^IRX"
COLUMNS = ["risk_on", "risk_off", "tbill_yield"]


def load_prices(
    start: str = "2000-01-01",
    end: str | None = None,
    risk_on: str = "SPY",
    risk_off: str = "SHY",
    refresh: bool = False,
    cache: Path = CACHE,
) -> pd.DataFrame:
    """DataFrame mit risk_on / risk_off (Total-Return-Preise) und tbill_yield (%)."""
    px = None
    if cache.exists() and not refresh:
        px = pd.read_csv(cache, index_col=0, parse_dates=True)
        if "tbill_yield" not in px:          # alter Cache ohne T-Bill-Daten
            px = None
    if px is None:
        import yfinance as yf  # erst hier importieren -> Tests laufen ohne Netz

        raw = yf.download([risk_on, risk_off, TBILL], start=start, end=end,
                          auto_adjust=True, progress=False)["Close"]
        px = raw.rename(columns={risk_on: "risk_on", risk_off: "risk_off",
                                 TBILL: "tbill_yield"})
        px.index = pd.to_datetime(px.index).tz_localize(None)
        cache.parent.mkdir(parents=True, exist_ok=True)
        px[COLUMNS].to_csv(cache)
    px = px.loc[start:end] if end else px.loc[start:]
    if "tbill_yield" not in px:
        px = px.assign(tbill_yield=float("nan"))
    return px[COLUMNS].dropna(subset=["risk_on"])


def _read_text_any(path: Path) -> str:
    """Liest Textdateien unabhängig von der Kodierung (UTF-8, UTF-16, Windows-1252)."""
    raw = Path(path).read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    if b"\x00" in raw[:200]:                        # UTF-16 ohne BOM
        try:
            return raw.decode("utf-16-le")
        except UnicodeDecodeError:
            pass
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


_DATE_PATTERNS = [
    (re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})"), "dmy"),      # 29.12.1989
    (re.compile(r"^(\d{4})-(\d{2})-(\d{2})"), "ymd"),              # 1989-12-29
    (re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})"), "dmy"),          # 29/12/1989
]


def _split(line: str) -> list[str]:
    """Zerlegt eine Zeile; Anführungszeichen schützen Dezimalkommas."""
    import csv
    for sep in ("\t", ";", ","):
        if sep not in line:
            continue
        parts = next(csv.reader([line], delimiter=sep, quotechar='"'))
        parts = [p.strip().strip("'") for p in parts]
        if len(parts) >= 2 and parts[0] and parts[1]:
            return parts
    return [line.strip()]


def _parse_line(line: str):
    """Gibt (Datum, Wert, ist_prozent) zurück oder None für Nicht-Datenzeilen.

    Wert ist der erste numerische Eintrag nach dem Datum: ein Kurs (PX_LAST) oder,
    wenn kein Kurs vorhanden ist, eine Log-Rendite in Prozent (z. B. "-1,51%").
    """
    parts = _split(line)
    if len(parts) < 2:
        return None
    d = parts[0].strip()
    for pat, order in _DATE_PATTERNS:
        m = pat.match(d)
        if m:
            a, b, c = m.groups()
            y, mo, dd = (int(c), int(b), int(a)) if order == "dmy" else (int(a), int(b), int(c))
            break
    else:
        return None
    for val in parts[1:]:
        val = val.strip()
        if not val:
            continue
        is_pct = val.endswith("%")
        val = val.rstrip("%").strip()
        if "," in val and "." in val:          # 1.084,43 -> 1084.43
            val = val.replace(".", "").replace(",", ".")
        elif "," in val:                        # 467,8 -> 467.8
            val = val.replace(",", ".")
        try:
            return pd.Timestamp(y, mo, dd), float(val), is_pct
        except ValueError:
            continue
    return None


def _rows_to_index(rows: dict) -> pd.Series:
    """Baut aus (Datum -> (Wert, ist_prozent)) eine Kursreihe.

    Liegen Kurse vor, werden sie direkt verwendet. Liegen nur Log-Renditen vor,
    wird ein Index aus exp(kumulierte Log-Renditen) mit Start 100 gebildet – für
    die Tagesrenditen im Backtest ist das gleichwertig.
    """
    if not rows:
        return pd.Series(dtype=float, name="LUATTRUU")
    s = pd.Series({k: v[0] for k, v in rows.items()}).sort_index()
    pct_share = sum(v[1] for v in rows.values()) / len(rows)
    if pct_share > 0.5:                              # Log-Renditen in %
        idx = 100 * np.exp((s / 100).cumsum()).rename("LUATTRUU")
        idx.attrs["mode"] = "returns"
        return idx
    s = s.rename("LUATTRUU")
    s.attrs["mode"] = "prices"
    return s


def load_treasury_index(path: Path = TREASURY_FILE) -> pd.Series:
    """Bloomberg US Treasury Total Return Index aus dem Export.

    Akzeptiert den Rohexport (Tab, Semikolon oder Komma getrennt; Datum als
    dd.mm.yyyy, yyyy-mm-dd oder dd/mm/yyyy; Dezimalkomma oder -punkt; UTF-8,
    UTF-16 oder Windows-1252) sowie .xlsx/.xls. Enthält die Datei Kurse (PX_LAST),
    werden diese verwendet; enthält sie nur Datum und Log-Rendite in Prozent,
    wird daraus eine gleichwertige Kursreihe gebildet. Fehlt die Datei, kommt
    eine leere Reihe zurück.
    """
    path = Path(path)
    if not path.exists():
        return pd.Series(dtype=float, name="LUATTRUU")
    rows = {}
    if path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path, header=None)
        for _, row in df.iterrows():
            vals = [v for v in row.tolist() if pd.notna(v)]
            if len(vals) < 2:
                continue
            d = vals[0]
            if isinstance(d, pd.Timestamp):
                v = vals[1]
                if isinstance(v, str):
                    parsed = _parse_line(f"{d:%d.%m.%Y}\t{v}")
                    if parsed:
                        rows[parsed[0]] = (parsed[1], parsed[2])
                else:
                    rows[d.normalize()] = (float(v), False)
            else:
                parsed = _parse_line("\t".join(str(v) for v in vals))
                if parsed:
                    rows[parsed[0]] = (parsed[1], parsed[2])
    else:
        for line in _read_text_any(path).splitlines():
            parsed = _parse_line(line.strip())
            if parsed:
                rows[parsed[0]] = (parsed[1], parsed[2])
    return _rows_to_index(rows)


def prepare_returns(px: pd.DataFrame, treasury: pd.Series | None = None) -> pd.DataFrame:
    """Tagesrenditen. Risk-Off: SHY, davor Treasury-Index, dann T-Bill, sonst 0 %.

    Spalte `risk_off_source`: 'SHY', 'LUATTRUU', 'T-Bill' oder 'none'.
    """
    r = px[["risk_on", "risk_off"]].pct_change()
    y = px.get("tbill_yield", pd.Series(float("nan"), index=px.index)).ffill()
    tbill_ret = (1 + y.shift(1) / 100) ** (1 / 252) - 1
    if treasury is None:
        treasury = load_treasury_index()
    if len(treasury):
        # Kurs auf die SPY-Handelstage bringen; fehlende Tage fortschreiben
        tr_px = treasury.reindex(treasury.index.union(px.index)).ffill()
        tr_px[tr_px.index > treasury.index.max()] = float("nan")   # nicht über das Ende hinaus
        tr_ret = tr_px.reindex(px.index).pct_change()
    else:
        tr_ret = pd.Series(float("nan"), index=px.index)
    src = pd.Series("SHY", index=px.index)
    miss = r["risk_off"].isna()
    src[miss & tr_ret.notna()] = "LUATTRUU"
    src[miss & tr_ret.isna() & tbill_ret.notna()] = "T-Bill"
    src[miss & tr_ret.isna() & tbill_ret.isna()] = "none"
    r["risk_off"] = r["risk_off"].fillna(tr_ret).fillna(tbill_ret).fillna(0.0)
    r["treasury"] = tr_ret
    r["tbill"] = tbill_ret.fillna(0.0)
    r["risk_off_source"] = src
    r = r.iloc[1:]
    if (r["risk_off_source"] == "none").any():
        warnings.warn("Weder Treasury-Index noch T-Bill-Daten für die Zeit vor SHY: "
                      "Risk-Off-Rendite dort 0 %.", stacklevel=2)
    return r


# Weitere Indizes und Anlageklassen für die Korrelationsmatrix
ASSETS = {
    "Nasdaq 100": "QQQ", "Russell 2000": "IWM", "MSCI EAFE": "EFA",
    "Emerging Markets": "EEM", "US Aggregate Bonds": "AGG", "Long Treasuries": "TLT",
    "Gold": "GLD", "Commodities": "DBC", "REITs": "VNQ", "Investment Grade": "LQD",
    "High Yield": "HYG", "US Treasuries (GOVT)": "GOVT",
}
ASSET_CACHE = CACHE.parent / "assets.csv"


def load_assets(start: str = "2000-01-01", refresh: bool = False,
                cache: Path = ASSET_CACHE) -> pd.DataFrame:
    """Tagesrenditen weiterer Anlageklassen. Ohne Netz und ohne Cache: leerer Frame."""
    px = None
    if cache.exists() and not refresh:
        px = pd.read_csv(cache, index_col=0, parse_dates=True)
    if px is None:
        try:
            import yfinance as yf

            raw = yf.download(list(ASSETS.values()), start=start, auto_adjust=True,
                              progress=False)["Close"]
        except Exception as exc:                       # kein Netz, Ticker weg, Rate-Limit
            warnings.warn(f"Anlageklassen nicht geladen: {exc}", stacklevel=2)
            return pd.DataFrame()
        px = raw.rename(columns={v: k for k, v in ASSETS.items()})
        px.index = pd.to_datetime(px.index).tz_localize(None)
        cache.parent.mkdir(parents=True, exist_ok=True)
        px.to_csv(cache)
    return px.pct_change().iloc[1:]
