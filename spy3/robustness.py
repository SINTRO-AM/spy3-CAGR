"""Tests zur Frage des Hedge-Fund-Managers:
"Kommt die Outperformance nur aus 2002 und 2008 – bleibt der Abstand danach gleich?"

Im Log-Raum bedeutet "Abstand bleibt gleich": keine Überschussrendite außerhalb der
Krisen. Die Funktionen hier machen das messbar.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import metrics as m

CRISES = {
    "Dotcom 2000–03": ("2000-01-01", "2003-03-31"),
    "GFC 2007–09": ("2007-10-01", "2009-06-30"),
    "Covid 2020": ("2020-02-15", "2020-06-30"),
    "Inflation 2022": ("2022-01-01", "2022-12-31"),
}
MAJOR = ["Dotcom 2000–03", "GFC 2007–09"]


def excess_log(r: pd.Series, bm: pd.Series) -> pd.Series:
    return np.log1p(r) - np.log1p(bm)


def crisis_mask(idx: pd.DatetimeIndex, names=None) -> pd.Series:
    names = names or list(CRISES)
    mask = pd.Series(False, index=idx)
    for n in names:
        a, b = CRISES[n]
        mask |= (idx >= a) & (idx <= b)
    return mask


def attribution(r: pd.Series, bm: pd.Series) -> pd.DataFrame:
    """Anteil der gesamten Log-Überschussrendite je Krisenfenster und Rest."""
    ex = excess_log(r, bm)
    rows = {}
    for n, (a, b) in CRISES.items():
        rows[n] = ex.loc[a:b].sum()
    rows["Außerhalb aller Krisen"] = ex[~crisis_mask(ex.index)].sum()
    out = pd.Series(rows, name="Log-Überschuss").to_frame()
    total = ex.sum()
    out["Anteil"] = out["Log-Überschuss"] / total if total else np.nan
    out.loc["Gesamt"] = [total, 1.0]
    return out


def ex_crisis_summary(r: pd.Series, bm: pd.Series, rf=0.0, names=None) -> pd.DataFrame:
    """Kennzahlen nur auf Nicht-Krisen-Tagen (Tage aneinandergehängt)."""
    keep = ~crisis_mask(r.index, names)
    rf_k = rf[keep] if isinstance(rf, pd.Series) else rf
    return m.summary_table({"SPY3": r[keep], "Benchmark": bm[keep]}, bm[keep], rf_k)


def yearly_excess(r: pd.Series, bm: pd.Series) -> pd.DataFrame:
    y = pd.DataFrame({"SPY3": r, "Benchmark": bm}).groupby(r.index.year).apply(
        lambda d: (1 + d).prod() - 1)
    y["Differenz"] = y["SPY3"] - y["Benchmark"]
    return y


def rolling_excess(r: pd.Series, bm: pd.Series, years: int = 5) -> pd.Series:
    """Annualisierte Log-Überschussrendite im rollierenden Fenster."""
    w = years * m.TD
    return excess_log(r, bm).rolling(w).sum() / years


def rolling_hit_rate(r: pd.Series, bm: pd.Series, years: int = 5) -> float:
    s = rolling_excess(r, bm, years).dropna()
    return float((s > 0).mean()) if len(s) else np.nan


def concentration(r: pd.Series, bm: pd.Series, top_k: int = 12) -> float:
    """Anteil der Gesamt-Überschussrendite aus den besten k Monaten."""
    mex = excess_log(r, bm).resample("ME").sum()
    return float(mex.nlargest(top_k).sum() / mex.sum()) if mex.sum() else np.nan


def static_mix(bm: pd.Series, off: pd.Series, weight: float) -> pd.Series:
    """Täglich rebalancierter Mix – fairer Vergleich bei gleicher Aktienquote."""
    return weight * bm + (1 - weight) * off


def timing_test(position: pd.Series, bm: pd.Series, off: pd.Series,
                cost_bps: float = 10.0, n: int = 500, seed: int = 0,
                min_shift: int = 252, rf: pd.Series | float = 0.0) -> dict:
    """Zirkulär verschobenes Signal: gleiche Quote, gleiche Regime-Längen,
    aber zufälliges Timing. p-Wert = Anteil Verschiebungen mit >= Sharpe/CAGR."""
    rng = np.random.default_rng(seed)
    pos = position.to_numpy()
    L = len(pos)

    def run(p):
        c = np.abs(np.diff(p, prepend=p[0])) * cost_bps / 1e4
        return pd.Series(p * bm.to_numpy() + (1 - p) * off.to_numpy() - c, index=bm.index)

    base = run(pos)
    b_sh, b_cg = m.sharpe(base, rf), m.cagr(base)
    shifts = rng.integers(min_shift, L - min_shift, size=n)
    sh, cg = np.empty(n), np.empty(n)
    for i, k in enumerate(shifts):
        s = run(np.roll(pos, k))
        sh[i], cg[i] = m.sharpe(s, rf), m.cagr(s)
    return {
        "Sharpe Strategie": b_sh, "Sharpe Zufalls-Timing (Median)": float(np.median(sh)),
        "p-Wert Sharpe": float((sh >= b_sh).mean()),
        "CAGR Strategie": b_cg, "CAGR Zufalls-Timing (Median)": float(np.median(cg)),
        "p-Wert CAGR": float((cg >= b_cg).mean()),
    }


def subperiods(r: pd.Series, bm: pd.Series, rf=0.0,
               cuts=("2000", "2010", "2020")) -> pd.DataFrame:
    edges = [pd.Timestamp(c) for c in cuts] + [r.index[-1] + pd.Timedelta(days=1)]
    rows = {}
    for a, b in zip(edges[:-1], edges[1:]):
        sl = (r.index >= a) & (r.index < b)
        if sl.sum() < m.TD:
            continue
        rf_s = rf[sl] if isinstance(rf, pd.Series) else rf
        label = f"{a.year}–{min(b.year - 1, r.index[-1].year)}"
        rows[label] = {
            "CAGR SPY3": m.cagr(r[sl]), "CAGR BM": m.cagr(bm[sl]),
            "Sharpe SPY3": m.sharpe(r[sl]), "Sharpe BM": m.sharpe(bm[sl]),
            "MaxDD SPY3": m.max_drawdown(r[sl]), "MaxDD BM": m.max_drawdown(bm[sl]),
        }
    return pd.DataFrame(rows)
