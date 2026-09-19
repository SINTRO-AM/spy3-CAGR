"""Preisdaten laden (yfinance, dividendenbereinigt) mit lokalem CSV-Cache.

Risk-Off vor SHY-Start (30.07.2002): Näherung über die Rendite 13-wöchiger
US-T-Bills (^IRX, annualisierte Rendite in %). Tagesrendite am Tag t aus der
Rendite vom Vortag: (1 + y/100)^(1/252) - 1.
"""
from __future__ import annotations

import warnings
from pathlib import Path

import pandas as pd

CACHE = Path(__file__).resolve().parent.parent / "data" / "prices.csv"
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


def prepare_returns(px: pd.DataFrame) -> pd.DataFrame:
    """Tagesrenditen. Risk-Off: SHY, davor T-Bill-Näherung, sonst 0 %.

    Spalte `risk_off_source`: 'SHY', 'T-Bill' oder 'none'.
    """
    r = px[["risk_on", "risk_off"]].pct_change()
    y = px.get("tbill_yield", pd.Series(float("nan"), index=px.index)).ffill()
    tbill_ret = (1 + y.shift(1) / 100) ** (1 / 252) - 1
    src = pd.Series("SHY", index=px.index)
    miss = r["risk_off"].isna()
    src[miss & tbill_ret.notna()] = "T-Bill"
    src[miss & tbill_ret.isna()] = "none"
    r["risk_off"] = r["risk_off"].fillna(tbill_ret).fillna(0.0)
    r["tbill"] = tbill_ret.fillna(0.0)
    r["risk_off_source"] = src
    r = r.iloc[1:]
    if (r["risk_off_source"] == "none").any():
        warnings.warn("Keine T-Bill-Daten für die Zeit vor SHY: Risk-Off-Rendite dort 0 %. "
                      "Mit --refresh neu laden.", stacklevel=2)
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
