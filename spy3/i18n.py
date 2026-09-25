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
    "sig_asof": ("Signal zum Handelsschluss am {d}.", "Signal as of the close on {d}."),
    "sig_rule": ("Risk Off durch den Risk-Faktor hat Vorrang. Sonst genügt ein Risk-On-Faktor "
                 "für eine Investition in SPY.",
                 "A Risk Off from the risk factor takes precedence. Otherwise one Risk On "
                 "factor is enough to hold SPY."),
    "f_var": ("1-Tages-VaR (99 %) {v}", "1-day VaR (99%) {v}"),
    "f_mom": ("MA{f} gegenüber MA{s}: {v}", "MA{f} vs. MA{s}: {v}"),
    "f_mr": ("Abstand zum {w}-Tage-Hoch: {v}", "Distance from {w}-day high: {v}"),
    # Hauptchart
    "perf": ("Wert einer Investition von 1.000 USD", "Value of a $1,000 investment"),
    "model_title": ("Inside the SPY3 Model", "Inside the SPY3 Model"),
    # Signal-Karte (Hover)
    "sc_title_on": ("Warum Risk On?", "Why risk on?"),
    "sc_title_off": ("Warum Risk Off?", "Why risk off?"),
    "sc_rule": ("SPY3 hält den S&P 500, solange das Marktrisiko tragbar ist und mindestens ein "
                "Grund für eine Investition vorliegt. Sonst wechselt es in kurzlaufende "
                "US-Staatsanleihen.",
                "SPY3 holds the S&P 500 as long as market risk is acceptable and at least one "
                "reason to invest applies. Otherwise it moves into short-term US Treasuries."),
    "sc_gate": ("Voraussetzung", "Requirement"),
    "sc_any": ("Mindestens ein Grund", "At least one reason"),
    "sc_risk": ("Risikogrenze", "Risk limit"),
    "sc_risk_ok": ("Tagesrisiko {v} – unter der Grenze von {lim}.",
                   "Daily risk {v} – below the {lim} limit."),
    "sc_risk_no": ("Tagesrisiko {v} – über der Grenze von {lim}. Das Modell steigt aus, "
                   "unabhängig von allen anderen Signalen.",
                   "Daily risk {v} – above the {lim} limit. The model stays out, regardless "
                   "of all other signals."),
    "sc_trend": ("Aufwärtstrend", "Uptrend"),
    "sc_trend_yes": ("30-Tage-Schnitt {v} über dem 200-Tage-Schnitt.",
                     "30-day average {v} above the 200-day average."),
    "sc_trend_no": ("30-Tage-Schnitt {v} unter dem 200-Tage-Schnitt.",
                    "30-day average {v} below the 200-day average."),
    "sc_calm": ("Ruhiger Markt", "Calm market"),
    "sc_calm_yes": ("Tagesrisiko {v} unter {lim}.", "Daily risk {v} below {lim}."),
    "sc_calm_no": ("Tagesrisiko {v}, Schwelle {lim}.", "Daily risk {v}, threshold {lim}."),
    "sc_dip": ("Einstiegschance", "Buying opportunity"),
    "sc_dip_yes": ("Kurs {v} unter dem 200-Tage-Hoch, Auslöser ab {lim}.",
                   "Price {v} below its 200-day high, trigger at {lim}."),
    "sc_dip_no": ("Kurs {v} unter dem 200-Tage-Hoch, Auslöser erst ab {lim}.",
                  "Price {v} below its 200-day high, trigger only at {lim}."),
    "sc_res_on": ("Ergebnis: investiert im S&P 500 – Risiko tragbar, {why}.",
                  "Result: invested in the S&P 500 – risk acceptable, {why}."),
    "sc_res_veto": ("Ergebnis: in Staatsanleihen – das Tagesrisiko liegt über der Grenze.",
                    "Result: in Treasuries – daily risk is above the limit."),
    "sc_res_none": ("Ergebnis: in Staatsanleihen – Risiko tragbar, aber kein Grund zu investieren.",
                    "Result: in Treasuries – risk acceptable, but no reason to invest."),
    "sc_why_trend": ("Aufwärtstrend", "uptrend"),
    "sc_why_calm": ("ruhiger Markt", "calm market"),
    "sc_why_dip": ("Einstiegschance nach starkem Rückgang", "buying opportunity after a sharp fall"),
    "sc_and": ("und", "and"),
    "sc_foot": ("Schlusskurs vom {d} · geprüft um {t} Uhr · aktualisiert sich automatisch",
                "Close of {d} · checked at {t} · updates automatically"),
    # Faktorkarten (Hover an den einzelnen Signalen)
    "fc_now": ("Aktuell", "Now"),
    "fc_rule": ("Regel", "Rule"),
    "fc_why": ("Wissenschaftlicher Hintergrund", "Scientific background"),
    "fc_state_on": ("spricht für Risk On", "supports risk on"),
    "fc_state_off": ("erzwingt Risk Off", "forces risk off"),
    "fc_state_neutral": ("neutral", "neutral"),
    "fc_state_mom_off": ("kein Aufwärtstrend", "no uptrend"),
    "fc_risk_title": ("Risk · Value-at-Risk", "Risk · value at risk"),
    "fc_risk_now": ("Tagesrisiko (99-%-VaR, 50 Tage): {v}.", "Daily risk (99% VaR, 50 days): {v}."),
    "fc_risk_rule": ("Über {hi}: Ausstieg, unabhängig von allen anderen Signalen. Unter {lo}: "
                     "ruhiger Markt, Grund zu investieren. Dazwischen entscheiden Trend und "
                     "Mean-Reversion.",
                     "Above {hi}: exit, regardless of all other signals. Below {lo}: calm market, "
                     "a reason to invest. In between, trend and mean reversion decide."),
    "fc_risk_why": ("Volatilität tritt in Clustern auf: Ruhige und turbulente Phasen halten an, "
                    "das Risiko von heute ist deshalb eine gute Prognose für morgen. Aktienquote "
                    "in Hochvolatilitätsphasen zu senken, hat historisch die risikoadjustierte "
                    "Rendite erhöht.",
                    "Volatility clusters: calm and turbulent periods persist, so today's risk is a "
                    "good forecast of tomorrow's. Reducing equity exposure when volatility is high "
                    "has historically raised risk-adjusted returns."),
    "fc_risk_src": ("Engle (1982); Bollerslev (1986); Moreira & Muir (2017), Journal of Finance",
                    "Engle (1982); Bollerslev (1986); Moreira & Muir (2017), Journal of Finance"),
    "fc_mom_title": ("Momentum · Trend", "Momentum · trend"),
    "fc_mom_now": ("30-Tage-Schnitt {v} {dir} dem 200-Tage-Schnitt.",
                   "30-day average {v} {dir} the 200-day average."),
    "fc_above": ("über", "above"), "fc_below": ("unter", "below"),
    "fc_mom_rule": ("Investiert, solange der 30-Tage-Schnitt über dem 200-Tage-Schnitt liegt.",
                    "Invested while the 30-day average is above the 200-day average."),
    "fc_mom_why": ("Trends halten über Monate an: Märkte, die gestiegen sind, steigen tendenziell "
                   "weiter (Time-Series-Momentum). Gleitende Durchschnitte haben das im US-Aktienmarkt "
                   "über lange Zeiträume erfasst. Erklärung: Anleger reagieren verzögert auf neue "
                   "Informationen.",
                   "Trends persist over months: markets that have risen tend to keep rising "
                   "(time-series momentum). Moving-average rules have captured this in US equities "
                   "over long periods. Explanation: investors react to new information with a delay."),
    "fc_mom_src": ("Brock, Lakonishok & LeBaron (1992), Journal of Finance; Moskowitz, Ooi & "
                   "Pedersen (2012), Journal of Financial Economics",
                   "Brock, Lakonishok & LeBaron (1992), Journal of Finance; Moskowitz, Ooi & "
                   "Pedersen (2012), Journal of Financial Economics"),
    "fc_mr_title": ("Mean-Reversion · Einstiegschance", "Mean reversion · buying opportunity"),
    "fc_mr_now": ("Kurs {v} unter dem 200-Tage-Hoch; Auslöser bei {lim}.",
                  "Price {v} below its 200-day high; trigger at {lim}."),
    "fc_mr_rule": ("Investiert nach einem Rückgang von mindestens {lim} gegenüber dem 200-Tage-Hoch.",
                   "Invested after a fall of at least {lim} from the 200-day high."),
    "fc_mr_why": ("Nach extremen Verlusten übertreiben Märkte und erholen sich teilweise wieder. "
                  "Starke Kursrückgänge erhöhen die erwartete Rendite, tiefe Einbrüche sind daher "
                  "historisch gute Einstiegszeitpunkte gewesen.",
                  "After extreme losses markets tend to overshoot and partly recover. Sharp sell-offs "
                  "raise expected returns, so deep drawdowns have historically been good entry points."),
    "fc_mr_src": ("De Bondt & Thaler (1985), Journal of Finance; Poterba & Summers (1988), "
                  "Journal of Financial Economics",
                  "De Bondt & Thaler (1985), Journal of Finance; Poterba & Summers (1988), "
                  "Journal of Financial Economics"),
    "sc_hint": ("Details zu jedem Faktor beim Überfahren der Faktoren rechts.",
                "Hover over the factors on the right for details."),
    # Kernaussage
    "hero_strong": ("Aktienähnliche Rendite bei weniger als halb so tiefen Verlusten.",
                    "Equity-like returns with less than half the drawdown."),
    "hero_lower": ("Geringere Verluste als der S&P 500.", "Lower drawdowns than the S&P 500."),
    "hero_plain": ("SPY3 auf einen Blick.", "SPY3 at a glance."),
    "hero_sub": ("SPY3 nach allen Gebühren gegenüber dem S&P 500, {a} bis {b}.",
                 "SPY3 net of all fees versus the S&P 500, {a} to {b}."),
    "hero_ret": ("Rendite p.a.", "Return p.a."),
    "hero_dd": ("Maximaler Verlust", "Maximum drawdown"),
    "hero_sharpe": ("Sharpe Ratio", "Sharpe ratio"),
    "hero_vs": ("S&P 500: {v}", "S&P 500: {v}"),
    "hint_close": ("Hinweis schließen", "Close hint"),
    # Methodik
    "meth_title": ("Methodik und Annahmen", "Methodology and assumptions"),
    "meth_data": ("Daten", "Data"),
    "meth_data_t": ("Tägliche Schlusskurse von Yahoo Finance, um Dividenden und Splits bereinigt: "
                    "SPY (S&P-500-ETF) und SHY (US-Staatsanleihen mit 1–3 Jahren Laufzeit). "
                    "Vor dem Start des SHY im Juli 2002 dient ein Treasury-Index gleicher "
                    "Laufzeit als Ersatz. Dividenden fließen genau einmal ein.",
                    "Daily closing prices from Yahoo Finance, adjusted for dividends and splits: "
                    "SPY (S&P 500 ETF) and SHY (US Treasuries, 1–3 years). Before SHY launched "
                    "in July 2002, a Treasury index of the same maturity stands in. Dividends "
                    "are included exactly once."),
    "meth_signal": ("Signal", "Signal"),
    "meth_signal_t": ("Täglich aus den Schlusskursen berechnet. Investiert wird, wenn das "
                      "Tagesrisiko (99-%-Value-at-Risk über 50 Tage) unter 5 % liegt und "
                      "mindestens eines gilt: 30-Tage-Schnitt über 200-Tage-Schnitt, "
                      "Tagesrisiko unter 2 % oder Kurs mindestens 23 % unter seinem "
                      "200-Tage-Hoch. Sonst hält das Portfolio SHY.",
                      "Computed daily from closing prices. The model invests when daily risk "
                      "(99% value at risk over 50 days) is below 5% and at least one of the "
                      "following holds: 30-day above 200-day average, daily risk below 2%, or "
                      "price at least 23% below its 200-day high. Otherwise the portfolio holds "
                      "SHY."),
    "meth_costs": ("Kosten und Gebühren", "Costs and fees"),
    "meth_costs_t": ("10 bp Handelskosten je Umschichtung. Die Netto-Reihe zieht zusätzlich "
                     "0,2 % Managementgebühr p.a. und 10 % Performancegebühr auf die "
                     "Überrendite gegenüber dem SPY ab, mit High-Water-Mark und "
                     "quartalsweiser Abrechnung.",
                     "10 bp trading costs per switch. The net series additionally deducts a "
                     "0.2% p.a. management fee and a 10% performance fee on returns above SPY, "
                     "with a high-water mark and quarterly crystallisation."),
    "meth_metrics": ("Kennzahlen", "Metrics"),
    "meth_metrics_t": ("Renditen geometrisch verkettet. Sharpe Ratio = CAGR ÷ Volatilität "
                       "ohne risikofreien Satz. Drawdown aus dem Vermögensverlauf. Beta und "
                       "Jensen's Alpha gegenüber SHY als risikofreier Anlage.",
                       "Returns compounded geometrically. Sharpe ratio = CAGR ÷ volatility "
                       "without a risk-free rate. Drawdown from the wealth path. Beta and "
                       "Jensen's alpha measured against SHY as the risk-free asset."),
    "meth_robust": ("Robustheit", "Robustness"),
    "meth_robust_t": ("Zum Vergleich: Wird der Wechsel zwischen SPY und SHY zufällig "
                      "gesetzt, bei gleicher Investitionsquote, liegt die Sharpe Ratio im "
                      "Median bei 0,3. Das Ergebnis des Modells ist damit kein Zufall "
                      "(p < 0,001).",
                       "For comparison: if the switches between SPY and SHY are placed at "
                      "random, at the same investment ratio, the median Sharpe ratio is 0.3. "
                      "The model's result is therefore not down to chance (p < 0.001)."),
    "meth_note": ("Bis August 2023 simulierte Wertentwicklung, danach Live-Betrieb. Vergangene "
                  "oder simulierte Ergebnisse sind kein verlässlicher Indikator für die Zukunft.",
                  "Simulated performance up to August 2023, live operation thereafter. Past or "
                  "simulated results are not a reliable indicator of future results."),
    "model_note": ("SPY-Kurs mit den drei Faktoren. Momentum: 30-Tage-Linie über 200-Tage-Linie. "
                   "Mean-Reversion: Kurs unter der gepunkteten Linie (23 % unter dem 200-Tage-Hoch). "
                   "Risk: 1-Tages-VaR über 5 % erzwingt Risk-Off, unter 2 % erlaubt immer Risk-On.",
                   "SPY price with the three factors. Momentum: 30-day above 200-day average. "
                   "Mean reversion: price below the dotted line (23% under the 200-day high). "
                   "Risk: 1-day VaR above 5% forces risk-off, below 2% always allows risk-on."),
    "m_price": ("SPY (Total Return)", "SPY (total return)"),
    "m_fast": ("30d MA", "30d MA"),
    "m_slow": ("200d MA", "200d MA"),
    "m_mr": ("Mean-Reversion-Schwelle", "Mean-reversion trigger"),
    "m_var": ("1-Tages-VaR 99 % (rechts)", "1-day VaR 99% (right)"),
    "m_var_high": ("Risk-Off-Schwelle 5 %", "Risk-off threshold 5%"),
    "m_var_low": ("Low-Vol-Schwelle 2 %", "Low-vol threshold 2%"),
    "roll_side_title": ("Rollierend, 3 Jahre", "Rolling, 3 years"),
    "roll_side_note": ("SPY3 netto (grün) gegen S&P 500 (grau).",
                       "SPY3 net (green) versus S&P 500 (grey)."),
    "rs_sharpe": ("Sharpe Ratio", "Sharpe ratio"),
    "rs_calmar": ("Calmar Ratio", "Calmar ratio"),
    "rs_vol": ("Volatilität p.a.", "Volatility p.a."),
    "perf_note": ("Rot hinterlegt: Strategie hält kurzlaufende US-T-Bills",
                  "Red shading: strategy holds short-term US T-Bills"),
    "tsy_label": ("SHY ETF", "SHY ETF"),
    "tsy_note_splice": ("Risk-Off-Bein und SHY-Spalte: bis {d} {x}, danach der SHY ETF selbst.",
                        "Risk-off leg and SHY column: {x} up to {d}, the SHY ETF itself "
                        "thereafter."),
    "tsy_note_none": ("Risk-Off-Bein vor 07/2002: 0 % (keine Treasury- und keine T-Bill-Daten).",
                      "Risk-off leg before 07/2002: 0% (no Treasury and no T-bill data)."),
    "col_tsy": ("SHY ETF (US-Staatsanleihen 1–3 Jahre), das Risk-Off-Instrument der "
                "Strategie. Vor 07/2002 Bloomberg US Treasury Index.",
                "SHY ETF (US Treasuries 1–3 years), the strategy's risk-off instrument. "
                "Bloomberg US Treasury index before 07/2002."),
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
    "kpi_note": ("60/40: 60 % SPY und 40 % SHY, monatlich rebalanciert. Sharpe Ratio ohne "
                 "risikofreien Satz (rf = 0 %), Beta und Alpha über kurzlaufende "
                 "Staatsanleihen.",
                 "60/40: 60% SPY and 40% SHY, rebalanced monthly. Sharpe ratio without a "
                 "risk-free rate (rf = 0%), beta and alpha against short-term Treasuries."),
    "col_gross": ("SPY3 brutto", "SPY3 gross"),
    "col_net": ("SPY3 netto", "SPY3 net"),
    # Tabs
    "t_dd": ("Drawdown", "Drawdown"),
    "t_gap": ("Abstand zum Markt", "Gap to market"),
    "t_roll": ("Rollierende Performance", "Rolling performance"),
    "t_ex": ("Ohne Krisen", "Excluding crises"),
    "t_years": ("Kalenderjahre", "Calendar years"),
    "t_timing": ("Timing-Test", "Timing test"),
    "t_risk": ("Risiko", "Risk"),
    "mc_x": ("Handelstage", "Trading days"),
    "stress_title": ("Stresstests", "Stress tests"),
    "stress_note": ("Wertentwicklung in historischen Stressfenstern. MaxDD ist der tiefste "
                    "Rückgang von SPY3 netto innerhalb des Fensters.",
                    "Performance in historical stress windows. MaxDD is the deepest decline "
                    "of SPY3 net within the window."),
    "var_title": ("Value-at-Risk", "Value at risk"),
    "var_note": ("Historischer VaR und CVaR (Expected Shortfall) auf Tagesbasis, als Verlust "
                 "angegeben. CVaR ist der Mittelwert jenseits der VaR-Schwelle.",
                 "Historical VaR and CVaR (expected shortfall) on a daily basis, stated as a "
                 "loss. CVaR is the average beyond the VaR threshold."),
    "var_hist_title": ("Verteilung der Tagesrenditen", "Distribution of daily returns"),
    "var_hist_note": ("SPY3 netto, mit den VaR-Schwellen.",
                      "SPY3 net, with the VaR thresholds."),
    "var_bt_title": ("VaR-Backtest (Kupiec)", "VaR backtest (Kupiec)"),
    "var_bt_note": ("Wie oft überschritt der Tagesverlust den rollierenden 99-%-VaR über 250 "
                    "Tage? Erwartet wird 1 % der Tage. Ein LR-Wert über 3,84 verwirft das "
                    "Modell auf dem 5-%-Niveau.",
                    "How often did the daily loss exceed the rolling 99% VaR over 250 days? "
                    "1% of days is expected. An LR value above 3.84 rejects the model at the "
                    "5% level."),
    "mc_title": ("Monte-Carlo, 1 Jahr", "Monte Carlo, 1 year"),
    "mc_note": ("2.000 Pfade über 252 Handelstage, Block-Bootstrap mit 20-Tage-Blöcken; "
                "Autokorrelation und Volatilitätscluster bleiben erhalten. Flächen: 5–95 % "
                "und 25–75 % der Pfade.",
                "2,000 paths over 252 trading days, block bootstrap with 20-day blocks, "
                "preserving autocorrelation and volatility clustering. Shaded: 5–95% and "
                "25–75% of paths."),
    "corr_title": ("Korrelationen zu Indizes und Anlageklassen",
                   "Correlations with indices and asset classes"),
    "corr_note": ("Monatsrenditen über den gewählten Zeitraum.",
                  "Monthly returns over the selected period."),
    "corr_missing": ("Für weitere Anlageklassen fehlen die Kursdaten. Einmalig laden mit: "
                     "python -c \"from spy3.data import load_assets; load_assets(refresh=True)\"",
                     "Price data for the additional asset classes is missing. Load it once "
                     "with: python -c \"from spy3.data import load_assets; "
                     "load_assets(refresh=True)\""),
    "beta_title": ("Beta und Korrelation je Anlageklasse",
                   "Beta and correlation by asset class"),
    "beta_note": ("SPY3 netto gegenüber der jeweiligen Anlageklasse, Tagesrenditen.",
                  "SPY3 net against each asset class, daily returns."),
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
    "Schlechtester Tag": "Worst day", "Schlechtester Monat": "Worst month",
    "Flash Crash 2010": "Flash crash 2010", "Taper Tantrum 2013": "Taper tantrum 2013",
    "China-Schock 2015": "China shock 2015", "Volmageddon 2018": "Volmageddon 2018",
    "Q4 2018": "Q4 2018", "MaxDD": "Max. DD",
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
    "col_mix": ("60 % SPY und 40 % SHY, zum Monatsende auf die Zielquote zurückgesetzt. "
                "Vor 07/2002 Bloomberg US Treasury Index statt SHY.",
                "60% SPY and 40% SHY, reset to target weights at each month end. Bloomberg "
                "US Treasury index instead of SHY before 07/2002."),
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
