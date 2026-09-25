"""SPY3 Dashboard (lokal: `python app.py`, Deployment: `gunicorn app:server`)."""
from __future__ import annotations

import base64

import pandas as pd
from dash import Dash, Input, Output, State, ctx, dcc, html, no_update

from scripts.run_report import build
from functools import lru_cache

from spy3 import (live, metrics as m, plots, report as rp, risk as rk, robustness as rb,
                  rolling as rl)
from functools import lru_cache

from spy3.data import load_assets, load_prices
from spy3.fees import apply_fees
from spy3.formatting import by_metric, dec, pct
from spy3.i18n import LANGS, t, term, tip
from spy3.strategy import OFF, ON, StrategyParams, factor_states

FONTS = "https://fonts.googleapis.com/css2?family=Jost:wght@300;400;500;600&display=swap"
PARAMS = StrategyParams()

R = build(load_prices(), PARAMS.cost_bps)
BT = R["bt"]
ASSET_RETURNS = load_assets()


def shy_benchmark() -> tuple[pd.Series, dict]:
    """SHY ETF als Vergleichsreihe: genau das Risk-Off-Bein der Strategie, also SHY
    ab 07/2002 und davor dieselbe Näherung (Bloomberg-Treasury-Index bzw. T-Bills)."""
    src = BT["risk_off_source"] if "risk_off_source" in BT else pd.Series("SHY", index=BT.index)
    pre = src[src != "SHY"]
    info = {"pre_end": pre.index[-1] if len(pre) else None,
            "pre_src": (pre.iloc[0] if len(pre) else None)}
    return BT["ret_off"].fillna(0.0), info


TSY_SERIES, TSY_INFO = shy_benchmark()
R["mixes"]["Treasury"] = TSY_SERIES
if "risk_off_source" in BT:
    _src = BT.loc[BT.index < "2002-07-30", "risk_off_source"].value_counts().to_dict()
    print(f"Risk-Off vor SHY (30.07.2002): {_src}  "
          f"[Treasury-Datei: {'ja' if TSY_INFO.get('pre_src') == 'LUATTRUU' else 'NEIN'}]")
LAST = BT.index[-1]
PERIODS = {"all": None, "10": 10, "5": 5, "3": 3, "1": 1}
STATE_CLS = {ON: "on", OFF: "off"}
PERSIST = dict(persistence=True, persistence_type="session")
KPI_ORDER = ["Total Return", "CAGR", "Volatilität p.a.", "Sharpe Ratio", "Calmar", "Beta",
             "Jensen's Alpha p.a.", "Max. Drawdown"]
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
    mixes = {(t("tsy_label", lang) if n == "Treasury" else n): s.loc[start:]
             for n, s in R["mixes"].items()}
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
def _live():
    """Aktuelles Signal; bei fehlendem Netz der letzte Stand bzw. der Backtest."""
    return live.current_signal(lambda refresh: load_prices(refresh=refresh), PARAMS,
                               fallback=BT.price)


def _sc_row(title: str, ok: bool, text: str, gate: bool = False) -> html.Div:
    return html.Div([
        html.Span("✓" if ok else "✕", className="sc-mark " + ("ok" if ok else "no")),
        html.Div([html.Span(title, className="sc-name"), html.Span(text, className="sc-text")]),
    ], className="sc-row" + (" sc-gate" if gate else ""))


def _foot(sig, lang: str) -> html.P:
    d = sig.asof.strftime("%d.%m.%Y" if lang == "de" else "%b %d, %Y")
    return html.P(t("sc_foot", lang, d=d, t=sig.checked.strftime("%H:%M")), className="sc-foot")


def _mark_row(ok: bool, name: str, text: str, veto: bool = False) -> html.Div:
    return html.Div([
        html.Span("✓" if ok else "✕", className="sc-mark " + ("ok" if ok else ("veto" if veto else "no"))),
        html.Div([html.Span(name, className="sc-name"), html.Span(text, className="sc-text")]),
    ], className="sc-row")


