"""Prüft, welche Quelle das Risk-Off-Bein vor SHY verwendet, und beziffert den Effekt.

    python scripts/check_risk_off.py            # Daten aus dem Cache / yfinance
    python scripts/check_risk_off.py --csv x.csv

Rechnet den Backtest zweimal: mit data/luattruu.csv (Bloomberg-Treasury-Index) und
mit der T-Bill-Näherung, und stellt die Kennzahlen gegenüber.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from spy3 import metrics as m  # noqa: E402
from spy3.data import (TREASURY_FILE, load_prices, load_short_treasury_returns,  # noqa: E402
                       load_treasury_index, prepare_returns)
from spy3.strategy import StrategyParams, backtest  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=None)
    ap.add_argument("--treasury", type=Path, default=None,
                    help="Pfad zur Bloomberg-Datei (Standard: data/luattruu.csv)")
    a = ap.parse_args()
    if a.treasury:
        os.environ["SPY3_TREASURY_FILE"] = str(a.treasury)
    px = (pd.read_csv(a.csv, index_col=0, parse_dates=True) if a.csv else load_prices())

    path = Path(os.environ.get("SPY3_TREASURY_FILE", TREASURY_FILE))
    tr = load_treasury_index(path)
    print(f"Treasury-Datei: {path} -> {'gefunden' if path.exists() else 'FEHLT'}")
    if path.exists() and not len(tr):
        print("  Datei vorhanden, aber keine Datenzeile erkannt. Erste Zeilen:")
        from spy3.data import _read_text_any
        for line in _read_text_any(path).splitlines()[:5]:
            print("   |", line[:80])
    elif len(tr):
        mode = ("aus Log-Renditen rekonstruiert" if tr.attrs.get("mode") == "returns"
                else "Kurse (PX_LAST)")
        print(f"  {len(tr)} Werte gelesen ({mode}), {tr.index[0].date()} bis {tr.index[-1].date()}")
    else:
        print("  Bitte den Bloomberg-Export unter diesem Pfad ablegen oder mit --treasury angeben.")
    cand = sorted(p for p in path.parent.glob("*") if "luattruu" in p.name.lower())
    if not path.exists() and cand:
        print("  Ähnliche Dateien im Ordner:", ", ".join(p.name for p in cand))

    runs = {}
    proxy = load_short_treasury_returns()
    if len(proxy):
        print(f"\nSHY-Proxy (1–3 Jahre): {proxy.attrs.get('source')}, "
              f"{proxy.index[0].date()} bis {proxy.index[-1].date()} -> hat Vorrang vor dem Index")
    else:
        print("\nKein SHY-Proxy (weder data/lt01truu.csv noch data/fred_yields.csv); "
              "python scripts/check_shy_proxy.py lädt die FRED-Renditen.")
    for label, treasury in (("aktuelle Konfiguration", tr),
                            ("T-Bill-Näherung", pd.Series(dtype=float))):
        rets = prepare_returns(px, treasury=treasury,
                               proxy=None if label != "T-Bill-Näherung" else pd.Series(dtype=float))
        bt = backtest(rets, px["risk_on"], StrategyParams())
        runs[label] = bt
        src = rets.loc[rets.index < "2002-07-30", "risk_off_source"].value_counts().to_dict()
        print(f"\n[{label}] Quellen vor 30.07.2002: {src}")
        off = bt[(bt.position == 0) & (bt.index < "2002-07-30")]
        leg = (1 + off.ret_off).prod() - 1 if len(off) else float("nan")
        print(f"  Risk-Off-Tage vor SHY: {len(off)} | Rendite des Risk-Off-Beins dort: {leg:.2%}")

    a_, b_ = runs["aktuelle Konfiguration"], runs["T-Bill-Näherung"]
    rows = {
        "Total Return": (m.total_return(a_.ret_pf), m.total_return(b_.ret_pf)),
        "CAGR": (m.cagr(a_.ret_pf), m.cagr(b_.ret_pf)),
        "Volatilität": (m.ann_vol(a_.ret_pf), m.ann_vol(b_.ret_pf)),
        "Sharpe": (m.sharpe(a_.ret_pf), m.sharpe(b_.ret_pf)),
        "Max. Drawdown": (m.max_drawdown(a_.ret_pf), m.max_drawdown(b_.ret_pf)),
        "Endwert 1.000 USD": (1000 * (1 + a_.ret_pf).prod(), 1000 * (1 + b_.ret_pf).prod()),
    }
    print(f"\n{'Kennzahl':20s} {'aktuell':>16s} {'T-Bill':>12s} {'Differenz':>12s}")
    for k, (x, y) in rows.items():
        if k == "Endwert 1.000 USD":
            print(f"{k:20s} {x:16,.0f} {y:12,.0f} {x - y:12,.0f}")
        elif k == "Sharpe":
            print(f"{k:20s} {x:16.2f} {y:12.2f} {x - y:12.2f}")
        else:
            print(f"{k:20s} {x:16.2%} {y:12.2%} {x - y:12.2%}")
    same = np.allclose(a_.ret_pf.to_numpy(), b_.ret_pf.to_numpy())
    print("\nErgebnis:", "IDENTISCH – weder Proxy noch Treasury-Datei werden verwendet!" if same
          else "die aktuelle Konfiguration weicht von der T-Bill-Näherung ab.")


if __name__ == "__main__":
    main()
