"""Aktuelles Signal, laufend aktualisiert.

Das Dashboard rechnet den Backtest einmal beim Start. Das Signal oben rechts soll
dagegen den jeweils letzten Schlusskurs widerspiegeln. Dieses Modul lädt die Kurse
bei Bedarf neu (höchstens alle `REFRESH` Minuten) und berechnet das Signal direkt
aus dem SPY-Kurs – mit derselben Funktion wie der Backtest.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from .strategy import StrategyParams, compute_signal

REFRESH_MIN = 30


@dataclass
class LiveSignal:
    asof: pd.Timestamp          # Schlusskurs, aus dem das Signal stammt
    checked: datetime           # Zeitpunkt der letzten Prüfung
    row: pd.Series              # price, ma_fast, ma_slow, var_1d, high_disc, signal
    reasons: dict               # Einzelbedingungen (bool)


_lock = threading.Lock()
_cache: dict = {}


def _reasons(row: pd.Series, p: StrategyParams) -> dict:
    return {
        "risk_ok": bool(row["var_1d"] < p.var_high),
        "trend": bool(row["ma_fast"] > row["ma_slow"]),
        "calm": bool(row["var_1d"] < p.var_low),
        "dip": bool(row["price"] < row["high_disc"]),
    }


def current_signal(price_loader, p: StrategyParams = StrategyParams(),
                   fallback: pd.Series | None = None) -> LiveSignal:
    """Letztes Signal aus den aktuellen Kursen.

    price_loader(refresh: bool) -> DataFrame mit Spalte risk_on. Beim ersten Aufruf und
    danach höchstens alle REFRESH_MIN Minuten wird mit refresh=True geladen; schlägt das
    fehl (kein Netz), bleibt der letzte Stand bzw. der Cache bestehen.
    """
    now = time.time()
    with _lock:
        fresh = _cache.get("sig") is not None and now - _cache.get("t", 0) < REFRESH_MIN * 60
        if fresh:
            return _cache["sig"]
        price = None
        try:
            price = price_loader(refresh=True)["risk_on"]
        except Exception:
            try:
                price = price_loader(refresh=False)["risk_on"]
            except Exception:
                price = fallback
        if price is None or price.dropna().empty:
            if _cache.get("sig") is not None:
                return _cache["sig"]
            raise RuntimeError("Keine Kursdaten für das aktuelle Signal")
        sig = compute_signal(price.dropna(), p).dropna(subset=["ma_slow", "var_1d"])
        row = sig.iloc[-1]
        out = LiveSignal(asof=sig.index[-1], checked=datetime.now(), row=row,
                         reasons=_reasons(row, p))
        _cache.update(sig=out, t=now)
        return out


def reset_cache() -> None:
    with _lock:
        _cache.clear()
