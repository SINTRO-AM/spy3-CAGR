"""Preisdaten laden (yfinance, dividendenbereinigt) mit lokalem CSV-Cache."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

CACHE = Path(__file__).resolve().parent.parent / "data" / "prices.csv"


def load_prices(
    start: str = "2000-01-01",
    end: str | None = None,
    risk_on: str = "SPY",
    risk_off: str = "SHY",
    refresh: bool = False,
    cache: Path = CACHE,
) -> pd.DataFrame:
    """Gibt DataFrame mit Spalten ['risk_on', 'risk_off'] (Total-Return-Preise) zurück.

    Hinweis: SHY existiert erst ab 30.07.2002. Davor wird die Risk-Off-Rendite
    mit 0 % angesetzt (konservativ: Cash ohne Verzinsung). Das wird in
    `prepare_returns` explizit gemacht und im Report ausgewiesen.
    """
    if cache.exists() and not refresh:
        px = pd.read_csv(cache, index_col=0, parse_dates=True)
    else:
        import yfinance as yf  # erst hier importieren -> Tests laufen ohne Netz

        raw = yf.download(
            [risk_on, risk_off], start=start, end=end,
            auto_adjust=True, progress=False,
        )["Close"]
        px = raw.rename(columns={risk_on: "risk_on", risk_off: "risk_off"})
        px.index = pd.to_datetime(px.index).tz_localize(None)
        cache.parent.mkdir(parents=True, exist_ok=True)
        px.to_csv(cache)
    px = px.loc[start:end] if end else px.loc[start:]
    return px[["risk_on", "risk_off"]].dropna(subset=["risk_on"])


def prepare_returns(px: pd.DataFrame) -> pd.DataFrame:
    """Einfache Tagesrenditen; fehlende Risk-Off-Renditen (vor SHY-Start) = 0."""
    r = px.pct_change()
    r["risk_off_missing"] = r["risk_off"].isna()
    r["risk_off"] = r["risk_off"].fillna(0.0)
    return r.iloc[1:]