def signal_card(sig, lang: str) -> html.Div:
    """Karte am Risk-On/Off-Button: das aktuelle Signal Faktor für Faktor erklärt."""
    r, ok = sig.row, sig.reasons
    P = lambda v, d=1: pct(v, d, lang=lang)                                       # noqa: E731
    on = int(r["signal"]) == 1
    hi, lo = P(PARAMS.var_high, 0), P(PARAMS.var_low, 0)
    var = P(r["var_1d"], 2)
    gap = r["ma_fast"] / r["ma_slow"] - 1
    high = r["high_disc"] * PARAMS.dd_trigger
    fall = max(1 - r["price"] / high, 0.0)
    trig = P(1 - 1 / PARAMS.dd_trigger, 0)

    if not ok["risk_ok"]:
        risk_txt, risk_ok = t("sc_f_risk_veto", lang, v=var, hi=hi), False
    elif ok["calm"]:
        risk_txt, risk_ok = t("sc_f_risk_calm", lang, v=var, lo=lo), True
    else:
        risk_txt, risk_ok = t("sc_f_risk_mid", lang, v=var, hi=hi, lo=lo), True
    rows = [
        _mark_row(risk_ok, "Risk", risk_txt, veto=not ok["risk_ok"]),
        _mark_row(ok["trend"], "Momentum",
                  t("sc_f_mom_on" if ok["trend"] else "sc_f_mom_off", lang, v=P(abs(gap)))),
        _mark_row(ok["dip"], "Mean-Reversion",
                  t("sc_f_mr_on" if ok["dip"] else "sc_f_mr_off", lang, v=P(fall), lim=trig)),
    ]
    if on:
        # Ausstieg bei Veto ODER wenn alle derzeit aktiven Gründe gleichzeitig wegfallen
        ends = []
        if ok["calm"]:
            ends.append(t("sc_end_calm", lang, lo=lo))
        if ok["trend"]:
            ends.append(t("sc_end_trend", lang, g=P(abs(gap))))
        if ok["dip"]:
            ends.append(t("sc_end_dip", lang, lim=trig, f=P(fall)))
        nxt = t("sc_next_on", lang, hi=hi, v=var, all=t("sc_and_all", lang).join(ends))
    elif not ok["risk_ok"]:
        nxt = t("sc_next_veto", lang, hi=hi, v=var)
    else:
        nxt = t("sc_next_none", lang, g=P(abs(gap)), lo=lo, v=var, lim=trig)
    return html.Div([
        html.Div(t("sc_lead_on" if on else "sc_lead_off", lang), className="sc-title"),
        html.P(t("sc_logic", lang), className="sc-rule"),
        *rows,
        html.Div([html.Span(t("sc_next", lang), className="fc-lbl"), html.Span(nxt)],
                 className="sc-result " + ("on" if on else "off")),
        _foot(sig, lang),
    ], className="sig-pop", role="tooltip")


def factor_card(name: str, state: str, sig, lang: str) -> html.Div:
    """Karte an einem Faktor: aktueller Wert, Regel, wissenschaftlicher Hintergrund."""
    r = sig.row
    P = lambda v, d=1: pct(v, d, lang=lang)                                       # noqa: E731
    cls = STATE_CLS.get(state, "neutral")
    if name == "Risk":
        title, now = t("fc_risk_title", lang), t("fc_risk_now", lang, v=P(r["var_1d"], 2))
        rule = t("fc_risk_rule", lang, hi=P(PARAMS.var_high, 0), lo=P(PARAMS.var_low, 0))
        why, src = t("fc_risk_why", lang), t("fc_risk_src", lang)
        st = t({"on": "fc_state_on", "off": "fc_state_off"}.get(cls, "fc_state_neutral"), lang)
    elif name == "Momentum":
        gap = r["ma_fast"] / r["ma_slow"] - 1
        title = t("fc_mom_title", lang)
        now = t("fc_mom_now", lang, v=P(abs(gap)), dir=t("fc_above" if gap > 0 else "fc_below", lang))
        rule, why, src = t("fc_mom_rule", lang), t("fc_mom_why", lang), t("fc_mom_src", lang)
        st = t("fc_state_on" if cls == "on" else "fc_state_mom_off", lang)
    else:
        high = r["high_disc"] * PARAMS.dd_trigger
        trig = 1 - 1 / PARAMS.dd_trigger
        title = t("fc_mr_title", lang)
        now = t("fc_mr_now", lang, v=P(max(1 - r["price"] / high, 0.0)), lim=P(trig, 0))
        rule, why = t("fc_mr_rule", lang, lim=P(trig, 0)), t("fc_mr_why", lang)
        src = t("fc_mr_src", lang)
        st = t("fc_state_on" if cls == "on" else "fc_state_neutral", lang)
    return html.Div([
        html.Div([html.Span(title, className="fc-title"),
                  html.Span(st, className="fc-state " + cls)], className="fc-head"),
        html.Div([html.Span(t("fc_now", lang), className="fc-lbl"), html.Span(now)], className="fc-row"),
        html.Div([html.Span(t("fc_rule", lang), className="fc-lbl"), html.Span(rule)], className="fc-row"),
        html.Div([html.Span(t("fc_why", lang), className="fc-lbl"),
                  html.Span([why, " ", html.Span(f"({src})", className="fc-src")])], className="fc-row"),
        _foot(sig, lang),
    ], className="sig-pop fc-pop", role="tooltip")


