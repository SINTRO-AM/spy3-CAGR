"""'Analysis' sheet for the Excel export: key figures, native Excel charts and monthly returns.

All charts are native Excel charts (XlsxWriter) that read from the 'Chart data' sheet, so they
stay editable in Excel. Monthly and annual returns are written as values; the annual totals
and differences are Excel formulas with cached results, so the matrix can be checked by hand.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from xlsxwriter.utility import xl_rowcol_to_cell as cell

from . import metrics as m
from .formatting import pct
from .metrics import TD

NAVY, NET, GROSS, SPY, MIX, INK, MUTED, GRID = (
    "#003274", "#1F6B45", "#1E3A8A", "#8C96A5", "#B38B4D", "#1B2638", "#5E6B7D", "#E4E8EE")
FONT = "Arial"
START = 1000

TXT = {
    "en": {
        "title": "SPY3 — Performance analysis",
        "sub": "SPY3 net of all fees versus the S&P 500 (SPY), {a} – {b}.",
        "fees": "Net: after {cost} bp trading costs per switch, {mgmt} management fee p.a. and "
                "{perf} performance fee above SPY (high-water mark). Gross: after trading costs only.",
        "sim": "Simulated performance based on the model rules; live since September 2023. "
               "Past or simulated performance is not a reliable indicator of future results.",
        "kpis": "Key figures", "net": "SPY3 net", "gross": "SPY3 gross", "spy": "S&P 500",
        "rows": ["Total return", "CAGR", "Volatility p.a.", "Sharpe ratio", "Max. drawdown",
                 "Calmar ratio", "Beta", "Jensen's alpha p.a.", "Positive months",
                 "Best month", "Worst month"],
        "c_value": "Value of USD 1,000", "c_dd": "Drawdown",
        "c_sharpe": "Rolling {w} Sharpe ratio", "c_excess": "Cumulative excess return vs. S&P 500",
        "c_alpha": "Rolling {w} Jensen's alpha p.a.", "c_years": "Calendar-year returns",
        "c_vol": "Rolling {w} volatility",
        "m_title": "Monthly returns — {name}", "year": "Year", "total": "Total",
        "diff": "Difference",
        "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct",
                   "Nov", "Dec"],
        "partial": "Partial years: {y}. Year totals are the compounded monthly returns.",
        "alpha_note": "Alpha and beta measured against SHY (short-term Treasuries) as the "
                      "risk-free asset.",
        "src": "Source: SINTRO SPY3 backtest engine. Daily data in 'Daily data', chart series "
               "in 'Chart data'.",
        "1y": "1-year", "3y": "3-year", "3m": "3-month",
        "date": "Date", "yr": "Year",
    },
    "de": {
        "title": "SPY3 — Performance-Analyse",
        "sub": "SPY3 nach allen Gebühren gegenüber dem S&P 500 (SPY), {a} – {b}.",
        "fees": "Netto: nach {cost} bp Handelskosten je Umschichtung, {mgmt} Managementgebühr p.a. "
                "und {perf} Performancegebühr über SPY (High-Water-Mark). Brutto: nur nach "
                "Handelskosten.",
        "sim": "Simulierte Wertentwicklung auf Basis der Modellregeln; live seit September 2023. "
               "Vergangene oder simulierte Ergebnisse sind kein verlässlicher Indikator für die "
               "Zukunft.",
        "kpis": "Kennzahlen", "net": "SPY3 netto", "gross": "SPY3 brutto", "spy": "S&P 500",
        "rows": ["Gesamtrendite", "Rendite p.a. (CAGR)", "Volatilität p.a.", "Sharpe Ratio",
                 "Max. Drawdown", "Calmar Ratio", "Beta", "Jensen's Alpha p.a.",
                 "Positive Monate", "Bester Monat", "Schlechtester Monat"],
        "c_value": "Wert von 1.000 USD", "c_dd": "Drawdown",
        "c_sharpe": "Rollierende {w} Sharpe Ratio", "c_excess": "Kumulierter Vorsprung vor dem S&P 500",
        "c_alpha": "Rollierendes {w} Jensen's Alpha p.a.", "c_years": "Renditen je Kalenderjahr",
        "c_vol": "Rollierende {w} Volatilität",
        "m_title": "Monatsrenditen — {name}", "year": "Jahr", "total": "Gesamt",
        "diff": "Differenz",
        "months": ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt",
                   "Nov", "Dez"],
        "partial": "Unvollständige Jahre: {y}. Jahreswerte sind die verketteten Monatsrenditen.",
        "alpha_note": "Alpha und Beta gegenüber SHY (kurzlaufende Staatsanleihen) als risikofreie "
                      "Anlage.",
        "src": "Quelle: SINTRO SPY3 Backtest-Engine. Tagesdaten im Blatt 'Daily data', "
               "Chartreihen im Blatt 'Chart data'.",
        "1y": "1-Jahres-", "3y": "3-Jahres-", "3m": "3-Monats-",
        "date": "Datum", "yr": "Jahr",
    },
}


# ---------------------------------------------------------------------------------------
def _monthly(r: pd.Series) -> pd.DataFrame:
    """Year x month matrix of compounded monthly returns."""
    mr = (1 + r).resample("ME").prod() - 1
    df = pd.DataFrame({"y": mr.index.year, "m": mr.index.month, "r": mr.values})
    return df.pivot(index="y", columns="m", values="r").reindex(columns=range(1, 13))


def _rolling_alpha(r: pd.Series, bm: pd.Series, rf: pd.Series, w: int) -> pd.Series:
    """Rolling Jensen's alpha p.a. (OLS on daily excess returns over rf), as in metrics."""
    y, x = r - rf, bm - rf
    beta = y.rolling(w).cov(x) / x.rolling(w).var()
    return (y.rolling(w).mean() - beta * x.rolling(w).mean()) * TD


