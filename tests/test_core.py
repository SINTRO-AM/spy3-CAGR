import numpy as np
import pandas as pd
import pytest

from spy3 import metrics as m, robustness as rb
from spy3.strategy import StrategyParams, backtest

IDX = pd.bdate_range("2000-01-03", periods=2000)


def _rets(pos, on, off=0.0):
    return pd.DataFrame({"risk_on": on, "risk_off": off}, index=IDX[:len(on)])


def test_total_return_and_cagr_geometric():
    r = pd.Series([0.1, -0.1], index=IDX[:2])
    assert m.total_return(r) == pytest.approx(-0.01)
    r = pd.Series(0.0004, index=IDX[:252])
    assert m.cagr(r) == pytest.approx(1.0004 ** 252 - 1)


def test_max_drawdown_price_based():
    r = pd.Series([0.0, -0.5, 0.5], index=IDX[:3])
    assert m.max_drawdown(r) == pytest.approx(-0.5)


def test_no_lookahead_and_single_cost_per_switch():
    n = 400
    # Preis steigt ruhig -> Signal 1 nach Warm-up; ein Crash-Tag schaltet später ab
    price = pd.Series(100 * np.exp(np.cumsum(np.full(n, 0.0005))), index=IDX[:n])
    rets = price.pct_change().iloc[1:].to_frame("risk_on").assign(risk_off=0.0)
    bt = backtest(rets, price, StrategyParams(cost_bps=10))
    # Position ist das um einen Tag verschobene Signal
    assert (bt.position.iloc[1:].values == bt.signal.shift(1).iloc[1:].values).all()
    switches = bt.position.diff().abs().sum()
    assert bt.cost.sum() == pytest.approx(switches * 0.001)


def test_beta_alpha_on_static_mix():
    rng = np.random.default_rng(1)
    bm = pd.Series(rng.normal(0.0004, 0.01, 2000), index=IDX)
    mix = rb.static_mix(bm, pd.Series(0.0, index=IDX), 0.6)
    a, b = m.alpha_beta(mix, bm)
    assert b == pytest.approx(0.6)
    assert a == pytest.approx(0.0, abs=1e-12)


def test_attribution_detects_crisis_only_alpha():
    """Genau das Muster aus dem Feedback: Outperformance nur in Krisen."""
    rng = np.random.default_rng(2)
    idx = pd.bdate_range("2000-01-03", "2015-12-31")
    bm = pd.Series(rng.normal(0.0004, 0.01, len(idx)), index=idx)
    crisis = rb.crisis_mask(idx, rb.MAJOR)
    bm[crisis] -= 0.001                        # Krisen: Markt fällt
    pf = bm.where(~crisis, 0.0)                # Strategie in Krisen neutral, sonst identisch
    att = rb.attribution(pf, bm)
    assert att.loc["Außerhalb aller Krisen", "Log-Überschuss"] == pytest.approx(0, abs=1e-9)
    assert att.loc[rb.MAJOR, "Anteil"].sum() == pytest.approx(1.0, abs=0.05)
    exs = rb.ex_crisis_summary(pf, bm, names=rb.MAJOR)
    assert exs.loc["CAGR", "SPY3"] == pytest.approx(exs.loc["CAGR", "Benchmark"])


def test_timing_test_runs():
    rng = np.random.default_rng(3)
    bm = pd.Series(rng.normal(0.0004, 0.01, 2000), index=IDX)
    pos = pd.Series((rng.random(2000) > 0.2).astype(int), index=IDX)
    res = rb.timing_test(pos, bm, pd.Series(0.0, index=IDX), n=50)
    assert 0 <= res["p-Wert Sharpe"] <= 1
