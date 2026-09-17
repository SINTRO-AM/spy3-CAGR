"""SPY3 Dashboard (lokal: `python app.py`, Deployment: `gunicorn app:server`)."""
from __future__ import annotations

import base64

import pandas as pd
from dash import Dash, Input, Output, ctx, dcc, html, no_update

from scripts.run_report import build
from functools import lru_cache

from spy3 import metrics as m, plots, robustness as rb, rolling as rl
from spy3.data import load_prices
from spy3.formatting import by_metric, dec, pct
from spy3.i18n import LANGS, t, term, tip
from spy3.strategy import OFF, ON, StrategyParams, factor_states

FONTS = "https://fonts.googleapis.com/css2?family=Jost:wght@300;400;500;600&display=swap"
PARAMS = StrategyParams()

R = build(load_prices(), PARAMS.cost_bps)
BT = R["bt"]
LAST = BT.index[-1]
PERIODS = {"all": None, "10": 10, "5": 5, "3": 3, "1": 1}
STATE_CLS = {ON: "on", OFF: "off"}
PERSIST = dict(persistence=True, persistence_type="session")
KPI_ORDER = ["Total Return", "CAGR", "Volatilität p.a.", "Sharpe Ratio", "Calmar", "Beta",
             "Jensen's Alpha p.a.", "Up-Capture", "Down-Capture", "Max. Drawdown"]
KPI_EMPHASIS = {"Sharpe Ratio", "Max. Drawdown"}
ROLL_SERIES = {"gross": BT.ret_pf, "net": BT.ret_pf_net, "sp": BT.ret_bm,
               "6040": R["mixes"]["60/40"]}

ROBOT = "/assets/robot.svg"
GLOBE = "data:image/svg+xml;base64," + base64.b64encode(
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
    b'stroke="#5E6B7D" stroke-width="1.6"><circle cx="12" cy="12" r="9"/>'
    b'<path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9'
    b's1.3-6.4 3.8-9z"/></svg>').decode()


# ---------- Hilfsfunktionen -------------------------------------------------
def slice_bt(period: str, lang: str):
    yrs = PERIODS.get(period)
    start = BT.index[0] if yrs is None else LAST - pd.DateOffset(years=yrs)
    b = BT.loc[start:]
    mixes = {n: s.loc[start:] for n, s in R["mixes"].items()}
    return b, mixes


def table(df: pd.DataFrame, lang: str, fmt=None, row_label="", highlight=(),
          sign_cols=(), emphasis=(), wrap_cls="", tips=None) -> html.Div:
    fmt = fmt or (lambda i, v: by_metric(i, v, lang))
    tips = tips or {}
    head = html.Tr([html.Th(row_label)] + [
        html.Th(c, className=" ".join(["hl"] * (c in highlight) + ["tip"] * bool(tips.get(c))),
                title=tips.get(c)) for c in df.columns])
    rows = []
    for idx, r in df.iterrows():
        rt = tip(idx, lang)
        cells = [html.Th(term(idx, lang), scope="row", title=rt,
                         className="tip" if rt else None)]
        for c, v in r.items():
            cls = ["num"] + (["hl"] if c in highlight else [])
            if c in sign_cols and isinstance(v, float) and v < 0:
                cls.append("neg")
            txt = pct(v, signed=True, lang=lang) if c in sign_cols else fmt(idx, v)
            cells.append(html.Td(txt, className=" ".join(cls)))
        rows.append(html.Tr(cells, className="em" if idx in emphasis else None))
    return html.Div(html.Table([html.Thead(head), html.Tbody(rows)], className="tbl"),
                    className=f"tbl-wrap {wrap_cls}".strip())


def section(title: str, note: str, *children, tip_key: str | None = None,
            lang: str = "de") -> html.Section:
    return html.Section([html.Div([html.H3(title), info(tip_key, lang)], className="h-row"),
                         html.P(note, className="note"), *children], className="panel")


GRAPH_CONFIG = {"displaylogo": False, "responsive": True,
                "modeBarButtonsToRemove": ["lasso2d", "select2d"]}