def _windows(n: int) -> tuple[int, str, int, str]:
    """Rolling windows that fit the selected period: (long window, label, vol window, label)."""
    if n >= 3 * TD + 126:
        long_w, long_k = 3 * TD, "3y"
    elif n >= TD + 63:
        long_w, long_k = TD, "1y"
    else:
        long_w, long_k = 63, "3m"
    vol_w, vol_k = (TD, "1y") if n >= TD + 63 else (63, "3m")
    return long_w, long_k, vol_w, vol_k


def chart_data(bt: pd.DataFrame, mixes: dict[str, pd.Series]) -> tuple[pd.DataFrame, dict]:
    """Daily series behind the charts (NaN where a rolling window is not yet filled)."""
    net, gross, bm, rf = bt.ret_pf_net, bt.ret_pf, bt.ret_bm, bt.ret_off
    long_w, long_k, vol_w, vol_k = _windows(len(bt))
    lr = lambda s: np.log1p(s)                                           # noqa: E731

    def roll_sharpe(s):
        ret = np.expm1(lr(s).rolling(long_w).sum() * TD / long_w)
        return ret / (s.rolling(long_w).std() * np.sqrt(TD))

    d = pd.DataFrame(index=bt.index)
    d["value_net"] = START * (1 + net).cumprod()
    d["value_gross"] = START * (1 + gross).cumprod()
    d["value_spy"] = START * (1 + bm).cumprod()
    for name, s in mixes.items():
        d[f"value_{name}"] = START * (1 + s.reindex(bt.index).fillna(0)).cumprod()
    d["dd_net"] = m.drawdown(net)
    d["dd_spy"] = m.drawdown(bm)
    d["sharpe_net"] = roll_sharpe(net)
    d["sharpe_spy"] = roll_sharpe(bm)
    d["excess_net"] = (1 + net).cumprod() / (1 + bm).cumprod() - 1
    d["alpha_net"] = _rolling_alpha(net, bm, rf, long_w)
    d["vol_net"] = net.rolling(vol_w).std() * np.sqrt(TD)
    d["vol_spy"] = bm.rolling(vol_w).std() * np.sqrt(TD)
    return d, {"long": long_k, "vol": vol_k}


def _date_axis(span_days: int) -> dict:
    years = span_days / 365.25
    if years > 12:
        unit, kind, fmt = 4, "years", "yyyy"
    elif years > 5:
        unit, kind, fmt = 2, "years", "yyyy"
    elif years > 2:
        unit, kind, fmt = 6, "months", "mmm yy"
    else:
        unit, kind, fmt = 3, "months", "mmm yy"
    return {"date_axis": True, "num_format": fmt, "major_unit": unit, "major_unit_type": kind,
            "num_font": {"name": FONT, "size": 8, "color": MUTED},
            "line": {"color": "#BFC6D0"}, "major_tick_mark": "none",
            "label_position": "low"}


