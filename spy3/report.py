"""Export: PDF-Report mit SINTRO-Logo und Excel-Mappe mit den Rohdaten.

Charts werden mit matplotlib gezeichnet (kein Browser nötig), das PDF mit reportlab
gesetzt. Beides läuft serverseitig, der Download liefert reine Bytes.

matplotlib, reportlab und XlsxWriter werden erst beim Export importiert. Fehlt eines
davon, bleibt das übrige Dashboard lauffähig; `missing_packages()` sagt, was fehlt.
"""
from __future__ import annotations

import importlib.util
import io
from datetime import date
from pathlib import Path

import pandas as pd

from . import metrics as m, robustness as rb
from .formatting import by_metric, pct
from .i18n import t, term

REQUIRED = {"matplotlib": "matplotlib", "reportlab": "reportlab", "xlsxwriter": "XlsxWriter"}
FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"


def _pdf_fonts() -> tuple[str, str]:
    """Registriert Garet für das PDF, wenn die TTF-Dateien vorliegen; sonst Helvetica."""
    reg, bold = FONT_DIR / "Garet-Regular.ttf", FONT_DIR / "Garet-Bold.ttf"
    if not (reg.exists() and bold.exists()):
        return "Helvetica", "Helvetica-Bold"
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        if "Garet" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("Garet", str(reg)))
            pdfmetrics.registerFont(TTFont("Garet-Bold", str(bold)))
        return "Garet", "Garet-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


def missing_packages() -> list[str]:
    """Namen der fehlenden Pakete (leer, wenn alles da ist)."""
    return [pip for mod, pip in REQUIRED.items() if importlib.util.find_spec(mod) is None]


def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    ttf = FONT_DIR / "Garet-Regular.ttf"
    if ttf.exists():
        try:
            from matplotlib import font_manager
            font_manager.fontManager.addfont(str(ttf))
            matplotlib.rcParams["font.family"] = "Garet"
        except Exception:
            pass
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    return matplotlib, mdates, plt


LOGO = Path(__file__).resolve().parent.parent / "assets" / "sintro-logo.png"
NAVY = "#003274"
NET = "#1F6B45"
SLATE = "#8C96A5"
MIX = "#B38B4D"
INK = "#1B2638"
MUTED = "#5E6B7D"
LINE = "#E4E8EE"
RISK_OFF = "#CE3E34"
START = 1_000

TXT = {
    "title": ("SPY3 – Backtest-Report", "SPY3 – Backtest report"),
    "sub": ("Zeitraum {start} bis {end} · Total Return in USD · Handelskosten {cost} bp je "
            "Umschichtung · Gebühren {mgmt} p.a. und {perf} Performancegebühr",
            "Period {start} to {end} · total return in USD · trading costs {cost} bp per "
            "switch · fees {mgmt} p.a. and {perf} performance fee"),
    "kpis": ("Kennzahlen", "Key figures"),
    "wealth": ("Wert einer Anlage von 1.000 USD (log. Skala)",
               "Value of a $1,000 investment (log scale)"),
    "dd": ("Drawdown", "Drawdown"),
    "alpha": ("Vorsprung gegenüber dem S&P 500 (Vielfaches)",
              "Lead over the S&P 500 (multiple)"),
    "years": ("Kalenderjahre", "Calendar years"),
    "attr": ("Beitrag der Krisenphasen (Log-Punkte)",
             "Contribution of crisis periods (log points)"),
    "gross": ("SPY3 vor Gebühren", "SPY3 before fees"),
    "net": ("SPY3 nach Gebühren", "SPY3 after fees"),
    "riskoff": ("Risk-Off-Phasen rot hinterlegt", "Risk-off phases shaded red"),
    "disc": ("Simulierte Wertentwicklung. Vergangene oder simulierte Ergebnisse sind kein "
             "verlässlicher Indikator für künftige Ergebnisse. Kein Angebot und keine "
             "Anlageberatung.",
             "Simulated performance. Past or simulated results are not a reliable indicator "
             "of future results. This is not an offer and not investment advice."),
    "created": ("Erstellt am {d}", "Created on {d}"),
    "year": ("Jahr", "Year"), "diff": ("Differenz", "Difference"),
}


def _t(key: str, lang: str, **kw) -> str:
    de, en = TXT[key]
    s = en if lang == "en" else de
    return s.format(**kw) if kw else s


