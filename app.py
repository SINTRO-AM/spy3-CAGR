"""SPY3 Dashboard (lokal: `python app.py`, Deployment: `gunicorn app:server`)."""
from __future__ import annotations

import pandas as pd
from dash import Dash, Input, Output, dcc, html

from scripts.run_report import build
from spy3 import metrics as m, plots, robustness as rb
from spy3.data import load_prices
from spy3.formatting import _de, by_metric, dec, label, pct
from spy3.strategy import OFF, ON, StrategyParams, factor_states

FONTS = ("https://fonts.googleapis.com/css2?family=Jost:wght@300;400;500;600"
         "&display=swap")

R = build(load_prices())
BT = R["bt"]
_Q = round(R["exposure"] * 100)
MIX_NAMES = dict(zip(R["mixes"], [f"Mix {_Q}/{100 - _Q}", f"Mix β {dec(R['beta'])}"]))
LAST = BT.index[-1]
PERIODS = {"Gesamt": None, "10 Jahre": 10, "5 Jahre": 5, "3 Jahre": 3, "1 Jahr": 1}


# ---------- Bausteine -------------------------------------------------------
def slice_bt(key: str) -> tuple[pd.DataFrame, dict[str, pd.Series]]:
    yrs = PERIODS[key]
    start = BT.index[0] if yrs is None else LAST - pd.DateOffset(years=yrs)
    b = BT.loc[start:]
    mixes = {MIX_NAMES[k]: s.loc[start:] for k, s in R["mixes"].items()}
    return b, mixes


def table(df: pd.DataFrame, fmt=by_metric, row_label="", highlight_col=None,
          sign_cols=()) -> html.Table:
    head = html.Tr([html.Th(row_label)] + [
        html.Th(c, className="hl" if c == highlight_col else None) for c in df.columns])
    rows = []
    for idx, r in df.iterrows():
        cells = [html.Th(label(idx), scope="row")]
        for c, v in r.items():
            cls = ["num"]
            if c == highlight_col:
                cls.append("hl")
            if c in sign_cols and isinstance(v, float) and v < 0:
                cls.append("neg")
            txt = pct(v, signed=True) if c in sign_cols else fmt(idx, v)
            cells.append(html.Td(txt, className=" ".join(cls)))
        rows.append(html.Tr(cells))
    return html.Div(html.Table([html.Thead(head), html.Tbody(rows)], className="tbl"),
                    className="tbl-wrap")


def section(title: str, note: str, *children) -> html.Section:
    return html.Section([html.H3(title), html.P(note, className="note"), *children],
                        className="panel")


def graph(fig, **kw):
    return dcc.Graph(figure=fig, config={"displaylogo": False, "responsive": True,
                                         "modeBarButtonsToRemove": ["lasso2d", "select2d"]},
                     **kw)


STATE_CLS = {ON: "on", OFF: "off"}


def signal_badge() -> html.Details:
    """Klickbarer Signal-Button; aufgeklappt zeigt er die Faktorwerte."""
    on = int(BT.signal.iloc[-1]) == 1
    factors = factor_states(BT.iloc[-1], StrategyParams())
    chips = [html.Span([html.I(className="led " + STATE_CLS.get(f["state"], "neutral")),
                        name], className="chip", title=f"{name}: {f['state']}")
             for name, f in factors.items()]
    rows = [html.Div([
        html.Span(name, className="f-name"),
        html.Span(f["state"], className="f-state " + STATE_CLS.get(f["state"], "neutral")),
        html.Span(_de(f["detail"]).replace("%", " %"), className="f-detail"),
    ], className="f-row") for name, f in factors.items()]
    return html.Details([
        html.Summary([
            html.Span([html.I(className="pulse"),
                       html.Span("Risk On" if on else "Risk Off", className="sig-main"),
                       html.Span("SPY" if on else "SHY", className="sig-asset")],
                      className="sig-btn " + ("on" if on else "off")),
            html.Span(chips, className="chips"),
        ], className="sig-summary", title="Details zu den Faktoren anzeigen"),
        html.Div([
            html.P(f"Signal zum Handelsschluss am {LAST:%d.%m.%Y}. Gehandelt wird am "
                   "nächsten Handelstag.", className="note small"),
            *rows,
            html.P("Risk Off durch den Risk-Faktor hat Vorrang. Sonst genügt ein "
                   "Risk-On-Faktor für eine Investition in SPY.", className="note small"),
        ], className="sig-pop"),
    ], className="signal")


