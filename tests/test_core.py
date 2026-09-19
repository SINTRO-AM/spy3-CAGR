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
    mix = rb.static_mix(bm, pd.Series(0.0, index=IDX), 0.6, rebalance=None)
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
    r = prepare_returns(px, treasury=pd.Series(dtype=float))   # ohne Treasury-Index
    assert (r.risk_off_source.iloc[:2] == "T-Bill").all()
    assert r.risk_off.iloc[0] == pytest.approx(1.017 ** (1 / 252) - 1)
    assert r.risk_off_source.iloc[-1] == "SHY"


# ---------- Rollierende Kennzahlen -----------------------------------------
from spy3 import rolling as rl  # noqa: E402


def test_rolling_max_dd_matches_direct():
    rng = np.random.default_rng(5)
    idx = pd.bdate_range("2010-01-01", periods=900)
    r = pd.Series(rng.normal(0.0003, 0.012, 900), index=idx)
    rd = rl.rolling_metric(r, r, "maxdd", 1)
    for end in (251, 500, 899):
        assert rd.iloc[end] == pytest.approx(m.max_drawdown(r.iloc[end - 251:end + 1]))
    assert rd.iloc[:251].isna().all()


def test_rolling_sharpe_return_beta():
    rng = np.random.default_rng(6)
    idx = pd.bdate_range("2010-01-01", periods=800)
    bm = pd.Series(rng.normal(0.0004, 0.01, 800), index=idx)
    r = 0.5 * bm
    sl = r.iloc[-756:]
    assert rl.rolling_metric(r, bm, "sharpe", 3).iloc[-1] == pytest.approx(m.sharpe(sl))
    assert rl.rolling_metric(r, bm, "return", 3).iloc[-1] == pytest.approx(m.cagr(sl))
    assert rl.rolling_metric(r, bm, "beta", 3).iloc[-1] == pytest.approx(0.5)
    assert rl.win_rate(rl.rolling_metric(r, bm, "vol", 3),
                       rl.rolling_metric(bm, bm, "vol", 3), "vol") == 1.0


# ---------- Export ---------------------------------------------------------
def test_pdf_and_xlsx_export(tmp_path):
    from spy3 import report as rp
    from spy3.data import prepare_returns
    idx = pd.bdate_range("2015-01-01", "2020-12-31")
    rng = np.random.default_rng(5)
    px = pd.DataFrame({"risk_on": 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.011, len(idx)))),
                       "risk_off": 80 * np.exp(np.cumsum(np.full(len(idx), 6e-5))),
                       "tbill_yield": 1.5}, index=idx)
    bt = backtest(prepare_returns(px), px["risk_on"], StrategyParams())
    mixes = {"60/40": 0.6 * bt.ret_bm + 0.4 * bt.ret_off}

    pdf = rp.build_pdf(bt, mixes, "de")
    assert pdf[:5] == b"%PDF-" and len(pdf) > 20_000

    xlsx = rp.build_xlsx(bt, mixes, "en")
    assert xlsx[:2] == b"PK"
    f = tmp_path / "x.xlsx"
    f.write_bytes(xlsx)
    sheets = pd.read_excel(f, sheet_name=None)
    assert set(sheets) == {"KPIs", "Daily data", "Calendar years", "Attribution", "Notes"}
    daily = sheets["Daily data"]
    assert len(daily) == len(bt)
    # Rohdaten müssen zum Backtest passen
    assert daily["ret_spy3_gross"].iloc[-1] == pytest.approx(bt.ret_pf.iloc[-1])
    assert daily["wealth_spy3_net"].iloc[-1] == pytest.approx(
        1000 * (1 + bt.ret_pf_net).prod())
    assert (daily["position"].isin([0, 1])).all()


def test_export_reports_missing_packages(monkeypatch):
    """Fehlt ein optionales Paket, meldet das Modul es, statt beim Import zu scheitern."""
    from spy3 import report as rp
    import importlib.util
    real = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec",
                        lambda name, *a, **k: None if name == "reportlab" else real(name))
    assert rp.missing_packages() == ["reportlab"]
    with pytest.raises(ModuleNotFoundError, match="reportlab"):
        rp.build_pdf(pd.DataFrame(), {}, "de")


def test_monthly_rebalancing(bt=None):
    """Monatliches Rebalancing: Gewichte driften im Monat, Monatsstart exakt 60/40."""
    idx = pd.bdate_range("2020-01-01", "2020-06-30")
    rng = np.random.default_rng(9)
    bm = pd.Series(rng.normal(0.001, 0.015, len(idx)), index=idx)
    off = pd.Series(rng.normal(0.0001, 0.002, len(idx)), index=idx)
    monthly = rb.static_mix(bm, off, 0.6)
    daily = rb.static_mix(bm, off, 0.6, rebalance=None)
    # Erster Tag eines Monats: identisch zur täglichen Variante (Gewichte frisch gesetzt)
    starts = idx.to_series().groupby(idx.to_period("M")).min()
    for d in starts:
        assert monthly[d] == pytest.approx(daily[d])
    # Danach laufen die Reihen auseinander, bleiben aber nah beieinander
    assert not np.allclose(monthly.to_numpy(), daily.to_numpy())
    assert abs(m.total_return(monthly) - m.total_return(daily)) < 0.02
    # Innerhalb eines Monats verkettet sich der Mix aus beiden Beinen
    jan = idx[idx < "2020-02-01"]
    expected = 0.6 * (1 + bm[jan]).prod() + 0.4 * (1 + off[jan]).prod() - 1
    assert m.total_return(monthly[jan]) == pytest.approx(expected)