# ---------- Charts ----------------------------------------------------------
def _style(ax):
    _, mdates, _ = _mpl()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(LINE)
    ax.tick_params(colors=MUTED, labelsize=8, length=3, color=LINE)
    ax.grid(axis="y", color=LINE, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def _risk_off(ax, position: pd.Series):
    off = position.eq(0)
    grp = (off != off.shift()).cumsum()
    for _, seg in position[off].groupby(grp[off]):
        ax.axvspan(seg.index[0], seg.index[-1], color=RISK_OFF, alpha=0.12, lw=0)


def _png(fig) -> io.BytesIO:
    _, _, plt = _mpl()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf


def wealth_png(bt: pd.DataFrame, mixes: dict[str, pd.Series], lang: str) -> io.BytesIO:
    matplotlib, _, plt = _mpl()
    fig, ax = plt.subplots(figsize=(7.4, 3.5))
    _risk_off(ax, bt.position)
    ax.plot(bt.index, START * (1 + bt.ret_bm).cumprod(), color=SLATE, lw=1.1, label="S&P 500")
    for name, s in mixes.items():
        ax.plot(s.index, START * (1 + s).cumprod(), color=MIX, lw=1.0, ls=":", label=name)
    ax.plot(bt.index, START * (1 + bt.ret_pf).cumprod(), color=NAVY, lw=1.0,
            label=_t("gross", lang))
    ax.plot(bt.index, START * (1 + bt.ret_pf_net).cumprod(), color=NET, lw=1.6,
            label=_t("net", lang))
    ax.set_yscale("log")
    lo = min((1 + bt.ret_bm).cumprod().min(), (1 + bt.ret_pf).cumprod().min()) * START
    hi = max((1 + bt.ret_pf).cumprod().max(), (1 + bt.ret_bm).cumprod().max()) * START
    ticks = [v for v in (250, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000)
             if lo * 0.7 <= v <= hi * 1.4]
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{v:,.0f}".replace(",", "." if lang == "de" else ",") for v in ticks])
    ax.minorticks_off()
    _style(ax)
    ax.legend(frameon=False, fontsize=8, ncol=4, loc="upper left", labelcolor=MUTED)
    return _png(fig)


def drawdown_png(bt: pd.DataFrame, lang: str) -> io.BytesIO:
    matplotlib, _, plt = _mpl()
    fig, ax = plt.subplots(figsize=(7.4, 2.1))
    _risk_off(ax, bt.position)
    ax.fill_between(bt.index, m.drawdown(bt.ret_bm), 0, color=SLATE, alpha=0.25, lw=0)
    ax.plot(bt.index, m.drawdown(bt.ret_bm), color=SLATE, lw=0.8, label="S&P 500")
    ax.plot(bt.index, m.drawdown(bt.ret_pf_net), color=NET, lw=1.2, label=_t("net", lang))
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    _style(ax)
    ax.legend(frameon=False, fontsize=8, ncol=2, loc="lower left", labelcolor=MUTED)
    return _png(fig)


def alpha_png(bt: pd.DataFrame, lang: str) -> io.BytesIO:
    matplotlib, _, plt = _mpl()
    fig, ax = plt.subplots(figsize=(7.4, 2.1))
    wb = (1 + bt.ret_bm).cumprod()
    ax.axhline(1, color=INK, lw=0.8)
    ax.plot(bt.index, (1 + bt.ret_pf).cumprod() / wb, color=NAVY, lw=0.9,
            label=_t("gross", lang))
    ax.plot(bt.index, (1 + bt.ret_pf_net).cumprod() / wb, color=NET, lw=1.4,
            label=_t("net", lang))
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.1f}x"))
    _style(ax)
    ax.legend(frameon=False, fontsize=8, ncol=2, loc="upper left", labelcolor=MUTED)
    return _png(fig)


# ---------- PDF -------------------------------------------------------------
def _table(data, lang, col_widths, highlight_rows=()):
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    base, bold = _pdf_fonts()
    style = [
        ("FONTNAME", (0, 0), (-1, -1), base),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("FONTNAME", (0, 0), (-1, 0), bold),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(MUTED)),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor(LINE)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FC")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]
    for r in highlight_rows:
        style += [("TEXTCOLOR", (0, r), (-1, r), colors.HexColor(NAVY)),
                  ("FONTNAME", (0, r), (-1, r), bold)]
    tbl = Table(data, colWidths=col_widths, hAlign="LEFT")
    tbl.setStyle(TableStyle(style))
    return tbl


