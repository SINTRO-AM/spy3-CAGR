"""Preisdaten laden (yfinance, dividendenbereinigt) mit lokalem CSV-Cache.

Risk-Off vor SHY-Start (30.07.2002), in dieser Reihenfolge:
  1. SHY-Proxy mit gleicher Laufzeit (1–3 Jahre): Bloomberg US Treasury 1-3 Year
     Index (data/lt01truu.csv) oder, wenn nicht vorhanden, synthetische Gesamtrendite
     aus den FRED-Renditen DGS1/DGS2/DGS3 (data/fred_yields.csv)
  2. Bloomberg US Treasury Total Return Index, alle Laufzeiten (data/luattruu.csv)
  3. 13-wöchige US-T-Bills (^IRX): Tagesrendite (1 + y/100)^(1/252) - 1
  4. 0 %
"""
from __future__ import annotations

import os
import re

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path(__file__).resolve().parent.parent / "data" / "prices.csv"
# Standardpfade; alternativ per Umgebungsvariable überschreiben
TREASURY_FILE = Path(os.environ.get("SPY3_TREASURY_FILE", CACHE.parent / "luattruu.csv"))
SHORT_TREASURY_FILE = Path(os.environ.get("SPY3_SHORT_TREASURY_FILE",
                                          CACHE.parent / "lt01truu.csv"))
FRED_FILE = CACHE.parent / "fred_yields.csv"
FRED_SERIES = {"DGS1": 1.0, "DGS2": 2.0, "DGS3": 3.0}      # Constant-Maturity-Renditen, Jahre
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


def prepare_returns(px: pd.DataFrame, treasury: pd.Series | None = None,
                    proxy: pd.Series | None = None) -> pd.DataFrame:
    """Tagesrenditen. Risk-Off: SHY, davor SHY-Proxy (1–3 J.), dann Treasury-Index
    (alle Laufzeiten), dann T-Bill, sonst 0 %.

    Spalte `risk_off_source`: 'SHY', 'SHY-Proxy', 'LUATTRUU', 'T-Bill' oder 'none'.
    """
    r = px[["risk_on", "risk_off"]].pct_change()
    y = px.get("tbill_yield", pd.Series(float("nan"), index=px.index)).ffill()
    tbill_ret = (1 + y.shift(1) / 100) ** (1 / 252) - 1
    if treasury is None:
        treasury = load_treasury_index()
    if len(treasury):
        tr_px = treasury.reindex(treasury.index.union(px.index)).ffill()
        tr_px[tr_px.index > treasury.index.max()] = float("nan")   # nicht über das Ende hinaus
        tr_ret = tr_px.reindex(px.index).pct_change()
    else:
        tr_ret = pd.Series(float("nan"), index=px.index)
    if proxy is None:
        proxy = load_short_treasury_returns()
    if len(proxy):
        # Renditen auf die SPY-Handelstage bringen: fehlende Tage über das Vermögen
        base = proxy.index.min() - pd.Timedelta(days=1)
        w = pd.concat([pd.Series([1.0], index=[base]), (1 + proxy).cumprod()])
        w = w.reindex(w.index.union(px.index)).ffill()
        w[w.index > proxy.index.max()] = float("nan")
        w[w.index < base] = float("nan")
        px_ret = w.reindex(px.index).pct_change()
    else:
        px_ret = pd.Series(float("nan"), index=px.index)
    src = pd.Series("SHY", index=px.index)
    miss = r["risk_off"].isna()
    src[miss & px_ret.notna()] = "SHY-Proxy"
    src[miss & px_ret.isna() & tr_ret.notna()] = "LUATTRUU"
    src[miss & px_ret.isna() & tr_ret.isna() & tbill_ret.notna()] = "T-Bill"
    src[miss & px_ret.isna() & tr_ret.isna() & tbill_ret.isna()] = "none"
    r["risk_off"] = (r["risk_off"].fillna(px_ret).fillna(tr_ret).fillna(tbill_ret)
                     .fillna(0.0))
    r["treasury"] = tr_ret
    r["shy_proxy"] = px_ret
    r["tbill"] = tbill_ret.fillna(0.0)
    r["risk_off_source"] = src
    r = r.iloc[1:]
    if (r["risk_off_source"] == "none").any():
        warnings.warn("Weder SHY-Proxy, Treasury-Index noch T-Bill-Daten für die Zeit vor SHY: "
                      "Risk-Off-Rendite dort 0 %.", stacklevel=2)
    return r


# ---------- SHY-Proxy: 1–3-jährige Treasuries vor dem ETF-Start ------------------
def load_fred_yields(refresh: bool = False, cache: Path = FRED_FILE,
                     start: str = "1999-01-01") -> pd.DataFrame:
    """Tägliche Constant-Maturity-Renditen (in %) von FRED; leer, wenn nicht ladbar."""
    if cache.exists() and not refresh:
        return pd.read_csv(cache, index_col=0, parse_dates=True)
    frames = []
    for sid in FRED_SERIES:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
        try:
            df = pd.read_csv(url, index_col=0, parse_dates=True, na_values=".")
        except Exception as exc:                        # kein Netz o. ä.
            warnings.warn(f"FRED {sid} nicht geladen: {exc}", stacklevel=2)
            return pd.DataFrame()
        df.columns = [sid]
        frames.append(df)
    out = pd.concat(frames, axis=1).loc[start:]
    cache.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(cache)
    return out


def cmt_total_return(yields_pct: pd.Series, maturity: float) -> pd.Series:
    """Tägliche Gesamtrendite einer Par-Anleihe mit konstanter Restlaufzeit.

    Am Vortag zu Rendite y0 (Kupon = y0, halbjährlich) zu pari gekauft, heute zur
    Rendite y1 bewertet, plus ein Tag Kuponabgrenzung. Standardverfahren für
    Anleihenrenditen aus Zinsreihen (Constant-Maturity-Total-Return).
    """
    y = yields_pct.ffill() / 100
    y0, y1 = y.shift(1), y
    n = 2 * maturity                                     # Anzahl Halbjahreskupons
    disc = (1 + y1 / 2) ** (-n)
    annuity = (1 - disc) / (y1 / 2)
    price = (y0 / 2) * annuity + disc                    # Kurs heute, Nominal 1
    return (price - 1 + y0 / 252).rename(f"CMT{maturity:g}y")


def short_treasury_proxy(yields: pd.DataFrame | None = None) -> pd.Series:
    """SHY-Proxy als gleichgewichteter Korb aus 1-, 2- und 3-jährigen Par-Anleihen."""
    if yields is None or yields.empty:
        return pd.Series(dtype=float)
    cols = [c for c in FRED_SERIES if c in yields]
    if not cols:
        return pd.Series(dtype=float)
    rets = pd.concat([cmt_total_return(yields[c], FRED_SERIES[c]) for c in cols], axis=1)
    out = rets.mean(axis=1).dropna().rename("SHY-Proxy")
    out.attrs["source"] = "CMT 1-3y (FRED)"
    return out


def load_short_treasury_returns() -> pd.Series:
    """Tägliche einfache Renditen des SHY-Proxys: Bloomberg 1-3y-Index, sonst FRED-CMT."""
    idx = load_treasury_index(SHORT_TREASURY_FILE)
    if len(idx):
        r = idx.pct_change().dropna().rename("SHY-Proxy")
        r.attrs["source"] = "LT01TRUU"
        return r
    y = load_fred_yields() if FRED_FILE.exists() else pd.DataFrame()
    return short_treasury_proxy(y)
