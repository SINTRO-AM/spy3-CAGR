# Changelog

## 2.x — 2026

**Performance calculation.** Earlier SPY3 materials reported cumulative log returns as
percentage returns and summed log returns into a "total return". Since version 2.0 all
figures are geometric: total return ∏(1 + r) − 1, CAGR, and drawdowns from the wealth path.
This affects the presentation of results, not the strategy: the reported total return of
SPY3 rose (for example from 350% to about 2,400% over 2000–2026), and the S&P 500 comparison
was restated in the same way (from 235% to about 740%).

**Engine.**
- Trading costs of 10 bp per switch, charged once on the portfolio value, including the
  initial purchase.
- Dividends included exactly once through adjusted prices.
- Pre-2002 risk-off leg based on a Treasury proxy of comparable maturity instead of T-bills.
- Frozen price history with incremental updates of completed trading days.
- Independent replication test of the full backtest.

**Dashboard.** Live signal with factor explanations, since-inception view, rolling
metrics, risk analysis, PDF and Excel exports, German and English, mobile layout.

**Metrics.** Sharpe ratio defined as CAGR ÷ volatility; beta and Jensen's alpha measured
against SHY; 60/40 comparison rebalanced monthly.

## 1.0 — 2023

First dashboard (`SPY3_Dash_web`).