def signal_badge(lang: str) -> html.Div:
    sig = _live()
    r = sig.row
    on = int(r["signal"]) == 1
    f = factor_states(r, PARAMS)
    chips = [html.Span([
        html.Span([html.I(className="led " + STATE_CLS.get(x["state"], "neutral")), n], className="chip"),
        factor_card(n, x["state"], sig, lang),
    ], className="hov chip-wrap", tabIndex="0") for n, x in f.items()]
    return html.Div([
        html.Div([
            html.Span([
                html.Span([html.I(className="pulse"),
                           html.Span(ON if on else OFF, className="sig-main"),
                           html.Span("SPY" if on else "SHY", className="sig-asset")],
                          className="sig-btn " + ("on" if on else "off")),
                signal_card(sig, lang),
            ], className="hov btn-wrap", tabIndex="0"),
            html.Span(chips, className="chips"),
        ], className="sig-summary"),
    ], className="signal")


def methodology(lang: str) -> html.Details:
    """Kurzer Methodik-Abschnitt zum Aufklappen."""
    items = [("meth_data", "meth_data_t"), ("meth_signal", "meth_signal_t"),
             ("meth_costs", "meth_costs_t"), ("meth_metrics", "meth_metrics_t"),
             ("meth_robust", "meth_robust_t")]
    return html.Details([
        html.Summary([html.Span(t("meth_title", lang)), html.Span("", className="meth-chev")],
                     className="meth-sum"),
        html.Div([
            html.Dl([el for k, v in items
                     for el in (html.Dt(t(k, lang)), html.Dd(t(v, lang)))], className="meth-list"),
            html.P(t("meth_note", lang), className="note small"),
        ], className="meth-body"),
    ], className="panel meth")


EXPORT_MISSING = rp.missing_packages()


def download_buttons() -> html.Div:
    """Export-Buttons; ohne die optionalen Pakete deaktiviert statt fehlerhaft."""
    off = bool(EXPORT_MISSING)
    hint = ("Fehlende Pakete: " + ", ".join(EXPORT_MISSING) +
            " – pip install -r requirements.txt") if off else None
    return html.Div([
        html.Button([html.Span("↓", className="dl-ico"), html.Span(id="dl-pdf-lbl")],
                    id="btn-pdf", n_clicks=0, disabled=off, title=hint,
                    className="dl-btn dl-btn--primary"),
        html.Button([html.Span("↓", className="dl-ico"), html.Span(id="dl-xlsx-lbl")],
                    id="btn-xlsx", n_clicks=0, disabled=off, title=hint, className="dl-btn"),
    ], className="downloads")


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


def fee_slider(id_: str, lo: float, hi: float, step: float, value: float, unit: str):
    marks = {lo: f"{lo:g}{unit}", hi: f"{hi:g}{unit}"}
    return html.Div(dcc.Slider(lo, hi, step, value=value, id=id_, marks=marks,
                               included=True, className="fee-slider",
                               tooltip={"placement": "bottom", "always_visible": False},
                               **PERSIST), className="fee-wrap")