def graph_box(size: str, graph_id: str | None = None, fig=None) -> html.Div:
    """Chart in einem Rahmen mit fester Höhe.

    Die Höhe hängt am äußeren Div, nicht am dcc.Graph: Dash baut den Graph beim
    Aktualisieren neu auf, sodass eine Höhe am Graph selbst kurz auf 0 fallen kann.
    """
    kw = {"id": graph_id} if graph_id else {}
    if fig is not None:
        kw["figure"] = fig
    return html.Div(dcc.Graph(config=GRAPH_CONFIG, style={"height": "100%", "width": "100%"},
                              **kw), className=f"graph-box graph-box--{size}")


def graph(fig) -> html.Div:
    return graph_box("tab", fig=fig)


def seg(id_, options, value):
    return dcc.RadioItems(options, value, id=id_, className="seg", inputClassName="seg-in",
                          labelClassName="seg-lbl", inline=True, **PERSIST)


# ---------- Kopfzeile -------------------------------------------------------
def signal_badge(lang: str) -> html.Details:
    row = BT.iloc[-1]
    on = int(row.signal) == 1
    f = factor_states(row, PARAMS)
    details = {
        "Risk": t("f_var", lang, v=pct(row.var_1d, 2, lang=lang)),
        "Momentum": t("f_mom", lang, f=PARAMS.fast_ma, s=PARAMS.slow_ma,
                      v=pct(row.ma_fast / row.ma_slow - 1, signed=True, lang=lang)),
        "Mean-Reversion": t("f_mr", lang, w=PARAMS.dd_window,
                            v=pct(row.price / (row.high_disc * PARAMS.dd_trigger) - 1,
                                  signed=True, lang=lang)),
    }
    chips = [html.Span([html.I(className="led " + STATE_CLS.get(x["state"], "neutral")), n],
                       className="chip", title=f"{n}: {x['state']}") for n, x in f.items()]
    rows = [html.Div([
        html.Span(n, className="f-name"),
        html.Span(x["state"], className="f-state " + STATE_CLS.get(x["state"], "neutral")),
        html.Span(details[n], className="f-detail"),
    ], className="f-row") for n, x in f.items()]
    date = LAST.strftime("%d.%m.%Y" if lang == "de" else "%b %d, %Y")
    return html.Details([
        html.Summary([
            html.Span([html.I(className="pulse"),
                       html.Span(ON if on else OFF, className="sig-main"),
                       html.Span("SPY" if on else "SHY", className="sig-asset")],
                      className="sig-btn " + ("on" if on else "off")),
            html.Span(chips, className="chips"),
        ], className="sig-summary", title=t("sig_title", lang)),
        html.Div([html.P(t("sig_asof", lang, d=date), className="note small"), *rows,
                  html.P(t("sig_rule", lang), className="note small")],
                 className="sig-pop"),
    ], className="signal")


def lang_menu() -> html.Details:
    return html.Details([
        html.Summary([html.Img(src=GLOBE, alt="", className="globe"),
                      html.Span("DE", id="lang-current")],
                     className="lang-btn", title="Sprache / Language"),
        html.Div([html.Button(name, id=f"lang-{code}", n_clicks=0, className="lang-opt",
                              lang=code) for code, name in LANGS.items()],
                 className="lang-pop", role="menu"),
    ], id="lang-menu", className="lang-menu", open=False)


# ---------- Seite -----------------------------------------------------------
def info(tip_key: str | None, lang: str) -> html.Span | None:
    """Kleines Fragezeichen mit Erklärung als Tooltip."""
    txt = tip(tip_key, lang) if tip_key else None
    return html.Span("?", className="info", title=txt, tabIndex=0,
                     role="img", **{"aria-label": txt}) if txt else None


def scale_hint(lang: str) -> html.Div:
    """Kurzer Hinweis zur Skala; blendet sich nach 5 Sekunden selbst aus (reines CSS)."""
    return html.Div([
        html.Img(src=ROBOT, alt="", className="hint-bot"),
        html.Div([html.Strong(t("hint_title", lang)),
                  html.Span(t("hint_body", lang))], className="hint-text"),
    ], className="hint", role="note")


