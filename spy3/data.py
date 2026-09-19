"""Preisdaten laden (yfinance, dividendenbereinigt) mit lokalem CSV-Cache.

Risk-Off vor SHY-Start (30.07.2002), in dieser Reihenfolge:
  1. Bloomberg US Treasury Total Return Index (LUATTRUU), wenn data/luattruu.csv
     vorliegt (Bloomberg-Export, wird direkt gelesen)
  2. 13-wöchige US-T-Bills (^IRX): Tagesrendite (1 + y/100)^(1/252) - 1
  3. 0 %
"""
from __future__ import annotations

import re

import warnings
from pathlib import Path

import pandas as pd

CACHE = Path(__file__).resolve().parent.parent / "data" / "prices.csv"
TREASURY_FILE = CACHE.parent / "luattruu.csv"
_ROW = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})[^\t;,]*[\t;,]\s*([-\d.,]+)")
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


def load_treasury_index(path: Path = TREASURY_FILE) -> pd.Series:
    """Bloomberg US Treasury Total Return Index (PX_LAST) aus dem Rohexport.

    Liest Zeilen der Form `29.12.1989<TAB>467,8<TAB>...`; Kopfzeilen und die
    log-return-Spalte werden ignoriert, Dezimalkomma und -punkt beide akzeptiert.
    Fehlt die Datei, kommt eine leere Reihe zurück.
    """
    if not Path(path).exists():
        return pd.Series(dtype=float, name="LUATTRUU")
    rows = {}
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        m = _ROW.match(line.strip())
        if not m:
            continue
        d, mo, y, val = m.groups()
        val = val.replace(".", "").replace(",", ".") if "," in val else val
        try:
            rows[pd.Timestamp(int(y), int(mo), int(d))] = float(val)
        except ValueError:
            continue
    return pd.Series(rows, name="LUATTRUU").sort_index()


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
        tr_px = treasury.reindex(treasury.index.union(px.index)).ffill().reindex(px.index)
        tr_ret = tr_px.pct_change()
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
    "High Yield": "HYG",
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
