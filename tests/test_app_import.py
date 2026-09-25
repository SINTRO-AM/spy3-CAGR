"""Rauchtest: Das Dashboard muss sich ohne Netz importieren und aufbauen lassen."""
import importlib
import sys

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_prices():
    idx = pd.bdate_range("2000-01-03", "2006-12-29")
    rng = np.random.default_rng(1)
    px = pd.DataFrame({
        "risk_on": 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.011, len(idx)))),
        "risk_off": np.where(idx < "2002-07-30", np.nan,
                             80 * np.exp(np.cumsum(np.full(len(idx), 6e-5)))),
        "tbill_yield": 3.0,
    }, index=idx)
    return px


def test_app_imports_and_builds_layout(monkeypatch, synthetic_prices):
    import spy3.data as d
    monkeypatch.setattr(d, "load_prices", lambda **k: synthetic_prices)
    monkeypatch.setattr(d, "load_assets", lambda **k: pd.DataFrame())
    monkeypatch.setattr(d, "load_short_treasury_returns", lambda: pd.Series(dtype=float))
    sys.modules.pop("app", None)
    app = importlib.import_module("app")
    assert app.server is not None
    assert app.BT.shape[0] > 1000
    assert "risk_off_source" in app.BT
    # Rendering-Callbacks laufen ohne Fehler durch
    page = app.render("en")
    assert page[0] and page[1]
    badge = app.update_signal("en", 0)
    assert badge is not None
    fig, kpis, dd, al, *_ = app.update_main("all", "linear", 0.2, 10, "en", "wide")
    assert fig.data and kpis and dd.data and al.data
    for tab in ("roll", "gap", "ex", "years", "risk", "timing"):
        assert app.update_tab(tab, "all", "en", "wide") is not None