def chart_panel(title: str, note: str, graph_id: str, lang: str,
                tip_key: str | None = None) -> html.Section:
    return html.Section([
        html.Div([html.H2(t(title, lang)), info(tip_key, lang)], className="h-row"),
        html.P(t(note, lang), className="note"),
        graph_box("side", graph_id),
    ], className="panel")


def page(lang: str) -> list:
    fmt_d = "%m/%Y"
    tab = lambda key, val: dcc.Tab(label=t(key, lang), value=val, className="tab",  # noqa: E731
                                   selected_className="tab--on")
    return [
        html.Div([
            html.H1(t("title", lang)),
            html.P(t("lede", lang, start=BT.index[0].strftime(fmt_d),
                     end=LAST.strftime(fmt_d)), className="lede"),
            html.P(t("lede_defs", lang, cost=f"{PARAMS.cost_bps:.0f}",
                     mgmt=pct(PARAMS.mgmt_fee, 1, lang=lang),
                     perf=pct(PARAMS.perf_fee, 0, lang=lang)), className="lede defs"),
        ], className="intro"),
        html.Div([
            html.Div([html.Span(t("period", lang), className="ctl-lbl"),
                      seg("period", [{"label": t(f"p_{k}", lang), "value": k}
                                     for k in PERIODS], "all")]),
            html.Div([html.Span(t("scale", lang), className="ctl-lbl"),
                      seg("scale", [{"label": t("log", lang), "value": "log"},
                                    {"label": t("linear", lang), "value": "linear"}], "log"),
                      scale_hint(lang)], className="ctl ctl--scale"),
        ], className="controls"),
        html.Div([
            html.Section([
                html.Div([html.Div([html.H2(t("perf", lang)),
                                    info("chart_perf", lang)], className="h-row"),
                          html.Span(t("perf_note", lang), className="note")],
                         className="panel-head"),
                graph_box("main", "wealth"),
                html.P(t("fees_note", lang), className="note small"),
            ], className="panel chart-panel"),
            html.Section([html.H2(t("kpis", lang)), html.Div(id="kpis")],
                         className="panel kpi-panel"),
        ], className="grid"),
        html.Div([
            chart_panel("dd_title", "dd_note", "dd-graph", lang, "chart_dd"),
            chart_panel("alpha_title", "alpha_note", "alpha-graph", lang, "chart_alpha"),
        ], className="two-col risk-row"),
        dcc.Tabs(id="analysis-tabs", value="gap", className="tabs", mobile_breakpoint=0,
                 children=[
            tab("t_gap", "gap"), tab("t_roll", "roll"),
            tab("t_ex", "ex"), tab("t_years", "years"), tab("t_timing", "timing"),
        ], **PERSIST),
        html.Div(id="tab-body", className="tab-body"),
    ]


app = Dash(__name__, title="SPY3 Dashboard · SINTRO", external_stylesheets=[FONTS],
           update_title=None, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    dcc.Store(id="lang-pref", storage_type="local", data="en"),
    html.Header([
        html.Img(src=app.get_asset_url("sintro-logo.png"), alt="SINTRO Asset Management",
                 className="logo"),
        html.Div([html.Div(id="signal"), lang_menu()], className="top-right"),
    ], className="topbar"),
    html.Main(id="page", className="page"),
    html.Footer(id="footer", className="foot"),
])


# ---------- Callbacks -------------------------------------------------------
@app.callback(Output("lang-pref", "data"),
              Input("lang-de", "n_clicks"), Input("lang-en", "n_clicks"),
              prevent_initial_call=True)
def choose_lang(_de, _en):
    if ctx.triggered_id is None:
        return no_update
    return ctx.triggered_id.split("-")[1]


# Menü nach Auswahl schließen (natives <details>, daher clientseitig)
app.clientside_callback(
    """function(lang) {
        const d = document.getElementById("lang-menu");
        if (d) { d.open = false; }
        document.documentElement.lang = lang || "de";
        return window.dash_clientside.no_update;
    }""",
    Output("lang-menu", "title"), Input("lang-pref", "data"))


@app.callback(Output("page", "children"), Output("signal", "children"),
              Output("footer", "children"), Output("lang-current", "children"),
              *[Output(f"lang-{c}", "className") for c in LANGS],
              Input("lang-pref", "data"))