def controls() -> html.Div:
    seg = dict(className="seg", inputClassName="seg-in", labelClassName="seg-lbl", inline=True)
    return html.Div([
        html.Div([html.Span("Zeitraum", className="ctl-lbl", id="lbl-period"),
                  dcc.RadioItems(list(PERIODS), "Gesamt", id="period", **seg)]),
        html.Div([html.Span("Skala", className="ctl-lbl"),
                  dcc.RadioItems([{"label": "Logarithmisch", "value": "log"},
                                  {"label": "Linear", "value": "linear"}],
                                 "log", id="scale", **seg)]),
    ], className="controls")


def timing_block() -> html.Div:
    t = R["timing"]
    items = [
        ("Sharpe Ratio", dec(t["Sharpe Strategie"]), dec(t["Sharpe Zufalls-Timing (Median)"]),
         dec(t["p-Wert Sharpe"])),
        ("CAGR", pct(t["CAGR Strategie"]), pct(t["CAGR Zufalls-Timing (Median)"]),
         dec(t["p-Wert CAGR"])),
    ]
    head = html.Tr([html.Th(""), html.Th("SPY3", className="hl"),
                    html.Th("Zufälliges Timing (Median)"), html.Th("p-Wert")])
    body = [html.Tr([html.Th(a, scope="row"), html.Td(b, className="num hl"),
                     html.Td(c, className="num"), html.Td(d, className="num")])
            for a, b, c, d in items]
    return html.Div(html.Table([html.Thead(head), html.Tbody(body)], className="tbl"),
                    className="tbl-wrap")


# ---------- Layout ----------------------------------------------------------
app = Dash(__name__, title="SPY3 Dashboard · SINTRO", external_stylesheets=[FONTS],
           update_title=None)
server = app.server

app.layout = html.Div([
    html.Header([
        html.Img(src=app.get_asset_url("sintro-logo.png"), alt="SINTRO Asset Management",
                 className="logo"),
        signal_badge(),
    ], className="topbar"),
    html.Main([
        html.Div([
            html.H1("SPY3 im Vergleich zum S&P 500"),
            html.P(f"Backtest {BT.index[0]:%m/%Y} bis {LAST:%m/%Y}, Total Return in USD, "
                   f"nach Kosten von {R['cost_bps']:.0f} bp je Umschichtung.", className="lede"),
        ], className="intro"),
        controls(),
        html.Div([
            html.Section([
                html.Div([html.H2("Wert von 1.000 USD"),
                          html.Span("Schattierte Phasen: Strategie hält kurzlaufende "
                                    "US-Staatsanleihen", className="note")],
                         className="panel-head"),
                dcc.Loading(dcc.Graph(id="wealth", className="wealth-graph",
                                      config={"displaylogo": False, "responsive": True}),
                            type="dot", color=plots.NAVY),
            ], className="panel chart-panel"),
            html.Section([html.H2("Kennzahlen"), html.Div(id="kpis")],
                         className="panel kpi-panel"),
        ], className="grid"),
        dcc.Tabs(id="tabs", value="gap", className="tabs", mobile_breakpoint=0, children=[
            dcc.Tab(label="Abstand zum Markt", value="gap", className="tab",
                    selected_className="tab--on"),
            dcc.Tab(label="Rollierende Überschussrendite", value="roll", className="tab",
                    selected_className="tab--on"),
            dcc.Tab(label="Ohne Krisen", value="excrisis", className="tab",
                    selected_className="tab--on"),
            dcc.Tab(label="Kalenderjahre", value="years", className="tab",
                    selected_className="tab--on"),
            dcc.Tab(label="Timing-Test", value="timing", className="tab",
                    selected_className="tab--on"),
        ]),
        html.Div(id="tab-body", className="tab-body"),
    ], className="page"),
    html.Footer(
        "SINTRO Asset Management GmbH · Simulierte Wertentwicklung. Vergangene oder "
        "simulierte Ergebnisse sind kein verlässlicher Indikator für künftige Ergebnisse.",
        className="foot"),
])


# ---------- Callbacks -------------------------------------------------------
@app.callback(Output("wealth", "figure"), Output("kpis", "children"),
              Input("period", "value"), Input("scale", "value"))
