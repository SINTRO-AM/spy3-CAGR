"""Zahlenformate je Sprache (de: 1.234,5 % / en: 1,234.5%)."""
from __future__ import annotations

import math

DEC_KEYS = ("Sharpe", "Beta", "Calmar", "p-Wert")


def _loc(s: str, lang: str) -> str:
    if lang != "de":
        return s
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _de(s: str) -> str:  # Rückwärtskompatibilität
    return _loc(s, "de")


def _nan(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def _num(v: float, digits: int) -> str:
    txt = f"{v:,.{digits}f}"
    if float(txt.replace(",", "")) == 0:
        txt = txt.lstrip("-")
    return txt


def pct(v, digits: int = 1, signed: bool = False, lang: str = "de") -> str:
    if _nan(v):
        return "–"
    txt = _num(v * 100, digits)
    if signed and not txt.startswith("-") and float(txt.replace(",", "")) != 0:
        txt = "+" + txt
    txt = _loc(txt, lang)
    return f"{txt} %" if lang == "de" else f"{txt}%"


def dec(v, digits: int = 2, lang: str = "de") -> str:
    return "–" if _nan(v) else _loc(_num(v, digits), lang)


def by_metric(name: str, v, lang: str = "de") -> str:
    """Ratios, Beta und p-Werte dezimal, alles andere in Prozent."""
    return dec(v, lang=lang) if any(k in str(name) for k in DEC_KEYS) else pct(v, lang=lang)


def usd(v, lang: str = "de") -> str:
    return f"{_loc(_num(v, 0), lang)} USD"


def label(name: str) -> str:  # Rückwärtskompatibilität
    return {"Calmar": "Calmar Ratio"}.get(name, name)
