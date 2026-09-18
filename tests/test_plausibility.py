"""Konsistenz zwischen den Kennzahlen und den Charts des Dashboards."""
import numpy as np
import pandas as pd
import pytest

from spy3 import metrics as m, robustness as rb, rolling as rl
from spy3.data import prepare_returns
from spy3.strategy import StrategyParams, backtest

IDX = pd.bdate_range("2000-01-03", "2020-12-31")


@pytest.fixture(scope="module")
def bt():
    rng = np.random.default_rng(11)
    r = rng.normal(0.0004, np.where(pd.Index(IDX).year.isin([2002, 2008]), 0.022, 0.009))
    px = pd.DataFrame({
        "risk_on": 100 * np.exp(np.cumsum(r)),
        "risk_off": np.where(IDX < "2002-07-30", np.nan,
                             80 * np.exp(np.cumsum(np.full(len(IDX), 7e-5)))),
        "tbill_yield": 4.0,
    }, index=IDX)
    return backtest(prepare_returns(px), px["risk_on"], StrategyParams())


def test_excess_log_matches_wealth_ratio(bt):
    """Kumulierter Log-Überschuss = ln(Endvermögen SPY3 / Endvermögen Benchmark)."""
    ex = rb.excess_log(bt.ret_pf, bt.ret_bm).sum()
    ratio = (1 + bt.ret_pf).prod() / (1 + bt.ret_bm).prod()
    assert ex == pytest.approx(np.log(ratio), rel=1e-10)
    # und: exp(Log-Überschuss) ist der Vermögensfaktor gegenüber der Benchmark
    assert np.exp(ex) == pytest.approx(ratio, rel=1e-10)


def test_attribution_sums_to_total(bt):
    att = rb.attribution(bt.ret_pf, bt.ret_bm)
    parts = att.drop(index="Gesamt")["Log-Überschuss"].sum()
    assert parts == pytest.approx(att.loc["Gesamt", "Log-Überschuss"], rel=1e-9)
    assert att["Anteil"].drop(index="Gesamt").sum() == pytest.approx(1.0, rel=1e-9)


def test_yearly_returns_compound_to_total(bt):
    y = rb.yearly_excess(bt.ret_pf, bt.ret_bm)
    assert (1 + y["SPY3"]).prod() - 1 == pytest.approx(m.total_return(bt.ret_pf), rel=1e-9)
    assert (1 + y["Benchmark"]).prod() - 1 == pytest.approx(m.total_return(bt.ret_bm), rel=1e-9)


def test_cagr_matches_total_return(bt):
    n = len(bt)
    assert (1 + m.cagr(bt.ret_pf)) ** (n / m.TD) - 1 == pytest.approx(
        m.total_return(bt.ret_pf), rel=1e-9)


def test_drawdown_series_min_equals_max_drawdown(bt):
    """Die Chart-Serie und die Kennzahl müssen dasselbe Minimum haben."""
    for r in (bt.ret_pf, bt.ret_pf_net, bt.ret_bm):
        assert m.drawdown(r).min() == pytest.approx(m.max_drawdown(r))
        assert m.drawdown(r).max() <= 0                     # nie über dem Höchststand


def test_net_is_below_gross_but_same_shape(bt):
    assert m.total_return(bt.ret_pf_net) < m.total_return(bt.ret_pf)
    assert m.cagr(bt.ret_pf) - m.cagr(bt.ret_pf_net) < 0.02        # < 2 Pp. Gebühren
    assert bt.ret_pf.corr(bt.ret_pf_net) > 0.99


def test_mix_60_40_between_components(bt):
    mix = rb.static_mix(bt.ret_bm, bt.ret_off, 0.60)
    assert m.ann_vol(mix) < m.ann_vol(bt.ret_bm)
    assert m.max_drawdown(mix) > m.max_drawdown(bt.ret_bm)
    _, beta = m.alpha_beta(mix, bt.ret_bm)
    assert beta == pytest.approx(0.60, abs=0.01)


def test_beta_and_jensen_consistent(bt):
    rf = bt.ret_off
    a, b = m.alpha_beta(bt.ret_pf, bt.ret_bm, rf)
    expected = (bt.ret_pf - rf).mean() - b * (bt.ret_bm - rf).mean()
    assert a == pytest.approx(expected * m.TD, rel=1e-9)
    assert 0 < b < 1                                   # zeitweise in Anleihen


def test_capture_ratios_in_range(bt):
    up, dn = m.capture(bt.ret_pf, bt.ret_bm)
    assert 0 < up < 1.2 and 0 < dn < 1.2