def update_main(period, scale):
    b, mixes = slice_bt(period)
    fig = plots.wealth_chart(b, mixes, log=scale == "log")
    tbl = m.summary_table({"SPY3": b.ret_pf, "S&P 500": b.ret_bm, **mixes},
                          b.ret_bm, b.ret_off)
    return fig, [table(tbl, highlight_col="SPY3"),
                 html.P("Mix: täglich rebalancierte Kombination aus SPY und SHY, entweder mit der "
                        "durchschnittlichen Aktienquote oder dem Beta von SPY3. "
                        "Sharpe Ratio ohne risikofreien Satz (rf = 0 %), Beta und Alpha über SHY.",
                        className="note small")]


@app.callback(Output("tab-body", "children"), Input("tabs", "value"),
              Input("period", "value"))
def update_tab(tab, period):
    b, _ = slice_bt(period)
    if tab == "gap":
        att = rb.attribution(b.ret_pf, b.ret_bm)
        att.columns = ["Überschuss (log)", "Anteil"]
        return html.Div([
            section("Relative Wertentwicklung",
                    "SPY3 geteilt durch S&P 500. Steigt die Linie, baut SPY3 Vorsprung auf; "
                    "verläuft sie waagerecht, entwickeln sich beide gleich.",
                    graph(plots.relative_chart(b))),
            section("Woher der Vorsprung kommt",
                    "Kumulierte logarithmische Überschussrendite und ihre Aufteilung auf "
                    "Krisenphasen.",
                    graph(plots.cum_excess_chart(b)),
                    table(att, fmt=lambda i, v: pct(v), row_label="Phase")),
        ], className="two-col")
    if tab == "roll":
        conc = rb.concentration(b.ret_pf, b.ret_bm, 12)
        conc_txt = pct(conc, 0) if conc == conc and conc > 0 else "–"
        hit = html.Div([
            html.Div([html.Strong(pct(rb.rolling_hit_rate(b.ret_pf, b.ret_bm, y), 0)),
                      html.Span(f"der {y}-Jahres-Fenster mit Outperformance")],
                     className="fact") for y in (3, 5)
        ] + [html.Div([html.Strong(conc_txt),
                       html.Span("12 beste Monate im Verhältnis zum Gesamtvorsprung")],
                      className="fact")], className="facts")
        return section("Rollierende Überschussrendite p.a.",
                       "Annualisierte Differenz der Log-Renditen im rollierenden Fenster.",
                       hit, graph(plots.rolling_excess_chart(b)))
    if tab == "excrisis":
        rf = b.ret_off
        a = rb.ex_crisis_summary(b.ret_pf, b.ret_bm, rf, rb.MAJOR)
        z = rb.ex_crisis_summary(b.ret_pf, b.ret_bm, rf)
        for d in (a, z):
            d.columns = ["SPY3", "S&P 500"]
        return html.Div([
            section("Ohne Dotcom-Crash und Finanzkrise",
                    "Kennzahlen ohne 01/2000–03/2003 und 10/2007–06/2009.",
                    table(a, highlight_col="SPY3")),
            section("Ohne alle Krisenphasen",
                    "Zusätzlich ohne Covid-Crash 2020 und das Jahr 2022.",
                    table(z, highlight_col="SPY3")),
        ], className="two-col")
    if tab == "years":
        y = rb.yearly_excess(b.ret_pf, b.ret_bm).sort_index(ascending=False)
        y.index = [f"{i} (lfd.)" if i == LAST.year else str(i) for i in y.index]
        y.columns = ["SPY3", "S&P 500", "Differenz"]
        sp = rb.subperiods(b.ret_pf, b.ret_bm, b.ret_off) if period == "Gesamt" else None
        parts = [section("Kalenderjahre", "Jahresrenditen und Differenz in Prozentpunkten.",
                         table(y, fmt=lambda i, v: pct(v), row_label="Jahr",
                               highlight_col="SPY3", sign_cols=("Differenz",)))]
        if sp is not None:
            sp.index = [i.replace(" BM", " S&P 500") for i in sp.index]
            parts.append(section("Jahrzehnte", "Kennzahlen je Teilperiode.",
                                 table(sp, row_label="")))
        return html.Div(parts, className="two-col")
    return section("Zufalls-Timing-Test",
                   "Das SPY3-Signal wird 500-mal zeitlich verschoben. Aktienquote und Länge "
                   "der Phasen bleiben gleich, nur das Timing ist zufällig. Der p-Wert gibt "
                   "an, wie oft zufälliges Timing mindestens so gut war. Immer über den "
                   "gesamten Zeitraum berechnet.",
                   timing_block())


if __name__ == "__main__":
    app.run(debug=False)
