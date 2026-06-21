"""Genera PDF del debriefing usando reportlab."""
import io
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

router = APIRouter(tags=["pdf"])

_DISCLAIMER = (
    "ADVERTENCIA: Herramienta educativa de simulación. "
    "Todos los valores clínicos tienen estado PENDING_MEDICAL_REVIEW "
    "y no deben utilizarse como referencia en la atención de pacientes reales."
)


def _fmt_time(s: float) -> str:
    m = int(s // 60)
    sec = int(s % 60)
    return f"{m:02d}:{sec:02d}"


def _build_pdf(debrief: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Debriefing — Simulador de Eventos Críticos",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title2",
        parent=styles["Title"],
        fontSize=16,
        textColor=colors.HexColor("#1e3a5f"),
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=colors.HexColor("#1e3a5f"),
        spaceBefore=12,
        spaceAfter=4,
    )
    body_style = styles["BodyText"]
    body_style.fontSize = 9
    small_style = ParagraphStyle("Small", parent=body_style, fontSize=8, textColor=colors.gray)
    warn_style = ParagraphStyle(
        "Warn",
        parent=body_style,
        fontSize=8,
        textColor=colors.HexColor("#7c4f00"),
        backColor=colors.HexColor("#fff3cd"),
        borderPadding=4,
    )

    story = []

    # Header
    story.append(Paragraph("Simulador de Eventos Críticos", title_style))
    story.append(Paragraph("Debriefing — Anafilaxia Perioperatoria", styles["Heading2"]))
    story.append(Paragraph(
        f"Generado: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        small_style,
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1e3a5f")))
    story.append(Spacer(1, 0.4 * cm))

    # Disclaimer
    story.append(Paragraph(_DISCLAIMER, warn_style))
    story.append(Spacer(1, 0.4 * cm))

    # Outcome
    story.append(Paragraph("Desenlace", h2_style))
    story.append(Paragraph(
        f"<b>{debrief.get('outcome_label', '—')}</b>: {debrief.get('outcome_description', '')}",
        body_style,
    ))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(debrief.get("educational_message", ""), body_style))
    story.append(Spacer(1, 0.3 * cm))

    # Stats table
    story.append(Paragraph("Estadísticas de la sesión", h2_style))
    stats_data = [
        ["Tiempo simulado", _fmt_time(debrief.get("total_sim_time_seconds", 0))],
        ["Acciones realizadas", str(debrief.get("total_actions_taken", 0))],
    ]
    t = Table(stats_data, colWidths=[6 * cm, 6 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8f0fe")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.3 * cm))

    sections = debrief.get("sections", {})

    # Correct actions
    story.append(Paragraph("Acciones correctas", h2_style))
    correct = sections.get("correct_actions", [])
    if correct:
        for a in correct:
            story.append(Paragraph(f"✓ {a}", body_style))
    else:
        story.append(Paragraph("Ninguna acción clave fue realizada.", small_style))
    story.append(Spacer(1, 0.2 * cm))

    # Missed actions
    story.append(Paragraph("Acciones omitidas", h2_style))
    missed = sections.get("missed_actions", [])
    if missed:
        for a in missed:
            story.append(Paragraph(f"✗ {a}", body_style))
    else:
        story.append(Paragraph("No hubo acciones omitidas.", small_style))
    story.append(Spacer(1, 0.2 * cm))

    # Timeline
    timeline = sections.get("timeline", [])
    if timeline:
        story.append(Paragraph("Cronología de acciones", h2_style))
        tl_data = [["Tiempo", "Acción", "Estado anterior", "Estado siguiente"]]
        for entry in timeline:
            tl_data.append([
                _fmt_time(entry.get("t", 0)),
                entry.get("action", ""),
                entry.get("state_before", ""),
                entry.get("state_after", ""),
            ])
        tl = Table(tl_data, colWidths=[2.2 * cm, 7 * cm, 4 * cm, 4 * cm])
        tl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(tl)
        story.append(Spacer(1, 0.3 * cm))

    # Clinical sources
    sources = sections.get("clinical_sources", [])
    if sources:
        story.append(Paragraph("Fuentes clínicas", h2_style))
        for src in sources:
            line = f"• {src.get('title', '')} ({src.get('year', '—')})"
            if src.get("url"):
                line += f" — {src['url']}"
            story.append(Paragraph(line, small_style))

    doc.build(story)
    return buf.getvalue()


def make_pdf_endpoint(get_debrief_fn):
    """Factory: wraps an existing debrief function as a PDF endpoint."""

    async def pdf_endpoint(session_id: str):
        debrief = get_debrief_fn(session_id)
        pdf_bytes = _build_pdf(debrief)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="debrief_{session_id[:8]}.pdf"'
            },
        )

    return pdf_endpoint
