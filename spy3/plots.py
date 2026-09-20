"""Plotly-Charts im SINTRO-Stil (zweisprachig)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from . import metrics as m
from .i18n import t, term
from .robustness import CRISES, excess_log, rolling_excess

NAVY = "#003274"
INK = "#1B2638"
SLATE = "#8C96A5"
LINE = "#E4E8EE"
MUTED = "#5E6B7D"
RISK_OFF = "rgba(206, 62, 52, 0.17)"
RISK_OFF_SOFT = "rgba(206, 62, 52, 0.09)"
VAR_GREY = "#9AA3AF"
NET = "#1F6B45"
MIX = "#B38B4D"
MIX2 = "#7A8FB5"
MIX_COLORS = [MIX, MIX2]
FONT = "Garet, Jost, 'Segoe UI', Helvetica, Arial, sans-serif"
START = 1_000
SEP = {"de": ",.", "en": ".,"}

pio.templates["sintro"] = go.layout.Template(layout=dict(
    font=dict(family=FONT, color=INK, size=17),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    colorway=[NAVY, NET, SLATE, MIX],
    margin=dict(l=8, r=8, t=28, b=8),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="white", bordercolor=LINE, font=dict(family=FONT, color=INK)),
    legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0,
                font=dict(color=MUTED, size=16), bgcolor="rgba(0,0,0,0)"),
    xaxis=dict(showgrid=False, linecolor=LINE, tickcolor=LINE, ticks="outside",
               tickfont=dict(color=MUTED, size=15), zeroline=False, automargin=True),
    yaxis=dict(gridcolor=LINE, zeroline=False, tickfont=dict(color=MUTED, size=15),
               ticks="", automargin=True),
))
TEMPLATE = "sintro"


def _base(fig: go.Figure, lang: str, compact: bool = False, **kw) -> go.Figure:
    """compact=True: kleinere Schrift, engere Ränder, weniger Ticks – für Smartphones."""
    fig.update_layout(template=TEMPLATE, separators=SEP.get(lang, ",."), **kw)
    if compact:
        fig.update_layout(font=dict(size=13),
                          legend=dict(font=dict(size=11.5), y=1.02, itemwidth=30, tracegroupgap=2),
                          margin=dict(l=4, r=4, t=22, b=4),
                          xaxis=dict(tickfont=dict(size=11), nticks=5),
                          yaxis=dict(tickfont=dict(size=11), nticks=6))
        if "yaxis2" in fig.layout:              # zweite Achse nur, wenn vorhanden
            fig.update_layout(yaxis2=dict(tickfont=dict(size=11), title=None, nticks=5))
    return fig


def _risk_off_shapes(position: pd.Series, color: str = RISK_OFF):
    off = position.eq(0)
    grp = (off != off.shift()).cumsum()
    return [dict(type="rect", xref="x", yref="paper", x0=seg.index[0], x1=seg.index[-1],
                 y0=0, y1=1, fillcolor=color, line_width=0, layer="below")
            for _, seg in position[off].groupby(grp[off])]


def _legend_box(fig: go.Figure, name: str):
    fig.add_scatter(x=[None], y=[None], mode="markers", name=name,
                    marker=dict(symbol="square", size=12, color=RISK_OFF))


def wealth_chart(bt: pd.DataFrame, extra: dict[str, pd.Series] | None = None,
                 log: bool = True, lang: str = "de", compact: bool = False) -> go.Figure:
    """Wert von 1.000 USD; ohne Drawdown (eigener Chart)."""
    fig = go.Figure()
    hov = "%{y:,.0f} USD"
    fig.add_scatter(x=bt.index, y=START * (1 + bt.ret_bm).cumprod(), name="S&P 500",
                    line=dict(color=SLATE, width=1.5), hovertemplate=hov)
    for i, (k, s) in enumerate((extra or {}).items()):
        fig.add_scatter(x=s.index, y=START * (1 + s).cumprod(), name=k,
                        line=dict(color=MIX_COLORS[i % 2], width=1.4, dash="dot"),
                        hovertemplate=hov)
    fig.add_scatter(x=bt.index, y=START * (1 + bt.ret_pf).cumprod(), name=t("gross", lang),
                    line=dict(color=NAVY, width=1.3), hovertemplate=hov)
    if "ret_pf_net" in bt:
        fig.add_scatter(x=bt.index, y=START * (1 + bt.ret_pf_net).cumprod(),
                        name=t("net", lang), line=dict(color=NET, width=2.1),
                        hovertemplate=hov)
    if "var_1d" in bt:
        fig.add_scatter(x=bt.index, y=bt.var_1d, name=t("var_line", lang), yaxis="y2",
                        line=dict(color=VAR_GREY, width=1, dash="dash"), opacity=0.85,
                        hovertemplate="%{y:.2%}")
    _legend_box(fig, t("riskoff", lang))
    lo = START * min((1 + bt.ret_pf).cumprod().min(), (1 + bt.ret_bm).cumprod().min())
    hi = START * max((1 + bt.ret_pf).cumprod().max(), (1 + bt.ret_bm).cumprod().max())
    wide = hi / lo > 4
    fig.update_yaxes(type="log" if log else "linear", tickformat=",.0f",
                     dtick="D2" if log and wide else None)
    fig.update_xaxes(showline=True)
    # Zweite Wertachse rechts für den VaR
    var_axis = dict(overlaying="y", side="right", showgrid=False, zeroline=False,
                    rangemode="tozero", tickformat=".0%", ticks="outside", ticklen=3,
                    dtick=0.02, automargin=True,
                    range=[0, float(bt.var_1d.max()) * 1.15] if "var_1d" in bt else None,
                    tickfont=dict(color=VAR_GREY, size=15), linecolor=LINE,
                    tickcolor=LINE, title=dict(text=t("var_axis", lang),
                                               font=dict(color=VAR_GREY, size=15)))
    return _base(fig, lang, compact, shapes=_risk_off_shapes(bt.position),
                 yaxis2=var_axis if "var_1d" in bt else None)


def drawdown_chart(bt: pd.DataFrame, extra: dict[str, pd.Series] | None = None,
                   lang: str = "de", compact: bool = False) -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(x=bt.index, y=m.drawdown(bt.ret_bm), name="S&P 500",
                    line=dict(color=SLATE, width=1), fill="tozeroy",
                    fillcolor="rgba(140,150,165,0.12)", hovertemplate="%{y:.1%}")
    for i, (k, s) in enumerate((extra or {}).items()):
        fig.add_scatter(x=s.index, y=m.drawdown(s), name=k,
                        line=dict(color=MIX_COLORS[i % 2], width=1.2, dash="dot"),
                        hovertemplate="%{y:.1%}")
    fig.add_scatter(x=bt.index, y=m.drawdown(bt.ret_pf), name=t("gross", lang),
                    line=dict(color=NAVY, width=1.1), hovertemplate="%{y:.1%}")
    if "ret_pf_net" in bt:
        fig.add_scatter(x=bt.index, y=m.drawdown(bt.ret_pf_net), name=t("net", lang),
                        line=dict(color=NET, width=1.8), hovertemplate="%{y:.1%}")
    fig.update_yaxes(tickformat=".0%")
    return _base(fig, lang, compact, shapes=_risk_off_shapes(bt.position, RISK_OFF_SOFT))


def alpha_chart(bt: pd.DataFrame, extra: dict[str, pd.Series] | None = None,
                lang: str = "de", compact: bool = False) -> go.Figure:
    """Vermögen relativ zum S&P 500 (Vielfaches). 3,0x = dreifaches Endvermögen.

    Die frühere Darstellung nutzte Log-Punkte: +110 Log-Punkte entsprechen 3,0x.
    Das Vielfache ist direkt interpretierbar und passt zu den Total Returns.
    """
    fig = go.Figure()
    hov = "%{y:,.2f}x"
    wb = (1 + bt.ret_bm).cumprod()
    for i, (k, s) in enumerate((extra or {}).items()):
        fig.add_scatter(x=s.index, y=(1 + s).cumprod() / wb, name=k,
                        line=dict(color=MIX_COLORS[i % 2], width=1.2, dash="dot"),
                        hovertemplate=hov)
    fig.add_scatter(x=bt.index, y=(1 + bt.ret_pf).cumprod() / wb, name=t("gross", lang),
                    line=dict(color=NAVY, width=1.1), hovertemplate=hov)
    if "ret_pf_net" in bt:
        fig.add_scatter(x=bt.index, y=(1 + bt.ret_pf_net).cumprod() / wb,
                        name=t("net", lang), line=dict(color=NET, width=1.8),
                        hovertemplate=hov)
    fig.add_hline(y=1, line=dict(color=INK, width=1))
    fig.update_yaxes(tickformat=",.1f", ticksuffix="x")
    return _base(fig, lang, compact, shapes=_risk_off_shapes(bt.position, RISK_OFF_SOFT))


def relative_chart(bt: pd.DataFrame, lang: str = "de", compact: bool = False) -> go.Figure:
    ratio = (1 + bt.ret_pf).cumprod() / (1 + bt.ret_bm).cumprod()
    fig = go.Figure(go.Scatter(x=ratio.index, y=ratio, line=dict(color=NAVY, width=2),
                               name="SPY3 / S&P 500", hovertemplate="%{y:,.3f}"))
    lo, hi = bt.index[0], bt.index[-1]
    for n, (a, b) in CRISES.items():
        if pd.Timestamp(b) < lo or pd.Timestamp(a) > hi:
            continue
        fig.add_vrect(x0=max(pd.Timestamp(a), lo), x1=min(pd.Timestamp(b), hi),
                      fillcolor=SLATE, opacity=0.1, line_width=0,
                      annotation_text=term(n.split(" ")[0], lang),
                      annotation_position="top left",
                      annotation_font=dict(size=15, color=MUTED))
    fig.add_hline(y=1, line=dict(color=LINE, width=1))
    wide = ratio.max() / ratio.min() > 4
    return _base(fig, lang, compact, yaxis_type="log", yaxis_dtick="D2" if wide else None,
                 yaxis_tickformat=",.2f", showlegend=False)


def rolling_excess_chart(bt: pd.DataFrame, years=(3, 5), lang: str = "de") -> go.Figure:
    fig = go.Figure()
    for y, c in zip(years, [SLATE, NAVY]):
        s = rolling_excess(bt.ret_pf, bt.ret_bm, y)
        fig.add_scatter(x=s.index, y=s, name=t("years_n", lang, y=y),
                        line=dict(color=c, width=1.8), hovertemplate="%{y:+.1%}")
    fig.add_hline(y=0, line=dict(color=INK, width=1))
    return _base(fig, lang, compact, yaxis_tickformat="+.0%")


def attribution_bars(att: pd.DataFrame, lang: str = "de", compact: bool = False) -> go.Figure:
    """Beitrag der Krisenphasen zur Überschussrendite (Log-Punkte)."""
    d = att.drop(index=[i for i in att.index if i.startswith(("Gesamt", "Total"))])
    vals = d.iloc[:, 0]
    fig = go.Figure(go.Bar(x=vals.values, y=[term(i, lang) for i in d.index], orientation="h",
                           marker_color=[NAVY if v >= 0 else "#C53A30" for v in vals],
                           hovertemplate="%{x:+.1%}<extra></extra>"))
    fig.update_xaxes(tickformat="+.0%", zeroline=True, zerolinecolor=INK, zerolinewidth=1)
    fig.update_yaxes(autorange="reversed")
    return _base(fig, lang, compact, showlegend=False, height=260, hovermode="closest",
                 margin=dict(l=8, r=8, t=10, b=8))


def cum_excess_chart(bt: pd.DataFrame, lang: str = "de", compact: bool = False) -> go.Figure:
    ex = excess_log(bt.ret_pf, bt.ret_bm).cumsum()
    fig = go.Figure(go.Scatter(x=ex.index, y=ex, fill="tozeroy",
                               line=dict(color=NAVY, width=1.8),
                               fillcolor="rgba(0,50,116,0.08)", hovertemplate="%{y:+.1%}"))
    return _base(fig, lang, compact, yaxis_tickformat="+.0%", height=300, showlegend=False)


def rolling_chart(series: dict[str, pd.Series], fmt: str, zero_line: bool,
                  lang: str = "de", compact: bool = False) -> go.Figure:
    """series: Name -> Zeitreihe; Stil nach Name (brutto, netto, S&P 500, 60/40)."""
    styles = {
        t("gross", lang): dict(color=NAVY, width=1.1),
        t("net", lang): dict(color=NET, width=1.9),
        "S&P 500": dict(color=SLATE, width=1.4),
        "60/40": dict(color=MIX, width=1.3, dash="dot"),
    }
    tick = ".0%" if fmt == "pct" else ",.1f"
    hov = "%{y:.1%}" if fmt == "pct" else "%{y:,.2f}"
    fig = go.Figure()
    for name in ["S&P 500", "60/40", t("gross", lang), t("net", lang)]:
        if name in series:
            s = series[name].dropna()
            fig.add_scatter(x=s.index, y=s, name=name, line=styles[name], hovertemplate=hov)
    if zero_line:
        fig.add_hline(y=0, line=dict(color=INK, width=1))
    fig.update_yaxes(tickformat=tick)
    return _base(fig, lang, compact)


HEAT = [[0, "#B03A2E"], [0.5, "#F4F6F9"], [1, "#12603C"]]


def mc_fan(paths: pd.DataFrame, lang: str = "de", compact: bool = False) -> go.Figure:
    """Monte-Carlo-Perzentilpfade als Fächer."""
    x = paths.index
    fig = go.Figure()
    for lo, hi, a in (("P5", "P95", 0.10), ("P25", "P75", 0.20)):
        fig.add_scatter(x=x, y=paths[hi], line=dict(width=0), showlegend=False,
                        hoverinfo="skip")
        fig.add_scatter(x=x, y=paths[lo], line=dict(width=0), fill="tonexty",
                        fillcolor=f"rgba(0,50,116,{a})", name=f"{lo}–{hi}",
                        hovertemplate="%{y:,.2f}x")
    fig.add_scatter(x=x, y=paths["P50"], line=dict(color=NAVY, width=2), name="P50",
                    hovertemplate="%{y:,.2f}x")
    fig.add_hline(y=1, line=dict(color=INK, width=1))
    fig.update_yaxes(tickformat=",.2f", ticksuffix="x")
    fig.update_xaxes(title=t("mc_x", lang))
    return _base(fig, lang, compact, height=320)


def corr_heatmap(c: pd.DataFrame, lang: str = "de", compact: bool = False) -> go.Figure:
    z = c.to_numpy(dtype=float)
    txt = [[("–" if not np.isfinite(v) else
             (f"{v:,.2f}".replace(".", ",") if lang == "de" else f"{v:,.2f}"))
            for v in row] for row in z]
    fig = go.Figure(go.Heatmap(z=z, x=list(c.columns), y=list(c.index), text=txt,
                               texttemplate="%{text}",
                               textfont=dict(size=10 if compact else 12),
                               colorscale=HEAT, zmid=0, zmin=-1, zmax=1, xgap=2, ygap=2,
                               showscale=False,
                               hovertemplate="%{y} / %{x}: %{z:.2f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(side="bottom", tickangle=-40)
    return _base(fig, lang, compact, hovermode="closest",
                 height=max(260, 30 * len(c) + 120),
                 margin=dict(l=8, r=8, t=10, b=8))


def return_hist(r: pd.Series, var95: float, var99: float, lang: str = "de",
                compact: bool = False) -> go.Figure:
    """Verteilung der Tagesrenditen mit den VaR-Schwellen."""
    sp = "" if lang == "en" else " "
    fig = go.Figure(go.Histogram(x=r, nbinsx=90, marker_color=NAVY, opacity=0.8,
                                 hovertemplate="%{x:.2%}: %{y}<extra></extra>"))
    for v, name, col in ((-var95, f"VaR 95{sp}%", MIX), (-var99, f"VaR 99{sp}%", "#C53A30")):
        fig.add_vline(x=v, line=dict(color=col, width=1.4, dash="dash"),
                      annotation_text=name, annotation_position="top left",
                      annotation_font=dict(size=12, color=col))
    fig.update_xaxes(tickformat=".0%", range=[r.quantile(0.002), r.quantile(0.998)])
    fig.update_yaxes(title=None)
    return _base(fig, lang, compact, height=300, showlegend=False, hovermode="closest")


def stress_bars(st: pd.DataFrame, lang: str = "de", compact: bool = False) -> go.Figure:
    """Rendite je Stressfenster als Balken (SPY3 gegen Benchmark)."""
    cols = [c for c in st.columns if c != "MaxDD"][:3]
    colors = {0: NET, 1: SLATE, 2: MIX}
    fig = go.Figure()
    for i, c in enumerate(cols):
        fig.add_bar(y=[term(i2, lang) for i2 in st.index], x=st[c], name=c,
                    orientation="h", marker_color=colors.get(i, SLATE),
                    hovertemplate="%{x:+.1%}<extra></extra>")
    fig.update_xaxes(tickformat="+.0%", zeroline=True, zerolinecolor=INK, zerolinewidth=1)
    fig.update_yaxes(autorange="reversed")
    return _base(fig, lang, compact, barmode="group", bargap=0.25,
                 height=max(280, 34 * len(st) + 80), hovermode="closest")


MR_COLOR = "#B8860B"


def model_chart(bt: pd.DataFrame, lang: str = "de", log: bool = True,
                compact: bool = False) -> go.Figure:
    """Blick ins Modell: SPY-Kurs mit den Faktoren, VaR auf der zweiten Achse.

    Die gleitenden Durchschnitte laufen im Modell über 29 und 198 Tage; im Chart
    werden sie der Lesbarkeit halber als 30d/200d bezeichnet.
    """
    fig = go.Figure()
    hov = "%{y:,.2f}"
    fig.add_scatter(x=bt.index, y=bt.price, name=t("m_price", lang),
                    line=dict(color=INK, width=1.3), hovertemplate=hov)
    fig.add_scatter(x=bt.index, y=bt.ma_fast, name=t("m_fast", lang),
                    line=dict(color=NAVY, width=1.1), hovertemplate=hov)
    fig.add_scatter(x=bt.index, y=bt.ma_slow, name=t("m_slow", lang),
                    line=dict(color="#C0392B", width=1.3), hovertemplate=hov)
    fig.add_scatter(x=bt.index, y=bt.high_disc, name=t("m_mr", lang),
                    line=dict(color=MR_COLOR, width=1.1, dash="dot"), hovertemplate=hov)
    fig.add_scatter(x=bt.index, y=bt.var_1d, name=t("m_var", lang), yaxis="y2",
                    line=dict(color=VAR_GREY, width=1, dash="dash"), opacity=0.85,
                    hovertemplate="%{y:.2%}")
    for y, col, key in ((0.05, "#C53A30", "m_var_high"), (0.02, "#1E8A5A", "m_var_low")):
        fig.add_scatter(x=[bt.index[0], bt.index[-1]], y=[y, y], yaxis="y2", name=t(key, lang),
                        mode="lines", line=dict(color=col, width=1, dash="dash"),
                        hoverinfo="skip")
    _legend_box(fig, t("riskoff", lang))
    fig.update_yaxes(type="log" if log else "linear", tickformat=",.0f")
    fig.update_xaxes(showline=True)
    _base(fig, lang, compact, shapes=_risk_off_shapes(bt.position),
          yaxis2=dict(overlaying="y", side="right", showgrid=False, zeroline=False,
                      rangemode="tozero", tickformat=".0%", dtick=0.02, automargin=True,
                      range=[0, max(0.07, float(bt.var_1d.max()) * 1.1)],
                      tickfont=dict(color=VAR_GREY, size=13 if not compact else 11),
                      title=dict(text=t("var_axis", lang),
                                 font=dict(color=VAR_GREY, size=13 if not compact else 11))))
    return fig


def mini_chart(series: dict[str, pd.Series], fmt: str, lang: str = "de",
               compact: bool = False, zero_line: bool = False) -> go.Figure:
    """Kleiner Verlauf für die Seitenleiste: SPY3 netto vs. S&P 500."""
    styles = [dict(color=NET, width=1.6), dict(color=SLATE, width=1.1)]
    fig = go.Figure()
    for (name, s), st in zip(series.items(), styles):
        fig.add_scatter(x=s.index, y=s, name=name, line=st,
                        hovertemplate="%{y:" + fmt.strip("%") + ("%}" if "%" in fmt else "}"))
    if zero_line:
        fig.add_hline(y=0, line=dict(color=INK, width=0.8))
    fig.update_yaxes(tickformat=fmt, nticks=4)
    fig.update_xaxes(nticks=4)
    _base(fig, lang, compact, height=150, showlegend=False,
          margin=dict(l=4, r=4, t=4, b=4))
    return fig
