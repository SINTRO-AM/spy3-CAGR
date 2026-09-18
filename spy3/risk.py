"""Risikoanalysen: Stresstests, VaR/CVaR, Monte-Carlo, Korrelationen."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import metrics as m
from .robustness import CRISES

LIVE_START = "2023-09-01"      # Start des Live-Track-Records von SPY3

# Zusätzliche kurze Stressfenster neben den Krisenphasen aus robustness.CRISES
SHOCKS = {
    "Flash Crash 2010": ("2010-04-23", "2010-07-02"),
    "Taper Tantrum 2013": ("2013-05-22", "2013-06-24"),
    "China-Schock 2015": ("2015-08-10", "2015-08-25"),
    "Volmageddon 2018": ("2018-01-26", "2018-02-08"),
    "Q4 2018": ("2018-10-01", "2018-12-24"),
}
WINDOWS = {**CRISES, **SHOCKS}


def stress_table(series: dict[str, pd.Series]) -> pd.DataFrame:
    """Rendite im Stressfenster je Reihe, plus tiefster Drawdown im Fenster."""
    rows = {}
    for name, (a, b) in WINDOWS.items():
        sl = {k: s.loc[a:b] for k, s in series.items()}
        if any(len(s) < 5 for s in sl.values()):
            continue
        row = {k: m.total_return(s) for k, s in sl.items()}
        row["MaxDD"] = m.max_drawdown(list(sl.values())[0])
        rows[name] = row
    return pd.DataFrame(rows).T


def var_table(series: dict[str, pd.Series], levels=(0.95, 0.99)) -> pd.DataFrame:
    """Historischer VaR und CVaR (Expected Shortfall) auf Tagesbasis, als Verlust > 0."""
    out = {}
    for name, s in series.items():
        col = {}
        for lv in levels:
            q = s.quantile(1 - lv)
            col[f"VaR {lv:.0%}"] = -q
            col[f"CVaR {lv:.0%}"] = -s[s <= q].mean()
        col["Schlechtester Tag"] = -s.min()
        col["Schlechtester Monat"] = -((1 + s).resample("ME").prod() - 1).min()
        out[name] = col
    return pd.DataFrame(out)


def var_backtest(r: pd.Series, level: float = 0.99, window: int = 250) -> dict:
    """Kupiec-Test: Wie oft wurde der rollierende historische VaR überschritten?"""
    var = -r.rolling(window).quantile(1 - level).shift(1)
    valid = var.notna()
    breaches = (r[valid] < -var[valid])
    n, x = int(valid.sum()), int(breaches.sum())
    p = 1 - level
    exp = n * p
    if 0 < x < n:
        lr = -2 * (np.log((1 - p) ** (n - x) * p ** x)
                   - np.log((1 - x / n) ** (n - x) * (x / n) ** x))
    else:
        lr = np.nan
    return {"Beobachtungen": n, "Überschreitungen": x, "Erwartet": exp,
            "Quote": x / n if n else np.nan, "Kupiec-LR": lr}


def _simulate(r: pd.Series, horizon_days: int, n_paths: int, block: int,
              seed: int) -> np.ndarray:
    """Block-Bootstrap der Tagesrenditen; erhält Autokorrelation und Vola-Cluster."""
    x = r.to_numpy()
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(horizon_days / block))
    starts = rng.integers(0, len(x) - block, size=(n_paths, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(n_paths, -1)
    return np.cumprod(1 + x[idx[:, :horizon_days]], axis=1)


def monte_carlo(r: pd.Series, horizon_days: int = 252, n_paths: int = 2000,
                block: int = 20, seed: int = 7) -> pd.DataFrame:
    """Perzentilpfade des Vermögens (Start 1) über den Horizont."""
    w = _simulate(r, horizon_days, n_paths, block, seed)
    pct = [5, 25, 50, 75, 95]
    return pd.DataFrame(np.percentile(w, pct, axis=0).T,
                        columns=[f"P{p}" for p in pct],
                        index=np.arange(1, horizon_days + 1))


def monte_carlo_stats(r: pd.Series, horizon_days: int = 252, n_paths: int = 2000,
                      block: int = 20, seed: int = 7) -> dict:
    w = _simulate(r, horizon_days, n_paths, block, seed)
    ends = w[:, -1] - 1
    dd = (w / np.maximum.accumulate(w, axis=1) - 1).min(axis=1)
    p5, p50, p95 = np.percentile(ends, [5, 50, 95])
    return {"P5": float(p5), "P50": float(p50), "P95": float(p95),
            "Verlustwahrscheinlichkeit": float((ends < 0).mean()),
            "Ø max. Drawdown": float(dd.mean()),
            "P(Drawdown > 20 %)": float((dd < -0.20).mean())}


def correlation(series: dict[str, pd.Series], freq: str | None = "ME") -> pd.DataFrame:
    df = pd.DataFrame(series)
    if freq:
        df = df.resample(freq).apply(lambda s: (1 + s).prod() - 1)
    return df.corr()


def monthly_table(r: pd.Series) -> pd.DataFrame:
    """Monatsrenditen als Matrix Jahre x Monate (für die Heatmap)."""
    mth = (1 + r).resample("ME").prod() - 1
    df = pd.DataFrame({"y": mth.index.year, "m": mth.index.month, "v": mth.values})
    return df.pivot(index="y", columns="m", values="v").sort_index(ascending=False)
