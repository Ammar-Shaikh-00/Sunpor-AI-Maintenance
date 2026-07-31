"""Build PDF of the operator-forms AI logic email reply."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    ListFlowable,
    ListItem,
)

OUT = Path(r"C:\Users\Ammar Shaikh\Desktop\Sunpor\Docs\SUNPOR_Operator_Forms_AI_Logic_Reply.pdf")


def P(text: str, style) -> Paragraph:
    return Paragraph(text.replace("\n", "<br/>"), style)


def main() -> None:
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title="SUNPOR Operator Forms — AI Logic Reply",
        author="SCLERA / Ammar",
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitleCustom",
        parent=styles["Heading1"],
        fontSize=14,
        spaceAfter=8,
        textColor=colors.HexColor("#1a365d"),
    )
    h2 = ParagraphStyle(
        "H2Custom",
        parent=styles["Heading2"],
        fontSize=11,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.HexColor("#1a365d"),
    )
    body = ParagraphStyle(
        "BodyCustom",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    bullet = ParagraphStyle(
        "BulletCustom",
        parent=body,
        leftIndent=10,
        spaceAfter=3,
    )
    meta = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#333333"),
        spaceAfter=3,
    )
    cell = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
    )

    story = []
    story.append(P("SUNPOR — Operator Forms &amp; AI Logic", title))
    story.append(P("<b>Reply regarding the original operator forms and future AI predictions</b>", meta))
    story.append(Spacer(1, 8))

    story.append(
        P(
            "Thank you for the detailed review and for redesigning the forms. "
            "Your goal is exactly right: we need structured operator knowledge that we can later "
            "correlate with process data and quality results.",
            body,
        )
    )
    story.append(
        P(
            "Below is the logic behind the <b>original forms</b>, how they connect to AI predictions, "
            "and how we see the full workflow. We also comment on how your redesigned categories "
            "fit with that approach.",
            body,
        )
    )

    # 1
    story.append(P("1. Reasoning behind the original forms", h2))
    story.append(
        P(
            "The original forms were built from three sources:",
            body,
        )
    )
    for item in [
        "the Excel input mask (<i>Input_Mask_Extrusion</i>) from Client",
        "the questionnaire / plant process description",
        "the idea that operators must enter data <b>quickly during a shift</b>",
    ]:
        story.append(P(f"• {item}", bullet))

    story.append(
        P(
            "So the design was intentionally <b>lean and event-based</b>, not a full incident "
            "investigation form. Each form answers one clear question:",
            body,
        )
    )

    form_rows = [
        [
            Paragraph("<b>Form</b>", cell),
            Paragraph("<b>What it captures</b>", cell),
            Paragraph("<b>Why it exists</b>", cell),
        ],
        [
            Paragraph("Production start", cell),
            Paragraph("Line, material/recipe, trial, shift, start time, comment", cell),
            Paragraph("Creates the <b>production run container</b> that everything else is linked to", cell),
        ],
        [
            Paragraph("Extruder events", cell),
            Paragraph("Phase / maintenance events (heating, shutdown, screen, nozzle, low production) + time + reason", cell),
            Paragraph("Labels process phases and maintenance actions for Process State / Nozzle–Screen learning", cell),
        ],
        [
            Paragraph("Granulator events", cell),
            Paragraph("Knife change / grinding + time", cell),
            Paragraph("Labels for knife wear / grain distribution models", cell),
        ],
        [
            Paragraph("Cleaning", cell),
            Paragraph("Water bath / centrifuge / cleaning work + reason", cell),
            Paragraph("Labels cleaning phases so they are not treated as faults", cell),
        ],
        [
            Paragraph("Faults", cell),
            Paragraph("Mechanical / electrical + subtype + time", cell),
            Paragraph("Labels real disturbances for Process State and fault patterns", cell),
        ],
        [
            Paragraph("Material behavior", cell),
            Paragraph("Observation type (lumps, twin beads, pentane, foaming…) + severity + time", cell),
            Paragraph("Operator “floor quality” labels for Material Behavior Risk", cell),
        ],
        [
            Paragraph("Material blocking", cell),
            Paragraph("Reason + time range", cell),
            Paragraph("Later ground truth for bad batches (Predictive Quality)", cell),
        ],
        [
            Paragraph("Daily quality", cell),
            Paragraph("Open holes %, sieve %, foaming OK/NOK + shift", cell),
            Paragraph("Regular quality ground truth for Predictive Quality", cell),
        ],
    ]
    t1 = Table(form_rows, colWidths=[3.2 * cm, 6.5 * cm, 7.0 * cm])
    t1.setStyle(
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
    story.append(t1)
    story.append(Spacer(1, 6))
    story.append(P("<b>Core idea of the original design:</b>", body))
    for item in [
        "Every entry is attached to a <b>production run</b>.",
        "Dropdowns force <b>structured labels</b> (not free text only).",
        "We keep the form short so operators actually fill it every shift.",
        "AI then joins: <b>WinCC signals + operator labels + later quality</b> for the same run.",
    ]:
        story.append(P(f"• {item}", bullet))
    story.append(
        P(
            "So the original forms were designed as <b>labels and context</b>, not as a complete "
            "root-cause investigation record.",
            body,
        )
    )

    # 2
    story.append(P("2. Which AI predictions we expect from this data", h2))
    story.append(
        P(
            "From the collected forms + live signals, we expect these predictions "
            "(aligned with our requirements document):",
            body,
        )
    )
    for item in [
        "<b>Process State</b> — current phase (heating, startup, stable, low production, cleaning, empty run, cooling, shutdown, fault)",
        "<b>Low-production cause &amp; severity</b> — when throughput is low: planned vs feeder vs material vs process",
        "<b>Early anomaly detection</b> — early doser/process drift before SCADA alarms",
        "<b>Material behavior risk</b> — rising risk of lumps, twin beads, pentane/foaming issues",
        "<b>Nozzle / screen / pressure risk</b> — clogging / screen change need",
        "<b>Granulator / knife wear risk</b> — knife condition / grain-distribution risk",
        "<b>Predictive quality</b> — quality risk during production (open holes, sieve, foaming, blocking), days before lab confirmation",
        "<b>Maintenance prioritization</b> — ranked maintenance hints",
    ]:
        story.append(P(f"• {item}", bullet))

    # 3
    story.append(P("3. Relationships / correlations the model should learn", h2))
    story.append(P("Exactly the chain you described:", body))
    for item in [
        "What did the operator observe? → Material Behavior / Faults / comments",
        "What happened before? → Extruder/Granulator/Cleaning events + signal trends before the event",
        "Why did they intervene? → Level 2/3 + reason (e.g. screen change because high ΔP / planned)",
        "What action was taken? → event type (knife change, nozzle grinding, cleaning, etc.)",
        "What was the result? → process recovery in signals + later Daily Quality / Material Blocking",
        "What was the later quality outcome? → Daily Quality + Material Blocking + lab/QA decision",
    ]:
        story.append(P(f"• {item}", bullet))

    story.append(P("Examples of concrete correlations:", body))
    for item in [
        "Rising screen ΔP + “Screen change / High differential pressure” → earlier screen-risk warning next time",
        "Knife torque drift + “Knife grinding” → knife-wear prediction",
        "Material behavior “twin beads” + process-water/granulator signals → material-risk score",
        "Stable-run signal pattern + later foaming NOK → predictive quality during production",
    ]:
        story.append(P(f"• {item}", bullet))

    # 4
    story.append(P("4. Links between operator inputs and future predictions", h2))
    link_rows = [
        [
            Paragraph("<b>Operator input</b>", cell),
            Paragraph("<b>Used as</b>", cell),
            Paragraph("<b>Feeds prediction</b>", cell),
        ],
        [
            Paragraph("Production start (material, trial, shift)", cell),
            Paragraph("Context for every model", cell),
            Paragraph("All capabilities", cell),
        ],
        [
            Paragraph("Extruder Level 2/3 + time", cell),
            Paragraph("Phase/maintenance labels", cell),
            Paragraph("Process State, Low Production, Nozzle/Screen", cell),
        ],
        [
            Paragraph("Granulator knife events", cell),
            Paragraph("Maintenance labels", cell),
            Paragraph("Granulator / Knife Wear", cell),
        ],
        [
            Paragraph("Cleaning events", cell),
            Paragraph("Planned non-production labels", cell),
            Paragraph("Process State (avoid false alarms)", cell),
        ],
        [
            Paragraph("Faults", cell),
            Paragraph("Disturbance labels", cell),
            Paragraph("Process State, anomaly validation", cell),
        ],
        [
            Paragraph("Material behavior + severity", cell),
            Paragraph("Observation labels", cell),
            Paragraph("Material Behavior Risk, Predictive Quality", cell),
        ],
        [
            Paragraph("Material blocking", cell),
            Paragraph("Bad-batch ground truth", cell),
            Paragraph("Predictive Quality", cell),
        ],
        [
            Paragraph("Daily quality", cell),
            Paragraph("Quality ground truth", cell),
            Paragraph("Predictive Quality, Granulator, Nozzle/Screen", cell),
        ],
    ]
    t2 = Table(link_rows, colWidths=[5.5 * cm, 4.5 * cm, 6.7 * cm])
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
    story.append(Spacer(1, 6))
    story.append(
        P(
            "Without these labels, we only have sensor curves. With them, we can say: "
            "<b>“This signal pattern + this operator observation → later this quality/maintenance outcome.”</b>",
            body,
        )
    )

    # 5
    story.append(P("5. Complete prediction workflow (data → AI output)", h2))
    for i, item in enumerate(
        [
            "<b>Production Start</b> opens a run (line, material, shift, recipe/order if available).",
            "During the run, WinCC signals are ingested continuously (features over 1/5/15/30 min windows).",
            "Operators log events/observations on the forms (structured dropdowns + time + comment).",
            "AI computes live outputs (process state, anomalies, risks) and stores them with the run + input window.",
            "Later, Daily Quality / Material Blocking / QA results are attached to the same run.",
            "Correlation layer builds labeled examples: "
            "<i>(signals + events + observations during run) → (later quality / maintenance outcome)</i>.",
            "Over time, rule-based risks improve into ML predictions for new runs <b>during production</b>.",
        ],
        start=1,
    ):
        story.append(P(f"{i}. {item}", bullet))

    # 6
    story.append(P("6. How your redesigned list fits", h2))
    story.append(
        P(
            "Your data categories are very good. Many already exist in our model "
            "(run, line, material, event time, event type, process area via Level 1/2, comments, quality results).",
            body,
        )
    )
    story.append(
        P(
            "Some of your fields are <b>richer than the original lean forms</b>, especially:",
            body,
        )
    )
    for item in [
        "time when problem first occurred / noticed / resolved",
        "duration until detection / resolution",
        "process conditions observed",
        "actions taken",
        "suspected cause",
        "events immediately before",
        "people notified",
        "result of intervention",
        "linked quality inspection / final QA decision",
    ]:
        story.append(P(f"• {item}", bullet))

    story.append(
        P(
            "We agree these strengthen AI learning. The only risk is operator load: "
            "if every event requires too many fields, data quality drops.",
            body,
        )
    )
    story.append(P("<b>Proposal for the next step:</b>", body))
    for i, item in enumerate(
        [
            "Keep the original <b>form separation by purpose</b> (start, events, material behavior, quality, blocking) — easy for daily use.",
            "Enrich the forms with the most valuable fields from your redesign, especially for incidents/faults: "
            "noticed time / resolved time, suspected cause, action taken, result of intervention, "
            "link to quality inspection / final decision.",
            "Keep optional/advanced fields for serious events, not for every routine entry "
            "(e.g. planned screen change).",
        ],
        start=1,
    ):
        story.append(P(f"{i}. {item}", bullet))

    story.append(
        P(
            "This way we collect the right AI information from the beginning, without making "
            "normal shift logging too heavy.",
            body,
        )
    )
    story.append(
        P(
            "We are happy to go through your redesigned forms field-by-field and mark: "
            "<b>must-have for AI from day one</b>, <b>useful later</b>, and <b>optional / nice-to-have</b>. "
            "Then we can freeze one shared form design before implementation continues.",
            body,
        )
    )
    doc.build(story)
    print(f"wrote: {OUT}")


if __name__ == "__main__":
    main()
