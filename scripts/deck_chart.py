"""Korrigierte Fassung des Performance-Charts aus dem Deck.

Gegenüber der alten Version:
  * Linke Achse zeigt den Wert einer Anlage von 1.000 USD auf logarithmischer Skala
    statt kumulierter Log-Renditen, die als Prozent beschriftet waren. Die Log-Skala
    ist im Achsentitel benannt, gleiche Abstände bedeuten gleiche prozentuale Änderung.
  * Kurvenform identisch zur alten Darstellung, aber jeder Punkt direkt ablesbar.
  * 200-Tage-Linie auf dem Kurs des Benchmarks, nicht auf einer Renditereihe.
  * Live-Track-Record ab 09/2023 markiert, Netto-Reihe nach Gebühren ergänzt.
  * VaR bleibt auf der rechten Achse, mit Schwellen für Risk-Off und Low-Vol.

    python scripts/deck_chart.py                 # Daten aus dem Cache oder yfinance
    python scripts/deck_chart.py --csv data.csv --lang de --net
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from spy3 import metrics as m, plots  # noqa: E402
from spy3.data import load_prices, prepare_returns  # noqa: E402
from spy3.strategy import StrategyParams, backtest  # noqa: E402

VAR_GREY = "#AAB3BF"
START = 1_000
LIVE_START = "2023-09-01"      # Beginn des Live-Track-Records von SPY3
TXT = {
    "en": {"y": f"Value of a ${START:,} investment (log scale)", "var": "Daily 99% VaR",
           "spy3": "SPY3 STF", "net": "SPY3 STF (net of fees)", "bm": "SPY ETF",
           "ma": "200d MA (SPY)", "vline": "Daily 99% VaR", "off": "Risk off",
           "thr": "VaR threshold 5%", "low": "Low vol 2%", "live": "live since 09/2023"},
    "de": {"y": f"Wert einer Anlage von {START:,} USD (log. Skala)".replace(",", "."),
           "var": "1-Tages-VaR 99 %", "spy3": "SPY3 STF", "net": "SPY3 STF (nach Gebühren)",
           "bm": "SPY ETF", "ma": "200-Tage-Linie (SPY)", "vline": "1-Tages-VaR 99 %",
           "off": "Risk Off", "thr": "VaR-Schwelle 5 %", "low": "Low Vol 2 %",
           "live": "live seit 09/2023"},
}


def build(bt: pd.DataFrame, price: pd.Series, lang: str = "en",
          show_net: bool = True) -> go.Figure:
    tx = TXT[lang]
    w_pf = START * (1 + bt.ret_pf).cumprod()
    w_bm = START * (1 + bt.ret_bm).cumprod()
    ma = w_bm.rolling(200).mean()
    hov = "%{y:,.0f} USD"

    fig = go.Figure()
    fig.add_scatter(x=ma.index, y=ma, name=tx["ma"], hovertemplate=hov, legendrank=4,
                    line=dict(color="#E0A32E", width=1.4, dash="dot"))
    fig.add_scatter(x=w_bm.index, y=w_bm, name=tx["bm"], hovertemplate=hov, legendrank=3,
                    line=dict(color=plots.SLATE, width=1.6))
    if show_net and "ret_pf_net" in bt:
        fig.add_scatter(x=bt.index, y=START * (1 + bt.ret_pf_net).cumprod(),
                        name=tx["net"], hovertemplate=hov, legendrank=2,
                        line=dict(color=plots.NET, width=1.6))
    fig.add_scatter(x=w_pf.index, y=w_pf, name=tx["spy3"], hovertemplate=hov, legendrank=1,
                    line=dict(color="#1668C1", width=2.2))
    fig.add_scatter(x=bt.index, y=bt.var_1d, name=tx["vline"], yaxis="y2", opacity=0.75, legendrank=5,
                    line=dict(color=VAR_GREY, width=1, dash="dash"),
                    hovertemplate="%{y:.2%}")
    fig.add_scatter(x=[None], y=[None], mode="markers", name=tx["off"], legendrank=6,
                    marker=dict(symbol="square", size=12, color=plots.RISK_OFF))

    # Schwellen als Linie plus Legendeneintrag, damit keine Beschriftung die Achse überlappt
    p = StrategyParams()
    for y, col, name in ((p.var_high, "#9B2C2C", tx["thr"]), (p.var_low, "#2F7A4F", tx["low"])):
        fig.add_hline(y=y, yref="y2", line=dict(color=col, width=1, dash="dash"))
        fig.add_scatter(x=[None], y=[None], mode="lines", name=name, legendrank=7,
                        line=dict(color=col, width=1, dash="dash"))
    live = pd.Timestamp(LIVE_START)
    if bt.index[0] <= live <= bt.index[-1]:
        fig.add_vline(x=live, line=dict(color=plots.INK, width=1.2, dash="dash"),
                      annotation_text=tx["live"], annotation_position="top left",
                      annotation_font=dict(size=11, color=plots.INK),
                      annotation_bgcolor="rgba(255,255,255,0.75)")

    hi = float(max(w_pf.max(), w_bm.max()))
    ticks = [v for v in (500, 1_000, 2_000, 5_000, 10_000, 20_000, 50_000) if v <= hi * 1.6]
    fig.update_layout(
        template=plots.TEMPLATE, separators="," if lang == "en" else ",.",
        shapes=plots._risk_off_shapes(bt.position), height=560, width=1120,
        margin=dict(l=70, r=95, t=60, b=50),
        legend=dict(orientation="h", y=1.06, x=0, font=dict(size=12)),
        yaxis=dict(type="log", title=tx["y"], tickvals=ticks,
                   ticktext=[f"{v:,.0f}".replace(",", "." if lang == "de" else ",")
                             for v in ticks]),
        yaxis2=dict(overlaying="y", side="right", title=tx["var"], tickformat=".0%",
                    showgrid=False, rangemode="tozero", zeroline=False),
    )
    return fig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=None)
    ap.add_argument("--lang", choices=["en", "de"], default="en")
    ap.add_argument("--net", action="store_true", help="Netto-Reihe einzeichnen")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", type=Path, default=ROOT / "reports")
    a = ap.parse_args()

    px = (pd.read_csv(a.csv, index_col=0, parse_dates=True) if a.csv
          else load_prices(refresh=a.refresh))
    bt = backtest(prepare_returns(px), px["risk_on"], StrategyParams())
    fig = build(bt, px["risk_on"], a.lang, a.net)

    a.out.mkdir(exist_ok=True)
    stem = a.out / f"deck_chart_{a.lang}"
    fig.write_html(stem.with_suffix(".html"), include_plotlyjs="cdn")
    for ext in ("png", "svg"):
        try:
            fig.write_image(stem.with_suffix(f".{ext}"), scale=2 if ext == "png" else 1)
        except Exception as exc:                       # kaleido fehlt oder kein Browser
            print(f"{ext.upper()} nicht erzeugt ({exc.__class__.__name__}). "
                  f"Mit 'pip install kaleido' und 'plotly_get_chrome' nachrüsten.")
    print(f"Geschrieben: {stem}.html / .png / .svg")
    print(f"Endwerte: SPY3 {START * (1 + bt.ret_pf).prod():,.0f} USD, "
          f"SPY {START * (1 + bt.ret_bm).prod():,.0f} USD, "
          f"Verhältnis {(1 + bt.ret_pf).prod() / (1 + bt.ret_bm).prod():,.2f}x")
    print(f"Total Return: SPY3 {m.total_return(bt.ret_pf):.1%}, "
          f"SPY {m.total_return(bt.ret_bm):.1%} | "
          f"CAGR {m.cagr(bt.ret_pf):.1%} vs {m.cagr(bt.ret_bm):.1%}")


if __name__ == "__main__":
    main()