# ---------- Treasury-Index als Risk-Off vor SHY -----------------------------
def test_treasury_export_parser(tmp_path):
    from spy3.data import load_treasury_index
    f = tmp_path / "lu.csv"
    f.write_text("Security\tLUATTRUU Index\nDate\tPX_LAST\tlog return\n"
                 "29.12.1989\t467,8\t\n31.01.1990\t460,81\t-1,51%\n"
                 "01.03.1994\t1.084,43\t-0,68%\n02.03.1994\t1084.56\t0,02%\n",
                 encoding="utf-8")
    s = load_treasury_index(f)
    assert list(s.index) == [pd.Timestamp("1989-12-29"), pd.Timestamp("1990-01-31"),
                             pd.Timestamp("1994-03-01"), pd.Timestamp("1994-03-02")]
    assert s.tolist() == pytest.approx([467.8, 460.81, 1084.43, 1084.56])
    assert load_treasury_index(tmp_path / "fehlt.csv").empty


def test_risk_off_priority_treasury_before_tbill():
    from spy3.data import prepare_returns
    idx = pd.bdate_range("2002-07-24", periods=7)      # SHY ab 30.07.2002
    px = pd.DataFrame({"risk_on": np.linspace(100, 106, 7),
                       "risk_off": [np.nan] * 4 + [80, 80.1, 80.2],
                       "tbill_yield": 1.7}, index=idx)
    tr = pd.Series([200, 201, 202, 203], index=idx[:4])     # deckt nur die ersten Tage ab
    r = prepare_returns(px, treasury=tr)
    # am ersten SHY-Kurstag gibt es noch keine SHY-Rendite; der Treasury-Index endet
    # einen Tag vorher -> dort greift die T-Bill-Näherung
    assert r.risk_off_source.tolist() == ["LUATTRUU"] * 3 + ["T-Bill", "SHY", "SHY"]
    assert r.risk_off.iloc[0] == pytest.approx(201 / 200 - 1)
    # ohne Treasury-Reihe fällt es auf T-Bills zurück
    r2 = prepare_returns(px, treasury=pd.Series(dtype=float))
    assert r2.risk_off_source.iloc[0] == "T-Bill"
    assert r2.risk_off.iloc[0] == pytest.approx(1.017 ** (1 / 252) - 1)


def test_treasury_index_gaps_are_carried_forward():
    """Fehlt ein Indexwert an einem SPY-Handelstag, ist die Rendite 0 und holt am
    nächsten Tag auf – keine Doppelzählung."""
    from spy3.data import prepare_returns
    idx = pd.bdate_range("2001-01-01", periods=5)
    px = pd.DataFrame({"risk_on": 100.0, "risk_off": np.nan}, index=idx)
    tr = pd.Series([100, 101, 103], index=[idx[0], idx[1], idx[3]])   # Tag 3 fehlt
    r = prepare_returns(px, treasury=tr)
    assert r.risk_off.tolist() == pytest.approx([0.01, 0.0, 103 / 101 - 1, 0.0])


def test_treasury_series_ends_with_the_data():
    from spy3.data import prepare_returns
    idx = pd.bdate_range("2001-01-01", periods=6)
    px = pd.DataFrame({"risk_on": 100.0, "risk_off": np.nan}, index=idx)
    tr = pd.Series([100, 101, 102], index=idx[:3])
    r = prepare_returns(px, treasury=tr)
    assert r.treasury.notna().tolist() == [True, True, False, False, False]
    assert r.risk_off_source.tolist() == ["LUATTRUU", "LUATTRUU", "none", "none", "none"]


def test_xlsx_export_has_log_columns(tmp_path):
    from spy3 import report as rp
    from spy3.data import prepare_returns
    idx = pd.bdate_range("2018-01-01", "2020-12-31")
    rng = np.random.default_rng(4)
    px = pd.DataFrame({"risk_on": 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.01, len(idx)))),
                       "risk_off": 80 * np.exp(np.cumsum(np.full(len(idx), 5e-5))),
                       "tbill_yield": 1.5}, index=idx)
    bt = backtest(prepare_returns(px, treasury=pd.Series(dtype=float)), px["risk_on"],
                  StrategyParams())
    f = tmp_path / "x.xlsx"
    f.write_bytes(rp.build_xlsx(bt, {}, "en"))
    d = pd.read_excel(f, sheet_name="Daily data")
    for c in ("log_ret_spy", "log_ret_spy3_gross", "cum_log_spy", "cum_log_spy3_gross",
              "cum_log_spy3_net", "cum_log_excess_gross"):
        assert c in d.columns
    # Log-Punkte müssen exakt zum Vermögen passen: 1.000 * exp(cum_log) = wealth
    assert np.allclose(1000 * np.exp(d.cum_log_spy3_gross), d.wealth_spy3_gross)
    assert np.allclose(1000 * np.exp(d.cum_log_spy), d.wealth_spy)
    assert np.allclose(d.cum_log_excess_gross, d.cum_log_spy3_gross - d.cum_log_spy)
    assert np.allclose(np.log1p(d.ret_spy3_gross), d.log_ret_spy3_gross)
