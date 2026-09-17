"""Einheitliche Zahlenformate (deutsch: 1.234,5 %)."""
from __future__ import annotations

import math

PCT_METRICS = {"Total Return", "CAGR", "Volatilität p.a.", "Max. Drawdown",
               "Jensen's Alpha p.a.", "Up-Capture", "Down-Capture"}
DEC_METRICS = {"Sharpe Ratio", "Calmar", "Beta"}

LABELS = {"Calmar": "Calmar Ratio"}


def _de(s: str) -> str:
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v, digits: int = 1, signed: bool = False) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "–"
    txt = f"{v * 100:,.{digits}f}"
    if float(txt.replace(",", "")) == 0:
        txt = txt.lstrip("-")
    sign = "+" if signed and not txt.startswith("-") and float(txt.replace(",", "")) != 0 else ""
    return f"{sign}{_de(txt)} %"


def dec(v, digits: int = 2) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "–"
    txt = f"{v:,.{digits}f}"
    if float(txt.replace(",", "")) == 0:
        txt = txt.lstrip("-")
    return _de(txt)


def by_metric(name: str, v) -> str:
    """Format anhand des Kennzahlnamens; Ratios/Beta/p-Werte dezimal, Rest Prozent."""
    n = str(name)
    if n in DEC_METRICS or any(k in n for k in ("Sharpe", "Beta", "Calmar", "p-Wert")):
        return dec(v)
    return pct(v)


def label(name: str) -> str:
    return LABELS.get(name, name)
