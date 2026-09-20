"""Robustheits-Audit des SPY3-Backtests auf den geladenen Daten.

    python scripts/audit.py              # Cache / yfinance
    python scripts/audit.py --csv x.csv  # eigene Kursdatei (Date, risk_on, risk_off[, tbill_yield])

Prüft: Ausführungsverzögerung, Kosten, Faktor-Ablation, Zufalls-Timing, Parameter-
Landschaft, Walk-Forward, Deflated Sharpe Ratio, Teilperioden und Attribution.
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, norm, skew

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

from spy3 import metrics as m, robustness as rb  # noqa: E402
from spy3.data import load_prices, prepare_returns  # noqa: E402
from spy3.strategy import StrategyParams, backtest  # noqa: E402


def line(name, r):
    print(f"  {name:38s} CAGR {m.cagr(r):6.2%}  Sharpe {m.sharpe(r):5.2f}  "
          f"MaxDD {m.max_drawdown(r):6.1%}  TR {m.total_return(r):6.0%}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=None)
    ap.add_argument("--start", default="2000-01-03")
    ap.add_argument("--n-random", type=int, default=200)
    a = ap.parse_args()
    px = (pd.read_csv(a.csv, index_col=0, parse_dates=True) if a.csv else load_prices())
    rets = prepare_returns(px)
    price = px["risk_on"]
    S = a.start

    def run(p=StrategyParams(), lag=1):
        bt = backtest(rets, price, p)
        if lag != 1:
            pos = bt.signal.shift(lag).fillna(0).astype(int)
            cost = pos.diff().fillna(0).ne(0) * p.cost_bps / 1e4
            bt = bt.assign(position=pos, ret_pf=pos * bt.ret_bm + (1 - pos) * bt.ret_off - cost)
        return bt.loc[S:]

    base = run()
    print(f"Zeitraum {base.index[0].date()} – {base.index[-1].date()} | Risk-Off-Quellen: "
          f"{rets.loc[S:, 'risk_off_source'].value_counts().to_dict()}")
    line("SPY3 brutto (Basis)", base.ret_pf); line("S&P 500", base.ret_bm)
    sw = base.position.diff().abs().sum()
    print(f"  investiert {base.position.mean():.1%} der Tage, {sw / (len(base) / 252):.1f} Switches p.a.")

    print("\n[1] Ausführungsverzögerung")
    line("Handel am Schluss des Signaltags", base.ret_pf)
    line("Handel einen Tag später", run(lag=2).ret_pf)
    line("Handel zwei Tage später", run(lag=3).ret_pf)

    print("\n[2] Handelskosten je Switch")
    for c in (1, 10, 25, 50):
        line(f"{c} bp", run(StrategyParams(cost_bps=c)).ret_pf)

    print("\n[3] Faktor-Ablation")
    line("ohne Mean-Reversion", run(StrategyParams(dd_trigger=999)).ret_pf)
    line("ohne Low-Vol-Regel", run(StrategyParams(var_low=0.0)).ret_pf)
    line("ohne VaR-Veto", run(StrategyParams(var_high=1.0)).ret_pf)
    line("nur Momentum", run(StrategyParams(dd_trigger=999, var_low=0.0, var_high=1.0)).ret_pf)

    print("\n[4] Zufalls-Timing (Signal zirkulär verschoben)")
    tt = rb.timing_test(base.position, base.ret_bm, base.ret_off, 10, n=500)
    print(f"  Sharpe {tt['Sharpe Strategie']:.2f} vs. Median Zufall {tt['Sharpe Zufalls-Timing (Median)']:.2f}, "
          f"p = {tt['p-Wert Sharpe']:.3f}")

    print("\n[5] Parameter-Landschaft (Sharpe)")
    tbl = pd.Series({(f, s): m.sharpe(run(StrategyParams(fast_ma=f, slow_ma=s)).ret_pf)
                     for f in (10, 20, 29, 40, 50) for s in (100, 150, 198, 250, 300)}).unstack()
    print("  MA schnell \\ langsam"); print(tbl.round(2).to_string())
    tbl = pd.DataFrame({w: {h: m.sharpe(run(StrategyParams(vol_window=w, var_high=h)).ret_pf)
                            for h in (0.035, 0.045, 0.05, 0.06, 0.07)} for w in (20, 30, 50, 90, 120)}).T
    print("  VaR-Fenster \\ Risk-Off-Schwelle"); print(tbl.round(2).to_string())

    rng = np.random.default_rng(0)
    trials = []
    for _ in range(a.n_random):
        kw = dict(fast_ma=int(rng.integers(10, 60)), slow_ma=int(rng.integers(120, 300)),
                  vol_window=int(rng.integers(20, 120)), var_high=float(rng.uniform(0.035, 0.07)),
                  var_low=float(rng.uniform(0.012, 0.03)), dd_trigger=float(rng.uniform(1.15, 1.5)))
        trials.append(run(StrategyParams(**kw)).ret_pf)
    srs = np.array([m.sharpe(t) for t in trials])
    print(f"  {a.n_random} zufällige Parametersätze: Sharpe Median {np.median(srs):.2f}, "
          f"P10–P90 {np.percentile(srs, 10):.2f}–{np.percentile(srs, 90):.2f}, Max {srs.max():.2f}; "
          f"Basis {m.sharpe(base.ret_pf):.2f} (Perzentil {(srs < m.sharpe(base.ret_pf)).mean():.0%})")

    print("\n[6] Walk-Forward (Parameter auf Training gewählt, auf Test bewertet)")
    grid = [dict(fast_ma=f, slow_ma=s, vol_window=w, dd_trigger=d)
            for f in (15, 29, 45) for s in (150, 198, 250) for w in (30, 50, 90) for d in (1.2, 1.3, 1.4)]
    bts = {tuple(sorted(g.items())): backtest(rets, price, StrategyParams(**g)) for g in grid}
    mid = base.index[len(base) // 2]
    for (t0, t1, v0, v1) in ((base.index[0], mid, mid, base.index[-1]),):
        best_k, best_bt = max(bts.items(), key=lambda kv: m.sharpe(kv[1].ret_pf.loc[t0:t1]))
        g = dict(best_k)
        print(f"  Training {t0.date()}–{t1.date()}: beste Parameter {g['fast_ma']}/{g['slow_ma']}, "
              f"VaR {g['vol_window']}d, DD {g['dd_trigger']}")
        print(f"  Test {v0.date()}–{v1.date()}: Sharpe gewählt {m.sharpe(best_bt.ret_pf.loc[v0:v1]):.2f} | "
              f"Basisparameter {m.sharpe(base.ret_pf.loc[v0:v1]):.2f} | S&P 500 {m.sharpe(base.ret_bm.loc[v0:v1]):.2f}")

    print("\n[7] Deflated Sharpe Ratio (Bailey & López de Prado)")
    r = base.ret_pf; T = len(r); sr_d = r.mean() / r.std(ddof=1)
    tr_d = np.array([t.mean() / t.std(ddof=1) for t in trials]); v = tr_d.var(ddof=1)
    g3, g4 = skew(r), kurtosis(r, fisher=False)
    for N in (100, 1000):
        e_max = np.sqrt(v) * ((1 - np.euler_gamma) * norm.ppf(1 - 1 / N)
                              + np.euler_gamma * norm.ppf(1 - 1 / (N * np.e)))
        z = (sr_d - e_max) * np.sqrt(T - 1) / np.sqrt(1 - g3 * sr_d + (g4 - 1) / 4 * sr_d ** 2)
        print(f"  N={N:5d} Varianten: erwartetes Max-Sharpe {e_max * np.sqrt(252):.2f}, "
              f"DSR = {norm.cdf(z):.3f}")

    print("\n[8] Attribution der Log-Überschussrendite")
    print(rb.attribution(base.ret_pf, base.ret_bm).round(3).to_string())
    print(f"  Trefferquote rollierender 5J-Fenster: {rb.rolling_hit_rate(base.ret_pf, base.ret_bm, 5):.0%}")


if __name__ == "__main__":
    main()
