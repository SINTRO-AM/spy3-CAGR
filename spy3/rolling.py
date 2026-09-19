"""Rollierende Kennzahlen (Fenster in Jahren, 252 Handelstage je Jahr)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from .metrics import TD

# Kennzahl -> (Format, höher ist besser)
METRICS = {
    "excess": ("pct", True),
    "return": ("pct", True),
    "vol": ("pct", False),
    "sharpe": ("dec", True),
    "calmar": ("dec", True),
    "maxdd": ("pct", True),     # weniger negativ = besser
    "beta": ("dec", None),
}


def _rolling_max_dd(r: pd.Series, w: int) -> pd.Series:
    out = pd.Series(np.nan, index=r.index)
    if len(r) < w:
        return out
    logw = np.cumsum(np.log1p(r.to_numpy()))
    logw = np.r_[0.0, logw]                                 # Wert vor dem ersten Tag
    win = sliding_window_view(logw, w + 1)                  # Fenster inkl. Startwert
    peak = np.maximum.accumulate(win, axis=1)
    dd = np.exp((win - peak).min(axis=1)) - 1
    out.iloc[w - 1:] = dd
    return out


def rolling_metric(r: pd.Series, bm: pd.Series, metric: str, years: int) -> pd.Series:
    w = int(years * TD)
    lr = np.log1p(r)
    if metric == "excess":
        return (lr - np.log1p(bm)).rolling(w).sum() / years
    if metric == "return":
        return np.expm1(lr.rolling(w).sum() / years)
    if metric == "vol":
        return r.rolling(w).std() * np.sqrt(TD)
    if metric == "sharpe":                       # geometrisch, wie in metrics.sharpe
        ret = np.expm1(lr.rolling(w).sum() / years)
        return ret / (r.rolling(w).std() * np.sqrt(TD))
    if metric == "maxdd":
        return _rolling_max_dd(r, w)
    if metric == "calmar":
        ret = np.expm1(lr.rolling(w).sum() / years)
        dd = _rolling_max_dd(r, w)
        return (ret / dd.abs()).where(dd < 0)
    if metric == "beta":
        return r.rolling(w).cov(bm) / bm.rolling(w).var()
    raise ValueError(metric)


def win_rate(a: pd.Series, b: pd.Series, metric: str) -> float:
    """Anteil der Fenster, in denen a besser ist als b."""
    higher = METRICS[metric][1]
    d = pd.concat([a, b], axis=1).dropna()
    if higher is None or d.empty:
        return float("nan")
    better = d.iloc[:, 0] > d.iloc[:, 1] if higher else d.iloc[:, 0] < d.iloc[:, 1]
    return float(better.mean())
