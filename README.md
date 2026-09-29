# SPY3 — Systematic 3-Factor US Equity Strategy

*by SINTRO Asset Management*

Most of the damage in equity investing happens in a handful of bad years. SPY3 is built
around that simple observation.

SPY3 aims to deliver consistent returns while staying out of the big crises. In normal and
rising markets it holds the S&P 500. When risk builds up, it moves into short-term US
Treasuries and waits until conditions improve. No discretion, no gut feeling: every decision
follows fixed rules and is executed automatically.

Over 26 years of backtesting, SPY3 has been a significantly better choice than a passive
S&P 500 investment in terms of risk/reward and drawdowns. The strategy has been running live
since Sep 2023.

This repo is the research and analytics stack behind it: backtest engine, validation suite
and the dashboard we use with investors.

---

## The numbers

**Jan 2000 – Sep 2026, SPY3 net of all fees vs. S&P 500**

| | SPY3 | S&P 500 |
|---|---|---|
| Return p.a. (CAGR) | 12.7% | 8.3% |
| Vol p.a. | 12.3% | 19.3% |
| Sharpe ratio | 1.04 | 0.43 |
| Max. DD | −20.1% | −55.2% |

Put simply: more return, about a third less volatility and less than half the worst loss.

And here's where the difference comes from:

| Crisis (S&P 500 peak to trough) | SPY3 | S&P 500 |
|---|---|---|
| Dot-com crash, 03/2000 – 10/2002 | +16.9% | −47.2% |
| Global financial crisis, 10/2007 – 03/2009 | +2.5% | −54.8% |
| Covid crash, 02/2020 – 03/2020 | −18.2% | −33.4% |
| 2022 bear market, 01/2022 – 10/2022 | −12.5% | −24.1% |

*Simulated performance based on the model rules, after 10 bp trading costs per switch, a
0.20% p.a. mgmt fee and a 10% perf fee. Figures as of 17 Sep 2026 — the dashboard always shows
the latest data. Past or simulated performance is not a reliable indicator of future results.*

---

## How it works

Every trading day, SPY3 asks one question first and three more after that.

**1. Is the risk acceptable?** If the daily 99% VaR (50-day window) is above 5%, SPY3 is out
of equities — full stop, whatever the other signals say.

**2. Is there a reason to be invested?** At least one of these has to be true:

- **Uptrend** — the 30-day MA is above the 200-day MA
- **Calm market** — daily VaR is below 2%
- **Buying opportunity** — the price is at least 23% below its 200-day high

If both checks pass, SPY3 holds SPY. Otherwise it holds SHY (1–3y US Treasuries). On average
that means about three switches a year.

None of this is new magic. Each factor rests on well-documented research: volatility
clusters (Engle 1982; Moreira & Muir 2017), trends persist (Moskowitz, Ooi & Pedersen 2012)
and markets overreact after extreme losses (De Bondt & Thaler 1985). What SPY3 adds is a
disciplined combination of the three.

The full methodology is in [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

---

## Why you can trust the backtest

We know that backtests are easy to make look good. So we built this one to be checked:

- **Rebuilt by hand.** An independent, share-by-share portfolio reproduces the engine on all
  6,193 trading days to the 14th decimal.
- **No look-ahead.** Signals only use what was known at the close of that day.
- **Real costs.** Every switch costs 10 bp, including the first purchase. Fees follow the
  actual terms: high-water mark, SPY hurdle, quarterly crystallisation.
- **Not luck.** Switch at random with the same equity exposure and you get a median Sharpe
  ratio of 0.30. SPY3's result is significant at p < 0.001.
- **52 automated tests** keep all of this in check on every change.

We're also upfront about the limits — simulated history before Sep 2023, parameter
sensitivity, execution assumptions and fast V-shaped crashes. It's all in
[docs/VALIDATION.md](docs/VALIDATION.md).

---

## The dashboard

What investors see:

- **Today's signal**, with a plain-English explanation of each factor, its current value
  and what would flip it — updated from the latest close
- **Performance** since 2000, since inception, YTD, or over 1, 3, 5 and 10 yrs — linear or log
  scale, with adjustable fees
- **Key figures** net and gross, drawdowns, lead over the S&P 500, calendar-year returns
- **Inside the SPY3 Model** — price, MAs, mean-reversion trigger and VaR with all thresholds,
  plus rolling Sharpe, Calmar and vol
- **Risk** — stress tests, VaR & expected shortfall, Monte Carlo, correlations with other
  asset classes
- **Downloads** — branded PDF report and an Excel file with every daily data point
- English & German, desktop & mobile — on phones every explanation opens with a tap, charts
  scroll with the page instead of zooming, and legends and labels stay readable

---

## For the team

```bash
pip install -r requirements.txt
python -m pytest -q                      # full test suite, no network needed
python app.py                            # dashboard on http://127.0.0.1:8050
python scripts/run_report.py --refresh   # append new closes, write reports/
python scripts/audit.py                  # rerun the validation suite
```

In production we run `gunicorn app:server` (see `Procfile`).

**About the data.** Prices are Yahoo Finance closes, adjusted for dividends and splits, cached
in `data/prices.csv`. The history is frozen: updates only append completed trading days, so
past numbers never shift. Use `--rebuild` if you really want to reload everything. Before
SHY launched in Jul 2002, a Treasury proxy of the same maturity stands in. Licensed
Bloomberg files live locally in `data/` and never get committed.

| Where | What |
|---|---|
| `app.py` | The dashboard |
| `spy3/strategy.py` | Signal logic & backtest engine |
| `spy3/data.py` | Prices, frozen history, risk-off data sources |
| `spy3/fees.py` | Mgmt & perf fees |
| `spy3/metrics.py` | Return & risk metrics |
| `spy3/robustness.py`, `rolling.py`, `risk.py` | Attribution, rolling metrics, stress tests, Monte Carlo |
| `spy3/live.py` | Today's signal |
| `spy3/report.py` | PDF & Excel exports |
| `scripts/` | Reports, presentation charts, data checks, validation |
| `tests/` | Automated tests |
| `docs/` | Methodology, validation, changelog |

---

## About SINTRO

At SINTRO we build Systematic-Traded Funds (STFs): strategies where every decision follows
transparent, research-based rules and runs automatically. SPY3 is the first of them. SINTRO
distributes it as a tied agent under the liability umbrella of INNO INVEST.

SINTRO Asset Management GmbH · Kettenhofweg 26 · 60325 Frankfurt am Main · [sintro.eu](https://www.sintro.eu)

---

*This repo and the dashboard are for information and for discussions with professional
investors. Nothing here is investment advice, an offer or a solicitation. Performance is
simulated unless stated otherwise. Past or simulated performance is not a reliable indicator
of future results.*

© 2026 SINTRO Asset Management GmbH. All rights reserved.
