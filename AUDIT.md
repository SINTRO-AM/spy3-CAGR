# Audit des SPY3-Backtests im Dashboard (Stand 20.09.2026)

Grundlage: echte SPY- und SHY-Kurse aus `backtest.xlsx` (07/1999–02/2024, solange SHY dort
vorliegt), Bloomberg-Treasury-Index vor 07/2002, Dashboard-Engine mit Standardparametern.
Alle Zahlen brutto vor Management- und Performancegebühr, nach 10 bp je Switch.
Reproduzierbar mit `python scripts/audit.py`.

## Befunde in der Excel-Datei (Basis von Deck und Whitepaper)

1. **Dividenden doppelt gezählt.** Spalte C ist der dividendenbereinigte Kurs (Adj Close),
   Spalte E addiert die Dividende trotzdem noch einmal (`+ Dividende/Kurs`). Effekt 2000–2023:
   +0,545 Log-Punkte, Faktor 1,73 auf das Endvermögen – bei Strategie *und* Benchmark.
   Whitepaper-CAGR 14,3 % → korrekt ca. 12,4 %; Benchmark 10,4 % → ca. 7,1 %.
2. **Risk-Off-Bein = Bloomberg-Index aller Laufzeiten** (Duration 5–6 J.) über den gesamten
   Backtest, nicht der SHY (1–3 J.). Nach dem 14.10.2022 (Datenende) ist die Risk-Off-Rendite 0 %.
3. **Switch-Tage doppelt bzw. gar nicht verbucht.** `R = L(t−1)·E − U − Y + F` addiert F über
   `L(t)`: am Tag des Wechsels in Risk-Off werden Aktien- und Anleiherendite gebucht, beim
   Wechsel in Risk-On keine von beiden. Kleiner, aber systematischer Logikfehler.
4. **Handelskosten 1 bp** im Modell, 10 bp im Deck. Kosten werden am Signaltag statt am Handelstag
   gebucht (einen Tag zu früh, unerheblich).
5. **VaR-Fenster 50 Tage** in Excel und Dashboard, das Whitepaper nennt 90 Tage. Mit 90 Tagen
   fällt die Sharpe Ratio von 0,98 auf 0,78.
6. Fenster: Excel MA 30/198 und 199-Tage-Hoch, Dashboard 29/198 und 200 Tage → 3 % der Signale
   weichen ab; Kennzahlen praktisch identisch.

Dashboard-Engine und Excel-Modell stimmen nach Bereinigung überein: CAGR 12,6 % (Engine) vs.
12,4 % (Excel ohne Doppelzählung), gleicher Zeitraum.

## Rechenlogik der Engine (geprüft)

- Position = Signal des Vortags (kein Look-ahead); Signale nur aus Daten bis t.
- Kosten genau einmal je Positionswechsel; 79 Wechsel in 24 Jahren (3,3 p.a.), 0,33 % p.a.
- Einfache Renditen, Total Return, CAGR, Drawdown geometrisch korrekt; Log-Punkte nur in der
  Attribution. 43 Tests decken das ab.
- Risikofreier Satz 0 % in der Sharpe Ratio (geometrisch, CAGR/Vol). Arithmetisch läge die
  Benchmark höher (0,51 statt 0,43 über 2000–2026).
- Performancegebühr: HWM, SPY-Hurdle, quartalsweise Kristallisierung, Vortrag – geprüft.

## Standardkonfiguration seit Commit dieser Version

- Kurse: Yahoo Finance Adjusted Close (auto_adjust), SPY und SHY, Dividenden genau einmal
  enthalten; SHY ab 30.07.2002, davor Proxy gleicher Laufzeit, sonst Bloomberg-Treasury-Index,
  sonst T-Bills (Reihenfolge in `spy3/data.py`).
- Ausführung (Standard): Signal aus der Schlussauktion von t, Handel zum selben Schlusskurs,
  Wirkung ab t+1 (`StrategyParams.exec_delay = 0`). Das ist eine Näherung: In der Praxis
  entsteht das Signal aus einem Indikationspreis kurz vor Schluss. Die konservative Variante
  MOC am Folgetag (`exec_delay = 1`) kostet 1,3 Pp. CAGR p.a. und hebt den maximalen
  Drawdown von −20 % auf −29 %; der Unterschied entsteht an 79 Switch-Tagen, fast die Hälfte
  davon am 12.03.2020.
- Parameter unverändert 29/198, VaR 50 Tage 5 %/2 %, Mean-Reversion 1,3; 10 bp je Switch.

## Robustheit mit MOC-Ausführung (2000-01 bis 2024-02, echte SPY/SHY-Kurse)