def test_rolling_metrics_match_full_period(bt):
    """Rollierendes Fenster über die Gesamtlänge = Kennzahl der Gesamtperiode."""
    years = len(bt) / m.TD
    for metric, ref in [("sharpe", m.sharpe(bt.ret_pf)),
                        ("vol", m.ann_vol(bt.ret_pf)),
                        ("maxdd", m.max_drawdown(bt.ret_pf)),
                        ("return", m.cagr(bt.ret_pf))]:
        s = rl.rolling_metric(bt.ret_pf, bt.ret_bm, metric, years).dropna()
        assert s.iloc[-1] == pytest.approx(ref, rel=0.02), metric


def test_rolling_beta_matches_regression(bt):
    years = len(bt) / m.TD
    s = rl.rolling_metric(bt.ret_pf, bt.ret_bm, "beta", years).dropna()
    _, beta = m.alpha_beta(bt.ret_pf, bt.ret_bm)
    assert s.iloc[-1] == pytest.approx(beta, rel=0.02)


def test_position_only_changes_after_signal(bt):
    assert (bt.position.iloc[1:].to_numpy() == bt.signal.shift(1).iloc[1:].to_numpy()).all()
    assert bt.ret_pf[bt.position.eq(0)].std() < bt.ret_pf[bt.position.eq(1)].std()


# ---------- Risiko-Analysen ------------------------------------------------
from spy3 import risk as rk  # noqa: E402


def test_var_levels_and_cvar_ordering(bt):
    v = rk.var_table({"SPY3": bt.ret_pf})["SPY3"]
    assert v["VaR 99%"] > v["VaR 95%"] > 0                 # 99 % ist strenger
    assert v["CVaR 99%"] >= v["VaR 99%"]                   # Tail-Mittel >= Schwelle
    assert v["CVaR 95%"] >= v["VaR 95%"]
    assert v["Schlechtester Tag"] >= v["CVaR 99%"]


def test_var_quantile_definition(bt):
    v = rk.var_table({"SPY3": bt.ret_pf})["SPY3"]["VaR 95%"]
    assert (bt.ret_pf < -v).mean() == pytest.approx(0.05, abs=0.005)


def test_var_backtest_counts(bt):
    res = rk.var_backtest(bt.ret_pf, level=0.99, window=250)
    assert res["Erwartet"] == pytest.approx(res["Beobachtungen"] * 0.01)
    assert 0 <= res["Quote"] <= 0.2


def test_stress_table_matches_direct_computation(bt):
    st = rk.stress_table({"SPY3": bt.ret_pf, "S&P 500": bt.ret_bm})
    a, b_ = rk.WINDOWS["GFC 2007–09"]
    assert st.loc["GFC 2007–09", "SPY3"] == pytest.approx(
        m.total_return(bt.ret_pf.loc[a:b_]))
    assert st.loc["GFC 2007–09", "MaxDD"] <= 0


def test_monte_carlo_percentiles_ordered(bt):
    paths = rk.monte_carlo(bt.ret_pf, horizon_days=60, n_paths=300)
    last = paths.iloc[-1]
    assert last["P5"] < last["P25"] < last["P50"] < last["P75"] < last["P95"]
    assert paths.iloc[0].between(0.8, 1.2).all()           # Start nahe 1
    stats = rk.monte_carlo_stats(bt.ret_pf, horizon_days=60, n_paths=300)
    assert 0 <= stats["Verlustwahrscheinlichkeit"] <= 1
    assert stats["Ø max. Drawdown"] <= 0


def test_monte_carlo_is_deterministic(bt):
    a = rk.monte_carlo(bt.ret_pf, horizon_days=30, n_paths=200)
    b_ = rk.monte_carlo(bt.ret_pf, horizon_days=30, n_paths=200)
    pd.testing.assert_frame_equal(a, b_)


def test_correlation_matrix_properties(bt):
    c = rk.correlation({"SPY3": bt.ret_pf, "S&P 500": bt.ret_bm,
                        "60/40": rb.static_mix(bt.ret_bm, bt.ret_off, 0.6)})
    assert np.allclose(np.diag(c), 1.0)
    assert np.allclose(c.to_numpy(), c.to_numpy().T)
    assert ((c >= -1) & (c <= 1)).all().all()
    assert c.loc["S&P 500", "60/40"] > c.loc["S&P 500", "SPY3"]   # statisch korrelierter


def test_monthly_table_compounds_to_yearly(bt):
    mt = rk.monthly_table(bt.ret_pf)
    y = rb.yearly_excess(bt.ret_pf, bt.ret_bm)["SPY3"]
    for year in [2005, 2010, 2015]:
        assert (1 + mt.loc[year].dropna()).prod() - 1 == pytest.approx(y[year], rel=1e-9)
