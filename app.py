"""SPY3 Dashboard (lokal: `python app.py`, Deployment: `gunicorn app:server`)."""
from __future__ import annotations

import base64

import pandas as pd
from dash import Dash, Input, Output, ctx, dcc, html, no_update

from scripts.run_report import build
from spy3 import metrics as m, plots, robustness as rb
from spy3.data import load_prices
from spy3.formatting import by_metric, dec, pct
from spy3.i18n import LANGS, t, term
from spy3.strategy import OFF, ON, StrategyParams, factor_states

FONTS = "https://fonts.googleapis.com/css2?family=Jost:wght@300;400;500;600&display=swap"
PARAMS = StrategyParams()

R = build(load_prices(), PARAMS.cost_bps)
BT = R["bt"]
LAST = BT.index[-1]
PERIODS = {"all": None, "10": 10, "5": 5, "3": 3, "1": 1}
STATE_CLS = {ON: "on", OFF: "off"}
PERSIST = dict(persistence=True, persistence_type="session")

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
          sign_cols=()) -> html.Div:
    fmt = fmt or (lambda i, v: by_metric(i, v, lang))
    head = html.Tr([html.Th(row_label)] + [
        html.Th(c, className="hl" if c in highlight else None) for c in df.columns])
    rows = []
    for idx, r in df.iterrows():
        cells = [html.Th(term(idx, lang), scope="row")]
        for c, v in r.items():
            cls = ["num"] + (["hl"] if c in highlight else [])
            if c in sign_cols and isinstance(v, float) and v < 0:
                cls.append("neg")
            txt = pct(v, signed=True, lang=lang) if c in sign_cols else fmt(idx, v)
            cells.append(html.Td(txt, className=" ".join(cls)))
        rows.append(html.Tr(cells))
    return html.Div(html.Table([html.Thead(head), html.Tbody(rows)], className="tbl"),
                    className="tbl-wrap")


def section(title: str, note: str, *children) -> html.Section:
    return html.Section([html.H3(title), html.P(note, className="note"), *children],
                        className="panel")


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
def chart_panel(title: str, note: str, graph_id: str, lang: str) -> html.Section:
    return html.Section([
        html.H2(t(title, lang)), html.P(t(note, lang), className="note"),
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
                                    {"label": t("linear", lang), "value": "linear"}], "log")]),
        ], className="controls"),
        html.Div([
            html.Section([
                html.Div([html.H2(t("perf", lang)),
                          html.Span(t("perf_note", lang), className="note")],
                         className="panel-head"),
                graph_box("main", "wealth"),
                html.P(t("fees_note", lang), className="note small"),
            ], className="panel chart-panel"),
            html.Section([html.H2(t("kpis", lang)), html.Div(id="kpis")],
                         className="panel kpi-panel"),
        ], className="grid"),
        html.Div([
            chart_panel("dd_title", "dd_note", "dd-graph", lang),
            chart_panel("alpha_title", "alpha_note", "alpha-graph", lang),
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
    tbl = m.summary_table(cols, b.ret_bm, b.ret_off)
    hl = (t("col_gross", lang), t("col_net", lang))
    return fig, [table(tbl, lang, highlight=hl),
                 html.P(t("kpi_note", lang), className="note small")], dd, al


@app.callback(Output("tab-body", "children"), Input("analysis-tabs", "value"),
              Input("period", "value"), Input("lang-pref", "data"))
def update_tab(tab, period, lang):
    b, _ = slice_bt(period, lang)
    pf, bm = b.ret_pf, b.ret_bm
    if tab in (None, "gap"):
        att = rb.attribution(pf, bm)
        att.columns = [t("excess_log", lang), t("share", lang)]
        return html.Div([
            section(t("rel_title", lang), t("rel_note", lang),
                    graph(plots.relative_chart(b, lang))),
            section(t("src_title", lang), t("src_note", lang),
                    table(att, lang, fmt=lambda i, v: pct(v, lang=lang),
                          row_label=t("phase", lang))),
        ], className="two-col")
    if tab == "roll":
        conc = rb.concentration(pf, bm, 12)
        facts = [(pct(rb.rolling_hit_rate(pf, bm, y), 0, lang=lang), t("hit", lang, y=y))
                 for y in (3, 5)]
        facts.append((pct(conc, 0, lang=lang) if conc == conc and conc > 0 else "–",
                      t("conc", lang)))
        return section(t("roll_title", lang), t("roll_note", lang),
                       html.Div([html.Div([html.Strong(a), html.Span(c)], className="fact")
                                 for a, c in facts], className="facts"),
                       graph(plots.rolling_excess_chart(b, lang=lang)))
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


if __name__ == "__main__":
    app.run(debug=False)
