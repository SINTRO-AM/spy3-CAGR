"""Lädt die FRED-Renditen (DGS1/DGS2/DGS3), baut den SHY-Proxy und prüft ihn gegen
den echten SHY ab 07/2002. Danach steht der Proxy dem Backtest zur Verfügung.

    python scripts/check_shy_proxy.py            # lädt FRED (einmalig) und vergleicht
    python scripts/check_shy_proxy.py --refresh  # FRED neu laden
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
from spy3.data import (FRED_FILE, SHORT_TREASURY_FILE, load_fred_yields, load_prices,  # noqa: E402
                       load_short_treasury_returns)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()

    if SHORT_TREASURY_FILE.exists():
        print(f"Bloomberg 1-3y-Index gefunden: {SHORT_TREASURY_FILE} (hat Vorrang)")
    y = load_fred_yields(refresh=a.refresh)
    if y.empty:
        print("FRED-Renditen nicht verfügbar (kein Netz?). Datei:", FRED_FILE)
    else:
        print(f"FRED-Renditen: {y.index[0].date()} bis {y.index[-1].date()}, "
              f"Spalten {list(y.columns)}")
    proxy = load_short_treasury_returns()
    if proxy.empty:
        print("Kein SHY-Proxy verfügbar.")
        return
    print(f"SHY-Proxy: Quelle {proxy.attrs.get('source')}, "
          f"{proxy.index[0].date()} bis {proxy.index[-1].date()}")

    px = load_prices()
    shy = px["risk_off"].pct_change().dropna()
    both = pd.concat([shy.rename("SHY"), proxy.rename("Proxy")], axis=1).dropna()
    if len(both) < 250:
        print("Zu wenig Überlappung mit SHY für einen Vergleich.")
        return
    a_, b_ = both["SHY"], both["Proxy"]
    print(f"\nVergleich mit dem echten SHY ({both.index[0].date()} bis {both.index[-1].date()}, "
          f"{len(both)} Tage):")
    print(f"  CAGR       SHY {m.cagr(a_):.2%} | Proxy {m.cagr(b_):.2%}")
    print(f"  Vol p.a.   SHY {m.ann_vol(a_):.2%} | Proxy {m.ann_vol(b_):.2%}")
    print(f"  Max DD     SHY {m.max_drawdown(a_):.2%} | Proxy {m.max_drawdown(b_):.2%}")
    print(f"  Korrelation Tagesrenditen: {a_.corr(b_):.3f}")
    mo = both.resample("ME").apply(lambda s: (1 + s).prod() - 1)
    print(f"  Korrelation Monatsrenditen: {mo['SHY'].corr(mo['Proxy']):.3f}")
    print(f"  Tracking Error p.a.: {(a_ - b_).std() * np.sqrt(252):.2%}")

    pre = proxy.loc["2000-01-03":"2002-07-29"]
    w = (1 + pre).cumprod()
    print(f"\nProxy im Ersatzzeitraum 03.01.2000–29.07.2002: Total Return {w.iloc[-1] - 1:.2%}, "
          f"CAGR {m.cagr(pre):.2%}, Vol {m.ann_vol(pre):.2%}, Max DD {m.max_drawdown(pre):.2%}")


if __name__ == "__main__":
    main()
