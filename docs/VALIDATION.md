# SPY3 Validation

A backtest is only as credible as the checks behind it. This document summarises how SINTRO
verifies the SPY3 engine and how robust the results are. All figures can be reproduced with
`python scripts/audit.py`.

Unless stated otherwise: SPY and SHY adjusted closes, January 2000 to February 2024, standard
parameters, 10 bp per switch, before management and performance fees.

## 1. Correctness of the engine

| Check | Result |
|---|---|
| Independent replication (hand-built portfolio in shares, switch at the close, costs on portfolio value) | identical on all 6,193 trading days (max. relative deviation 7 × 10⁻¹⁵) |
| Look-ahead | none: signals use data up to the close of the signal day only |
| Switch days | exactly one leg earns the return on every switch day — never both, never neither |
| Trading costs | charged once per switch, including the initial purchase: 80 trades, 0.33% p.a. |
| Dividends | contained once, via adjusted prices; no separate dividend booking |
| Return arithmetic | total return, CAGR and drawdowns compounded geometrically; verified against analytic cases |
| Fees | high-water mark, SPY hurdle, quarterly crystallisation and loss carry-forward tested |

These checks run automatically as part of the test suite (52 tests).

## 2. Is the result more than luck?

| Test | Result |
|---|---|
| Random timing: switches placed at random with the same investment ratio (500 runs) | median Sharpe ratio 0.30 versus 0.98 for SPY3; p < 0.001 |
| Deflated Sharpe ratio (Bailey & López de Prado), accounting for 1,000 tested variants | expected maximum by chance 0.28; DSR ≈ 1.00 |
| 300 random parameter sets | median Sharpe ratio 0.62, versus 0.36 for the S&P 500 |

The combination of trend following and a volatility veto on SPY/SHY adds value across a wide
range of parameters, not only for the chosen one.

## 3. Sensitivity

| Variation | CAGR | Sharpe | Max. drawdown |
|---|---|---|---|
| **Standard** | **12.5%** | **0.98** | **−20.0%** |
| Trading costs 25 bp per switch | | 0.94 | |
| Trading costs 50 bp per switch | | 0.87 | |
| Execution at the close of the following day | 11.2% | 0.87 | −29.0% |
| Without mean reversion | 10.0% | 0.84 | |
| Without VaR veto | | 0.72 | −38.7% |
| Momentum only | 9.2% | 0.73 | −29.9% |
| S&P 500 (SPY) | 7.1% | 0.36 | −55.2% |

Every factor contributes; removing the VaR veto nearly doubles the maximum drawdown.

## 4. Out-of-sample behaviour

| Walk-forward | Sharpe in-sample | Sharpe out-of-sample |
|---|---|---|
| Parameters chosen on 2000–2007, tested on 2008–2015 | 1.28 | 0.63 (standard parameters: 0.92) |
| Parameters chosen on 2008–2015, tested on 2016–2024 | 0.96 | 0.97 |

## 5. Where the return comes from

- **Crisis periods.** The outperformance is earned in prolonged bear markets (dot-com crash,
  global financial crisis). In rising markets SPY3 is invested in the S&P 500 and tracks it.
- **Asymmetry.** Up-capture of about 70% against down-capture of about 35–40%, at a beta of
  roughly 0.4.
- **Consistency.** SPY3 has a higher Sharpe ratio than the S&P 500 in the majority of rolling
  three-year windows since 2003; its return is higher in slightly less than half of all
  rolling five-year windows.

## 6. Limitations

We state these openly because institutional investors ask for them:

- **Simulated performance.** Results before September 2023 are a backtest, not live trading.
- **Parameter selection.** The standard parameters sit at the upper end of the parameter
  landscape. Neighbouring settings deliver Sharpe ratios of roughly 0.75–0.90, which is a
  prudent expectation for future risk-adjusted returns.
- **Execution.** The backtest assumes trading at the close of the signal day. Trading one day
  later lowers the CAGR by about 1.3 percentage points and deepens the maximum drawdown, mainly
  because of single days such as 12 March 2020.
- **Fast crashes.** The volatility veto protects against prolonged bear markets; in V-shaped
  crashes such as 2020 the exit comes after part of the decline.
- **Pre-2002 data.** Before SHY's launch the risk-off leg uses a Treasury proxy of comparable
  maturity.

## 7. Reproducing the results

```bash
python scripts/audit.py               # all tests above on the current data
python scripts/check_risk_off.py      # effect of the pre-2002 risk-off data source
python -m pytest -q                   # automated correctness tests
```
