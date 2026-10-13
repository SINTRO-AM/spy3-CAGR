"""Current SPY3 signal, recomputed from the latest completed close.

The backtest is computed once at start-up; the signal in the header reflects the latest
close. A request never waits for the data provider: the signal is computed from the local
price cache straight away, and fresh prices are fetched in a background thread at most every
REFRESH_MIN minutes. Without network access the last known state remains in place.
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


def _compute(price: pd.Series, p: StrategyParams) -> LiveSignal:
    sig = compute_signal(price.dropna(), p).dropna(subset=["ma_slow", "var_1d"])
    row = sig.iloc[-1]
    return LiveSignal(asof=sig.index[-1], checked=datetime.now(), row=row,
                      reasons=_reasons(row, p))


def _load(price_loader, refresh: bool, fallback):
    try:
        price = price_loader(refresh=refresh)["risk_on"]
        if price is not None and not price.dropna().empty:
            return price
    except Exception:
        pass
    return fallback


def _refresh(price_loader, p: StrategyParams, fallback) -> None:
    """Hintergrund: neue Schlusskurse laden und das Signal aktualisieren."""
    try:
        price = _load(price_loader, True, fallback)
        if price is not None and not price.dropna().empty:
            sig = _compute(price, p)
            with _lock:
                _cache["sig"] = sig
    finally:
        with _lock:
            _cache["t"] = time.time()
            _cache["busy"] = False


def current_signal(price_loader, p: StrategyParams = StrategyParams(),
                   fallback: pd.Series | None = None, background: bool = True) -> LiveSignal:
    """Letztes Signal; blockiert nie auf den Datenanbieter.

    price_loader(refresh: bool) -> DataFrame mit Spalte risk_on. Beim ersten Aufruf wird das
    Signal sofort aus dem lokalen Cache (refresh=False) berechnet; ein Abruf neuer Kurse
    (refresh=True) läuft im Hintergrund, danach höchstens alle REFRESH_MIN Minuten.
    """
    with _lock:
        sig = _cache.get("sig")
        due = time.time() - _cache.get("t", 0.0) >= REFRESH_MIN * 60
        start = due and not _cache.get("busy", False)
        if start:
            _cache["busy"] = True
    if sig is None:
        price = _load(price_loader, False, fallback)
        if price is None or price.dropna().empty:
            with _lock:
                _cache["busy"] = False
            raise RuntimeError("Keine Kursdaten für das aktuelle Signal")
        sig = _compute(price, p)
        with _lock:
            _cache.setdefault("sig", sig)
    if start:
        if background:
            threading.Thread(target=_refresh, args=(price_loader, p, fallback),
                             daemon=True, name="spy3-live-refresh").start()
        else:
            _refresh(price_loader, p, fallback)
            with _lock:
                sig = _cache["sig"]
    return sig


def wait_idle(timeout: float = 30.0) -> None:
    """Wartet, bis ein laufender Hintergrundabruf fertig ist (für Tests)."""
    end = time.time() + timeout
    while time.time() < end:
        with _lock:
            if not _cache.get("busy"):
                return
        time.sleep(0.02)


def reset_cache() -> None:
    with _lock:
        _cache.clear()
