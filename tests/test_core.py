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


# ---------- Gebühren -------------------------------------------------------
from spy3.fees import apply_fees  # noqa: E402

QIDX = pd.bdate_range("2020-01-01", "2020-12-31")


def test_no_perf_fee_when_underperforming_spy():
    g = pd.Series(0.0005, index=QIDX)
    b = pd.Series(0.0008, index=QIDX)
    f = apply_fees(g, b, mgmt_fee=0.0, perf_fee=0.10)
    assert f.perf_fee_paid.sum() == 0
    assert f.nav_net.iloc[-1] == pytest.approx((1.0005) ** len(QIDX))


def test_perf_fee_is_ten_percent_of_excess_over_hurdle():
    q1 = QIDX[QIDX < "2020-04-01"]
    g = pd.Series(0.001, index=q1)
    b = pd.Series(0.0, index=q1)
    f = apply_fees(g, b, mgmt_fee=0.0, perf_fee=0.10)
    gross = 1.001 ** len(q1)
    assert f.perf_fee_paid.iloc[-1] == pytest.approx(0.1 * (gross - 1))
    assert f.nav_net.iloc[-1] == pytest.approx(gross - 0.1 * (gross - 1))


def test_high_water_mark_no_double_charge():
    q = QIDX[QIDX < "2020-10-01"]
    g = pd.Series(0.0, index=q)
    g[q < "2020-04-01"] = 0.001             # Q1 Gewinn -> Gebühr
    g[(q >= "2020-04-01") & (q < "2020-07-01")] = -0.001   # Q2 Verlust
    g[q >= "2020-07-01"] = 0.001            # Q3 Erholung, aber kaum über HWM
    f = apply_fees(g, pd.Series(-0.01 / 63, index=q), mgmt_fee=0.0)
    paid = f.perf_fee_paid
    assert paid[q < "2020-04-01"].sum() > 0
    assert paid[(q >= "2020-04-01") & (q < "2020-07-01")].sum() == 0
    # Q3: Gebühr nur auf den Teil über der HWM (nicht auf die Erholung)
    nav_q2 = f.nav_net[q < "2020-07-01"].iloc[-1]
    hwm = f.nav_net[q < "2020-04-01"].iloc[-1]
    q3_gross_end = nav_q2 * 1.001 ** (q >= "2020-07-01").sum()
    assert paid.iloc[-1] == pytest.approx(0.1 * max(q3_gross_end - hwm, 0))


def test_mgmt_fee_annual_rate():
    idx = pd.bdate_range("2020-01-01", periods=252)
    f = apply_fees(pd.Series(0.0, index=idx), pd.Series(0.0, index=idx),
                   mgmt_fee=0.002, perf_fee=0.0)
    assert f.nav_net.iloc[-1] == pytest.approx(1 / 1.002)


def test_tbill_proxy_before_shy():
    from spy3.data import prepare_returns
    idx = pd.bdate_range("2002-07-25", periods=6)
    px = pd.DataFrame({"risk_on": [100, 101, 102, 103, 104, 105],
                       "risk_off": [np.nan, np.nan, np.nan, 80, 80.1, 80.2],
                       "tbill_yield": [1.7] * 6}, index=idx)
    r = prepare_returns(px)
    assert (r.risk_off_source.iloc[:2] == "T-Bill").all()
    assert r.risk_off.iloc[0] == pytest.approx(1.017 ** (1 / 252) - 1)
    assert r.risk_off_source.iloc[-1] == "SHY"