def scale_hint(lang: str) -> html.Div:
    """Kurzer Hinweis zur Skala; blendet sich nach 5 Sekunden selbst aus (reines CSS)."""
    return html.Div([
        html.Img(src=ROBOT, alt="", className="hint-bot"),
        html.Div([html.Strong(t("hint_title", lang)),
                  html.Span(t("hint_body", lang))], className="hint-text"),
        html.Button("×", id="hint-close", n_clicks=0, className="hint-close",
                    title=t("hint_close", lang), **{"aria-label": t("hint_close", lang)}),
    ], id="scale-hint", className="hint", role="note")


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
            html.P(id="lede-defs", className="lede defs"),
        ], className="intro"),
        html.Div([
            html.Div([html.Span(t("period", lang), className="ctl-lbl"),
                      seg("period", [{"label": t(f"p_{k}", lang), "value": k}
                                     for k in PERIODS], "all")]),
            html.Div([html.Span([t("scale", lang), info("scale_tip", lang)],
                                className="ctl-lbl"),
                      seg("scale-mode", [{"label": t("linear", lang), "value": "linear"},
                                         {"label": t("log", lang), "value": "log"}],
                          "linear"),
                      scale_hint(lang)], className="ctl ctl--scale"),
            html.Div([html.Span([t("mgmt_fee", lang), html.B(id="mgmt-fee-val"),
                                 info("fee_tip", lang)], className="ctl-lbl"),
                      fee_slider("mgmt-fee", 0, 2.0, 0.1, PARAMS.mgmt_fee * 100, "%")],
                     className="ctl ctl--fee"),
            html.Div([html.Span([t("perf_fee", lang), html.B(id="perf-fee-val")],
                                className="ctl-lbl"),
                      fee_slider("perf-fee", 0, 30, 1, PARAMS.perf_fee * 100, "%")],
                     className="ctl ctl--fee"),
        ], className="controls"),
        html.Div([
            html.Section([
                html.Div([html.Div([html.H2(t("perf", lang)),
                                    info("chart_perf", lang)], className="h-row"),
                          html.Span(t("perf_note", lang), className="note")],
                         className="panel-head"),
                graph_box("main", "wealth"),
                html.P(id="fees-note", className="note small"),
            ], className="panel chart-panel"),
            html.Section([html.H2(t("kpis", lang)), html.Div(id="kpis")],
                         className="panel kpi-panel"),
        ], className="grid"),
        methodology(lang),
        html.Div([
            html.Section([
                html.Div([html.H2(t("model_title", lang))], className="h-row"),
                html.P(t("model_note", lang), className="note"),
                graph_box("model", "model-graph"),
            ], className="panel"),
            html.Section([
                html.H2(t("roll_side_title", lang)),
                html.P(t("roll_side_note", lang), className="note"),
                *[html.Div([html.Div([html.Span(t(k, lang), className="mini-lbl"),
                                      html.Span(id=f"{gid}-val", className="mini-val")],
                                     className="mini-head"),
                           graph_box("mini", gid)], className="mini")
                  for k, gid in (("rs_sharpe", "mini-sharpe"), ("rs_calmar", "mini-calmar"),
                                 ("rs_vol", "mini-vol"))],
            ], className="panel side-panel"),
        ], className="grid model-row"),
        html.Div([
            chart_panel("dd_title", "dd_note", "dd-graph", lang, "chart_dd"),
            chart_panel("alpha_title", "alpha_note", "alpha-graph", lang, "chart_alpha"),
        ], className="two-col risk-row"),
        dcc.Tabs(id="analysis-tabs2", value="roll", className="tabs", mobile_breakpoint=0,
                 children=[
            tab("t_roll", "roll"), tab("t_gap", "gap"),
            tab("t_ex", "ex"), tab("t_years", "years"), tab("t_risk", "risk"), tab("t_timing", "timing"),
        ], **PERSIST),
        html.Div(id="tab-body", className="tab-body"),
    ]


