# SPY3 — Systematic 3-Factor US Equity Strategy

**SINTRO Asset Management** · Research, backtesting and investor analytics for SPY3

SPY3 is SINTRO's first Systematic-Traded Fund (STF): a fully rule-based strategy that holds the
S&P 500 in normal and rising markets and moves into short-term US Treasuries when market risk
is elevated. The objective is equity-like returns with materially lower drawdowns — a higher
Sharpe ratio, not a bet against the index. The strategy has been managed live since
September 2023.

This repository contains the complete research and analytics stack behind SPY3: the backtest
engine, the validation suite and the interactive dashboard used with investors.

---

## Results at a glance

| January 2000 – September 2026 | SPY3 (net of all fees) | S&P 500 (SPY) |
|---|---|---|
| Return p.a. (CAGR) | 12.7% | 8.3% |
| Volatility p.a. | 12.3% | 19.3% |
| Sharpe ratio | 1.04 | 0.43 |
| Maximum drawdown | −20.1% | −55.2% |

*Simulated performance based on the model rules, after trading costs of 10 bp per switch,
a 0.20% management fee and a 10% performance fee. Figures as of 17 September 2026; the
dashboard always shows the current data. Past or simulated performance is not a reliable
indicator of future results.*

The advantage is earned where it matters most for long-term investors: in market crises.

| Crisis (S&P 500 peak to trough) | SPY3 net | S&P 500 |
|---|---|---|
| Dot-com crash (03/2000 – 10/2002) | +16.9% | −47.2% |
| Global financial crisis (10/2007 – 03/2009) | +2.5% | −54.8% |
| Covid crash (02/2020 – 03/2020) | −18.2% | −33.4% |
| 2022 bear market (01/2022 – 10/2022) | −12.5% | −24.1% |

---

## How SPY3 decides

Every trading day the model evaluates one requirement and three reasons to invest, based on
closing prices:

| | Factor | Condition |
|---|---|---|
| Requirement | **Risk** | Daily 99% value-at-risk (50-day window) below 5% |
| Reason 1 | **Momentum** | 30-day moving average above the 200-day moving average |
| Reason 2 | **Calm market** | Daily value-at-risk below 2% |
| Reason 3 | **Mean reversion** | Price at least 23% below its 200-day high |

SPY3 holds the S&P 500 (SPY) when the requirement and at least one reason are met; otherwise
it holds short-term US Treasuries (SHY). Each factor builds on established research:
volatility clustering (Engle 1982; Moreira & Muir 2017), time-series momentum (Moskowitz,
Ooi & Pedersen 2012) and overreaction after extreme losses (De Bondt & Thaler 1985).

Details: [docs/METHODOLOGY.md](docs/METHODOLOGY.md)

---

## Built to be verified

Institutional investors rightly distrust backtests. SPY3's engine is designed to be checked:

- **Independent replication.** A hand-built share-by-share portfolio matches the engine on
  every one of 6,193 trading days to within 10⁻¹⁴.
- **No look-ahead.** Signals use only information available at the close of the signal day.
- **Costs and fees modelled explicitly.** Every switch is charged once; management and
  performance fees follow the actual fee terms (high-water mark, SPY hurdle, quarterly
  crystallisation).
- **Not luck.** With randomly placed switches at the same investment ratio, the median Sharpe
  ratio is 0.30; SPY3's result is significant at p < 0.001.
- **52 automated tests** cover return arithmetic, costs, fees, data handling and the dashboard.

The full validation — including parameter sensitivity, walk-forward tests and known
limitations — is documented in [docs/VALIDATION.md](docs/VALIDATION.md).

---

## Investor dashboard

The dashboard presents SPY3 against the S&P 500 and a classic 60/40 portfolio:

- **Live signal** with a plain-language explanation of each factor, its current value, its
  threshold and what would change the signal; updated automatically from the latest close
- **Performance** since 2000, since inception or over 1, 3, 5 and 10 years, on a logarithmic
  or linear scale, with adjustable fees
- **Key figures** (net and gross), drawdowns, lead over the index, calendar-year returns
- **Inside the SPY3 Model:** price, moving averages, mean-reversion trigger and value-at-risk
  with all thresholds, plus rolling Sharpe, Calmar and volatility
- **Risk analysis:** stress tests, VaR and expected shortfall, Monte Carlo simulation and
  correlations with other asset classes
- **Downloads:** PDF report with SINTRO branding and an Excel file with all daily data
- English and German, optimised for desktop and mobile

---

## For the team: getting started

```bash
pip install -r requirements.txt
python -m pytest -q                      # full test suite, no network required
python app.py                            # dashboard at http://127.0.0.1:8050
python scripts/run_report.py --refresh   # append new closing prices, write reports/
python scripts/audit.py                  # validation suite on the current data
```

Production: `gunicorn app:server` (see `Procfile`).

**Data.** Prices come from Yahoo Finance (dividend- and split-adjusted closes) and are cached
in `data/prices.csv`. The history is frozen: updates only append completed trading days, so
figures never shift retroactively. `--rebuild` reloads the full history deliberately. For
the period before SHY's launch in July 2002, the engine uses a Treasury proxy of comparable
maturity; licensed Bloomberg files are kept locally in `data/` and are never committed.

| Path | Purpose |
|---|---|
| `app.py` | Dash dashboard |
| `spy3/strategy.py` | Signal logic and backtest engine |
| `spy3/data.py` | Price loading, frozen history, risk-off data sources |
| `spy3/fees.py` | Management and performance fees |
| `spy3/metrics.py` | Return and risk metrics |
| `spy3/robustness.py`, `spy3/rolling.py`, `spy3/risk.py` | Attribution, rolling metrics, stress tests, Monte Carlo |
| `spy3/live.py` | Current signal from the latest close |
| `spy3/report.py` | PDF and Excel exports |
| `scripts/` | Reports, presentation charts, data checks, validation suite |
| `tests/` | Automated tests |
| `docs/` | Methodology, validation, changelog |

---

## About SINTRO

SINTRO Asset Management GmbH builds Systematic-Traded Funds: investment strategies in which
every decision follows transparent, scientifically grounded rules and is executed
automatically. SPY3 is distributed by SINTRO as a tied agent under the liability umbrella of
INNO INVEST.

SINTRO Asset Management GmbH · Kettenhofweg 26 · 60325 Frankfurt am Main · [www.sintro.eu](https://www.sintro.eu)

---

*Important information: This repository and the dashboard are provided for information
purposes and for discussions with professional investors. They do not constitute investment
advice, an offer or a solicitation. Performance shown is simulated unless stated otherwise.
Past or simulated performance is not a reliable indicator of future results.*

© 2026 SINTRO Asset Management GmbH. All rights reserved. Proprietary — not for redistribution.
