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
| Sharpe | ohne risikofreien Satz | weiterhin rf = 0 %; Beta und Jensen's Alpha über SHY (vor 07/2002: T-Bills) |
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

* Kopfzeile: SINTRO-Logo, Signal-Button (Risk On grün / Risk Off rot) mit den Faktoren Risk,
  Momentum und Mean-Reversion (Klick zeigt die Werte) sowie Sprachmenü Deutsch/Englisch
  (Auswahl bleibt im Browser gespeichert)
* Wert von 1.000 USD vor und nach Gebühren, rot markierte Risk-Off-Phasen; Vergleichs-Mixe per
  Legende einblendbar. Kennzahlen für SPY3 brutto und netto
* Reiter: Drawdown, Abstand zum Markt, Rollierende Überschussrendite, Ohne Krisen,
  Kalenderjahre, Timing-Test
* Zeitraum- und Skalenumschalter; Zahlenformate je Sprache (`spy3/formatting.py`),
  Texte in `spy3/i18n.py`

## Daten und Gebühren

* **Risk-Off vor SHY (bis 07/2002):** 13-Wochen-T-Bills (`^IRX`) als Näherung für kurzlaufende
  US-Staatsanleihen. Ein alter Cache ohne T-Bill-Spalte wird automatisch neu geladen.
* **Managementgebühr:** 0,2 % p.a., täglich abgegrenzt.
* **Performancegebühr (`spy3/fees.py`):** 10 % auf den Wertzuwachs über max(High-Water-Mark,
  Hurdle). Die Hurdle ist die HWM, fortgeschrieben mit dem SPY Total Return seit der letzten
  Gebührenzahlung. Tägliche Abgrenzung, Kristallisierung zum Quartalsende, Minderperformance wird
  vorgetragen. Modelliert ist ein Anteil, der zum Backtest-Start gezeichnet wurde.
* **Sharpe Ratio:** rf = 0 %. Beta und Jensen's Alpha über SHY bzw. T-Bills.

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
