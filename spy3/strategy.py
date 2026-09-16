"""SPY3-Signal und Backtest.

Signal-Logik 1:1 aus SPY3_Dash_web übernommen (Risk / Momentum / Mean-Reversion).
Korrigiert gegenüber dem alten Code:
  * Transaktionskosten fallen genau einmal pro Positionswechsel an
    (alt: Vergleich Signal(t) vs. Signal(t-2) -> Kosten an zwei Tagen, Timing verschoben)
  * Kostensatz konfigurierbar; Default 10 bp je Switch (wie im Deck angegeben;
    alter Code rechnete 1 bp)
  * Portfoliorenditen werden als einfache Renditen gerechnet und erst für Charts
    in Log-Renditen umgewandelt.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import norm


@dataclass(frozen=True)
class StrategyParams:
    fast_ma: int = 29           # Legacy-Werte aus SPY3_Dash_web (≈30/200)
    slow_ma: int = 198
    vol_window: int = 50
    var_conf: float = 0.99
    var_high: float = 0.05      # Risk-Off, wenn 1d-VaR darüber
    var_low: float = 0.02       # "Low Vol" -> immer investiert
    dd_trigger: float = 1.3     # Preis < 200d-Hoch / 1.3  (≈ -23 %) -> Mean-Reversion
    dd_window: int = 200
    cost_bps: float = 10.0      # je Positionswechsel


def compute_signal(price: pd.Series, p: StrategyParams = StrategyParams()) -> pd.DataFrame:
    """Signal am Tagesende t (1 = SPY, 0 = SHY). Gehandelt wird ab t+1."""
    logret = np.log(price / price.shift(1))
    out = pd.DataFrame(index=price.index)
    out["ma_fast"] = price.rolling(p.fast_ma).mean()
    out["ma_slow"] = price.rolling(p.slow_ma).mean()
    out["var_1d"] = logret.rolling(p.vol_window).std() * norm.ppf(p.var_conf)
    out["high_disc"] = price.rolling(p.dd_window).max() / p.dd_trigger

    momentum = out["ma_fast"] > out["ma_slow"]
    low_vol = out["var_1d"] < p.var_low
    mean_rev = price < out["high_disc"]
    risk_ok = out["var_1d"] < p.var_high
    out["signal"] = (risk_ok & (momentum | low_vol | mean_rev)).astype(int)
    return out


def backtest(returns: pd.DataFrame, price: pd.Series,
             p: StrategyParams = StrategyParams()) -> pd.DataFrame:
    """returns: Spalten risk_on / risk_off (einfache Renditen), Index = Handelstage."""
    sig = compute_signal(price, p).reindex(returns.index)
    bt = sig.copy()
    bt["position"] = sig["signal"].shift(1).fillna(0).astype(int)   # kein Look-ahead
    switched = bt["position"].diff().fillna(0).ne(0)
    bt["cost"] = switched * p.cost_bps / 1e4
    bt["ret_bm"] = returns["risk_on"]
    bt["ret_off"] = returns["risk_off"]
    bt["ret_pf"] = (bt["position"] * bt["ret_bm"]
                    + (1 - bt["position"]) * bt["ret_off"] - bt["cost"])
    bt["wealth_pf"] = (1 + bt["ret_pf"]).cumprod()
    bt["wealth_bm"] = (1 + bt["ret_bm"]).cumprod()
    return bt
