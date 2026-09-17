# SPY3 Backtest & Robustness (v2)

Nachfolger von [`SINTRO-AM/SPY3_Dash_web`](https://github.com/SINTRO-AM/SPY3_Dash_web).
Signal-Logik unverändert (Risk / Momentum / Mean-Reversion, SPY ↔ SHY), aber mit korrigierter
Kennzahlenberechnung und einem Robustness-Modul, das das Feedback eines Hedge-Fund-Managers
prüfbar macht:

> *"Die Outperformance kommt aus 2002 und 2008. Wenn die Strategie funktioniert, müsste der
> Chart exponentieller aussehen – der Abstand bleibt langfristig gleich."*

## Was sich gegenüber v1 ändert

| Thema | v1 | v2 |
|---|---|---|
| Performance-Chart | kumulierte **Log**-Renditen auf linearer Achse | Vermögen (Wert von 1 USD), Log-Skala umschaltbar |
| "Total Return" | Summe der Log-Renditen (3,50 → als „350 %“ gezeigt) | `∏(1+r) − 1` |
| "Annualized Return" | Ø Log-Rendite × 252 | CAGR |
| Sharpe | ohne risikofreien Satz | Überschuss über SHY (vor 07/2002: 0 %) |
| Max. Drawdown | in Log-Punkten | preisbasiert |
| Transaktionskosten | 1 bp, an zwei falschen Tagen (Signal(t) vs. Signal(t−2)) | 10 bp je Positionswechsel, genau einmal (`--cost`) |
| Beta / Jensen's Alpha | nicht im Code (Deck) | OLS auf Überschussrenditen |
| Benchmark-Fairness | nur 100 % SPY | zusätzlich statische SPY/SHY-Mixe mit gleicher Ø-Quote bzw. gleichem Beta |
| Robustness | – | Krisen-Attribution, Ex-Krisen-Kennzahlen, rollierende Überschussrendite, Konzentration, Zufalls-Timing-Test, Teilperioden |

## Nutzung

```bash
pip install -r requirements.txt
python -m pytest -q                      # Unit-Tests (ohne Netz)
python scripts/run_report.py --refresh   # Daten via yfinance, Report in reports/
python app.py                            # Dashboard lokal
```

## Dashboard

`python app.py` startet das Dashboard unter http://127.0.0.1:8050 (Deployment: `gunicorn app:server`).

* SINTRO-Logo und aktueller Signalstatus in der Kopfzeile
* Zeitraum (Gesamt, 10, 5, 3, 1 Jahr) und Skala (log/linear) als Umschalter; Kennzahlen und
  Analysen rechnen für den gewählten Zeitraum neu
* Vermögenskurve mit Drawdown und markierten Risk-Off-Phasen; Vergleichs-Mixe per Legende einblendbar
* Reiter: Abstand zum Markt, Rollierende Überschussrendite, Ohne Krisen, Kalenderjahre, Timing-Test
* Einheitliche deutsche Zahlenformate (`spy3/formatting.py`): Renditen, Volatilität, Drawdown,
  Alpha und Capture in %, Sharpe, Calmar, Beta und p-Werte als Dezimalzahl mit 2 Nachkommastellen
* Responsiv bis Smartphone-Breite

## Wie man die Ergebnisse gegenüber dem Manager liest

* **Attribution → „Außerhalb aller Krisen“** ≈ 0 oder negativ ⇒ sein Punkt stimmt: die Rendite-Outperformance
  stammt aus wenigen Crash-Phasen.
* **Relative-Chart (SPY3 / S&P 500)** waagerecht nach 2009 ⇒ derselbe Befund visuell.
* **Static-/Beta-Mix**: Liegt SPY3 bei Sharpe und Drawdown klar über einem Mix mit gleicher Aktienquote,
  ist das Timing wertvoll – auch wenn es keine Rendite-Alpha in Bullenmärkten liefert.
* **Zufalls-Timing-Test**: p-Wert < 5 % ⇒ das Timing ist nicht durch Quote und Regime-Längen erklärbar.
* **Rollierende 5J-Trefferquote**: ehrlichere Kennzahl als ein über 26 Jahre annualisiertes Alpha.

Bekannte Einschränkungen: 1 Pfad (SPY), Parameter aus v1 übernommen (nicht out-of-sample kalibriert),
Krisenfenster manuell definiert (`spy3/robustness.py::CRISES`).
