"""Plotly-Charts im SINTRO-Stil. Standard: Vermögen auf Log-Skala."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from . import metrics as m
from .robustness import CRISES, excess_log, rolling_excess

NAVY = "#003274"
INK = "#1B2638"
SLATE = "#8C96A5"
LINE = "#E4E8EE"
MUTED = "#5E6B7D"
RISK_OFF = "rgba(214, 150, 60, 0.13)"
MIX_COLORS = ["#6F9BD1", "#B7A07A"]
FONT = "Jost, 'Segoe UI', Helvetica, Arial, sans-serif"

pio.templates["sintro"] = go.layout.Template(layout=dict(
    font=dict(family=FONT, color=INK, size=13),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    separators=",.",
    colorway=[NAVY, SLATE, *MIX_COLORS],
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


def _risk_off_shapes(position: pd.Series, yref="paper"):
    off = position.eq(0)
    grp = (off != off.shift()).cumsum()
    return [dict(type="rect", xref="x", yref=yref, x0=seg.index[0], x1=seg.index[-1],
                 y0=0, y1=1, fillcolor=RISK_OFF, line_width=0, layer="below")
            for _, seg in position[off].groupby(grp[off])]


def wealth_chart(bt: pd.DataFrame, extra: dict[str, pd.Series] | None = None,
                 log: bool = True) -> go.Figure:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.74, 0.26],
                        vertical_spacing=0.05)
    wf = (1 + bt.ret_pf).cumprod()
    wb = (1 + bt.ret_bm).cumprod()
    for i, (k, s) in enumerate((extra or {}).items()):
        fig.add_scatter(x=s.index, y=(1 + s).cumprod(), name=k, row=1, col=1,
                        line=dict(color=MIX_COLORS[i % 2], width=1.3, dash="dot"),
                        visible="legendonly", hovertemplate="%{y:,.2f}")
    fig.add_scatter(x=bt.index, y=wb, name="S&P 500", line=dict(color=SLATE, width=1.6),
                    row=1, col=1, hovertemplate="%{y:,.2f}")
    fig.add_scatter(x=bt.index, y=wf, name="SPY3", line=dict(color=NAVY, width=2.2),
                    row=1, col=1, hovertemplate="%{y:,.2f}")
    fig.add_scatter(x=bt.index, y=m.drawdown(bt.ret_bm), name="Drawdown S&P 500",
                    line=dict(color=SLATE, width=1), fill="tozeroy",
                    fillcolor="rgba(140,150,165,0.18)", showlegend=False, row=2, col=1,
                    hovertemplate="%{y:.1%}")
    fig.add_scatter(x=bt.index, y=m.drawdown(bt.ret_pf), name="Drawdown SPY3",
                    line=dict(color=NAVY, width=1.4), showlegend=False, row=2, col=1,
                    hovertemplate="%{y:.1%}")
    fig.add_scatter(x=[None], y=[None], mode="markers", name="Risk-Off (SHY)",
                    marker=dict(symbol="square", size=12, color=RISK_OFF), row=1, col=1)
    fig.update_yaxes(type="log" if log else "linear", title=None, tickformat=",.1f",
                     dtick="D2" if log else None, row=1, col=1)
    fig.update_yaxes(tickformat=".0%", nticks=4, row=2, col=1)
    fig.update_layout(template=TEMPLATE, shapes=_risk_off_shapes(bt.position),
                      height=520)
    fig.update_xaxes(showline=True, row=1, col=1, ticks="", showticklabels=False)
    return fig


def relative_chart(bt: pd.DataFrame) -> go.Figure:
    ratio = (1 + bt.ret_pf).cumprod() / (1 + bt.ret_bm).cumprod()
    fig = go.Figure(go.Scatter(x=ratio.index, y=ratio, line=dict(color=NAVY, width=2),
                               name="SPY3 / S&P 500", hovertemplate="%{y:,.3f}"))
    lo, hi = bt.index[0], bt.index[-1]
    for n, (a, b) in CRISES.items():
        if pd.Timestamp(b) < lo or pd.Timestamp(a) > hi:
            continue
        fig.add_vrect(x0=max(pd.Timestamp(a), lo), x1=min(pd.Timestamp(b), hi),
                      fillcolor=SLATE, opacity=0.1, line_width=0,
                      annotation_text=n.split(" ")[0], annotation_position="top left",
                      annotation_font=dict(size=11, color=MUTED))
    fig.add_hline(y=1, line=dict(color=LINE, width=1))
    fig.update_layout(template=TEMPLATE, yaxis_type="log", height=340, showlegend=False,
                      yaxis_dtick="D2",
                      yaxis_tickformat=",.2f")
    return fig


def rolling_excess_chart(bt: pd.DataFrame, years=(3, 5)) -> go.Figure:
    fig = go.Figure()
    for y, c in zip(years, [SLATE, NAVY]):
        s = rolling_excess(bt.ret_pf, bt.ret_bm, y)
        fig.add_scatter(x=s.index, y=s, name=f"{y} Jahre", line=dict(color=c, width=1.8),
                        hovertemplate="%{y:+.1%}")
    fig.add_hline(y=0, line=dict(color=INK, width=1))
    fig.update_layout(template=TEMPLATE, yaxis_tickformat="+.0%", height=340)
    return fig


def cum_excess_chart(bt: pd.DataFrame) -> go.Figure:
    ex = excess_log(bt.ret_pf, bt.ret_bm).cumsum()
    fig = go.Figure(go.Scatter(x=ex.index, y=ex, fill="tozeroy", line=dict(color=NAVY, width=1.8),
                               fillcolor="rgba(0,50,116,0.08)", hovertemplate="%{y:+.1%}"))
    fig.update_layout(template=TEMPLATE, yaxis_tickformat="+.0%", height=300, showlegend=False)
    return fig
