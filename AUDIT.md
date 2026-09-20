# Audit des SPY3-Backtests (Stand 20.09.2026)

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

## Robustheit (2000-01 bis 2024-02)

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

## Einordnung

- **Der Effekt ist real.** Zufalls-Timing und DSR zeigen: Der Vorteil aus Trendfolge plus
  Volatilitätsveto auf SPY/SHY ist kein Zufallsprodukt. Selbst zufällige Parameter liefern
  Sharpe 0,62 gegenüber 0,36 für den S&P 500.
- **Die Höhe ist optimiert.** Die gewählten Parameter liegen in jeder Landschaft auf dem Maximum
  und über allen 300 Zufallssätzen. Der Mean-Reversion-Trigger 1,3 ist ein Spitzenwert
  (1,2 → 0,87, 1,4 → 0,84). Realistische Out-of-Sample-Erwartung: Sharpe 0,7–0,9, nicht 1,0.
- **Der Drawdown hängt an der Ausführung.** Ein Tag Verzögerung hebt den Maximaldrawdown von
  −20 % auf −29 %. 35 % der Risk-Off-Phasen dauern höchstens drei Tage. Wer das Signal aus dem
  Schlusskurs berechnet, kann nicht zum selben Schlusskurs handeln.
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
