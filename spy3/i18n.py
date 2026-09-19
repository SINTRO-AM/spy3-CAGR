"""Texte für das Dashboard (Deutsch/Englisch)."""
from __future__ import annotations

LANGS = {"de": "Deutsch", "en": "English"}

TXT: dict[str, tuple[str, str]] = {
    # Kopf und Einleitung
    "title": ("SPY3 im Vergleich zum S&P 500", "SPY3 compared with the S&P 500"),
    "lede": ("Backtest {start} bis {end}, Total Return in USD.",
             "Backtest {start} to {end}, total return in USD."),
    "lede_defs": ("SPY3 brutto: nach Handelskosten von {cost} bp je Umschichtung. "
                  "SPY3 netto: zusätzlich nach {mgmt} Managementgebühr p.a. und {perf} "
                  "Performancegebühr.",
                  "SPY3 gross: after trading costs of {cost} bp per switch. "
                  "SPY3 net: additionally after the {mgmt} p.a. management fee and the "
                  "{perf} performance fee."),
    "lang_menu": ("Sprache", "Language"),
    "period": ("Zeitraum", "Period"),
    "scale": ("Skala", "Scale"),
    "dl_pdf": ("PDF-Report", "PDF report"),
    "dl_xlsx": ("Rohdaten (Excel)", "Raw data (Excel)"),
    "dl_missing": ("Export nicht verfügbar – fehlende Pakete: {pkgs}. Installation: "
                   "pip install -r requirements.txt",
                   "Export unavailable – missing packages: {pkgs}. Install with: "
                   "pip install -r requirements.txt"),
    "dl_note": ("Report und Rohdaten enthalten den gewählten Zeitraum und die eingestellten "
                "Gebühren.",
                "Report and raw data reflect the selected period and the fee settings."),
    "mgmt_fee": ("Managementgebühr", "Management fee"),
    "perf_fee": ("Performancegebühr", "Performance fee"),
    "log": ("Logarithmisch", "Logarithmic"),
    "hint_title": ("Tipp zur Skala", "A note on the scale"),
    "hint_body": ("Logarithmisch: gleiche Abstände bedeuten gleiche prozentuale "
                  "Veränderungen – gut zum Vergleich der Wachstumsraten über 26 Jahre. "
                  "Linear zeigt absolute Beträge und damit den Zinseszinseffekt.",
                  "Logarithmic: equal distances mean equal percentage changes, which is "
                  "how to compare growth rates over 26 years. Linear shows absolute "
                  "amounts, and therefore the compounding effect."),
    "linear": ("Linear", "Linear"),
    "p_all": ("Gesamt", "Full"), "p_10": ("10 Jahre", "10 years"),
    "p_5": ("5 Jahre", "5 years"), "p_3": ("3 Jahre", "3 years"), "p_1": ("1 Jahr", "1 year"),
    # Signal
    "sig_title": ("Details zu den Faktoren anzeigen", "Show factor details"),
    "sig_asof": ("Signal zum Handelsschluss am {d}. Gehandelt wird am nächsten Handelstag.",
                 "Signal as of the close on {d}. Trades are executed on the next trading day."),
    "sig_rule": ("Risk Off durch den Risk-Faktor hat Vorrang. Sonst genügt ein Risk-On-Faktor "
                 "für eine Investition in SPY.",
                 "A Risk Off from the risk factor takes precedence. Otherwise one Risk On "
                 "factor is enough to hold SPY."),
    "f_var": ("1-Tages-VaR (99 %) {v}", "1-day VaR (99%) {v}"),
    "f_mom": ("MA{f} gegenüber MA{s}: {v}", "MA{f} vs. MA{s}: {v}"),
    "f_mr": ("Abstand zum {w}-Tage-Hoch: {v}", "Distance from {w}-day high: {v}"),
    # Hauptchart
    "perf": ("Wert einer Investition von 1.000 USD", "Value of a $1,000 investment"),
    "perf_note": ("Rot hinterlegt: Strategie hält kurzlaufende US-T-Bills",
                  "Red shading: strategy holds short-term US T-Bills"),
    "gross": ("SPY3 vor Gebühren", "SPY3 before fees"),
    "net": ("SPY3 nach Gebühren", "SPY3 after fees"),
    "riskoff": ("Risk-Off", "Risk off"),
    "var_line": ("1-Tages-VaR 99 % (rechte Achse)", "1-day VaR 99% (right axis)"),
    "var_axis": ("1-Tages-VaR 99 %", "1-day VaR 99%"),
    "fees_note": ("Gebühren: {mgmt} Managementgebühr p.a. und {perf} Performancegebühr über "
                  "High-Water-Mark und SPY-Hurdle, quartalsweise abgerechnet.",
                  "Fees: {mgmt} p.a. management fee and {perf} performance fee above the "
                  "high-water mark and the SPY hurdle, crystallised quarterly."),
    # Kennzahlen
    "kpis": ("Kennzahlen", "Key figures"),
    "kpi_note": ("60/40: 60 % SPY und 40 % SHY, täglich rebalanciert. Sharpe Ratio ohne "
                 "risikofreien Satz (rf = 0 %), Beta und Alpha über kurzlaufende "
                 "Staatsanleihen. Vor 07/2002 ersetzen 13-Wochen-T-Bills den SHY.",
                 "60/40: 60% SPY and 40% SHY, rebalanced daily. Sharpe ratio without a "
                 "risk-free rate (rf = 0%), beta and alpha against short-term Treasuries. "
                 "Before 07/2002, 13-week T-bills stand in for SHY."),
    "col_gross": ("SPY3 brutto", "SPY3 gross"),
    "col_net": ("SPY3 netto", "SPY3 net"),
    # Tabs
    "t_dd": ("Drawdown", "Drawdown"),
    "t_gap": ("Abstand zum Markt", "Gap to market"),
    "t_roll": ("Rollierende Performance", "Rolling performance"),
    "t_ex": ("Ohne Krisen", "Excluding crises"),
    "t_years": ("Kalenderjahre", "Calendar years"),
    "t_timing": ("Timing-Test", "Timing test"),
    "dd_title": ("Maximaler Drawdown", "Maximum drawdown"),
    "dd_note": ("Rückgang vom jeweils letzten Höchststand. Rot hinterlegt: Risk-Off-Phasen.",
                "Decline from the previous peak. Red shading: risk-off phases."),
    "alpha_title": ("Vorsprung gegenüber dem S&P 500", "Lead over the S&P 500"),
    "alpha_note": ("Vermögen relativ zum S&P 500. 3,0x bedeutet dreifaches Endvermögen – "
                   "genau das Verhältnis der Total Returns.",
                   "Wealth relative to the S&P 500. 3.0x means three times the ending "
                   "wealth, exactly the ratio of the two total returns."),
    "cum_title": ("Kumulierte Überschussrendite", "Cumulative excess return"),
    "cum_note": ("In Log-Punkten, damit sich die Phasen sauber aufteilen lassen. "
                 "110 Log-Punkte entsprechen dem 3,0-fachen Vermögen der Benchmark.",
                 "In log points, so the periods add up cleanly. 110 log points correspond "
                 "to 3.0x the benchmark wealth."),
    "att_title": ("Beitrag der Krisenphasen", "Contribution of crisis periods"),
    "att_note": ("Beitrag zur kumulierten Log-Überschussrendite je Phase (vor Gebühren).",
                 "Contribution to the cumulative log excess return by period (before fees)."),
    "rel_title": ("Relative Wertentwicklung", "Relative performance"),
    "rel_note": ("SPY3 geteilt durch S&P 500. Steigt die Linie, baut SPY3 Vorsprung auf; "
                 "verläuft sie waagerecht, entwickeln sich beide gleich.",
                 "SPY3 divided by the S&P 500. A rising line means SPY3 is pulling ahead; "
                 "a flat line means both move alike."),
    "src_title": ("Woher der Vorsprung kommt", "Where the lead comes from"),
    "src_note": ("Aufteilung der kumulierten Überschussrendite (log, vor Gebühren) auf "
                 "Krisenphasen und übrige Zeit.",
                 "Split of the cumulative excess return (log, before fees) across crisis "
                 "periods and the rest."),
    "phase": ("Phase", "Period"), "excess_log": ("Überschuss (log)", "Excess (log)"),
    "share": ("Anteil", "Share"),
    "roll_title": ("Rollierende Performance", "Rolling performance"),
    "roll_note_x": ("Kennzahl im rollierenden Fenster, jeweils bis zum dargestellten Datum.",
                    "Metric over a rolling window ending on each date shown."),
    "roll_metric": ("Kennzahl", "Metric"),
    "roll_window": ("Fenster", "Window"),
    "rm_excess": ("Überschussrendite p.a.", "Excess return p.a."),
    "rm_return": ("Rendite p.a.", "Return p.a."),
    "rm_vol": ("Volatilität", "Volatility"),
    "rm_sharpe": ("Sharpe Ratio", "Sharpe ratio"),
    "rm_calmar": ("Calmar Ratio", "Calmar ratio"),
    "rm_maxdd": ("Max. Drawdown", "Max. drawdown"),
    "rm_beta": ("Beta", "Beta"),
    "rm_excess_note": ("Annualisierte Differenz der Log-Renditen gegenüber dem S&P 500.",
                       "Annualised difference in log returns versus the S&P 500."),
    "win_sp": ("der {y}-Jahres-Fenster: SPY3 netto besser als S&P 500",
               "of {y}-year windows: SPY3 net better than S&P 500"),
    "win_6040": ("der {y}-Jahres-Fenster: SPY3 netto besser als 60/40",
                 "of {y}-year windows: SPY3 net better than 60/40"),
    "median_net": ("Median SPY3 netto ({y} Jahre)", "Median SPY3 net ({y}-year)"),
    "median_sp": ("Median S&P 500 ({y} Jahre)", "Median S&P 500 ({y}-year)"),
    "yr_short": ("{y} J.", "{y}Y"),
    "years_n": ("{y} Jahre", "{y} years"),
    "ex1_title": ("Ohne Dotcom-Crash und Finanzkrise", "Excluding dot-com crash and GFC"),
    "ex1_note": ("Kennzahlen ohne 01/2000–03/2003 und 10/2007–06/2009.",
                 "Figures excluding 01/2000–03/2003 and 10/2007–06/2009."),
    "ex2_title": ("Ohne alle Krisenphasen", "Excluding all crisis periods"),
    "ex2_note": ("Zusätzlich ohne Covid-Crash 2020 und das Jahr 2022.",
                 "Also excluding the 2020 Covid crash and the year 2022."),
    "yr_title": ("Kalenderjahre", "Calendar years"),
    "yr_note": ("Jahresrenditen vor Gebühren und Differenz in Prozentpunkten.",
                "Annual returns before fees and difference in percentage points."),
    "year": ("Jahr", "Year"), "diff": ("Differenz", "Difference"), "ytd": ("lfd.", "YTD"),
    "dec_title": ("Jahrzehnte", "Decades"),
    "dec_note": ("Kennzahlen je Teilperiode.", "Figures by sub-period."),
    "tt_title": ("Zufalls-Timing-Test", "Random timing test"),
    "tt_note": ("Das SPY3-Signal wird 500-mal zeitlich verschoben. Aktienquote und Länge der "
                "Phasen bleiben gleich, nur das Timing ist zufällig. Der p-Wert gibt an, wie "
                "oft zufälliges Timing mindestens so gut war. Immer über den gesamten "
                "Zeitraum berechnet.",
                "The SPY3 signal is shifted in time 500 times. Equity weight and phase "
                "lengths stay the same; only the timing is random. The p-value shows how "
                "often random timing did at least as well. Always computed over the full "
                "period."),
    "tt_random": ("Zufälliges Timing (Median)", "Random timing (median)"),
    "p_value": ("p-Wert", "p-value"),
    "footer": ("SINTRO Asset Management GmbH · Simulierte Wertentwicklung. Vergangene oder "
               "simulierte Ergebnisse sind kein verlässlicher Indikator für künftige "
               "Ergebnisse.",
               "SINTRO Asset Management GmbH · Simulated performance. Past or simulated "
               "results are not a reliable indicator of future results."),
}

