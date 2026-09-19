"""Prüft, welche Quelle das Risk-Off-Bein vor SHY verwendet, und beziffert den Effekt.

    python scripts/check_risk_off.py            # Daten aus dem Cache / yfinance
    python scripts/check_risk_off.py --csv x.csv

Rechnet den Backtest zweimal: mit data/luattruu.csv (Bloomberg-Treasury-Index) und
mit der T-Bill-Näherung, und stellt die Kennzahlen gegenüber.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from spy3 import metrics as m  # noqa: E402
from spy3.data import TREASURY_FILE, load_prices, load_treasury_index, prepare_returns  # noqa: E402
from spy3.strategy import StrategyParams, backtest  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=None)
    a = ap.parse_args()
    px = (pd.read_csv(a.csv, index_col=0, parse_dates=True) if a.csv else load_prices())

    tr = load_treasury_index()
    print(f"Treasury-Datei: {TREASURY_FILE} -> {'gefunden' if TREASURY_FILE.exists() else 'FEHLT'}")
    if len(tr):
        print(f"  {len(tr)} Kurse gelesen, {tr.index[0].date()} bis {tr.index[-1].date()}")
    else:
        print("  keine verwertbaren Zeilen (Format: dd.mm.yyyy<TAB>Kurs, Dezimalkomma erlaubt)")

    runs = {}
    for label, treasury in (("Treasury-Index", None), ("T-Bill-Näherung", pd.Series(dtype=float))):
        rets = prepare_returns(px, treasury=treasury)
        bt = backtest(rets, px["risk_on"], StrategyParams())
        runs[label] = bt
        src = rets.loc[rets.index < "2002-07-30", "risk_off_source"].value_counts().to_dict()
        print(f"\n[{label}] Quellen vor 30.07.2002: {src}")
        off = bt[(bt.position == 0) & (bt.index < "2002-07-30")]
        leg = (1 + off.ret_off).prod() - 1 if len(off) else float("nan")
        print(f"  Risk-Off-Tage vor SHY: {len(off)} | Rendite des Risk-Off-Beins dort: {leg:.2%}")

    a_, b_ = runs["Treasury-Index"], runs["T-Bill-Näherung"]
    rows = {
        "Total Return": (m.total_return(a_.ret_pf), m.total_return(b_.ret_pf)),
        "CAGR": (m.cagr(a_.ret_pf), m.cagr(b_.ret_pf)),
        "Volatilität": (m.ann_vol(a_.ret_pf), m.ann_vol(b_.ret_pf)),
        "Sharpe": (m.sharpe(a_.ret_pf), m.sharpe(b_.ret_pf)),
        "Max. Drawdown": (m.max_drawdown(a_.ret_pf), m.max_drawdown(b_.ret_pf)),
        "Endwert 1.000 USD": (1000 * (1 + a_.ret_pf).prod(), 1000 * (1 + b_.ret_pf).prod()),
    }
    print(f"\n{'Kennzahl':20s} {'Treasury-Index':>16s} {'T-Bill':>12s} {'Differenz':>12s}")
    for k, (x, y) in rows.items():
        if k == "Endwert 1.000 USD":
            print(f"{k:20s} {x:16,.0f} {y:12,.0f} {x - y:12,.0f}")
        elif k == "Sharpe":
            print(f"{k:20s} {x:16.2f} {y:12.2f} {x - y:12.2f}")
        else:
            print(f"{k:20s} {x:16.2%} {y:12.2%} {x - y:12.2%}")
    same = np.allclose(a_.ret_pf.to_numpy(), b_.ret_pf.to_numpy())
    print("\nErgebnis:", "IDENTISCH – die Treasury-Datei wird nicht verwendet!" if same
          else "die beiden Läufe unterscheiden sich, die Datei greift.")


if __name__ == "__main__":
    main()
