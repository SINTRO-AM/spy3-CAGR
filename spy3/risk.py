"""Risikoanalysen: Stresstests, VaR/CVaR, Monte-Carlo, Korrelationen.

Bewusst ohne Abhängigkeit zu spy3.plots, damit keine Importschleife entsteht.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import metrics as m
from .robustness import CRISES

# Zusätzliche kurze Stressfenster neben den Krisenphasen aus robustness.CRISES
SHOCKS = {
    "Flash Crash 2010": ("2010-04-23", "2010-07-02"),
    "Taper Tantrum 2013": ("2013-05-22", "2013-06-24"),
    "China-Schock 2015": ("2015-08-10", "2015-08-25"),
    "Volmageddon 2018": ("2018-01-26", "2018-02-08"),
    "Q4 2018": ("2018-10-01", "2018-12-24"),
}
WINDOWS = {**CRISES, **SHOCKS}


def stress_table(series: dict[str, pd.Series], first_dd: bool = True) -> pd.DataFrame:
    """Rendite je Reihe im Stressfenster, dazu der tiefste Drawdown der ersten Reihe."""
    rows = {}
    for name, (a, b) in WINDOWS.items():
        sl = {k: s.loc[a:b] for k, s in series.items()}
        if any(len(s) < 5 for s in sl.values()):
            continue
        row = {k: m.total_return(s) for k, s in sl.items()}
        if first_dd:
            row["MaxDD"] = m.max_drawdown(next(iter(sl.values())))
        rows[name] = row
    return pd.DataFrame(rows).T


def var_table(series: dict[str, pd.Series], levels=(0.95, 0.99)) -> pd.DataFrame:
    """Historischer VaR und CVaR auf Tagesbasis, als Verlust (positiv) ausgewiesen."""
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
    """Kupiec-Test: Überschreitungen des rollierenden historischen VaR."""
    var = -r.rolling(window).quantile(1 - level).shift(1)
    valid = var.notna()
    breaches = r[valid] < -var[valid]
    n, x = int(valid.sum()), int(breaches.sum())
    p = 1 - level
    if 0 < x < n:
        lr = -2 * (np.log((1 - p) ** (n - x) * p ** x)
                   - np.log((1 - x / n) ** (n - x) * (x / n) ** x))
    else:
        lr = np.nan
    return {"n": n, "breaches": x, "expected": n * p,
            "rate": x / n if n else np.nan, "lr": float(lr)}


def _simulate(r: pd.Series, horizon: int, n_paths: int, block: int, seed: int) -> np.ndarray:
    """Block-Bootstrap der Tagesrenditen; erhält Autokorrelation und Vola-Cluster."""
    x = r.dropna().to_numpy()
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(horizon / block))
    starts = rng.integers(0, max(len(x) - block, 1), size=(n_paths, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(n_paths, -1)
    return np.cumprod(1 + x[idx[:, :horizon]], axis=1)


def monte_carlo(r: pd.Series, horizon: int = 252, n_paths: int = 2000,
                block: int = 20, seed: int = 7) -> pd.DataFrame:
    """Perzentilpfade des Vermögens (Start 1) über den Horizont."""
    w = _simulate(r, horizon, n_paths, block, seed)
    pct = [5, 25, 50, 75, 95]
    return pd.DataFrame(np.percentile(w, pct, axis=0).T,
                        columns=[f"P{p}" for p in pct],
                        index=np.arange(1, horizon + 1))


def monte_carlo_stats(r: pd.Series, horizon: int = 252, n_paths: int = 2000,
                      block: int = 20, seed: int = 7) -> dict:
    w = _simulate(r, horizon, n_paths, block, seed)
    ends = w[:, -1] - 1
    dd = (w / np.maximum.accumulate(w, axis=1) - 1).min(axis=1)
    p5, p50, p95 = np.percentile(ends, [5, 50, 95])
    return {"p5": float(p5), "p50": float(p50), "p95": float(p95),
            "loss_prob": float((ends < 0).mean()),
            "avg_dd": float(dd.mean()),
            "dd20_prob": float((dd < -0.20).mean())}


def correlation(series: dict[str, pd.Series], freq: str | None = "ME") -> pd.DataFrame:
    """Korrelationsmatrix, standardmäßig auf Monatsrenditen."""
    df = pd.DataFrame(series).dropna(how="all")
    if freq:
        df = df.resample(freq).apply(lambda s: (1 + s).prod() - 1 if s.notna().any() else np.nan)
    return df.corr()


def beta_table(r: pd.Series, others: dict[str, pd.Series]) -> pd.DataFrame:
    """Beta und Korrelation von r gegenüber weiteren Anlageklassen (Tagesbasis)."""
    rows = {}
    for name, s in others.items():
        d = pd.concat([r, s], axis=1).dropna()
        if len(d) < 60:
            continue
        a, b = d.iloc[:, 0], d.iloc[:, 1]
        rows[name] = {"Beta": float(np.cov(a, b, ddof=1)[0, 1] / np.var(b, ddof=1)),
                      "Korrelation": float(a.corr(b))}
    return pd.DataFrame(rows).T
