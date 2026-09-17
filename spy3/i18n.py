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
    "log": ("Logarithmisch", "Logarithmic"),
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
    "perf_note": ("Rot hinterlegt: Strategie hält kurzlaufende US-Staatsanleihen",
                  "Red shading: strategy holds short-term US Treasuries"),
    "gross": ("SPY3 vor Gebühren", "SPY3 before fees"),
    "net": ("SPY3 nach Gebühren", "SPY3 after fees"),
    "riskoff": ("Risk-Off", "Risk off"),
    "fees_note": ("Gebühren: 0,2 % Managementgebühr p.a. und 10 % Performancegebühr über "
                  "High-Water-Mark und SPY-Hurdle, quartalsweise abgerechnet.",
                  "Fees: 0.2% p.a. management fee and 10% performance fee above the "
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
    "alpha_title": ("Alpha gegenüber S&P 500", "Alpha versus the S&P 500"),
    "alpha_note": ("Kumulierte Überschussrendite (log). Steigt die Linie, liegt die Strategie "
                   "vor dem S&P 500.",
                   "Cumulative excess return (log). A rising line means the strategy is "
                   "ahead of the S&P 500."),
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


def t(key: str, lang: str, **kw) -> str:
    de, en = TXT[key]
    s = en if lang == "en" else de
    return s.format(**kw) if kw else s


def term(name, lang: str) -> str:
    n = str(name)
    return EN_TERMS.get(n, n) if lang == "en" else DE_TERMS.get(n, n)
