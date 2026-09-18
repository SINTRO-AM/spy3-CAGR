"""Plotly-Charts im SINTRO-Stil (zweisprachig)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from . import metrics as m
from .i18n import t, term
from .risk import LIVE_START
from .robustness import CRISES, excess_log, rolling_excess

NAVY = "#003274"
INK = "#1B2638"
SLATE = "#8C96A5"
LINE = "#E4E8EE"
MUTED = "#5E6B7D"
RISK_OFF = "rgba(206, 62, 52, 0.17)"
RISK_OFF_SOFT = "rgba(206, 62, 52, 0.09)"
NET = "#1F6B45"
MIX = "#B38B4D"
FONT = "Jost, 'Segoe UI', Helvetica, Arial, sans-serif"
START = 1_000
VAR_COLOR = "#2E7D8F"
HEAT = [[0, "#B03A2E"], [0.5, "#F4F6F9"], [1, "#12603C"]]
SEP = {"de": ",.", "en": ".,"}

pio.templates["sintro"] = go.layout.Template(layout=dict(
    font=dict(family=FONT, color=INK, size=13),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    colorway=[NAVY, NET, SLATE, MIX],
    margin=dict(l=8, r=8, t=28, b=8),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="white", bordercolor=LINE, font=dict(family=FONT, color=INK)),
    legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0, font=dict(color=MUTED),
                bgcolor="rgba(0,0,0,0)"),
    xaxis=dict(showgrid=False, linecolor=LINE, tickcolor=LINE, ticks="outside",
               tickfont=dict(color=MUTED), zeroline=False, automargin=True),
    yaxis=dict(gridcolor=LINE, zeroline=False, tickfont=dict(color=MUTED), ticks="",
               automargin=True),
))
TEMPLATE = "sintro"


def _base(fig: go.Figure, lang: str, **kw) -> go.Figure:
    fig.update_layout(template=TEMPLATE, separators=SEP.get(lang, ",."), **kw)
    return fig


def _risk_off_shapes(position: pd.Series, color: str = RISK_OFF):
    off = position.eq(0)
    grp = (off != off.shift()).cumsum()
    return [dict(type="rect", xref="x", yref="paper", x0=seg.index[0], x1=seg.index[-1],
                 y0=0, y1=1, fillcolor=color, line_width=0, layer="below")
            for _, seg in position[off].groupby(grp[off])]


def _live_line(fig: go.Figure, idx: pd.DatetimeIndex, lang: str, yref: str = "paper"):
    """Gestrichelte Linie am Start des Live-Track-Records."""
    d = pd.Timestamp(LIVE_START)
    if idx[0] <= d <= idx[-1]:
        fig.add_vline(x=d, line=dict(color=INK, width=1.2, dash="dash"),
                      annotation_text=t("live_since", lang), annotation_position="top left",
                      annotation_font=dict(size=11, color=INK),
                      annotation_bgcolor="rgba(255,255,255,0.75)")


def _legend_box(fig: go.Figure, name: str):
    fig.add_scatter(x=[None], y=[None], mode="markers", name=name,
                    marker=dict(symbol="square", size=12, color=RISK_OFF))


def wealth_chart(bt: pd.DataFrame, extra: dict[str, pd.Series] | None = None,
                 log: bool = True, lang: str = "de") -> go.Figure:
    """Wert von 1.000 USD; ohne Drawdown (eigener Chart)."""
    fig = go.Figure()
    hov = "%{y:,.0f} USD"
    fig.add_scatter(x=bt.index, y=START * (1 + bt.ret_bm).cumprod(), name="S&P 500",
                    line=dict(color=SLATE, width=1.5), hovertemplate=hov)
    for k, s in (extra or {}).items():
        fig.add_scatter(x=s.index, y=START * (1 + s).cumprod(), name=k,
                        line=dict(color=MIX, width=1.4, dash="dot"), hovertemplate=hov)
    fig.add_scatter(x=bt.index, y=START * (1 + bt.ret_pf).cumprod(), name=t("gross", lang),
                    line=dict(color=NAVY, width=1.3), hovertemplate=hov)
    if "ret_pf_net" in bt:
        fig.add_scatter(x=bt.index, y=START * (1 + bt.ret_pf_net).cumprod(),
                        name=t("net", lang), line=dict(color=NET, width=2.1),
                        hovertemplate=hov)
    if "var_1d" in bt:
        fig.add_scatter(x=bt.index, y=bt.var_1d, name=t("var_line", lang), yaxis="y2",
                        line=dict(color=VAR_COLOR, width=1), opacity=0.65,
                        hovertemplate="%{y:.2%}")
    _legend_box(fig, t("riskoff", lang))
    lo = START * min((1 + bt.ret_pf).cumprod().min(), (1 + bt.ret_bm).cumprod().min())
    hi = START * max((1 + bt.ret_pf).cumprod().max(), (1 + bt.ret_bm).cumprod().max())
    wide = hi / lo > 4
    fig.update_yaxes(type="log" if log else "linear", tickformat=",.0f",
                     dtick="D2" if log and wide else None)
    fig.update_xaxes(showline=True)
    _base(fig, lang, shapes=_risk_off_shapes(bt.position),
          yaxis2=dict(overlaying="y", side="right", showgrid=False, tickformat=".0%",
                      tickfont=dict(color=VAR_COLOR), title=None, rangemode="tozero",
                      zeroline=False))
    _live_line(fig, bt.index, lang)
    return fig


def drawdown_chart(bt: pd.DataFrame, extra: dict[str, pd.Series] | None = None,
                   lang: str = "de") -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(x=bt.index, y=m.drawdown(bt.ret_bm), name="S&P 500",
                    line=dict(color=SLATE, width=1), fill="tozeroy",
                    fillcolor="rgba(140,150,165,0.12)", hovertemplate="%{y:.1%}")
    for k, s in (extra or {}).items():
        fig.add_scatter(x=s.index, y=m.drawdown(s), name=k,
                        line=dict(color=MIX, width=1.2, dash="dot"), hovertemplate="%{y:.1%}")
    fig.add_scatter(x=bt.index, y=m.drawdown(bt.ret_pf), name=t("gross", lang),
                    line=dict(color=NAVY, width=1.1), hovertemplate="%{y:.1%}")
    if "ret_pf_net" in bt:
        fig.add_scatter(x=bt.index, y=m.drawdown(bt.ret_pf_net), name=t("net", lang),
                        line=dict(color=NET, width=1.8), hovertemplate="%{y:.1%}")
    fig.update_yaxes(tickformat=".0%")
    _base(fig, lang, shapes=_risk_off_shapes(bt.position, RISK_OFF_SOFT))
    _live_line(fig, bt.index, lang)
    return fig


def alpha_chart(bt: pd.DataFrame, extra: dict[str, pd.Series] | None = None,
                lang: str = "de") -> go.Figure:
    """Vermögen relativ zum S&P 500 (Vielfaches). 3,0x = dreifaches Endvermögen.

    Die frühere Darstellung nutzte Log-Punkte: +110 Log-Punkte entsprechen 3,0x.
    Das Vielfache ist direkt interpretierbar und passt zu den Total Returns.
    """
    fig = go.Figure()
    hov = "%{y:,.2f}x"
    wb = (1 + bt.ret_bm).cumprod()
    for k, s in (extra or {}).items():
        fig.add_scatter(x=s.index, y=(1 + s).cumprod() / wb, name=k,
                        line=dict(color=MIX, width=1.2, dash="dot"), hovertemplate=hov)
    fig.add_scatter(x=bt.index, y=(1 + bt.ret_pf).cumprod() / wb, name=t("gross", lang),
                    line=dict(color=NAVY, width=1.1), hovertemplate=hov)
    if "ret_pf_net" in bt:
        fig.add_scatter(x=bt.index, y=(1 + bt.ret_pf_net).cumprod() / wb,
                        name=t("net", lang), line=dict(color=NET, width=1.8),
                        hovertemplate=hov)
    fig.add_hline(y=1, line=dict(color=INK, width=1))
    fig.update_yaxes(tickformat=",.1f", ticksuffix="x")
    _base(fig, lang, shapes=_risk_off_shapes(bt.position, RISK_OFF_SOFT))
    _live_line(fig, bt.index, lang)
    return fig


def relative_chart(bt: pd.DataFrame, lang: str = "de") -> go.Figure:
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
                      annotation_font=dict(size=11, color=MUTED))
    fig.add_hline(y=1, line=dict(color=LINE, width=1))
    wide = ratio.max() / ratio.min() > 4
    return _base(fig, lang, yaxis_type="log", yaxis_dtick="D2" if wide else None,
                 yaxis_tickformat=",.2f", showlegend=False)


def rolling_excess_chart(bt: pd.DataFrame, years=(3, 5), lang: str = "de") -> go.Figure:
    fig = go.Figure()
    for y, c in zip(years, [SLATE, NAVY]):
        s = rolling_excess(bt.ret_pf, bt.ret_bm, y)
        fig.add_scatter(x=s.index, y=s, name=t("years_n", lang, y=y),
                        line=dict(color=c, width=1.8), hovertemplate="%{y:+.1%}")
    fig.add_hline(y=0, line=dict(color=INK, width=1))
    return _base(fig, lang, yaxis_tickformat="+.0%")


def attribution_bars(att: pd.DataFrame, lang: str = "de") -> go.Figure:
    """Beitrag der Krisenphasen zur Überschussrendite (Log-Punkte)."""
    d = att.drop(index=[i for i in att.index if i.startswith(("Gesamt", "Total"))])
    vals = d.iloc[:, 0]
    fig = go.Figure(go.Bar(x=vals.values, y=[term(i, lang) for i in d.index], orientation="h",
                           marker_color=[NAVY if v >= 0 else "#C53A30" for v in vals],
                           hovertemplate="%{x:+.1%}<extra></extra>"))
    fig.update_xaxes(tickformat="+.0%", zeroline=True, zerolinecolor=INK, zerolinewidth=1)
    fig.update_yaxes(autorange="reversed")
    return _base(fig, lang, showlegend=False, height=260, hovermode="closest",
                 margin=dict(l=8, r=8, t=10, b=8))


def cum_excess_chart(bt: pd.DataFrame, lang: str = "de") -> go.Figure:
    ex = excess_log(bt.ret_pf, bt.ret_bm).cumsum()
    fig = go.Figure(go.Scatter(x=ex.index, y=ex, fill="tozeroy",
                               line=dict(color=NAVY, width=1.8),
                               fillcolor="rgba(0,50,116,0.08)", hovertemplate="%{y:+.1%}"))
    return _base(fig, lang, yaxis_tickformat="+.0%", height=300, showlegend=False)


def rolling_chart(series: dict[str, pd.Series], fmt: str, zero_line: bool,
                  lang: str = "de") -> go.Figure:
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
    return _base(fig, lang)


def monthly_heatmap(mt: pd.DataFrame, lang: str = "de") -> go.Figure:
    """Monatsrenditen: Zeilen Jahre, Spalten Monate."""
    months = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt",
              "Nov", "Dez"] if lang == "de" else \
             ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct",
              "Nov", "Dec"]
    z = mt.reindex(columns=range(1, 13)).to_numpy(dtype=float)
    lim = float(np.nanmax(np.abs(z))) if np.isfinite(z).any() else 0.1
    txt = [["" if not np.isfinite(v) else f"{v * 100:.1f}" for v in row] for row in z]
    fig = go.Figure(go.Heatmap(
        z=z, x=months, y=[str(i) for i in mt.index], text=txt, texttemplate="%{text}",
        textfont=dict(size=10), colorscale=HEAT, zmid=0, zmin=-lim, zmax=lim,
        xgap=2, ygap=2, showscale=False, hovertemplate="%{y} %{x}: %{z:+.2%}<extra></extra>"))
    fig.update_xaxes(side="top", showline=False, ticks="")
    fig.update_yaxes(type="category", tickmode="array", tickfont=dict(size=10),
                     tickvals=[str(i) for i in mt.index],
                     autorange="reversed" if mt.index[0] > mt.index[-1] else True)
    return _base(fig, lang, hovermode="closest", height=max(240, 26 * len(mt) + 60),
                 margin=dict(l=8, r=8, t=26, b=8))


def yearly_bars(y: pd.DataFrame, lang: str = "de") -> go.Figure:
    """Jahresrenditen SPY3 und S&P 500 als Balken, Differenz als Linie."""
    cols = list(y.columns)
    fig = go.Figure()
    for c, col in zip(cols[:2], [NAVY, SLATE]):
        fig.add_bar(x=[str(i) for i in y.index], y=y[c], name=c, marker_color=col,
                    hovertemplate="%{y:+.1%}")
    if len(cols) > 2:
        fig.add_scatter(x=[str(i) for i in y.index], y=y[cols[2]], name=cols[2],
                        mode="markers", marker=dict(color=MIX, size=7, symbol="diamond"),
                        hovertemplate="%{y:+.1%}")
    fig.add_hline(y=0, line=dict(color=INK, width=1))
    fig.update_yaxes(tickformat="+.0%")
    return _base(fig, lang, barmode="group", bargap=0.25, height=340)


def mc_fan(paths: pd.DataFrame, lang: str = "de") -> go.Figure:
    """Monte-Carlo-Perzentilpfade als Fächer."""
    x = paths.index
    fig = go.Figure()
    for lo, hi, a in (("P5", "P95", 0.10), ("P25", "P75", 0.20)):
        fig.add_scatter(x=x, y=paths[hi], line=dict(width=0), showlegend=False,
                        hoverinfo="skip")
        fig.add_scatter(x=x, y=paths[lo], line=dict(width=0), fill="tonexty",
                        fillcolor=f"rgba(0,50,116,{a})", name=f"{lo}–{hi}",
                        hovertemplate="%{y:,.2f}")
    fig.add_scatter(x=x, y=paths["P50"], line=dict(color=NAVY, width=2), name="P50",
                    hovertemplate="%{y:,.2f}")
    fig.add_hline(y=1, line=dict(color=INK, width=1))
    fig.update_yaxes(tickformat=",.2f", ticksuffix="x")
    fig.update_xaxes(title=t("mc_x", lang))
    return _base(fig, lang, height=340)


def corr_heatmap(c: pd.DataFrame, lang: str = "de") -> go.Figure:
    z = c.to_numpy(dtype=float)
    fig = go.Figure(go.Heatmap(
        z=z, x=list(c.columns), y=list(c.index),
        text=[[f"{v:,.2f}".replace(".", ",") if lang == "de" else f"{v:,.2f}" for v in row]
              for row in z],
        texttemplate="%{text}", textfont=dict(size=11), colorscale=HEAT, zmid=0,
        zmin=-1, zmax=1, xgap=2, ygap=2, showscale=False,
        hovertemplate="%{y} / %{x}: %{z:.2f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    return _base(fig, lang, hovermode="closest", height=300,
                 margin=dict(l=8, r=8, t=10, b=8))


def return_hist(r: pd.Series, var95: float, var99: float, lang: str = "de") -> go.Figure:
    """Verteilung der Tagesrenditen mit eingezeichneten VaR-Schwellen."""
    fig = go.Figure(go.Histogram(x=r, nbinsx=120, marker_color=NAVY, opacity=0.75,
                                 hovertemplate="%{x:.2%}: %{y}<extra></extra>"))
    sp = "" if lang == "en" else " "
    for v, name, col in ((-var95, f"VaR 95{sp}%", MIX), (-var99, f"VaR 99{sp}%", "#C53A30")):
        fig.add_vline(x=v, line=dict(color=col, width=1.4, dash="dash"),
                      annotation_text=name, annotation_position="top left",
                      annotation_font=dict(size=11, color=col))
    fig.update_xaxes(tickformat=".0%", range=[r.quantile(0.001), r.quantile(0.999)])
    return _base(fig, lang, height=300, showlegend=False, hovermode="closest")
