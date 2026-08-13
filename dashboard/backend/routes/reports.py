"""
EvOLve — dashboard/backend/routes/reports.py
PDF report generation endpoint.
"""

import os
import json
import io
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

router = APIRouter()
RESULTS_DIR = "results"


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def generate_pdf_report(date_from: str, date_to: str) -> bytes:
    """Generate a PDF forest health report using ReportLab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        raise HTTPException(500, "ReportLab not installed. Run: pip install reportlab")

    # Load data
    clf  = load_json(os.path.join(RESULTS_DIR, "classifier_results.json"))
    carb = load_json(os.path.join(RESULTS_DIR, "carbon_stock.json"))
    corr = load_json(os.path.join(RESULTS_DIR, "corridor_analysis.json"))
    fire = load_json(os.path.join(RESULTS_DIR, "fire_risk.json"))
    enc  = load_json(os.path.join(RESULTS_DIR, "encroachment_alerts.json"))
    ref  = load_json(os.path.join(RESULTS_DIR, "reforestation_priority.json"))

    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm,   bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'Title', parent=styles['Title'],
        textColor=colors.HexColor('#1B4332'), fontSize=20, spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        textColor=colors.HexColor('#52796F'), fontSize=11, spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        'Heading', parent=styles['Heading2'],
        textColor=colors.HexColor('#2D6A4F'), fontSize=13, spaceBefore=16, spaceAfter=6,
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=10, spaceAfter=6,
    )

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("EvOLve Forest Intelligence Report", title_style))
    story.append(Paragraph(
        f"Wayanad Wildlife Sanctuary (Muthanga Range) · {date_from} to {date_to}",
        subtitle_style
    ))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')} IST",
        styles['Normal']
    ))
    story.append(HRFlowable(width="100%", color=colors.HexColor('#52796F'), thickness=1))
    story.append(Spacer(1, 12))

    # ── Executive Summary ─────────────────────────────────────────────────────
    story.append(Paragraph("1. Executive Summary", heading_style))

    if clf:
        total = len(clf["patch_scores"])
        degraded = sum(1 for v in clf["patch_scores"].values() if v["prediction"] == 1)
        pct = round(degraded / total * 100, 1)
        story.append(Paragraph(
            f"The EvOLve system monitored {total} forest patches across the study area "
            f"covering 6 years (2019–2025) using 72 months of Sentinel-2 satellite imagery. "
            f"{degraded} patches ({pct}%) showed evidence of forest degradation based on "
            f"the self-supervised encoder + Genetic Algorithm adaptive thresholds.",
            body_style
        ))

    # ── Model Performance ─────────────────────────────────────────────────────
    story.append(Paragraph("2. Model Performance (Benchmark Comparison)", heading_style))
    if clf:
        m_evolve  = clf.get("evolve_classifier", {})
        m_sup     = clf.get("supervised_baseline", {})
        m_rf      = clf.get("random_forest", {})

        perf_data = [
            ["Model", "Accuracy", "F1 Score", "AUC", "Precision", "Recall"],
            ["EvOLve (self-supervised)", m_evolve.get("accuracy","—"), m_evolve.get("f1","—"),
             m_evolve.get("auc","—"), m_evolve.get("precision","—"), m_evolve.get("recall","—")],
            ["Supervised Baseline", m_sup.get("accuracy","—"), m_sup.get("f1","—"),
             m_sup.get("auc","—"), m_sup.get("precision","—"), m_sup.get("recall","—")],
            ["Random Forest", m_rf.get("accuracy","—"), m_rf.get("f1","—"),
             m_rf.get("auc","—"), m_rf.get("precision","—"), m_rf.get("recall","—")],
        ]
        t = Table(perf_data, colWidths=[5.5*cm, 2.2*cm, 2.0*cm, 2.0*cm, 2.2*cm, 2.0*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,0), colors.HexColor('#2D6A4F')),
            ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
            ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor('#F0F4F0')]),
            ("GRID",         (0,0), (-1,-1), 0.5, colors.grey),
            ("ALIGN",        (1,0), (-1,-1), "CENTER"),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

    # ── Wildlife Corridors ─────────────────────────────────────────────────────
    story.append(Paragraph("3. Wildlife Corridor Status", heading_style))
    if corr:
        story.append(Paragraph(
            f"Of {corr['total_corridors']} north-south wildlife corridors analysed: "
            f"{corr['intact']} are Intact, {corr['weakened']} are Weakened, "
            f"and {corr['broken']} are Broken. "
            f"Broken corridors restrict elephant and tiger movement — "
            f"immediate intervention is recommended.",
            body_style
        ))

    # ── Fire Risk ─────────────────────────────────────────────────────────────
    story.append(Paragraph("4. Fire Risk Assessment", heading_style))
    if fire:
        rs = fire.get("risk_summary", {})
        story.append(Paragraph(
            f"Fire risk assessment (NDVI + SWIR + seasonal analysis): "
            f"{rs.get('Critical',0)} patches Critical, {rs.get('High',0)} High, "
            f"{rs.get('Moderate',0)} Moderate, {rs.get('Low',0)} Low risk. "
            f"Pre-fire season monitoring (Feb–May) is critical for Wayanad.",
            body_style
        ))

    # ── Carbon Stock ─────────────────────────────────────────────────────────
    story.append(Paragraph("5. Carbon Stock Estimation", heading_style))
    if carb:
        story.append(Paragraph(
            f"Total carbon stock: {carb['total_stock_tCO2']:,.1f} tons CO₂ eq "
            f"(est. USD {carb['total_stock_value_usd']:,.0f}). "
            f"Annual carbon loss due to degradation: {carb['total_annual_loss_tCO2']:,.1f} tons CO₂ "
            f"(est. USD {carb['total_annual_loss_usd']:,.0f}/year at "
            f"USD {carb['carbon_price_usd_per_ton']}/ton).",
            body_style
        ))

    # ── Encroachment ─────────────────────────────────────────────────────────
    story.append(Paragraph("6. Encroachment Alerts", heading_style))
    if enc:
        story.append(Paragraph(
            f"Total anomalies detected: {enc['total_alerts']} "
            f"({enc['high']} High, {enc['medium']} Medium, {enc['low']} Low severity). "
            f"High severity events indicate sudden NDVI drops inconsistent with seasonal patterns — "
            f"likely indicators of illegal clearing or rapid encroachment.",
            body_style
        ))

    # ── Reforestation ─────────────────────────────────────────────────────────
    story.append(Paragraph("7. Reforestation Priorities", heading_style))
    if ref and ref.get("top_candidates"):
        top3 = ref["top_candidates"][:3]
        ref_rows = [["Rank", "Patch ID", "Priority Score", "Degradation", "Justification"]]
        for c in top3:
            ref_rows.append([
                str(c["priority_rank"]),
                str(c["patch_id"]),
                str(c["priority_score"]),
                str(c["degradation_score"]),
                c["justification"][:60] + "..." if len(c["justification"]) > 60 else c["justification"],
            ])
        t2 = Table(ref_rows, colWidths=[1.2*cm, 1.8*cm, 2.5*cm, 2.5*cm, 7.5*cm])
        t2.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), colors.HexColor('#40916C')),
            ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor('#F0F4F0')]),
            ("GRID",        (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        story.append(t2)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", color=colors.HexColor('#52796F'), thickness=0.5))
    story.append(Paragraph(
        "Generated by EvOLve — Evolutionary-Optimized Adaptive Self-Supervised Framework "
        "for Forest Degradation Detection | Amrita School of Computing, Coimbatore",
        ParagraphStyle('Footer', parent=styles['Normal'],
                       fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


@router.get("/export-pdf")
def export_pdf(
    date_from: str = Query("2019-01", description="Start month YYYY-MM"),
    date_to:   str = Query("2025-12", description="End month YYYY-MM"),
):
    """Generate and download a PDF forest health report."""
    pdf_bytes = generate_pdf_report(date_from, date_to)
    filename  = f"EvOLve_Forest_Report_{date_from}_to_{date_to}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
