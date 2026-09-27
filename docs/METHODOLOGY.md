# SPY3 Methodology

## 1. Investment universe

| Role | Instrument |
|---|---|
| Risk-on asset | SPDR S&P 500 ETF Trust (SPY) |
| Risk-off asset | iShares 1–3 Year Treasury Bond ETF (SHY) |
| Benchmark | SPY |
| Additional comparison | 60% SPY / 40% SHY, rebalanced monthly |

The strategy is always fully invested in exactly one of the two instruments.

## 2. Signal

All inputs are computed from daily closing prices of SPY.

**Risk (value-at-risk).** The daily 99% value-at-risk is estimated from the standard deviation
of daily log returns over the last 50 trading days: `VaR = σ₅₀ · z₀.₉₉`. It serves two purposes:

- above **5%** it vetoes any equity exposure, regardless of all other signals;
- below **2%** it counts as a reason to invest (calm market).

**Momentum.** Uptrend when the 30-day moving average is above the 200-day moving average
(implementation: 29 and 198 trading days).

**Mean reversion.** Buying opportunity when the price is at least 23% below its 200-day high
(price × 1.3 below the 200-day high).

**Rule.**

```
invest  =  VaR < 5%  AND  ( uptrend  OR  VaR < 2%  OR  buying opportunity )
```

| Factor | Research basis |
|---|---|
| Risk | Volatility clustering: Engle (1982), Bollerslev (1986); volatility-managed portfolios: Moreira & Muir (2017) |
| Momentum | Brock, Lakonishok & LeBaron (1992); time-series momentum: Moskowitz, Ooi & Pedersen (2012) |
| Mean reversion | Overreaction: De Bondt & Thaler (1985); mean reversion in stock prices: Poterba & Summers (1988) |

## 3. Execution and costs

- Signals are computed from the closing price of day *t*; the new position earns returns from
  day *t+1*.
- Trading costs of **10 bp** are charged on the portfolio value for every switch, including
  the initial purchase. On average the strategy switches 3.2 times per year, which amounts to
  roughly 0.3% p.a.
- A more conservative execution variant (trade at the close of *t+1*) is available as
  `StrategyParams(exec_delay=1)` and reported in [VALIDATION.md](VALIDATION.md).

## 4. Fees (net series)

- **Management fee:** 0.20% p.a., accrued daily.
- **Performance fee:** 10% of the return above SPY, subject to a high-water mark, crystallised
  quarterly; underperformance is carried forward.

The gross series is after trading costs only.

## 5. Data

| Period | Risk-on | Risk-off |
|---|---|---|
| from 30 July 2002 | SPY, adjusted close | SHY, adjusted close |
| January 2000 – July 2002 | SPY, adjusted close | Treasury proxy of comparable maturity (1–3 years) |

- Prices are Yahoo Finance closes adjusted for dividends and splits (total return).
  Dividends therefore enter exactly once; there is no separate dividend booking.
- Before SHY's launch, the risk-off leg uses, in this order of priority: the Bloomberg US
  Treasury 1–3 Year Index, a constant-maturity total-return series built from Federal Reserve
  1-, 2- and 3-year yields, the Bloomberg US Treasury Index, or 13-week T-bills. The source
  used for each day is recorded in the Excel export (`risk_off_source`).
- The price history is frozen: updates only append completed trading days and chain new
  prices to the stored level, so later revisions by the data provider cannot change past
  results.

## 6. Metrics

| Metric | Definition |
|---|---|
| Total return | ∏(1 + rₜ) − 1 |
| CAGR | (1 + total return)^(252 / n) − 1 |
| Volatility | standard deviation of daily returns × √252 |
| Sharpe ratio | CAGR ÷ volatility, without a risk-free rate |
| Maximum drawdown | largest peak-to-trough decline of the wealth path |
| Calmar ratio | CAGR ÷ |maximum drawdown| |
| Beta, Jensen's alpha | regression on excess returns over SHY |
| Up/down capture | average return in up/down months of the benchmark, relative to the benchmark |

Returns are compounded geometrically throughout. Log returns are used only where additivity
is required (VaR estimation, attribution); cumulative log returns are always labelled as such.
