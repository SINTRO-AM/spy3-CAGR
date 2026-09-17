"""Erzeugt den Robustness-Report (Konsole + HTML unter reports/).

    python scripts/run_report.py              # nutzt data/prices.csv oder lädt via yfinance
    python scripts/run_report.py --refresh    # Daten neu laden
    python scripts/run_report.py --cost 10    # bp je Switch
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from spy3 import plots, robustness as rb, metrics as m  # noqa: E402
from spy3.formatting import by_metric  # noqa: E402
from spy3.data import load_prices, prepare_returns  # noqa: E402
from spy3.strategy import StrategyParams, backtest  # noqa: E402


def build(px: pd.DataFrame, cost_bps: float = 10.0):
    rets = prepare_returns(px)
    p = StrategyParams(cost_bps=cost_bps)
    bt = backtest(rets, px["risk_on"], p)
    rf = rets["risk_off"]  # SHY als rf-Proxy (vor 2002: 0 %)
    exposure = bt.position.mean()
    _, beta = m.alpha_beta(bt.ret_pf, bt.ret_bm, rf)
    # Klassisches 60/40: 60 % SPY, 40 % SHY (vor 07/2002 T-Bills), täglich rebalanciert
    mixes = {
        "60/40": rb.static_mix(bt.ret_bm, bt.ret_off, 0.60),
    }
    res = {
        "bt": bt, "mixes": mixes, "exposure": exposure, "beta": beta, "cost_bps": cost_bps,
        "summary": m.summary_table({"SPY3": bt.ret_pf, "SPY3 netto": bt.ret_pf_net,
                                    "S&P 500": bt.ret_bm, **mixes},
                                   bt.ret_bm, rf),
        "attribution": rb.attribution(bt.ret_pf, bt.ret_bm),
        "ex_major": rb.ex_crisis_summary(bt.ret_pf, bt.ret_bm, rf, rb.MAJOR),
        "ex_all": rb.ex_crisis_summary(bt.ret_pf, bt.ret_bm, rf),
        "subperiods": rb.subperiods(bt.ret_pf, bt.ret_bm, rf),
        "yearly": rb.yearly_excess(bt.ret_pf, bt.ret_bm),
        "hit_3y": rb.rolling_hit_rate(bt.ret_pf, bt.ret_bm, 3),
        "hit_5y": rb.rolling_hit_rate(bt.ret_pf, bt.ret_bm, 5),
        "conc_12m": rb.concentration(bt.ret_pf, bt.ret_bm, 12),
        "timing": rb.timing_test(bt.position, bt.ret_bm, bt.ret_off, cost_bps),
        "switches_pa": bt.position.diff().abs().sum() / (len(bt) / m.TD),
        "pre_shy_days": int((rets["risk_off_source"] != "SHY").sum()),
        "perf_fees": float(bt["perf_fee_paid"].sum()),
    }
    return res


def fmt(df: pd.DataFrame) -> str:
    out = df.copy().astype(object)
    for i in df.index:
        out.loc[i] = [by_metric(i, v) if isinstance(v, float) else v for v in df.loc[i]]
    return out.to_string()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--cost", type=float, default=10.0)
    ap.add_argument("--csv", type=Path, default=None,
                    help="eigene CSV mit Spalten Date,risk_on,risk_off")
    a = ap.parse_args()
    px = (pd.read_csv(a.csv, index_col=0, parse_dates=True) if a.csv
          else load_prices(refresh=a.refresh))
    r = build(px, a.cost)
    bt = r["bt"]
    print(f"Zeitraum {bt.index[0].date()} – {bt.index[-1].date()} | "
          f"Ø Aktienquote {r['exposure']:.0%} | Switches p.a. {r['switches_pa']:.1f} | "
          f"Tage mit T-Bill-Näherung statt SHY: {r['pre_shy_days']}\n")
    for k, t in [("Kennzahlen (inkl. 60/40-Portfolio)", "summary"),
                 ("Attribution der Log-Überschussrendite", "attribution"),
                 ("Ohne Dotcom & GFC", "ex_major"), ("Ohne alle Krisenfenster", "ex_all"),
                 ("Teilperioden", "subperiods"), ("Jahresrenditen", "yearly")]:
        print(f"== {k} ==\n{fmt(r[t])}\n")
    print(f"Anteil rollierender 3J-Fenster mit Outperformance: {r['hit_3y']:.0%}")
    print(f"Anteil rollierender 5J-Fenster mit Outperformance: {r['hit_5y']:.0%}")
    print(f"Anteil der Überschussrendite aus den 12 besten Monaten: {r['conc_12m']:.0%}")
    print("Zufalls-Timing-Test:", {k: round(v, 3) for k, v in r["timing"].items()})

    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    figs = [plots.wealth_chart(bt, r["mixes"]), plots.drawdown_chart(bt), plots.alpha_chart(bt),
            plots.relative_chart(bt), plots.rolling_excess_chart(bt)]
    with open(out / "robustness_report.html", "w", encoding="utf-8") as f:
        f.write("<html><head><meta charset='utf-8'><title>SPY3 Robustness</title></head><body>")
        for i, fig in enumerate(figs):
            f.write(fig.to_html(full_html=False, include_plotlyjs="cdn" if i == 0 else False))
        for k in ["summary", "attribution", "ex_major", "subperiods", "yearly"]:
            f.write(f"<h3>{k}</h3>" + r[k].to_html(float_format=lambda v: f"{v:,.3f}"))
        f.write("</body></html>")
    print(f"\nReport: {out / 'robustness_report.html'}")


if __name__ == "__main__":
    main()