app = Dash(__name__, title="SPY3 Dashboard · SINTRO", external_stylesheets=[FONTS],
           update_title=None, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    dcc.Store(id="lang-pref", storage_type="local", data="en"),
    dcc.Store(id="viewport", data="wide"),
    dcc.Interval(id="viewport-tick", interval=2000, n_intervals=0),
    dcc.Interval(id="signal-tick", interval=10 * 60 * 1000, n_intervals=0),
    html.Header([
        html.A(html.Img(src=app.get_asset_url("sintro-logo.png"),
                        alt="SINTRO Asset Management", className="logo"),
               href="https://www.sintro.eu", target="_blank", rel="noopener noreferrer",
               className="logo-link", title="www.sintro.eu"),
        html.Div([html.Div(id="signal"), download_buttons(), lang_menu()],
                 className="top-right"),
        dcc.Download(id="dl-pdf"), dcc.Download(id="dl-xlsx"),
    ], className="topbar"),
    html.Div(t("dl_missing", "en", pkgs=", ".join(EXPORT_MISSING)) if EXPORT_MISSING else "",
             id="dl-warn", className="dl-warn" if EXPORT_MISSING else ""),
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


app.clientside_callback(
    "function(n) { return n ? 'hint hint--closed' : window.dash_clientside.no_update; }",
    Output("scale-hint", "className"), Input("hint-close", "n_clicks"), prevent_initial_call=True)


@app.callback(Output("signal", "children"), Input("lang-pref", "data"),
              Input("signal-tick", "n_intervals"))
def update_signal(lang, _n):
    """Aktuelles Signal; der Timer löst alle 10 Minuten eine Prüfung aus, neu geladen
    werden die Kurse höchstens alle 30 Minuten (spy3.live.REFRESH_MIN)."""
    return signal_badge(lang if lang in LANGS else "en")


# Bildschirmbreite melden, damit Charts auf Smartphones kompakter gezeichnet werden
# Nur die Stufe melden (kompakt/breit), nicht die Pixelbreite: sonst löst jede
# Pixeländerung ein Neuzeichnen der Reiterinhalte aus und der Chart flackert.
app.clientside_callback(
    """function(_, current) {
        const mode = window.innerWidth < 820 ? "compact" : "wide";
        return mode === current ? window.dash_clientside.no_update : mode;
    }""",
    Output("viewport", "data"), Input("viewport-tick", "n_intervals"),
    State("viewport", "data"))


# Menü nach Auswahl schließen (natives <details>, daher clientseitig)
app.clientside_callback(
    """function(lang) {
        const d = document.getElementById("lang-menu");
        if (d) { d.open = false; }
        document.documentElement.lang = lang || "de";
        return window.dash_clientside.no_update;
    }""",
    Output("lang-menu", "title"), Input("lang-pref", "data"))


@app.callback(Output("page", "children"),
              Output("footer", "children"), Output("lang-current", "children"),
              Output("dl-pdf-lbl", "children"), Output("dl-xlsx-lbl", "children"),
              *[Output(f"lang-{c}", "className") for c in LANGS],
              Input("lang-pref", "data"))
def render(lang):
    lang = lang if lang in LANGS else "en"
    opts = ["lang-opt is-current" if c == lang else "lang-opt" for c in LANGS]
    return (page(lang), t("footer", lang), lang.upper(),
            t("dl_pdf", lang), t("dl_xlsx", lang), *opts)


@lru_cache(maxsize=64)
def net_series(mgmt_pct: float, perf_pct: float) -> pd.Series:
    """Netto-Reihe für die gewählten Gebühren, über die volle Historie gerechnet
    (High-Water-Mark und Hurdle laufen seit Auflage, nicht seit Periodenbeginn)."""
    if (mgmt_pct, perf_pct) == (PARAMS.mgmt_fee * 100, PARAMS.perf_fee * 100):
        return BT.ret_pf_net
    return apply_fees(BT.ret_pf, BT.ret_bm, mgmt_pct / 100, perf_pct / 100)["ret_net"]


@app.callback(Output("wealth", "figure"), Output("kpis", "children"),
              Output("dd-graph", "figure"), Output("alpha-graph", "figure"),
              Output("model-graph", "figure"),
              Output("mini-sharpe", "figure"), Output("mini-calmar", "figure"),
              Output("mini-vol", "figure"),
              Output("mini-sharpe-val", "children"), Output("mini-calmar-val", "children"),
              Output("mini-vol-val", "children"),
              Output("fees-note", "children"), Output("lede-defs", "children"),
              Output("mgmt-fee-val", "children"), Output("perf-fee-val", "children"),
              Input("period", "value"), Input("scale-mode", "value"),
              Input("mgmt-fee", "value"), Input("perf-fee", "value"),
              Input("lang-pref", "data"), Input("viewport", "data"))
def update_main(period, scale, mgmt, perf, lang, vw):
    compact = vw == "compact"
    mgmt = PARAMS.mgmt_fee * 100 if mgmt is None else float(mgmt)
    perf = PARAMS.perf_fee * 100 if perf is None else float(perf)
    b, mixes = slice_bt(period, lang)
    b = b.assign(ret_pf_net=net_series(mgmt, perf).loc[b.index])
    fee_txt = t("fees_note", lang, mgmt=pct(mgmt / 100, 1, lang=lang),
                perf=pct(perf / 100, 0, lang=lang))
    defs_txt = t("lede_defs", lang, cost=f"{PARAMS.cost_bps:.0f}",
                 mgmt=pct(mgmt / 100, 1, lang=lang), perf=pct(perf / 100, 0, lang=lang))
    # SHY-Reihe weder im Vermögenschart noch in der Tabelle; Drawdown- und
    # Vorsprung-Chart behalten sie als Referenz
    shown = {k: v for k, v in mixes.items() if k != t("tsy_label", lang)}
    fig = plots.wealth_chart(b, shown, log=scale == "log", lang=lang, compact=compact)
    dd = plots.drawdown_chart(b, mixes, lang=lang, compact=compact)
    al = plots.alpha_chart(b, mixes, lang=lang, compact=compact)
    model = plots.model_chart(b, lang, log=scale == "log", compact=compact)
    minis, vals = [], []
    for metric, fmt in (("sharpe", ".2f"), ("calmar", ".2f"), ("vol", ".0%")):
        s_net = _rolling("net", metric, 3).loc[b.index[0]:b.index[-1]]
        s_bm = _rolling("sp", metric, 3).loc[b.index[0]:b.index[-1]]
        minis.append(plots.mini_chart({"SPY3": s_net, "S&P 500": s_bm}, fmt, lang, compact,
                                      zero_line=metric != "vol"))
        last = s_net.dropna().iloc[-1] if s_net.notna().any() else float("nan")
        vals.append(pct(last, 1, lang=lang) if metric == "vol" else dec(last, lang=lang))
    cols = {t("col_gross", lang): b.ret_pf, t("col_net", lang): b.ret_pf_net,
            "S&P 500": b.ret_bm, **shown}
    tbl = m.summary_table(cols, b.ret_bm, b.ret_off).loc[KPI_ORDER]
    hl = (t("col_net", lang),)
    col_tips = {t("col_gross", lang): tip("col_gross", lang),
                t("col_net", lang): tip("col_net", lang),
                "S&P 500": tip("col_bm", lang), "60/40": tip("col_mix", lang),
                t("tsy_label", lang): tip("col_tsy", lang)}
    tsy_note = ""
    if TSY_INFO.get("pre_end") is not None:
        names = {"SHY-Proxy": ("SHY-Proxy (US-Treasuries 1–3 Jahre)",
                               "SHY proxy (US Treasuries 1–3 years)"),
                 "LUATTRUU": ("Bloomberg US Treasury Index (alle Laufzeiten)",
                              "Bloomberg US Treasury index (all maturities)"),
                 "T-Bill": ("13-Wochen-T-Bills", "13-week T-bills")}
        key = TSY_INFO["pre_src"]
        if key == "none":
            tsy_note = t("tsy_note_none", lang)
        else:
            src = names.get(key, (key, key))[1 if lang == "en" else 0]
            tsy_note = t("tsy_note_splice", lang, d=f"{TSY_INFO['pre_end']:%m/%Y}", x=src)
    kpis = [table(tbl, lang, highlight=hl, emphasis=KPI_EMPHASIS, wrap_cls="fill",
                  tips=col_tips),
            html.P(t("kpi_note", lang) + (" " + tsy_note if tsy_note else ""),
                   className="note small")]
    return (fig, kpis, dd, al, model, *minis, *vals, fee_txt, defs_txt,
            pct(mgmt / 100, 1, lang=lang), pct(perf / 100, 0, lang=lang))




def risk_tab(b: pd.DataFrame, lang: str, compact: bool) -> html.Div:
    """Stresstests, VaR, Monte-Carlo und Korrelationen zu anderen Anlageklassen."""
    net, bm = b.ret_pf_net, b.ret_bm
    series = {t("net", lang): net, "S&P 500": bm,
              "60/40": rb.static_mix(bm, b.ret_off, 0.60)}
    stress = rk.stress_table(series)
    stress.columns = list(series) + ["MaxDD"]
    var = rk.var_table(series)
    res = rk.var_backtest(net)
    lbl = {"n": ("Beobachtungen", "Observations"), "breaches": ("Überschreitungen", "Breaches"),
           "expected": ("Erwartet", "Expected"), "rate": ("Quote", "Rate"),
           "lr": ("Kupiec-LR", "Kupiec LR")}
    i = 1 if lang == "en" else 0
    bt_tbl = pd.DataFrame({"SPY3": {
        lbl["n"][i]: dec(res["n"], 0, lang=lang),
        lbl["breaches"][i]: dec(res["breaches"], 0, lang=lang),
        lbl["expected"][i]: dec(res["expected"], 0, lang=lang),
        lbl["rate"][i]: pct(res["rate"], 2, lang=lang),
        lbl["lr"][i]: dec(res["lr"], lang=lang)}})
    mc = rk.monte_carlo_stats(net)
    mc_lbl = {"p5": ("P5", "P5"), "p50": ("Median", "Median"), "p95": ("P95", "P95"),
              "loss_prob": ("Verlustwahrscheinlichkeit", "Probability of a loss"),
              "avg_dd": ("Ø max. Drawdown", "Average max. drawdown"),
              "dd20_prob": ("P(Drawdown > 20 %)", "P(drawdown > 20%)")}
    mc_tbl = pd.DataFrame({"SPY3": {mc_lbl[k][i]: v for k, v in mc.items()}})

    assets = {}
    if not ASSET_RETURNS.empty:
        sl = ASSET_RETURNS.loc[b.index[0]:b.index[-1]]
        assets = {c: sl[c] for c in sl.columns if sl[c].notna().sum() > 60}
    corr = rk.correlation({**series, **assets})
    corr_block = [graph_box("corr", fig=plots.corr_heatmap(corr, lang, compact))]
    if not assets:
        corr_block.append(html.P(t("corr_missing", lang), className="note small"))

    parts = [
        section(t("stress_title", lang), t("stress_note", lang),
                graph(plots.stress_bars(stress, lang, compact)),
                table(stress, lang, fmt=lambda i_, v: pct(v, lang=lang),
                      row_label=t("phase", lang), highlight=(t("net", lang),))),
        section(t("var_title", lang), t("var_note", lang),
                table(var, lang, fmt=lambda i_, v: pct(v, 2, lang=lang),
                      highlight=(t("net", lang),)),
                graph_box("bars", fig=plots.return_hist(
                    net, var.loc["VaR 95%"].iloc[0], var.loc["VaR 99%"].iloc[0],
                    lang, compact))),
        section(t("mc_title", lang), t("mc_note", lang),
                graph_box("mc", fig=plots.mc_fan(rk.monte_carlo(net), lang, compact)),
                table(mc_tbl, lang, fmt=lambda i_, v: pct(v, lang=lang), wrap_cls="narrow")),
        section(t("corr_title", lang), t("corr_note", lang), *corr_block),
        section(t("var_bt_title", lang), t("var_bt_note", lang),
                table(bt_tbl, lang, fmt=lambda i_, v: v, wrap_cls="narrow")),
    ]
    if assets:
        beta = rk.beta_table(net, assets)
        beta.columns = ["Beta", "Korrelation" if lang == "de" else "Correlation"]
        parts.append(section(t("beta_title", lang), t("beta_note", lang),
                             table(beta, lang, fmt=lambda i_, v: dec(v, lang=lang))))
    return html.Div(parts, className="two-col")


@app.callback(Output("tab-body", "children"), Input("analysis-tabs2", "value"),
              Input("period", "value"), Input("lang-pref", "data"),
              Input("viewport", "data"))
def update_tab(tab, period, lang, vw):
    compact = vw == "compact"
    b, _ = slice_bt(period, lang)
    pf, bm = b.ret_pf, b.ret_bm
    if tab == "risk":
        return risk_tab(b, lang, compact)
    if tab == "gap":
        att = rb.attribution(pf, bm)
        att.columns = [t("excess_log", lang), t("share", lang)]
        att_tips = {t("excess_log", lang): tip("excess_log", lang),
                    t("share", lang): tip("share", lang)}
        return html.Div([
            section(t("cum_title", lang), t("cum_note", lang),
                    graph(plots.cum_excess_chart(b, lang, compact)), tip_key="excess_log", lang=lang),
            section(t("src_title", lang), t("src_note", lang),
                    graph_box("bars", fig=plots.attribution_bars(att, lang, compact)),
                    table(att, lang, fmt=lambda i, v: pct(v, lang=lang),
                          row_label=t("phase", lang), tips=att_tips)),
        ], className="two-col")
    if tab in (None, "roll"):
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
              Input("period", "value"), Input("lang-pref", "data"),
              Input("viewport", "data"))