# Kennzahlen, Zeilen und Phasen (deutscher Schlüssel -> englisch)
EN_TERMS = {
    "Total Return": "Total return", "CAGR": "CAGR", "Volatilität p.a.": "Volatility p.a.",
    "Sharpe Ratio": "Sharpe ratio", "Max. Drawdown": "Max. drawdown",
    "Calmar": "Calmar ratio", "Beta": "Beta", "Jensen's Alpha p.a.": "Jensen's alpha p.a.",
    "Up-Capture": "Up capture", "Down-Capture": "Down capture",
    "Dotcom 2000–03": "Dot-com 2000–03", "GFC 2007–09": "GFC 2007–09",
    "Covid 2020": "Covid 2020", "Inflation 2022": "Inflation 2022",
    "Außerhalb aller Krisen": "Outside all crises", "Gesamt": "Total",
    "Dotcom": "Dot-com", "GFC": "GFC", "Covid": "Covid", "Inflation": "Inflation",
    "CAGR SPY3": "CAGR SPY3", "CAGR BM": "CAGR S&P 500",
    "Sharpe SPY3": "Sharpe SPY3", "Sharpe BM": "Sharpe S&P 500",
    "MaxDD SPY3": "Max. DD SPY3", "MaxDD BM": "Max. DD S&P 500",
}
DE_TERMS = {"Calmar": "Calmar Ratio", "CAGR BM": "CAGR S&P 500",
            "Sharpe BM": "Sharpe S&P 500", "MaxDD SPY3": "Max. DD SPY3",
            "MaxDD BM": "Max. DD S&P 500"}


