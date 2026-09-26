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
| Sharpe | ohne risikofreien Satz | weiterhin rf = 0 %; Beta und Jensen's Alpha über SHY (vor 07/2002: Bloomberg Treasury Index) |
| Max. Drawdown | in Log-Punkten | preisbasiert |
| Transaktionskosten | 1 bp, an zwei falschen Tagen (Signal(t) vs. Signal(t−2)) | 10 bp je Positionswechsel, genau einmal (`--cost`) |
| Ausführung | Handel zum selben Schlusskurs wie das Signal (implizit) | explizit: `exec_delay=0` = Signal aus der Schlussauktion, Handel zum selben Schluss (Näherung); `exec_delay=1` = MOC am Folgetag als konservative Variante |
| Beta / Jensen's Alpha | nicht im Code (Deck) | OLS auf Überschussrenditen |
| Benchmark-Fairness | nur 100 % SPY | zusätzlich klassisches 60/40-Portfolio (SPY/SHY, monatlich rebalanciert, vor 07/2002 Bloomberg Treasury Index) |
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
* Wert von 1.000 USD mit zweiter Werteachse rechts für den 1-Tages-VaR (99 %, grau
  gestrichelt): SPY3 vor Gebühren (dünn, blau), SPY3 nach Gebühren (grün), S&P 500 und
  klassisches 60/40-Portfolio; rot markierte Risk-Off-Phasen. Daneben die Kennzahlen in gleicher Höhe (Sharpe Ratio und Max. Drawdown hervorgehoben)
* „Inside the SPY3 Model“: SPY-Kurs mit 30d/200d-Linie (im Modell 29/198), Mean-Reversion-Schwelle,
  1-Tages-VaR mit den Schwellen 5 %/2 % auf der zweiten Achse und rot markierten Risk-Off-Phasen;
  rechts daneben rollierende 3-Jahres-Sharpe, -Calmar und -Volatilität (SPY3 netto vs. S&P 500)
* Darunter nebeneinander: maximaler Drawdown und Vorsprung gegenüber dem S&P 500 (Vermögen
  relativ zur Benchmark, z. B. 3,0x = dreifaches Endvermögen)
* Tooltips an Kennzahlen, Spaltenköpfen und Charts (Definition und Einheit)
* Reiter (Standard: Rollierende Performance mit 3-Jahres-Sharpe-Ratio): Rollierende
  Performance, Abstand zum Markt, Ohne Krisen, Kalenderjahre, Timing-Test
* Rollierende Performance (`spy3/rolling.py`): Überschussrendite, Rendite p.a., Volatilität,
  Sharpe Ratio, Calmar Ratio, Max. Drawdown und Beta über 1, 3 oder 5 Jahre, jeweils für SPY3
  brutto/netto, S&P 500 und 60/40, dazu der Anteil der Fenster, in denen SPY3 netto besser war
* Aktuelles Signal oben: Der Risk-On/Off-Button erklärt Regel und Ergebnis; jeder Faktor-Chip
  hat eine eigene Karte mit aktuellem Wert, Regel und wissenschaftlichem Hintergrund samt
  Quellen (Engle 1982, Bollerslev 1986, Moreira & Muir 2017; Brock, Lakonishok & LeBaron 1992,
  Moskowitz, Ooi & Pedersen 2012; De Bondt & Thaler 1985, Poterba & Summers 1988). Das Signal wird unabhängig vom
  Backtest laufend aus den neuesten Schlusskursen berechnet (`spy3/live.py`, Kurse höchstens
  alle 30 Minuten neu geladen, ohne Netz Rückfall auf den Cache)
* Methodik-Abschnitt zum Aufklappen unter Chart und Kennzahlen
* Download-Buttons in der Kopfzeile: PDF-Report mit SINTRO-Logo (Kennzahlen, Vermögens-,
  Drawdown- und Vorsprung-Chart, Attribution, Kalenderjahre, Disclaimer) und Excel-Mappe mit
  den Rohdaten (Tagesdaten inkl. Log-Renditen und kumulierten Log-Punkten, KPIs, Kalenderjahre,
  Attribution, Notes). Beide übernehmen den
  gewählten Zeitraum und die eingestellten Gebühren (`spy3/report.py`). matplotlib, reportlab
  und XlsxWriter werden erst beim Export importiert: fehlen sie, läuft das Dashboard weiter und
  die Buttons sind deaktiviert (`pip install -r requirements.txt` behebt das)
* Regler für Managementgebühr (0–2,0 % p.a.) und Performancegebühr (0–30 %); die Netto-Reihe,
  die Kennzahlen und alle Charts rechnen sofort neu (brutto bleibt unverändert)
* Zeitraum- (Gesamt, 10, 5, 3, 1 Jahr, seit Auflage 09/2023) und Skalenumschalter (Standard: linear), mit kurzem Hinweis zur Log-/Linear-Skala
  beim Laden und einem Tooltip an der Skala
  (blendet sich nach 10 Sekunden aus, reines CSS); Zahlenformate je Sprache (`spy3/formatting.py`),
  Texte in `spy3/i18n.py`

## Chart fürs Deck