def update_rolling(metric, years, period, lang, vw):
    compact = vw == "compact"
    metric = metric if metric in rl.METRICS else "sharpe"
    years = int(years or 3)
    b, _ = slice_bt(period, lang)
    start = b.index[0]
    fmt, _higher = rl.METRICS[metric]
    names = {"gross": t("gross", lang), "net": t("net", lang), "sp": "S&P 500",
             "6040": "60/40"}
    keys = ["gross", "net", "6040"] if metric == "excess" else list(names)
    series = {names[k]: _rolling(k, metric, years).loc[start:] for k in keys}
    fig = plots.rolling_chart(series, fmt, metric in ("excess", "sharpe", "calmar"),
                              lang, compact)

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


# ---------- Downloads -------------------------------------------------------
def _export_frame(period, mgmt, perf, lang):
    mgmt = PARAMS.mgmt_fee * 100 if mgmt is None else float(mgmt)
    perf = PARAMS.perf_fee * 100 if perf is None else float(perf)
    b, mixes = slice_bt(period or "all", lang)
    b = b.assign(ret_pf_net=net_series(mgmt, perf).loc[b.index])
    return b, mixes, mgmt, perf


@app.callback(Output("dl-pdf", "data"), Input("btn-pdf", "n_clicks"),
              State("period", "value"), State("mgmt-fee", "value"),
              State("perf-fee", "value"), State("lang-pref", "data"),
              prevent_initial_call=True)
