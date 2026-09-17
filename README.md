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
| Benchmark-Fairness | nur 100 % SPY | zusätzlich klassisches 60/40-Portfolio (SPY/SHY, vor 07/2002 T-Bills) |
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
* Wert von 1.000 USD: SPY3 vor Gebühren (dünn, blau), SPY3 nach Gebühren (grün), S&P 500 und
  klassisches 60/40-Portfolio; rot markierte Risk-Off-Phasen. Daneben die Kennzahlen in gleicher Höhe (Sharpe Ratio und Max. Drawdown hervorgehoben)
* Darunter nebeneinander: maximaler Drawdown und Alpha (kumulierte Log-Überschussrendite
  gegenüber dem S&P 500)
* Reiter: Abstand zum Markt, Rollierende Performance, Ohne Krisen, Kalenderjahre, Timing-Test
* Rollierende Performance (`spy3/rolling.py`): Überschussrendite, Rendite p.a., Volatilität,
  Sharpe Ratio, Calmar Ratio, Max. Drawdown und Beta über 1, 3 oder 5 Jahre, jeweils für SPY3
  brutto/netto, S&P 500 und 60/40, dazu der Anteil der Fenster, in denen SPY3 netto besser war
* Zeitraum- und Skalenumschalter, mit kurzem Hinweis zur Log-/Linear-Skala beim Laden
  (blendet sich nach 5 Sekunden aus, reines CSS); Zahlenformate je Sprache (`spy3/formatting.py`),
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
* **60/40-Portfolio**: Liegt SPY3 bei Rendite, Sharpe und Drawdown über dem klassischen 60/40,
  liefert das Timing Mehrwert gegenüber einer statischen defensiven Allokation.
* **Zufalls-Timing-Test**: p-Wert < 5 % ⇒ das Timing ist nicht durch Quote und Regime-Längen erklärbar.
* **Rollierende 5J-Trefferquote**: ehrlichere Kennzahl als ein über 26 Jahre annualisiertes Alpha.

Bekannte Einschränkungen: 1 Pfad (SPY), Parameter aus v1 übernommen (nicht out-of-sample kalibriert),
Krisenfenster manuell definiert (`spy3/robustness.py::CRISES`).