`python scripts/deck_chart.py --lang de --net` erzeugt die korrigierte Fassung des
Performance-Charts aus dem Pitch-Deck als HTML, PNG und SVG unter `reports/`. Gegenüber der
alten Folie: Wert einer Anlage von 1.000 USD auf logarithmischer Skala statt kumulierter
Log-Renditen mit Prozent-Beschriftung, 200-Tage-Linie auf dem Kurs statt auf einer
Renditereihe, Netto-Reihe nach Gebühren und Markierung des Live-Track-Records ab 09/2023.
VaR und Schwellen bleiben auf der rechten Achse. PNG/SVG brauchen `kaleido`
(`pip install kaleido`, danach einmalig `plotly_get_chrome`); ohne das entsteht nur die
HTML-Datei.

## Einheiten: Log-Punkte vs. Vielfaches

Die Attribution rechnet in Log-Punkten, weil sich nur so die Beiträge der Phasen exakt zum
Gesamtwert addieren. Umrechnung: `exp(x)`. 110 Log-Punkte entsprechen dem 3,0-fachen Vermögen
gegenüber der Benchmark, was zu Total Returns von 2.423 % und 737 % passt
(25.225 / 8.367 = 3,01). Der Vorsprung-Chart zeigt deshalb das Vielfache, nicht die Log-Punkte.

## Schrift

Die Oberfläche nutzt **Garet**, mit Jost als Rückfall. Garet ist lizenzpflichtig und liegt
deshalb nicht im Repository: Schriftdateien nach `assets/fonts/` legen (Details in der README
dort), dann greifen sowohl Dashboard als auch PDF-Report automatisch darauf zu. Ohne die
Dateien sieht alles aus wie bisher.

## Daten und Gebühren

* **Risk-Off vor SHY (bis 07/2002):** ein Proxy mit gleicher Laufzeit wie der SHY (1–3 Jahre),
  in dieser Reihenfolge: Bloomberg US Treasury 1-3 Year Index (`data/lt01truu.csv`, gleiches
  Format wie unten); sonst eine synthetische Gesamtrendite aus den FRED-Renditen DGS1/DGS2/DGS3
  (`python scripts/check_shy_proxy.py` lädt sie einmalig und vergleicht den Proxy mit dem echten
  SHY ab 2002); sonst der Bloomberg US Treasury Total Return Index (LUATTRUU) aus
  `data/luattruu.csv` (anderer Ort per Umgebungsvariable `SPY3_TREASURY_FILE`). Der Loader
  liest den Bloomberg-Export unverändert, auch als `.xlsx`, mit Tab, Semikolon oder Komma,
  Dezimalkomma oder -punkt, in UTF-8, UTF-16 oder Windows-1252. Dürfen die Kurse nicht
  abgelegt werden, genügt eine Datei mit Datum und Log-Rendite in Prozent (die dritte Spalte
  des Exports); daraus wird eine gleichwertige Kursreihe gebildet. Die Datei liegt wegen der
  Bloomberg-Lizenz nicht im Repository.
  Fehlt sie, greifen 13-Wochen-T-Bills (`^IRX`), danach 0 %. Welche Quelle tatsächlich gilt,
  zeigen die Startmeldung von `app.py`, die Fußnote unter der Kennzahlentabelle und die Spalte
  `risk_off_source` im Excel-Export. `python scripts/check_risk_off.py` rechnet beide
  Varianten und beziffert den Unterschied.
* **SHY ETF als Vergleichsreihe:** Das Risk-Off-Bein der Strategie erscheint zusätzlich als
  Spalte in der Kennzahlentabelle und als Linie in Vermögens-, Drawdown- und Vorsprung-Chart,
  also SHY ab 07/2002 und davor dieselbe Näherung wie im Backtest (Bloomberg-Treasury-Index,
  sonst T-Bills). Die Fußnote nennt Datum und Quelle der Näherung.
* **Managementgebühr:** 0,2 % p.a., täglich abgegrenzt.
* **Performancegebühr (`spy3/fees.py`):** 10 % auf den Wertzuwachs über max(High-Water-Mark,
  Hurdle). Die Hurdle ist die HWM, fortgeschrieben mit dem SPY Total Return seit der letzten
  Gebührenzahlung. Tägliche Abgrenzung, Kristallisierung zum Quartalsende, Minderperformance wird
  vorgetragen. Modelliert ist ein Anteil, der zum Backtest-Start gezeichnet wurde.
* **Sharpe Ratio:** geometrisch, also CAGR geteilt durch annualisierte Volatilität, rf = 0 %.
  Damit passt sie zur CAGR-Zeile der Tabelle. Die klassische arithmetische Variante liegt bei
  volatilen Reihen höher (S&P 500: 0,51 statt 0,43). Beta und Jensen's Alpha über SHY bzw. Treasury-Index.

## Audit

`python scripts/audit.py` rechnet die Robustheitsprüfungen auf den geladenen Daten:
Ausführungsverzögerung, Kostensensitivität, Faktor-Ablation, Zufalls-Timing,
Parameter-Landschaft mit zufälligen Parametersätzen, Walk-Forward, Deflated Sharpe Ratio,
Attribution. Ergebnisse und Einordnung siehe `AUDIT.md`.

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