def _nice_axis(lo: float, hi: float, max_ticks: int = 11) -> dict:
    """Axis bounds on round steps that include all data (no clipping, no odd tick labels)."""
    for step in (0.01, 0.02, 0.05, 0.1, 0.2, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0,
                 100.0, 200.0, 250.0, 500.0, 1000.0, 2000.0, 2500.0, 5000.0, 10000.0):
        a, b = np.floor(lo / step) * step, np.ceil(hi / step) * step
        if (b - a) / step <= max_ticks:
            return {"min": float(a), "max": float(b), "major_unit": step}
    return {}


def _style(chart, title: str, y_fmt: str, x_axis: dict, legend: bool = True, y_extra=None):
    chart.set_title({"name": title, "name_font": {"name": FONT, "size": 10, "bold": True,
                                                  "color": INK}, "overlay": False})
    y = {"num_format": y_fmt, "num_font": {"name": FONT, "size": 8, "color": MUTED},
         "major_gridlines": {"visible": True, "line": {"color": GRID, "width": 0.75}},
         "line": {"none": True}, "major_tick_mark": "none"}
    y.update(y_extra or {})
    chart.set_y_axis(y)
    chart.set_x_axis(x_axis)
    chart.set_legend({"position": "top", "font": {"name": FONT, "size": 8, "color": INK}}
                     if legend else {"none": True})
    chart.set_chartarea({"border": {"none": True}, "fill": {"color": "#FFFFFF"}})
    chart.set_plotarea({"border": {"none": True}})
    chart.show_blanks_as("gap")


