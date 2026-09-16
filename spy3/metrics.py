"""Kennzahlen – geometrisch korrekt und mit Risikofreiem Satz.

Alter Code: 'Total Return' = Summe der Log-Renditen (z. B. 3.50 -> als "350 %"
ausgewiesen; tatsächlich exp(3.50)-1 ≈ 3.200 %), 'Annualized Return' = mittlere
Log-Rendite, Sharpe ohne risikofreien Satz, Drawdown in Log-Punkten.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TD = 252


def total_return(r: pd.Series) -> float:
    return float((1 + r).prod() - 1)


def cagr(r: pd.Series) -> float:
    n = len(r)
    return float((1 + r).prod() ** (TD / n) - 1) if n else np.nan


def ann_vol(r: pd.Series) -> float:
    return float(r.std(ddof=1) * np.sqrt(TD))


def sharpe(r: pd.Series, rf: pd.Series | float = 0.0) -> float:
    ex = r - rf
    sd = ex.std(ddof=1)
    return float(ex.mean() / sd * np.sqrt(TD)) if sd > 0 else np.nan


def drawdown(r: pd.Series) -> pd.Series:
    w = (1 + r).cumprod()
    return w / w.cummax() - 1


def max_drawdown(r: pd.Series) -> float:
    return float(drawdown(r).min())


def alpha_beta(r: pd.Series, bm: pd.Series, rf: pd.Series | float = 0.0) -> tuple[float, float]:
    """OLS auf tägliche Überschussrenditen. Alpha annualisiert (arithmetisch)."""
    y = (r - rf).to_numpy()
    x = (bm - rf).to_numpy()
    beta = np.cov(x, y, ddof=1)[0, 1] / np.var(x, ddof=1)
    alpha = (y.mean() - beta * x.mean()) * TD
    return float(alpha), float(beta)


def capture(r: pd.Series, bm: pd.Series, freq: str = "ME") -> tuple[float, float]:
    """Up-/Down-Capture auf Monatsbasis."""
    m = pd.DataFrame({"r": r, "bm": bm}).resample(freq).apply(lambda s: (1 + s).prod() - 1)
    up, dn = m[m.bm > 0], m[m.bm < 0]
    upc = up.r.mean() / up.bm.mean() if len(up) else np.nan
    dnc = dn.r.mean() / dn.bm.mean() if len(dn) else np.nan
    return float(upc), float(dnc)


def summary(r: pd.Series, bm: pd.Series, rf: pd.Series | float = 0.0) -> dict:
    a, b = alpha_beta(r, bm, rf)
    upc, dnc = capture(r, bm)
    return {
        "Total Return": total_return(r),
        "CAGR": cagr(r),
        "Volatilität p.a.": ann_vol(r),
        "Sharpe (ex rf)": sharpe(r, rf),
        "Max. Drawdown": max_drawdown(r),
        "Calmar": cagr(r) / abs(max_drawdown(r)) if max_drawdown(r) < 0 else np.nan,
        "Beta": b,
        "Jensen's Alpha p.a.": a,
        "Up-Capture": upc,
        "Down-Capture": dnc,
    }


def summary_table(cols: dict[str, pd.Series], bm: pd.Series,
                  rf: pd.Series | float = 0.0) -> pd.DataFrame:
    return pd.DataFrame({k: summary(v, bm, rf) for k, v in cols.items()})