def download_pdf(_n, period, mgmt, perf, lang):
    if EXPORT_MISSING:
        return no_update
    lang = lang if lang in LANGS else "en"
    b, mixes, mgmt, perf = _export_frame(period, mgmt, perf, lang)
    pdf = rp.build_pdf(b, mixes, lang, PARAMS.cost_bps, mgmt / 100, perf / 100)
    name = f"SPY3-report-{b.index[-1]:%Y-%m-%d}.pdf"
    return dcc.send_bytes(lambda buf: buf.write(pdf), name)


@app.callback(Output("dl-xlsx", "data"), Input("btn-xlsx", "n_clicks"),
              State("period", "value"), State("mgmt-fee", "value"),
              State("perf-fee", "value"), State("lang-pref", "data"),
              prevent_initial_call=True)
def download_xlsx(_n, period, mgmt, perf, lang):
    if EXPORT_MISSING:
        return no_update
    lang = lang if lang in LANGS else "en"
    b, mixes, mgmt, perf = _export_frame(period, mgmt, perf, lang)
    xlsx = rp.build_xlsx(b, mixes, lang)
    name = f"SPY3-data-{b.index[-1]:%Y-%m-%d}.xlsx"
    return dcc.send_bytes(lambda buf: buf.write(xlsx), name)


if __name__ == "__main__":
    app.run(debug=False)