# Tooltips: Kennzahlen und Charts (de, en)
TIPS: dict[str, tuple[str, str]] = {
    "Total Return": ("Gesamtertrag über den Zeitraum, geometrisch verkettet: "
                     "Endwert geteilt durch Startwert minus 1.",
                     "Total gain over the period, geometrically linked: ending value "
                     "divided by starting value minus 1."),
    "CAGR": ("Geometrische Durchschnittsrendite pro Jahr, die den Startwert auf den "
             "Endwert bringt.",
             "Geometric average return per year that turns the starting value into the "
             "ending value."),
    "Volatilität p.a.": ("Standardabweichung der Tagesrenditen, mit Wurzel 252 auf ein "
                         "Jahr skaliert.",
                         "Standard deviation of daily returns, scaled to one year by the "
                         "square root of 252."),
    "Sharpe Ratio": ("Rendite je Einheit Risiko: CAGR geteilt durch die annualisierte "
                     "Volatilität, ohne risikofreien Satz (rf = 0 %). Geometrische "
                     "Variante, deshalb konsistent mit der CAGR-Zeile.",
                     "Return per unit of risk: CAGR divided by annualised volatility, "
                     "without a risk-free rate (rf = 0%). Geometric definition, hence "
                     "consistent with the CAGR row."),
    "Calmar": ("Rendite je Einheit Verlustrisiko: CAGR geteilt durch den Betrag des "
               "maximalen Drawdowns.",
               "Return per unit of downside risk: CAGR divided by the absolute maximum "
               "drawdown."),
    "Beta": ("Sensitivität gegenüber dem S&P 500 aus einer Regression auf Tagesrenditen. "
             "1,00 = Indexrisiko, 0,41 = rund 40 % davon.",
             "Sensitivity to the S&P 500 from a regression on daily returns. 1.00 = index "
             "risk, 0.41 = roughly 40% of it."),
    "Jensen's Alpha p.a.": ("Rendite über dem, was Beta gegenüber dem Index erklärt, "
                            "annualisiert. Risikofreier Satz: kurzlaufende Staatsanleihen.",
                            "Return beyond what beta versus the index explains, "
                            "annualised. Risk-free rate: short-term Treasuries."),
    "Up-Capture": ("Anteil der Indexrendite, den die Strategie in Monaten mit steigendem "
                   "Index erzielt.",
                   "Share of the index return the strategy captures in months when the "
                   "index rises."),
    "Down-Capture": ("Anteil der Indexverluste, den die Strategie in Monaten mit fallendem "
                     "Index mitmacht. Niedriger ist besser.",
                     "Share of index losses the strategy participates in during months "
                     "when the index falls. Lower is better."),
    "Max. Drawdown": ("Größter Rückgang vom bisherigen Höchststand bis zum Tief, auf "
                      "Basis des Vermögensverlaufs.",
                      "Largest decline from a previous peak to the trough, based on the "
                      "wealth path."),
    # Charts und Spalten
    "chart_perf": ("Wert einer Anlage von 1.000 USD. Auf der Log-Skala bedeuten gleiche "
                   "Abstände gleiche prozentuale Veränderungen.",
                   "Value of a $1,000 investment. On the log scale, equal distances mean "
                   "equal percentage changes."),
    "chart_dd": ("Laufender Rückgang vom jeweils letzten Höchststand, Tag für Tag.",
                 "Running decline from the most recent peak, day by day."),
    "chart_alpha": ("Endvermögen SPY3 geteilt durch Endvermögen S&P 500. 3,0x entspricht "
                    "110 Log-Punkten kumulierter Überschussrendite.",
                    "SPY3 wealth divided by S&P 500 wealth. 3.0x corresponds to 110 log "
                    "points of cumulative excess return."),
    "col_gross": ("Nach Handelskosten, vor Management- und Performancegebühr.",
                  "After trading costs, before management and performance fees."),
    "col_net": ("Zusätzlich nach Management- und Performancegebühr in der oben gewählten "
                "Höhe (High-Water-Mark, Hurdle SPY, quartalsweise).",
                "Additionally after the management and performance fee set above "
                "(high-water mark, SPY hurdle, quarterly)."),
    "col_bm": ("SPY Total Return, also inklusive reinvestierter Dividenden.",
               "SPY total return, i.e. including reinvested dividends."),
    "col_mix": ("60 % SPY und 40 % SHY, täglich rebalanciert. Vor 07/2002 T-Bills statt SHY.",
                "60% SPY and 40% SHY, rebalanced daily. T-bills instead of SHY before 07/2002."),
    "excess_log": ("Log-Punkte: 110 Log-Punkte entsprechen dem 3,0-fachen Vermögen "
                   "gegenüber der Benchmark (exp(1,10) = 3,0).",
                   "Log points: 110 log points correspond to 3.0x the benchmark wealth "
                   "(exp(1.10) = 3.0)."),
    "fee_tip": ("Gebühren wirken nur auf die Netto-Reihe; brutto bleibt unverändert. Die "
                "Performancegebühr läuft seit Auflage über High-Water-Mark und SPY-Hurdle "
                "und wird quartalsweise abgerechnet.",
                "Fees affect the net series only; gross is unchanged. The performance fee "
                "runs since inception above the high-water mark and the SPY hurdle and is "
                "crystallised quarterly."),
    "scale_tip": ("Logarithmisch: gleiche Abstände bedeuten gleiche prozentuale "
                  "Veränderungen. Eine Verdopplung von 1.000 auf 2.000 USD sieht so groß aus "
                  "wie eine von 10.000 auf 20.000 USD, dadurch bleiben frühe und späte Jahre "
                  "vergleichbar. Linear: gleiche Abstände bedeuten gleiche Beträge in USD; "
                  "die Kurve zeigt den Zinseszinseffekt, die ersten Jahre werden aber "
                  "flachgedrückt.",
                  "Logarithmic: equal distances mean equal percentage changes. A move from "
                  "$1,000 to $2,000 looks as large as one from $10,000 to $20,000, which "
                  "keeps early and late years comparable. Linear: equal distances mean equal "
                  "dollar amounts; the curve shows the compounding effect, but the early "
                  "years are squeezed flat."),
    "share": ("Anteil dieser Phase an der gesamten Überschussrendite.",
              "Share of this period in the total excess return."),
}


def tip(key: str, lang: str) -> str | None:
    v = TIPS.get(str(key))
    return None if v is None else (v[1] if lang == "en" else v[0])


def t(key: str, lang: str, **kw) -> str:
    de, en = TXT[key]
    s = en if lang == "en" else de
    return s.format(**kw) if kw else s


def term(name, lang: str) -> str:
    n = str(name)
    return EN_TERMS.get(n, n) if lang == "en" else DE_TERMS.get(n, n)