| Test | Ergebnis |
|---|---|
| **Basis (MOC t+1)** | **CAGR 11,2 %, Vol 12,9 %, Sharpe 0,87, MaxDD −29,0 %** (SPY: 7,1 %, 19,6 %, 0,36, −55,2 %) |
| alte Annahme (Handel Schluss t) | CAGR 12,5 %, Sharpe 0,98, MaxDD −20,0 % |
| Kosten 0 / 25 / 50 bp | Sharpe 0,90 / 0,83 / 0,75 (3,3 Switches p.a.) |
| ohne Mean-Reversion / ohne VaR-Veto | Sharpe 0,75 / 0,63 (MaxDD −37,9 %) |
| Zufalls-Timing (500×) | Median 0,30, p < 0,001 |
| 200 zufällige Parametersätze | Median 0,63, P90 0,74, Max 0,82; Basis 0,87 = Perzentil 100 % |
| Nachbarn | MA 29/150: 0,74; 29/250: 0,78; VaR 30d: 0,77; 90d: 0,74; DD 1,2: 0,84; 1,4: 0,81 |
| Teilperioden Sharpe SPY3 vs SPY | 2000–04 1,08/−0,12 · 2005–09 1,10/0,02 · 2010–14 0,95/0,97 · 2015–19 0,73/0,86 · 2020–24 0,52/0,57 |
| Attribution Log-Überschuss | Dotcom 97 %, GFC 65 %, Covid −26 %, außerhalb Krisen −50 % |
| 5J-Fenster geschlagen | 45 % · Up/Down-Capture 71 %/38 % · Beta 0,41 |

**Covid 2020 mit MOC-Ausführung:** investiert bis 12.03. (−26,5 % mitgenommen), Risk-Off
13.03.–16.06. (SPY in dieser Zeit +26,9 %, SPY3 +0,6 %), Wiedereinstieg 17.06. Tief am
26.06.2020 bei −29,0 %, altes Hoch erst am 29.04.2021 wieder erreicht. Das VaR-Veto schützt
vor langen Bärenmärkten, nicht vor einem V-förmigen Crash.

## Robustheit (alte Annahme, Handel zum Schluss von t)

| Test | Ergebnis |
|---|---|
| Basis | CAGR 12,5 %, Sharpe 0,98, MaxDD −20,0 % (SPY: 7,1 %, 0,36, −55,2 %) |
| Handel einen Tag später | CAGR 11,2 %, Sharpe 0,87, **MaxDD −29,0 %** |
| Kosten 25 / 50 bp | Sharpe 0,94 / 0,87 |
| ohne Mean-Reversion | CAGR 10,0 %, Sharpe 0,84 |
| ohne VaR-Veto | Sharpe 0,72, MaxDD −38,7 % |
| nur Momentum 29/198 | CAGR 9,2 %, Sharpe 0,73, MaxDD −29,9 % |
| Zufalls-Timing (500×) | Median-Sharpe 0,30, p < 0,001 |
| 300 zufällige Parametersätze | Median 0,62, P90 0,74, Max 0,83 – **Basis 0,98 = Perzentil 100 %** |
| Walk-Forward 2000–07 → 2008–15 | Train 1,28 → Test 0,63 (Basisparameter im Test: 0,92) |
| Walk-Forward 2008–15 → 2016–24 | Train 0,96 → Test 0,97 |
| Deflated Sharpe (N = 1.000) | erwartetes Max 0,28 → DSR ≈ 1,00 |
| Rollierende 5J-Fenster geschlagen | 47 % |
| Attribution Log-Überschuss | Dotcom 87 %, GFC 46 %, außerhalb Krisen **−34 %** |

## Einordnung (Dashboard)

- **Der Effekt ist real.** Zufalls-Timing und DSR zeigen: Der Vorteil aus Trendfolge plus
  Volatilitätsveto auf SPY/SHY ist kein Zufallsprodukt. Selbst zufällige Parameter liefern
  Sharpe 0,62 gegenüber 0,36 für den S&P 500.
- **Die Höhe ist optimiert.** Die gewählten Parameter liegen in jeder Landschaft auf dem Maximum
  und über allen 300 Zufallssätzen. Der Mean-Reversion-Trigger 1,3 ist ein Spitzenwert
  (1,2 → 0,87, 1,4 → 0,84). Realistische Out-of-Sample-Erwartung: Sharpe 0,7–0,9, nicht 1,0.
- **Der Drawdown ist jetzt ehrlich.** Mit MOC-Ausführung liegt er bei −29 % statt −20 %; die
  frühere Zahl setzte Handel zum selben Schlusskurs voraus, aus dem das Signal stammt. Die
  Volatilität bleibt bei 12,9 %, die Sharpe Ratio fällt auf 0,87.
- **Die Outperformance ist regimeabhängig.** Zwei Crashs erklären den gesamten Vorsprung,
  außerhalb der Krisen ist der Beitrag negativ. Das ist das Design (Verlustvermeidung), sollte
  aber genau so kommuniziert werden – nicht als „Alpha über alle Marktzyklen“.
- **Live-Zeitraum:** ab 09/2023 bis 02/2024 SPY3 10,5 % vs. SPY 10,5 %. Zu kurz für eine Aussage.

## Empfehlungen

1. Excel-Doppelzählung der Dividenden beheben (E = D) und Deck/Whitepaper auf die bereinigten
   Werte umstellen; VaR-Fenster im Text an den Code angleichen.
2. Ausführung konservativ modellieren: Signal aus Schlusskurs t, Handel zum Schluss t+1
   (`lag=2`), oder Eröffnungskurse t+1 verwenden. Diese Variante als Hauptfall ausweisen.
3. Parameter regularisieren: Fenster auf runde Werte (30/200, VaR 50 oder 60 Tage,
   Mean-Reversion 25 % statt 1/1,3) und die Ergebnisse mit Nachbarparametern mitzeigen.
4. Walk-Forward als festen Bestandteil des Reports; Live-Track-Record separat gegen SPY ausweisen.
5. Risk-Off-Bein einheitlich: SHY ab 2002, davor Proxy gleicher Laufzeit (`check_shy_proxy.py`).