# ---------------------------------------------------------------------------------------
def write_analysis(book, ws, data_ws_name: str, bt: pd.DataFrame, mixes: dict[str, pd.Series],
                   lang: str = "en", fees: dict | None = None) -> None:
    """Fill the 'Analysis' worksheet `ws`. The chart series must already be on
    `data_ws_name` in the layout produced by `chart_data` (index in column A)."""
    T = TXT.get(lang, TXT["en"])
    fees = fees or {}
    d, win = chart_data(bt, mixes)
    net, gross, bm, rf = bt.ret_pf_net, bt.ret_pf, bt.ret_bm, bt.ret_off
    n = len(d)
    first, last = 1, n                                     # data rows on the chart-data sheet
    col = {c: i + 1 for i, c in enumerate(d.columns)}       # column A holds the dates

    def ref(name):
        return [data_ws_name, first, col[name], last, col[name]]
    dates = [data_ws_name, first, 0, last, 0]

    # ---------- formats ----------
    f = lambda **k: book.add_format({"font_name": FONT, "font_size": 9, **k})   # noqa: E731
    f_title = f(font_size=16, bold=True, font_color=NAVY)
    f_sub = f(font_size=10, font_color=INK)
    f_note = f(font_size=8, font_color=MUTED, italic=True)
    f_h = f(bold=True, font_color="#FFFFFF", bg_color=NAVY, align="center", valign="vcenter")
    f_hl = f(bold=True, font_color="#FFFFFF", bg_color=NAVY, align="left", valign="vcenter")
    f_sec = f(font_size=11, bold=True, font_color=NAVY, bottom=2, bottom_color=NAVY)
    f_lbl = f(font_color=INK, bottom=1, bottom_color=GRID)
    pct1 = f(num_format="0.0%", align="right", bottom=1, bottom_color=GRID)
    pct1b = f(num_format="0.0%", align="right", bold=True, bg_color="#EEF2F8", font_color=NAVY,
              bottom=1, bottom_color=GRID)
    dec2 = f(num_format="0.00", align="right", bottom=1, bottom_color=GRID)
    dec2b = f(num_format="0.00", align="right", bold=True, bg_color="#EEF2F8", font_color=NAVY,
              bottom=1, bottom_color=GRID)
    pct0 = f(num_format="#,##0%", align="right", bottom=1, bottom_color=GRID)
    pct0b = f(num_format="#,##0%", align="right", bold=True, bg_color="#EEF2F8", font_color=NAVY,
              bottom=1, bottom_color=GRID)
    def pair(num, num_tiny, **k):
        """Format for normal values and for |v| < 0.05 % (shown without a minus sign)."""
        return f(num_format=num, **k), f(num_format=num_tiny, **k)
    m_cell = pair("0.0%;-0.0%;0.0%", "0.0%;0.0%;0.0%", align="center", border=1,
                  border_color="#FFFFFF")
    m_year = pair("0.0%;-0.0%;0.0%", "0.0%;0.0%;0.0%", align="center", bold=True, left=2,
                  left_color=NAVY, bottom=1, bottom_color=GRID)
    m_cmp = pair("0.0%;-0.0%;0.0%", "0.0%;0.0%;0.0%", align="center", bottom=1,
                 bottom_color=GRID, font_color=MUTED)
    m_diff = pair("+0.0%;-0.0%;0.0%", "0.0%;0.0%;0.0%", align="center", bold=True, bottom=1,
                  bottom_color=GRID)

    def pick(fm, v):
        return fm[1] if pd.notna(v) and abs(v) < 0.0005 else fm[0]
    m_yr = f(bold=True, align="left", font_color=INK, bottom=1, bottom_color=GRID)

    ws.hide_gridlines(2)
    ws.set_column(0, 0, 24)
    ws.set_column(1, 16, 8.6)
    ws.set_zoom(100)

    # ---------- header ----------
    a, b_ = bt.index[0].strftime("%d.%m.%Y"), bt.index[-1].strftime("%d.%m.%Y")
    ws.write(0, 0, T["title"], f_title)
    ws.set_row(0, 26)
    ws.write(1, 0, T["sub"].format(a=a, b=b_), f_sub)
    if fees:
        ws.write(2, 0, T["fees"].format(cost=f"{fees.get('cost_bps', 10):.0f}",
                                        mgmt=pct(fees.get("mgmt", 0), 2, lang=lang),
                                        perf=pct(fees.get("perf", 0), 0, lang=lang)), f_note)
    ws.write(3, 0, T["sim"], f_note)

    # ---------- key figures ----------
    series = {T["net"]: net, T["gross"]: gross, T["spy"]: bm}
    for name, s in mixes.items():
        series[name] = s.reindex(bt.index).fillna(0)
    r0 = 5
    ws.merge_range(r0, 0, r0, len(series), T["kpis"], f_sec)
    ws.write(r0 + 1, 0, "", f_hl)
    for j, name in enumerate(series):
        ws.write(r0 + 1, j + 1, name, f_h)
    stats = {}
    for name, s in series.items():
        mm = (1 + s).resample("ME").prod() - 1
        a_, b2 = m.alpha_beta(s, bm, rf)
        mdd = m.max_drawdown(s)
        stats[name] = [m.total_return(s), m.cagr(s), m.ann_vol(s), m.sharpe(s), mdd,
                       m.cagr(s) / abs(mdd) if mdd < 0 else np.nan, b2, a_,
                       float((mm > 0).mean()), float(mm.max()), float(mm.min())]
    kinds = ["pct0", "pct1", "pct1", "dec", "pct1", "dec", "dec", "pct1", "pct0", "pct1", "pct1"]
    fmt = {("pct0", False): pct0, ("pct0", True): pct0b, ("pct1", False): pct1,
           ("pct1", True): pct1b, ("dec", False): dec2, ("dec", True): dec2b}
    for i, (label, kind) in enumerate(zip(T["rows"], kinds)):
        rr = r0 + 2 + i
        ws.write(rr, 0, label, f_lbl)
        for j, name in enumerate(series):
            v = stats[name][i]
            hl = j == 0
            if v is None or (isinstance(v, float) and not np.isfinite(v)):
                ws.write_blank(rr, j + 1, None, fmt[(kind, hl)])
            else:
                ws.write_number(rr, j + 1, float(v), fmt[(kind, hl)])
    kpi_end = r0 + 2 + len(T["rows"])
    ws.write(kpi_end, 0, T["alpha_note"], f_note)

    # ---------- charts ----------
    xa = _date_axis((bt.index[-1] - bt.index[0]).days)
    W, H = 600, 300

    def line_chart(title, cols, y_fmt, y_extra=None):
        ch = book.add_chart({"type": "line"})
        for c, name, color, width, dash in cols:
            s = {"name": name, "categories": dates, "values": ref(c),
                 "line": {"color": color, "width": width}}
            if dash:
                s["line"]["dash_type"] = dash
            ch.add_series(s)
        _style(ch, title, y_fmt, xa, legend=len(cols) > 1, y_extra=y_extra)
        return ch

    value_cols = [("value_spy", T["spy"], SPY, 1.25, None)]
    for name in mixes:
        value_cols.append((f"value_{name}", name, MIX, 1.25, "dash"))
    value_cols += [("value_gross", T["gross"], GROSS, 1.25, None),
                   ("value_net", T["net"], NET, 2.0, None)]
    vals = d[[c for c, *_ in value_cols]]
    c_value = line_chart(T["c_value"], value_cols, "#,##0",
                         y_extra=_nice_axis(float(vals.min().min()), float(vals.max().max()), 8))

    c_dd = book.add_chart({"type": "area"})
    c_dd.add_series({"name": T["spy"], "categories": dates, "values": ref("dd_spy"),
                     "fill": {"color": SPY, "transparency": 55}, "line": {"color": SPY, "width": 0.75}})
    c_dd.add_series({"name": T["net"], "categories": dates, "values": ref("dd_net"),
                     "fill": {"color": NET, "transparency": 25}, "line": {"color": NET, "width": 1.0}})
    _style(c_dd, T["c_dd"], "0%", xa,
           y_extra=_nice_axis(float(d[["dd_net", "dd_spy"]].min().min()), 0.0, 7))

    wl = T[win["long"]]
    sh = d[["sharpe_net", "sharpe_spy"]]
    c_sh = line_chart(T["c_sharpe"].format(w=wl),
                      [("sharpe_spy", T["spy"], SPY, 1.25, None),
                       ("sharpe_net", T["net"], NET, 1.75, None)], "0.0",
                      y_extra=_nice_axis(float(min(0.0, sh.min().min())), float(sh.max().max()), 8)
                      if sh.notna().any().any() else None)

    c_ex = book.add_chart({"type": "area"})
    c_ex.add_series({"name": T["net"], "categories": dates, "values": ref("excess_net"),
                     "fill": {"color": NAVY, "transparency": 70}, "line": {"color": NAVY, "width": 1.5}})
    _style(c_ex, T["c_excess"], "0%", xa, legend=False,
           y_extra=_nice_axis(min(0.0, float(d["excess_net"].min())),
                              max(0.0, float(d["excess_net"].max()))))

    c_al = line_chart(T["c_alpha"].format(w=wl), [("alpha_net", T["net"], NET, 1.75, None)], "0%")

    c_vol = line_chart(T["c_vol"].format(w=T[win["vol"]]),
                       [("vol_spy", T["spy"], SPY, 1.25, None),
                        ("vol_net", T["net"], NET, 1.75, None)], "0%")

    # annual returns (from the monthly matrices below; written later, referenced here)
    mat_n, mat_s = _monthly(net), _monthly(bm)
    years = list(mat_n.index)
    yr_n = (1 + net).groupby(net.index.year).prod() - 1
    yr_s = (1 + bm).groupby(bm.index.year).prod() - 1

    # layout: value chart beside the key figures, then a 2-column grid
    # column A = 173 px, columns B.. = 65 px; the grid below is 2 x 600 + 10 = 1210 px wide
    x0 = 173 + (len(series) + 1) * 65 + 6
    c_value.set_size({"width": 2 * W + 10 - x0, "height": H})
    ws.insert_chart(r0, len(series) + 2, c_value, {"x_offset": 6, "y_offset": 0,
                                                   "object_position": 1})
    grid_top = max(kpi_end + 3, r0 + 17)
    step = 16                                             # rows per chart row (20 px each)
    grid = [(c_dd, c_sh), (c_ex, c_al), (None, c_vol)]
    for i, (left, right) in enumerate(grid):
        rr = grid_top + i * step
        for k, ch in enumerate((left, right)):
            if ch is None:
                continue
            ch.set_size({"width": W, "height": H})
            ws.insert_chart(rr, 0, ch, {"x_offset": k * (W + 10), "y_offset": 0,
                                        "object_position": 1})

    # ---------- monthly matrices ----------
    def matrix(top, name, mat, yr, compare=None):
        ws.merge_range(top, 0, top, 15 if compare is not None else 13,
                       T["m_title"].format(name=name), f_sec)
        hdr = [T["year"]] + T["months"] + [T["total"]]
        if compare is not None:
            hdr += [T["spy"], T["diff"]]
        for j, h in enumerate(hdr):
            ws.write(top + 1, j, h, f_hl if j == 0 else f_h)
        first_cell = last_cell = None
        for i, y in enumerate(mat.index):
            rr = top + 2 + i
            ws.write(rr, 0, str(y), m_yr)
            for mo in range(1, 13):
                v = mat.loc[y, mo]
                if pd.notna(v):
                    ws.write_number(rr, mo, float(v), pick(m_cell, v))
                else:
                    ws.write_blank(rr, mo, None, m_cell[0])
            rng = f"{cell(rr, 1)}:{cell(rr, 12)}"
            v_y = float(yr.get(y, np.nan))
            ws.write_formula(rr, 13, f"=EXP(SUMPRODUCT(LN(1+{rng})))-1", pick(m_year, v_y), v_y)
            if compare is not None:
                cmp_row = compare(y)
                v_s = float(yr_s.get(y, np.nan))
                ws.write_formula(rr, 14, f"={cell(cmp_row, 13)}", pick(m_cmp, v_s), v_s)
                ws.write_formula(rr, 15, f"={cell(rr, 13)}-{cell(rr, 14)}",
                                 pick(m_diff, v_y - v_s), v_y - v_s)
            first_cell = first_cell or cell(rr, 1)
            last_cell = cell(rr, 12)
        ws.conditional_format(f"{first_cell}:{last_cell}", {
            "type": "3_color_scale", "min_type": "num", "min_value": -0.08,
            "mid_type": "num", "mid_value": 0, "max_type": "num", "max_value": 0.08,
            "min_color": "#E59A93", "mid_color": "#FFFFFF", "max_color": "#86BE98"})
        if compare is not None:
            ws.conditional_format(f"{cell(top + 2, 15)}:{cell(top + 1 + len(mat), 15)}", {
                "type": "cell", "criteria": "<", "value": 0,
                "format": book.add_format({"font_color": "#B3261E"})})
            ws.conditional_format(f"{cell(top + 2, 15)}:{cell(top + 1 + len(mat), 15)}", {
                "type": "cell", "criteria": ">", "value": 0,
                "format": book.add_format({"font_color": NET})})
        return top + 2 + len(mat)

    m_top = grid_top + len(grid) * step + 1
    spy_top = m_top + len(mat_n) + 4
    after_net = matrix(m_top, T["net"], mat_n, yr_n,
                       compare=lambda y: spy_top + 2 + list(mat_s.index).index(y))
    partial = []
    if bt.index[0] > pd.Timestamp(year=bt.index[0].year, month=1, day=1) + pd.Timedelta(days=7):
        partial.append(str(bt.index[0].year))
    if bt.index[-1] < pd.Timestamp(year=bt.index[-1].year, month=12, day=24):
        partial.append(f"{bt.index[-1].year} (YTD {bt.index[-1]:%d.%m.%Y})")
    if partial:
        ws.write(after_net, 0, T["partial"].format(y=", ".join(partial)), f_note)
    after_spy = matrix(spy_top, T["spy"], mat_s, yr_s)

    # calendar-year column chart, placed in the free left slot of the last grid row
    yc = book.add_chart({"type": "column"})
    yrow0 = m_top + 2
    cats = [ws.name, yrow0, 0, yrow0 + len(years) - 1, 0]
    yc.add_series({"name": T["net"], "categories": cats,
                   "values": [ws.name, yrow0, 13, yrow0 + len(years) - 1, 13],
                   "fill": {"color": NET}, "gap": 60, "overlap": -10})
    yc.add_series({"name": T["spy"], "categories": cats,
                   "values": [ws.name, yrow0, 14, yrow0 + len(years) - 1, 14],
                   "fill": {"color": SPY}})
    x_cat = {"num_font": {"name": FONT, "size": 8, "color": MUTED, "rotation": -45},
             "line": {"color": "#BFC6D0"}, "major_tick_mark": "none", "label_position": "low"}
    _style(yc, T["c_years"], "0%", x_cat)
    yc.set_size({"width": W, "height": H})
    ws.insert_chart(grid_top + 2 * step, 0, yc, {"x_offset": 0, "y_offset": 0,
                                                 "object_position": 1})

    ws.write(after_spy + 1, 0, T["src"], f_note)
    ws.set_landscape()
    ws.fit_to_pages(1, 0)
    ws.set_paper(9)
    ws.set_h_pagebreaks([grid_top + step, m_top])
    ws.activate()
