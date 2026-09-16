"""Plotly-Charts. Standard: Log-Skala auf Vermögensbasis.

Alter Chart: kumulierte Log-Renditen auf linearer Achse. Das ist mathematisch eine
Log-Darstellung – ein konstanter Abstand heißt: keine zusätzliche Überschussrendite.
Wir zeigen das jetzt explizit (Wealth-Ratio-Chart) statt es zu verstecken.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import metrics as m
from .robustness import CRISES, excess_log, rolling_excess

BLUE, GREY, RED = "#1f5fbf", "#8a8a8a", "rgba(200,60,60,0.12)"


def _risk_off_shapes(position: pd.Series):
    off = position.eq(0)
    grp = (off != off.shift()).cumsum()
    shapes = []
    for _, seg in position[off].groupby(grp[off]):
        shapes.append(dict(type="rect", xref="x", yref="paper", x0=seg.index[0],
                           x1=seg.index[-1], y0=0, y1=1, fillcolor=RED, line_width=0,
                           layer="below"))
    return shapes


def wealth_chart(bt: pd.DataFrame, extra: dict[str, pd.Series] | None = None,
                 log: bool = True) -> go.Figure:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.72, 0.28],
                        vertical_spacing=0.04)
    fig.add_scatter(x=bt.index, y=bt.wealth_pf, name="SPY3", line_color=BLUE, row=1, col=1)
    fig.add_scatter(x=bt.index, y=bt.wealth_bm, name="S&P 500 (SPY TR)", line_color=GREY,
                    row=1, col=1)
    for k, s in (extra or {}).items():
        fig.add_scatter(x=s.index, y=(1 + s).cumprod(), name=k,
                        line=dict(dash="dot"), row=1, col=1)
    fig.add_scatter(x=bt.index, y=m.drawdown(bt.ret_pf), name="DD SPY3", line_color=BLUE,
                    fill="tozeroy", showlegend=False, row=2, col=1)
    fig.add_scatter(x=bt.index, y=m.drawdown(bt.ret_bm), name="DD BM", line_color=GREY,
                    showlegend=False, row=2, col=1)
    fig.update_yaxes(type="log" if log else "linear", title="Wert von 1 USD", row=1, col=1)
    fig.update_yaxes(tickformat=".0%", title="Drawdown", row=2, col=1)
    fig.update_layout(shapes=_risk_off_shapes(bt.position), template="simple_white",
                      title="SPY3 vs. S&P 500 – Vermögensentwicklung"
                      + (" (log)" if log else ""), legend_orientation="h")
    return fig


def relative_chart(bt: pd.DataFrame) -> go.Figure:
    """Verhältnis SPY3/Benchmark. Waagerecht = keine Outperformance in der Phase."""
    ratio = bt.wealth_pf / bt.wealth_bm
    fig = go.Figure(go.Scatter(x=ratio.index, y=ratio, line_color=BLUE, name="SPY3 / BM"))
    for n, (a, b) in CRISES.items():
        fig.add_vrect(x0=a, x1=b, fillcolor="grey", opacity=0.12, line_width=0,
                      annotation_text=n, annotation_position="top left")
    fig.update_layout(template="simple_white", yaxis_type="log",
                      title="Relative Vermögensentwicklung (SPY3 / S&P 500, log)")
    return fig


def rolling_excess_chart(bt: pd.DataFrame, years=(3, 5)) -> go.Figure:
    fig = go.Figure()
    for y in years:
        s = rolling_excess(bt.ret_pf, bt.ret_bm, y)
        fig.add_scatter(x=s.index, y=s, name=f"{y}J rollierend")
    fig.add_hline(y=0, line_color="black", line_width=1)
    fig.update_layout(template="simple_white", yaxis_tickformat=".0%",
                      title="Rollierende Überschussrendite p.a. (log)")
    return fig


def cum_excess_chart(bt: pd.DataFrame) -> go.Figure:
    ex = excess_log(bt.ret_pf, bt.ret_bm).cumsum()
    fig = go.Figure(go.Scatter(x=ex.index, y=ex, fill="tozeroy", line_color=BLUE))
    fig.update_layout(template="simple_white", yaxis_tickformat=".0%",
                      title="Kumulierte Log-Überschussrendite (entspricht dem 'Abstand')")
    return fig
