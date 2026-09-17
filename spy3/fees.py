"""Gebühren: Managementgebühr und Performancegebühr.

Performancegebühr (Standardausgestaltung)
* Satz 10 % auf die Wertentwicklung über der Referenz
* Referenz = max(High-Water-Mark, Hurdle); Hurdle = HWM fortgeschrieben mit der
  Total-Return-Entwicklung des SPY seit der letzten Gebührenzahlung
* Tägliche Abgrenzung im NAV, Kristallisierung zum Quartalsende
* Minderperformance wird vorgetragen: HWM und Hurdle-Startpunkt werden nur
  zurückgesetzt, wenn tatsächlich eine Gebühr kristallisiert
* Managementgebühr wird täglich vor der Performancegebühr abgegrenzt
Modelliert wird ein Anteil, der zum Start des Backtests gezeichnet wurde.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def apply_fees(gross: pd.Series, bm: pd.Series, mgmt_fee: float = 0.002,
               perf_fee: float = 0.10, freq: str = "QE") -> pd.DataFrame:
    """gross/bm: einfache Tagesrenditen. Rückgabe: ret_net, nav_net, perf_fee_paid."""
    daily_mgmt = (1 + mgmt_fee) ** (1 / 252) - 1
    idx = gross.index
    period = idx.to_period(freq.replace("E", ""))
    is_end = np.r_[period[1:] != period[:-1], True]   # letzter Tag je Quartal

    g = gross.to_numpy()
    b = bm.to_numpy()
    nav_pre = 1.0          # NAV nach Mgmt-Gebühr, vor Abgrenzung der Perf.-Gebühr
    hwm = 1.0
    hurdle = 1.0           # HWM fortgeschrieben mit SPY
    nav_net = np.empty(len(g))
    paid = np.zeros(len(g))
    for i in range(len(g)):
        nav_pre *= (1 + g[i]) / (1 + daily_mgmt)
        hurdle *= 1 + b[i]
        ref = max(hwm, hurdle)
        accrued = perf_fee * max(nav_pre - ref, 0.0)
        nav_net[i] = nav_pre - accrued
        if is_end[i] and accrued > 0:
            paid[i] = accrued
            nav_pre -= accrued
            hwm = nav_pre
            hurdle = nav_pre
    nav = pd.Series(nav_net, index=idx)
    ret = nav.pct_change()
    ret.iloc[0] = nav.iloc[0] - 1
    return pd.DataFrame({"ret_net": ret, "nav_net": nav, "perf_fee_paid": paid}, index=idx)
