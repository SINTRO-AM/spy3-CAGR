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

from .fees import apply_fees


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
    exec_delay: int = 0         # Handelstage zwischen Signal-Schlusskurs und Ausführung.
                                # 0 = Signal aus der Schlussauktion, Ausführung zum selben
                                #     Schlusskurs (Näherung, in der Praxis nur mit Indikations-
                                #     preis kurz vor Schluss erreichbar)
                                # 1 = Market-on-Close am Folgetag (konservative Untergrenze)
    mgmt_fee: float = 0.002     # Managementgebühr p.a., täglich abgegrenzt
    perf_fee: float = 0.10      # Performancegebühr (HWM, Hurdle SPY, quartalsweise)


def compute_signal(price: pd.Series, p: StrategyParams = StrategyParams()) -> pd.DataFrame:
    """Signal am Tagesende t (1 = SPY, 0 = SHY); nur Daten bis einschließlich t."""
    logret = np.log(price / price.shift(1))
    out = pd.DataFrame(index=price.index)
    out["price"] = price
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
    # Signal am Schluss von t, Ausführung am Schluss von t+exec_delay, Wirkung ab t+exec_delay+1
    bt["position"] = sig["signal"].shift(1 + p.exec_delay).fillna(0).astype(int)
    switched = bt["position"].diff().fillna(0).ne(0)
    bt["cost"] = switched * p.cost_bps / 1e4
    bt["ret_bm"] = returns["risk_on"]
    bt["ret_off"] = returns["risk_off"]
    if "risk_off_source" in returns:
        bt["risk_off_source"] = returns["risk_off_source"]
    if "treasury" in returns:
        bt["treasury"] = returns["treasury"]
    bt["ret_pf"] = (bt["position"] * bt["ret_bm"]
                    + (1 - bt["position"]) * bt["ret_off"] - bt["cost"])
    fees = apply_fees(bt["ret_pf"], bt["ret_bm"], p.mgmt_fee, p.perf_fee)
    bt["ret_pf_net"] = fees["ret_net"]
    bt["perf_fee_paid"] = fees["perf_fee_paid"]
    bt["wealth_pf"] = (1 + bt["ret_pf"]).cumprod()
    bt["wealth_bm"] = (1 + bt["ret_bm"]).cumprod()
    return bt


ON, NEUTRAL, OFF = "Risk On", "Neutral", "Risk Off"


def factor_states(row: pd.Series, p: StrategyParams = StrategyParams()) -> dict[str, dict]:
    """Zustand der drei Faktoren am Tagesende.

    Risk (VaR):      > var_high -> Risk Off (Veto), < var_low -> Risk On, sonst Neutral
    Momentum:        schneller MA über langsamem -> Risk On, sonst Risk Off
    Mean-Reversion:  Kurs unter 200d-Hoch / dd_trigger -> Risk On, sonst Neutral
    """
    var = row["var_1d"]
    risk = OFF if var >= p.var_high else ON if var < p.var_low else NEUTRAL
    mom = ON if row["ma_fast"] > row["ma_slow"] else OFF
    mr = ON if row["price"] < row["high_disc"] else NEUTRAL
    return {
        "Risk": {"state": risk, "detail": f"1-Tages-VaR {var:.2%}"},
        "Momentum": {"state": mom,
                     "detail": f"MA{p.fast_ma} / MA{p.slow_ma} = {row['ma_fast'] / row['ma_slow'] - 1:+.1%}"},
        "Mean-Reversion": {"state": mr,
                           "detail": f"Abstand zum {p.dd_window}d-Hoch "
                                     f"{row['price'] / (row['high_disc'] * p.dd_trigger) - 1:+.1%}"},
    }
