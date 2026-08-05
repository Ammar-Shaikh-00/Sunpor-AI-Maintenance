"""Short client status brief PDF — SUNPOR architecture, progress, data needs."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = Path(r"c:\Users\Ammar Shaikh\Desktop\SUNPOR_Client_Status_Brief.pdf")
OUT_DOCS = Path(r"c:\Users\Ammar Shaikh\Desktop\Sunpor\Docs\SUNPOR_Client_Status_Brief.pdf")


def P(text: str, style) -> Paragraph:
    return Paragraph(text, style)


def main() -> None:
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title="SUNPOR Client Status Brief",
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "T",
        parent=styles["Heading1"],
        fontSize=13,
        alignment=TA_CENTER,
        spaceAfter=4,
        textColor=colors.HexColor("#0f172a"),
    )
    sub = ParagraphStyle(
        "S",
        parent=styles["Normal"],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569"),
        spaceAfter=8,
    )
    h2 = ParagraphStyle(
        "H",
        parent=styles["Heading2"],
        fontSize=10.5,
        spaceBefore=9,
        spaceAfter=4,
        textColor=colors.HexColor("#1e3a5f"),
    )
    body = ParagraphStyle(
        "B",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        alignment=TA_JUSTIFY,
        spaceAfter=4,
    )
    bullet = ParagraphStyle(
        "Bu",
        parent=body,
        leftIndent=10,
        spaceAfter=2,
    )
    cell = ParagraphStyle(
        "C",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
    )
    mono = ParagraphStyle(
        "M",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=10,
        fontName="Courier",
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
        leftIndent=6,
    )

    story = []
    story.append(P("SUNPOR — Status Brief", title))
    story.append(P("Architecture · Progress · Data · Prediction Timeline", sub))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=8))

    # 1 Architecture
    story.append(P("1. How data enters the ML models", h2))
    story.append(
        P(
            "Live WinCC signals and operator forms feed one pipeline:",
            body,
        )
    )
    story.append(
        P(
            "WinCC (104 signals, Line E10)<br/>"
            "→ Ingestion (~10s) → Cleaner → Rolling buffer → Feature engine (1/5/15/30 min)<br/>"
            "→ Process State · Early Anomaly · Low-Production detail → Stored predictions<br/>"
            "→ Operator forms + Daily Quality / Material Blocking → Learning over time",
            mono,
        )
    )
    story.append(
        P(
            "<b>Automatic data</b> = machine behavior. <b>Operator forms</b> = human labels "
            "(events, observations, quality). Linked by production run.",
            body,
        )
    )

    # 2 Done / Missing
    story.append(P("2. Completed vs missing", h2))
    rows = [
        [P("<b>Completed</b>", cell), P("<b>Still missing</b>", cell)],
        [
            P(
                "• Live ingestion + cleaning + features<br/>"
                "• Process State (Stable production confirmed on E10)<br/>"
                "• Early Anomaly Detection (Stages 0–2)<br/>"
                "• Low-Production cause &amp; severity<br/>"
                "• Prediction storage + tests<br/>"
                "• Requirements Document (EN/DE)",
                cell,
            ),
            P(
                "• Client confirmation of other 8 phases<br/>"
                "• Consistent operator logging (knife, screen, nozzle, low production, quality)<br/>"
                "• Doser vibration / feed-in times (if available)<br/>"
                "• Enough labeled runs with later lab/quality outcomes<br/>"
                "• Material / Granulator / Nozzle risk models<br/>"
                "• Predictive Quality ML (needs delayed quality data)",
                cell,
            ),
        ],
    ]
    t = Table(rows, colWidths=[8.3 * cm, 8.3 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t)

    # 3 Data so far
    story.append(P("3. Data collected so far — what we see", h2))
    story.append(
        P(
            "<b>We collect:</b> continuous Line E10 signals, features, and live predictions "
            "(process state, anomaly scores, low-production detail).",
            body,
        )
    )
    story.append(
        P(
            "<b>We see:</b> stable production is detected reliably during normal runs; "
            "anomaly safety advisories can fire (e.g. process-water pressure); pipeline writes predictions live.",
            body,
        )
    )
    story.append(
        P(
            "<b>We do not yet have enough:</b> operator-confirmed non-stable phases, "
            "maintenance events (knife/screen/nozzle), planned vs unplanned low production, "
            "and daily quality / blocking linked to runs. "
            "There was no historical dataset — learning starts from live capture.",
            body,
        )
    )

    # 4 Timeline
    story.append(P("4. When predictions become accurate", h2))
    rows2 = [
        [P("<b>When</b>", cell), P("<b>What becomes reliable</b>", cell), P("<b>Needs</b>", cell)],
        [
            P("Now", cell),
            P("Stable production; basic anomaly safety thresholds", cell),
            P("Live signals (available)", cell),
        ],
        [
            P("~2–4 weeks*", cell),
            P("Better Process State for other phases; useful low-production causes", cell),
            P("Phase examples + Low Production events", cell),
        ],
        [
            P("~1–2 months*", cell),
            P("Stronger early warnings; knife/screen/nozzle hints", cell),
            P("Maintenance + material behavior labels", cell),
        ],
        [
            P("~2–3+ months*", cell),
            P("First useful Predictive Quality during production", cell),
            P("Daily quality + blocking linked to runs", cell),
        ],
    ]
    t2 = Table(rows2, colWidths=[2.8 * cm, 7.5 * cm, 6.3 * cm])
    t2.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    story.append(t2)
    story.append(
        P(
            "*Depends on how consistently operators log events and how often phases / maintenance / quality outcomes occur.",
            bullet,
        )
    )

    # 5 Data amounts
    story.append(P("5. Data we need — type and amount (minimum to start)", h2))
    rows3 = [
        [P("<b>Data</b>", cell), P("<b>Minimum</b>", cell), P("<b>Better</b>", cell)],
        [P("Each process phase (confirmed examples)", cell), P("5 per phase", cell), P("15+", cell)],
        [P("Low Production (with cause / planned–unplanned)", cell), P("10", cell), P("30+", cell)],
        [P("Knife / blade change or grinding", cell), P("10", cell), P("20–30", cell)],
        [P("Screen change", cell), P("10", cell), P("20–30", cell)],
        [P("Nozzle change / flush / grind", cell), P("10", cell), P("20–30", cell)],
        [P("Material behavior observations", cell), P("15", cell), P("40+", cell)],
        [P("Daily quality (per shift / run)", cell), P("20–30", cell), P("ongoing", cell)],
        [P("Material blocking", cell), P("all cases", cell), P("all cases", cell)],
    ]
    t3 = Table(rows3, colWidths=[8.5 * cm, 4 * cm, 4.1 * cm])
    t3.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    story.append(t3)
    story.append(Spacer(1, 4))
    story.append(
        P(
            "<b>Example:</b> ~10 knife/blade change entries is enough to start learning wear patterns; "
            "20–30 makes it clearly more useful. Also needed: Material Production Status meaning, "
            "feeder mode meanings, and low-production / ΔP thresholds.",
            body,
        )
    )

    # Bottom line
    story.append(P("6. Bottom line", h2))
    for item in [
        "Architecture is live: signals → features → Process State / Anomaly / Low-Production → predictions.",
        "Stable production works today; broader accuracy needs labeled operator and quality data.",
        "Ask: consistent logging — e.g. ~10 knife changes, ~10 screen changes, ~10 low-production events, phase examples, and daily quality each shift.",
    ]:
        story.append(P(f"• {item}", bullet))

    doc.build(story)
    OUT_DOCS.write_bytes(OUT.read_bytes())
    print(f"wrote: {OUT}")
    print(f"wrote: {OUT_DOCS}")


if __name__ == "__main__":
    main()