def render(lang):
    lang = lang if lang in LANGS else "en"
    opts = ["lang-opt is-current" if c == lang else "lang-opt" for c in LANGS]
    return (page(lang), signal_badge(lang), t("footer", lang), lang.upper(), *opts)


@app.callback(Output("wealth", "figure"), Output("kpis", "children"),
              Output("dd-graph", "figure"), Output("alpha-graph", "figure"),
              Input("period", "value"), Input("scale", "value"), Input("lang-pref", "data"))
def update_main(period, scale, lang):
    b, mixes = slice_bt(period, lang)
    fig = plots.wealth_chart(b, mixes, log=scale != "linear", lang=lang)
    dd = plots.drawdown_chart(b, mixes, lang=lang)
    al = plots.alpha_chart(b, mixes, lang=lang)
    cols = {t("col_gross", lang): b.ret_pf, t("col_net", lang): b.ret_pf_net,
            "S&P 500": b.ret_bm, **mixes}
    tbl = m.summary_table(cols, b.ret_bm, b.ret_off).loc[KPI_ORDER]
    hl = (t("col_gross", lang), t("col_net", lang))
    col_tips = {t("col_gross", lang): tip("col_gross", lang),
                t("col_net", lang): tip("col_net", lang),
                "S&P 500": tip("col_bm", lang), "60/40": tip("col_mix", lang)}
    return fig, [table(tbl, lang, highlight=hl, emphasis=KPI_EMPHASIS, wrap_cls="fill",
                       tips=col_tips),
                 html.P(t("kpi_note", lang), className="note small")], dd, al


@app.callback(Output("tab-body", "children"), Input("analysis-tabs", "value"),
              Input("period", "value"), Input("lang-pref", "data"))
def update_tab(tab, period, lang):
    b, _ = slice_bt(period, lang)
    pf, bm = b.ret_pf, b.ret_bm
    if tab in (None, "gap"):
        att = rb.attribution(pf, bm)
        att.columns = [t("excess_log", lang), t("share", lang)]
        att_tips = {t("excess_log", lang): tip("excess_log", lang),
                    t("share", lang): tip("share", lang)}
        return html.Div([
            section(t("cum_title", lang), t("cum_note", lang),
                    graph(plots.cum_excess_chart(b, lang)), tip_key="excess_log", lang=lang),
            section(t("src_title", lang), t("src_note", lang),
                    graph_box("bars", fig=plots.attribution_bars(att, lang)),
                    table(att, lang, fmt=lambda i, v: pct(v, lang=lang),
                          row_label=t("phase", lang), tips=att_tips)),
        ], className="two-col")
    if tab == "roll":
        metric_opts = [{"label": t(f"rm_{k}", lang), "value": k} for k in rl.METRICS]
        win_opts = [{"label": t("yr_short", lang, y=y), "value": y} for y in (1, 3, 5)]
        return html.Section([
            html.H3(t("roll_title", lang)),
            html.P(id="roll-note", className="note"),
            html.Div([
                html.Div([html.Span(t("roll_metric", lang), className="ctl-lbl"),
                          seg("roll-metric", metric_opts, "sharpe")]),
                html.Div([html.Span(t("roll_window", lang), className="ctl-lbl"),
                          seg("roll-window", win_opts, 3)]),
            ], className="controls"),
            html.Div(id="roll-facts", className="facts"),
            graph_box("tab", "roll-graph"),
        ], className="panel")
    if tab == "ex":
        out = []
        for key, names in (("ex1", rb.MAJOR), ("ex2", None)):
            d = rb.ex_crisis_summary(pf, bm, b.ret_off, names)
            d.columns = ["SPY3", "S&P 500"]
            out.append(section(t(f"{key}_title", lang), t(f"{key}_note", lang),
                               table(d, lang, highlight=("SPY3",))))
        return html.Div(out, className="two-col")
    if tab == "years":
        y = rb.yearly_excess(pf, bm).sort_index(ascending=False)
        y.index = [f"{i} ({t('ytd', lang)})" if i == LAST.year else str(i) for i in y.index]
        y.columns = ["SPY3", "S&P 500", t("diff", lang)]
        parts = [section(t("yr_title", lang), t("yr_note", lang),
                         table(y, lang, fmt=lambda i, v: pct(v, lang=lang),
                               row_label=t("year", lang), highlight=("SPY3",),
                               sign_cols=(t("diff", lang),)))]
        if period in (None, "all"):
            sp = rb.subperiods(pf, bm, b.ret_off)
            parts.append(section(t("dec_title", lang), t("dec_note", lang), table(sp, lang)))
        return html.Div(parts, className="two-col")
    tt = R["timing"]
    rows = [
        ("Sharpe Ratio" if lang == "de" else "Sharpe ratio",
         dec(tt["Sharpe Strategie"], lang=lang),
         dec(tt["Sharpe Zufalls-Timing (Median)"], lang=lang),
         dec(tt["p-Wert Sharpe"], lang=lang)),
        ("CAGR", pct(tt["CAGR Strategie"], lang=lang),
         pct(tt["CAGR Zufalls-Timing (Median)"], lang=lang),
         dec(tt["p-Wert CAGR"], lang=lang)),
    ]
    head = html.Tr([html.Th(""), html.Th("SPY3", className="hl"),
                    html.Th(t("tt_random", lang)), html.Th(t("p_value", lang))])
    body = [html.Tr([html.Th(a, scope="row"), html.Td(b_, className="num hl"),
                     html.Td(c, className="num"), html.Td(d, className="num")])
            for a, b_, c, d in rows]
    return section(t("tt_title", lang), t("tt_note", lang),
                   html.Div(html.Table([html.Thead(head), html.Tbody(body)], className="tbl"),
                            className="tbl-wrap narrow"))


