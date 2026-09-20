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


def test_sharpe_is_geometric(bt):
    """Sharpe = CAGR / annualisierte Volatilität, passend zur CAGR-Zeile der Tabelle."""
    for r in (bt.ret_pf, bt.ret_bm):
        assert m.sharpe(r) == pytest.approx(m.cagr(r) / m.ann_vol(r))
    rf = bt.ret_off
    assert m.sharpe(bt.ret_pf, rf) == pytest.approx(
        (m.cagr(bt.ret_pf) - m.cagr(rf)) / m.ann_vol(bt.ret_pf))
    # klassische (arithmetische) Variante liegt bei volatilen Reihen höher
    arith = bt.ret_bm.mean() / bt.ret_bm.std(ddof=1) * np.sqrt(m.TD)
    assert arith > m.sharpe(bt.ret_bm)


# ---------- Risiko-Reiter ---------------------------------------------------
from spy3 import risk as rk  # noqa: E402


def test_var_ordering_and_definition(bt):
    v = rk.var_table({"SPY3": bt.ret_pf})["SPY3"]
    assert v["VaR 99%"] > v["VaR 95%"] > 0
    assert v["CVaR 99%"] >= v["VaR 99%"] and v["CVaR 95%"] >= v["VaR 95%"]
    assert v["Schlechtester Tag"] >= v["CVaR 99%"]
    assert (bt.ret_pf < -v["VaR 95%"]).mean() == pytest.approx(0.05, abs=0.005)


def test_var_backtest_expectation(bt):
    res = rk.var_backtest(bt.ret_pf, level=0.99, window=250)
    assert res["expected"] == pytest.approx(res["n"] * 0.01)
    assert 0 <= res["rate"] <= 0.2


def test_stress_table_matches_direct_computation(bt):
    st = rk.stress_table({"SPY3": bt.ret_pf, "S&P 500": bt.ret_bm})
    a, b_ = rk.WINDOWS["GFC 2007–09"]
    assert st.loc["GFC 2007–09", "SPY3"] == pytest.approx(m.total_return(bt.ret_pf.loc[a:b_]))
    assert st.loc["GFC 2007–09", "MaxDD"] <= 0


def test_monte_carlo_is_ordered_and_deterministic(bt):
    paths = rk.monte_carlo(bt.ret_pf, horizon=60, n_paths=300)
    last = paths.iloc[-1]
    assert last["P5"] < last["P25"] < last["P50"] < last["P75"] < last["P95"]
    pd.testing.assert_frame_equal(paths, rk.monte_carlo(bt.ret_pf, horizon=60, n_paths=300))
    stats = rk.monte_carlo_stats(bt.ret_pf, horizon=60, n_paths=300)
    assert 0 <= stats["loss_prob"] <= 1 and stats["avg_dd"] <= 0
    assert stats["p5"] < stats["p50"] < stats["p95"]


def test_correlation_and_beta_tables(bt):
    mix = rb.static_mix(bt.ret_bm, bt.ret_off, 0.6)
    c = rk.correlation({"SPY3": bt.ret_pf, "S&P 500": bt.ret_bm, "60/40": mix})
    assert np.allclose(np.diag(c), 1.0) and np.allclose(c.to_numpy(), c.to_numpy().T)
    assert ((c >= -1) & (c <= 1)).all().all()
    b_tbl = rk.beta_table(bt.ret_pf, {"S&P 500": bt.ret_bm, "60/40": mix})
    _, beta = m.alpha_beta(bt.ret_pf, bt.ret_bm)
    assert b_tbl.loc["S&P 500", "Beta"] == pytest.approx(beta, rel=1e-6)


def test_engine_matches_hand_built_portfolio(bt):
    """Unabhängiger Nachbau: Depot in Stücken, Umschichtung zum Schluss des Signaltags,
    Kosten multiplikativ auf den Depotwert. Muss exakt zur Engine passen."""
    from spy3.strategy import StrategyParams
    p = StrategyParams()
    spy = (1 + bt.ret_bm).cumprod()
    shy = (1 + bt.ret_off).cumprod()
    sig = bt.signal.astype(int)
    # Start: Depot hält bereits die Position des ersten Tages (Aufbau davor, Kosten dort)
    held = "SPY" if bt.position.iloc[0] == 1 else "SHY"
    units = 1.0 / (spy.iloc[0] if held == "SPY" else shy.iloc[0])
    wealth, trades = [], 1
    for i, d in enumerate(bt.index):
        val = units * (spy[d] if held == "SPY" else shy[d])
        want = "SPY" if sig.iloc[i] == 1 else "SHY"
        if held != want:                      # Umschichtung zum Schluss des Signaltags
            val *= 1 - p.cost_bps / 1e4
            trades += 1
            units, held = val / (spy[d] if want == "SPY" else shy[d]), want
        wealth.append(val)
    ctrl = pd.Series(wealth, index=bt.index)
    eng = (1 + bt.ret_pf).cumprod() / (1 + bt.ret_pf.iloc[0])   # gleicher Startpunkt
    ratio = (eng / ctrl).dropna()
    assert np.allclose(ratio.to_numpy(), ratio.iloc[0], rtol=1e-12)   # Pfade deckungsgleich
    assert trades == int(bt.cost.ne(0).sum())          # jeder Trade genau einmal belastet
    assert bt.cost.sum() == pytest.approx(trades * p.cost_bps / 1e4)


def test_switch_days_book_exactly_one_leg(bt):
    """An Wechseltagen genau eine Rendite – weder beide noch keine."""
    p_cost = bt.cost
    leg = bt.position * bt.ret_bm + (1 - bt.position) * bt.ret_off
    assert np.allclose(bt.ret_pf, (1 + leg) * (1 - p_cost) - 1)
    switch = bt.position.diff().fillna(0).ne(0)
    assert switch.sum() > 0
    both = (1 + bt.ret_bm + bt.ret_off) * (1 - p_cost) - 1
    assert not np.allclose(bt.ret_pf[switch], both[switch])   # nie beide Beine
    assert bt.ret_pf.notna().all()                            # nie gar keine Rendite


def test_returns_come_only_from_adjusted_prices(bt):
    """Keine separate Dividendenbuchung: Benchmarkrendite = Kursveränderung der Reihe."""
    w = (1 + bt.ret_bm).cumprod()
    assert np.allclose(w.pct_change().dropna(), bt.ret_bm.iloc[1:])
