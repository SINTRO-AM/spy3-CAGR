"""Dash-Dashboard (Heroku/Render: `gunicorn app:server`)."""
from dash import Dash, Input, Output, dash_table, dcc, html

from scripts.run_report import build
from spy3 import plots
from spy3.data import load_prices

R = build(load_prices())
BT = R["bt"]


def table(df, pct=True):
    d = df.copy()
    d = d.map(lambda v: f"{v:.1%}" if pct and isinstance(v, float) and abs(v) < 5 else
              (f"{v:.2f}" if isinstance(v, float) else v))
    d.insert(0, "", d.index)
    return dash_table.DataTable(d.to_dict("records"), [{"name": c, "id": c} for c in d.columns],
                                style_cell={"fontFamily": "Segoe UI", "padding": "4px"})


app = Dash(__name__)
server = app.server
app.layout = html.Div([
    html.H2("SPY3 – Backtest & Robustness"),
    html.Div(f"Aktuelles Signal: {'Risk On' if BT.signal.iloc[-1] == 1 else 'Risk Off'} | "
             f"1d-VaR {BT.var_1d.iloc[-1]:.2%} | Stand {BT.index[-1].date()}"),
    dcc.RadioItems(["log", "linear"], "log", id="scale", inline=True),
    dcc.Graph(id="wealth"),
    dcc.Tabs([
        dcc.Tab(label="Kennzahlen", children=[table(R["summary"])]),
        dcc.Tab(label="Abstand / Attribution", children=[
            dcc.Graph(figure=plots.relative_chart(BT)),
            dcc.Graph(figure=plots.cum_excess_chart(BT)),
            table(R["attribution"])]),
        dcc.Tab(label="Rollierend", children=[dcc.Graph(figure=plots.rolling_excess_chart(BT))]),
        dcc.Tab(label="Ohne Krisen", children=[table(R["ex_major"]), table(R["ex_all"])]),
        dcc.Tab(label="Teilperioden", children=[table(R["subperiods"]), table(R["yearly"])]),
    ]),
], style={"fontFamily": "Segoe UI", "margin": "20px"})


@app.callback(Output("wealth", "figure"), Input("scale", "value"))
def _wealth(scale):
    return plots.wealth_chart(BT, R["mixes"], log=scale == "log")


if __name__ == "__main__":
    app.run(debug=False)