@lru_cache(maxsize=128)
def _rolling(key: str, metric: str, years: int) -> pd.Series:
    return rl.rolling_metric(ROLL_SERIES[key], BT.ret_bm, metric, years)


@app.callback(Output("roll-graph", "figure"), Output("roll-facts", "children"),
              Output("roll-note", "children"),
              Input("roll-metric", "value"), Input("roll-window", "value"),
              Input("period", "value"), Input("lang-pref", "data"))
def update_rolling(metric, years, period, lang):
    metric = metric if metric in rl.METRICS else "sharpe"
    years = int(years or 3)
    b, _ = slice_bt(period, lang)
    start = b.index[0]
    fmt, _higher = rl.METRICS[metric]
    names = {"gross": t("gross", lang), "net": t("net", lang), "sp": "S&P 500",
             "6040": "60/40"}
    keys = ["gross", "net", "6040"] if metric == "excess" else list(names)
    series = {names[k]: _rolling(k, metric, years).loc[start:] for k in keys}
    fig = plots.rolling_chart(series, fmt, metric in ("excess", "sharpe", "calmar"), lang)

    net = series[names["net"]]
    show = (lambda v: pct(v, 1, lang=lang)) if fmt == "pct" else (lambda v: dec(v, lang=lang))
    facts = []
    if metric == "excess":
        facts.append((pct((net.dropna() > 0).mean(), 0, lang=lang),
                      t("win_sp", lang, y=years)))
        sp_rel = _rolling("6040", "excess", years).loc[start:]
        facts.append((pct(rl.win_rate(net, sp_rel, "excess"), 0, lang=lang),
                      t("win_6040", lang, y=years)))
        facts.append((show(net.median()), t("median_net", lang, y=years)))
    elif _higher is not None:
        facts.append((pct(rl.win_rate(net, series["S&P 500"], metric), 0, lang=lang),
                      t("win_sp", lang, y=years)))
        facts.append((pct(rl.win_rate(net, series["60/40"], metric), 0, lang=lang),
                      t("win_6040", lang, y=years)))
        facts.append((show(net.median()), t("median_net", lang, y=years)))
        facts.append((show(series["S&P 500"].median()), t("median_sp", lang, y=years)))
    else:
        facts.append((show(net.median()), t("median_net", lang, y=years)))
    facts_el = [html.Div([html.Strong(a), html.Span(c)], className="fact") for a, c in facts]
    note = t("rm_excess_note", lang) if metric == "excess" else t("roll_note_x", lang)
    return fig, facts_el, note


if __name__ == "__main__":
    app.run(debug=False)