def build_pdf(bt: pd.DataFrame, mixes: dict[str, pd.Series], lang: str = "en",
              cost_bps: float = 10.0, mgmt: float = 0.002, perf: float = 0.10) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                    SimpleDocTemplate, Spacer)

    missing = missing_packages()
    if missing:
        raise ModuleNotFoundError("Fehlende Pakete für den Export: " + ", ".join(missing))
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=16 * mm, bottomMargin=16 * mm,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            title=_t("title", lang), author="SINTRO Asset Management")
    base, bold = _pdf_fonts()
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], fontName=base, fontSize=17,
                        textColor=colors.HexColor(INK), alignment=0, spaceAfter=2)
    sub = ParagraphStyle("sub", parent=ss["Normal"], fontName=base, fontSize=9,
                         textColor=colors.HexColor(MUTED), leading=12)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName=bold, fontSize=11.5,
                        textColor=colors.HexColor(INK), spaceBefore=10, spaceAfter=4)
    small = ParagraphStyle("small", parent=sub, fontSize=7.5)

    story = []
    if LOGO.exists():
        logo = Image(str(LOGO), width=42 * mm, height=42 * mm * 451 / 1563)
        logo.hAlign = "LEFT"
        story.append(logo)
        story.append(Spacer(1, 6))
    story.append(Paragraph(_t("title", lang), h1))
    story.append(Paragraph(_t("sub", lang, start=f"{bt.index[0]:%m/%Y}",
                              end=f"{bt.index[-1]:%m/%Y}", cost=f"{cost_bps:.0f}",
                              mgmt=pct(mgmt, 1, lang=lang), perf=pct(perf, 0, lang=lang)), sub))
    story.append(Spacer(1, 10))

    cols = {_t("gross", lang): bt.ret_pf, _t("net", lang): bt.ret_pf_net,
            "S&P 500": bt.ret_bm, **mixes}
    kpi = m.summary_table(cols, bt.ret_bm, bt.ret_off)
    order = ["Total Return", "CAGR", "Volatilität p.a.", "Sharpe Ratio", "Calmar", "Beta",
             "Jensen's Alpha p.a.", "Up-Capture", "Down-Capture", "Max. Drawdown"]
    kpi = kpi.loc[order]
    esc = lambda x: str(x).replace("&", "&amp;")
    data = [[""] + [Paragraph(f"<b>{esc(c)}</b>", small) for c in kpi.columns]]
    for idx, row in kpi.iterrows():
        data.append([term(idx, lang)] + [by_metric(idx, v, lang) for v in row])
    hl = [order.index("Sharpe Ratio") + 1, order.index("Max. Drawdown") + 1]
    story.append(Paragraph(_t("kpis", lang), h2))
    story.append(_table(data, lang, [52 * mm] + [24 * mm] * len(kpi.columns), hl))

    story.append(Paragraph(_t("wealth", lang), h2))
    story.append(Image(wealth_png(bt, mixes, lang), width=170 * mm, height=80 * mm))
    story.append(Paragraph(_t("riskoff", lang), small))

    story.append(PageBreak())
    story.append(Paragraph(_t("dd", lang), h2))
    story.append(Image(drawdown_png(bt, lang), width=170 * mm, height=48 * mm))
    story.append(Paragraph(_t("alpha", lang), h2))
    story.append(Image(alpha_png(bt, lang), width=170 * mm, height=48 * mm))

    att = rb.attribution(bt.ret_pf, bt.ret_bm)
    adata = [["", "Log", "%"]]
    for idx, row in att.iterrows():
        adata.append([term(idx, lang), pct(row.iloc[0], lang=lang),
                      pct(row.iloc[1], lang=lang)])
    y = rb.yearly_excess(bt.ret_pf, bt.ret_bm).sort_index(ascending=False)
    ydata = [[_t("year", lang), "SPY3", "S&P 500", _t("diff", lang)]]
    for idx, row in y.iterrows():
        ydata.append([str(idx), pct(row.iloc[0], lang=lang), pct(row.iloc[1], lang=lang),
                      pct(row.iloc[2], signed=True, lang=lang)])
    story.append(KeepTogether([Paragraph(_t("attr", lang), h2),
                               _table(adata, lang, [52 * mm, 26 * mm, 26 * mm])]))
    story.append(PageBreak())
    story.append(Paragraph(_t("years", lang), h2))
    story.append(_table(ydata, lang, [26 * mm, 28 * mm, 28 * mm, 28 * mm]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(_t("disc", lang), small))
    story.append(Paragraph(_t("created", lang, d=date.today().strftime("%d.%m.%Y")), small))

    def footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont(base, 7.5)
        canvas.setFillColor(colors.HexColor(MUTED))
        canvas.drawString(18 * mm, 10 * mm, "SINTRO Asset Management GmbH · www.sintro.eu")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"{doc_.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()


# ---------- Excel -----------------------------------------------------------
def build_xlsx(bt: pd.DataFrame, mixes: dict[str, pd.Series], lang: str = "en") -> bytes:
    daily = pd.DataFrame({
        "date": bt.index, "signal": bt.signal.values, "position": bt.position.values,
        "risk_off_source": (bt["risk_off_source"].values if "risk_off_source" in bt
                            else "n/a"),
        "var_1d_99": bt.var_1d.values, "ret_spy": bt.ret_bm.values,
        "ret_risk_off": bt.ret_off.values, "ret_spy3_gross": bt.ret_pf.values,
        "ret_spy3_net": bt.ret_pf_net.values, "cost": bt.cost.values,
        "perf_fee_paid": bt.perf_fee_paid.values,
        "wealth_spy3_gross": START * (1 + bt.ret_pf).cumprod().values,
        "wealth_spy3_net": START * (1 + bt.ret_pf_net).cumprod().values,
        "wealth_spy": START * (1 + bt.ret_bm).cumprod().values,
        "drawdown_spy3_net": m.drawdown(bt.ret_pf_net).values,
        "drawdown_spy": m.drawdown(bt.ret_bm).values,
    })
    for name, s in mixes.items():
        daily[f"ret_{name.replace('/', '_')}"] = s.values
    cols = {"SPY3 gross": bt.ret_pf, "SPY3 net": bt.ret_pf_net, "S&P 500": bt.ret_bm, **mixes}
    kpi = m.summary_table(cols, bt.ret_bm, bt.ret_off)
    yearly = rb.yearly_excess(bt.ret_pf, bt.ret_bm)
    yearly.columns = ["SPY3 gross", "S&P 500", "difference"]
    att = rb.attribution(bt.ret_pf, bt.ret_bm)
    att.columns = ["excess_log", "share"]
    notes = pd.DataFrame({"note": [
        "All returns are simple (geometric) daily returns, not log returns.",
        "wealth_* columns: value of an initial 1,000 USD investment.",
        "ret_spy3_gross: after trading costs. ret_spy3_net: additionally after management "
        "and performance fee (high-water mark, SPY hurdle, quarterly).",
        "Before 30/07/2002 the risk-off leg uses the Bloomberg US Treasury Total Return "
        "Index (LUATTRUU) instead of SHY; 13-week T-bills only if that file is missing.",
        "Source: SINTRO SPY3 backtest dashboard.",
    ]})
    missing = missing_packages()
    if "XlsxWriter" in missing:
        raise ModuleNotFoundError("Fehlende Pakete für den Export: XlsxWriter")
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter", datetime_format="yyyy-mm-dd") as xl:
        kpi.to_excel(xl, sheet_name="KPIs")
        daily.to_excel(xl, sheet_name="Daily data", index=False)
        yearly.to_excel(xl, sheet_name="Calendar years")
        att.to_excel(xl, sheet_name="Attribution")
        notes.to_excel(xl, sheet_name="Notes", index=False)
        book = xl.book
        pctf = book.add_format({"num_format": "0.00%"})
        numf = book.add_format({"num_format": "#,##0.00"})
        xl.sheets["Daily data"].set_column("A:A", 12)
        xl.sheets["Daily data"].set_column("B:C", 9)
        xl.sheets["Daily data"].set_column("D:J", 13, pctf)
        xl.sheets["Daily data"].set_column("K:M", 14, numf)
        xl.sheets["Daily data"].set_column("N:R", 13, pctf)
        xl.sheets["KPIs"].set_column("A:A", 24)
        xl.sheets["Notes"].set_column("A:A", 110)
    return buf.getvalue()
