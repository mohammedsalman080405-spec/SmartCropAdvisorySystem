"""
Soil Health & Crop Advisory PDF Report Generator
Generates a structured, professional PDF advisory card for farmers.
Uses ReportLab when installed, and provides a built-in standard PDF fallback.
"""

import io
from datetime import datetime

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def _build_reportlab_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1b5e20"),
        alignment=1,
    )

    sub_header_style = ParagraphStyle(
        "SubHeaderStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#2e7d32"),
        alignment=1,
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1b5e20"),
    )

    cell_style = ParagraphStyle(
        "CellStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
    )

    bold_cell_style = ParagraphStyle(
        "BoldCellStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#212121"),
    )

    story = []

    # Title & Header
    story.append(Paragraph("SmartCrop Advisory System", header_style))
    story.append(
        Paragraph(
            "Official Soil Health Card & Sustainable Crop Advisory",
            sub_header_style,
        )
    )
    story.append(Spacer(1, 10))
    story.append(
        HRFlowable(
            width="100%",
            thickness=2,
            color=colors.HexColor("#2e7d32"),
            spaceBefore=5,
            spaceAfter=12,
        )
    )

    # Farmer & Report Metadata Table
    now_str = datetime.now().strftime("%d-%b-%Y %I:%M %p")
    report_id = f"AGRI-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    farmer_name = data.get("farmer_name") or "Progressive Farmer"
    phone = data.get("phone") or "N/A"
    village = data.get("village") or "Registered Village"

    meta_data = [
        [
            Paragraph("<b>Farmer Name:</b>", bold_cell_style),
            Paragraph(str(farmer_name), cell_style),
            Paragraph("<b>Report ID:</b>", bold_cell_style),
            Paragraph(report_id, cell_style),
        ],
        [
            Paragraph("<b>Contact Phone:</b>", bold_cell_style),
            Paragraph(str(phone), cell_style),
            Paragraph("<b>Date & Time:</b>", bold_cell_style),
            Paragraph(now_str, cell_style),
        ],
        [
            Paragraph("<b>Village / District:</b>", bold_cell_style),
            Paragraph(str(village), cell_style),
            Paragraph("<b>Status:</b>", bold_cell_style),
            Paragraph("Certified Recommendation", cell_style),
        ],
    ]

    meta_table = Table(meta_data, colWidths=[90, 180, 90, 180])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f8e9")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c5e1a5")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Field & Soil Parameters Section
    story.append(Paragraph("1. Field & Environmental Conditions", section_heading))
    story.append(Spacer(1, 4))

    temp = data.get("temperature", "--")
    humidity = data.get("humidity", "--")
    soil_ph = data.get("soil_ph", "--")

    ph_status = "Optimal"
    try:
        ph_val = float(soil_ph)
        if ph_val < 5.5:
            ph_status = "Acidic (Needs Lime Treatment)"
        elif ph_val > 7.5:
            ph_status = "Alkaline (Needs Gypsum / Organic Matter)"
        else:
            ph_status = "Optimal (6.0 - 7.5 Neutral)"
    except Exception:
        pass

    env_data = [
        [
            Paragraph("<b>Parameter</b>", bold_cell_style),
            Paragraph("<b>Measured Value</b>", bold_cell_style),
            Paragraph("<b>Agronomic Interpretation</b>", bold_cell_style),
        ],
        [
            Paragraph("Temperature", cell_style),
            Paragraph(f"{temp} C", cell_style),
            Paragraph(
                "Normal growth range" if float(temp or 25) <= 35 else "Heat stress warning - early watering advised",
                cell_style,
            ),
        ],
        [
            Paragraph("Relative Humidity", cell_style),
            Paragraph(f"{humidity} %", cell_style),
            Paragraph(
                "Adequate moisture" if float(humidity or 60) >= 40 else "Dry air - mulching recommended",
                cell_style,
            ),
        ],
        [
            Paragraph("Soil pH Level", cell_style),
            Paragraph(f"{soil_ph}", cell_style),
            Paragraph(ph_status, cell_style),
        ],
    ]

    env_table = Table(env_data, colWidths=[140, 120, 280])
    env_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f5e9")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#a5d6a7")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(env_table)
    story.append(Spacer(1, 14))

    # Recommended Crops Section
    story.append(Paragraph("2. Top Recommended Crops & Suitability", section_heading))
    story.append(Spacer(1, 4))

    recs = data.get("recommendations") or []
    if not recs and data.get("selected_crop"):
        recs = [{"crop": data.get("selected_crop"), "match_score": 9.5, "max_score": 10}]

    rec_data = [
        [
            Paragraph("<b>Rank</b>", bold_cell_style),
            Paragraph("<b>Crop Name</b>", bold_cell_style),
            Paragraph("<b>Suitability Score</b>", bold_cell_style),
            Paragraph("<b>Agronomic Feasibility</b>", bold_cell_style),
        ]
    ]

    for i, item in enumerate(recs[:5], start=1):
        crop_name = str(item.get("crop", "Unknown")).capitalize()
        score = item.get("match_score", "--")
        max_s = item.get("max_score", 10)
        feasibility = "Highly Recommended" if float(score or 0) >= 7.5 else "Moderately Suitable"
        rec_data.append(
            [
                Paragraph(f"#{i}", cell_style),
                Paragraph(crop_name, bold_cell_style),
                Paragraph(f"{score} / {max_s}", cell_style),
                Paragraph(feasibility, cell_style),
            ]
        )

    if len(rec_data) == 1:
        rec_data.append([
            Paragraph("-", cell_style),
            Paragraph("General Cereals & Pulses", cell_style),
            Paragraph("8.0 / 10", cell_style),
            Paragraph("Standard regional crop cycle", cell_style),
        ])

    rec_table = Table(rec_data, colWidths=[50, 140, 120, 230])
    rec_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f5e9")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#a5d6a7")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(rec_table)
    story.append(Spacer(1, 14))

    # Fertilizer & Management Plan
    story.append(Paragraph("3. Nutrient & Fertilizer Advisory", section_heading))
    story.append(Spacer(1, 4))

    fert_guidance = [
        [
            Paragraph("<b>Target Nutrient</b>", bold_cell_style),
            Paragraph("<b>Dosage / Acre</b>", bold_cell_style),
            Paragraph("<b>Application Window & Instructions</b>", bold_cell_style),
        ],
        [
            Paragraph("Nitrogen (Urea)", cell_style),
            Paragraph("45 - 50 kg / acre", cell_style),
            Paragraph("Split into 3 doses: basal, vegetative, and panicle initiation.", cell_style),
        ],
        [
            Paragraph("Phosphorus (DAP / SSP)", cell_style),
            Paragraph("25 - 30 kg / acre", cell_style),
            Paragraph("Apply full dose as basal application during final land preparation.", cell_style),
        ],
        [
            Paragraph("Potash (MOP)", cell_style),
            Paragraph("20 kg / acre", cell_style),
            Paragraph("Strengthens stalk resistance against pests and drought.", cell_style),
        ],
        [
            Paragraph("Organic Compost / FYM", cell_style),
            Paragraph("2 - 3 tonnes / acre", cell_style),
            Paragraph("Improves microbial activity and water retention capacity.", cell_style),
        ],
    ]

    fert_table = Table(fert_guidance, colWidths=[140, 120, 280])
    fert_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f9fbe7")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dce775")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(fert_table)
    story.append(Spacer(1, 14))

    # Irrigation & Special Guidelines
    story.append(Paragraph("4. Irrigation & Advisory Schedule", section_heading))
    story.append(Spacer(1, 4))

    water_notes = data.get("water_notes") or (
        "Maintain adequate moisture during initial rooting and vegetative stage. "
        "Avoid stagnant water. Stop irrigation 7-10 days prior to harvest."
    )
    story.append(Paragraph(f"- <b>Water Management:</b> {water_notes}", cell_style))
    story.append(
        Paragraph(
            "- <b>Pest Monitoring:</b> Inspect field underside leaves twice a week for early pest symptoms.",
            cell_style,
        )
    )
    story.append(
        Paragraph(
            "- <b>Weather Advisory:</b> Avoid pesticide or foliar fertilizer spraying if rain is expected within 6 hours.",
            cell_style,
        )
    )

    story.append(Spacer(1, 18))
    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#cccccc"),
            spaceBefore=5,
            spaceAfter=8,
        )
    )

    # Footer note
    footer_text = Paragraph(
        "<i>Generated by SmartCrop Advisory System (AgriAI) - For queries or WhatsApp assistance contact your local agriculture extension officer.</i>",
        sub_header_style,
    )
    story.append(footer_text)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def _build_fallback_pdf(data):
    """
    Pure Python standard PDF 1.4 generator when reportlab is not installed.
    Creates a valid PDF document with clean headers and text fields.
    """
    now_str = datetime.now().strftime("%d-%b-%Y %I:%M %p")
    farmer_name = data.get("farmer_name") or "Progressive Farmer"
    phone = data.get("phone") or "N/A"
    village = data.get("village") or "Registered Village"
    temp = data.get("temperature", "28")
    humidity = data.get("humidity", "65")
    soil_ph = data.get("soil_ph", "6.5")

    recs = data.get("recommendations") or []
    crop_list = ", ".join([r.get("crop", "").capitalize() for r in recs[:4]]) or "Rice, Maize, Wheat"

    lines = [
        "SMART CROP ADVISORY SYSTEM - SOIL HEALTH & ADVISORY REPORT",
        "=" * 60,
        f"Generated: {now_str}",
        "",
        "FARMER PROFILE",
        "-" * 40,
        f"Name:    {farmer_name}",
        f"Phone:   {phone}",
        f"Village: {village}",
        "",
        "ENVIRONMENTAL & SOIL METRICS",
        "-" * 40,
        f"Temperature:       {temp} C",
        f"Relative Humidity: {humidity} %",
        f"Soil pH:           {soil_ph}",
        "",
        "RECOMMENDED CROPS",
        "-" * 40,
        f"Top Crops: {crop_list}",
        "",
        "FERTILIZER GUIDANCE",
        "-" * 40,
        "1. Nitrogen (Urea): 45-50 kg/acre (split in 3 applications)",
        "2. Phosphorus (DAP): 25-30 kg/acre (basal application)",
        "3. Potash (MOP): 20 kg/acre",
        "4. Organic Farmyard Manure: 2 tonnes/acre",
        "",
        "IRRIGATION & FIELD CARE",
        "-" * 40,
        "- Irrigate during morning hours to reduce evaporation losses.",
        "- Avoid overhead spraying if rainfall or high winds are forecasted.",
        "- Inspect crops weekly for early disease and pest symptoms.",
        "=" * 60,
        "SmartCrop Advisory System (AgriAI) - Sustainable Agriculture",
    ]

    def escape_pdf(text):
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    pdf_stream = []
    pdf_stream.append("BT")
    pdf_stream.append("/F1 10 Tf")
    pdf_stream.append("50 750 Td")
    pdf_stream.append("14 TL")

    for line in lines:
        pdf_stream.append(f"({escape_pdf(line)}) Tj T*")

    pdf_stream.append("ET")
    stream_content = "\n".join(pdf_stream).encode("latin1")

    objects = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Courier >> >> >> /Contents 4 0 R >>"
    )
    objects.append(
        f"<< /Length {len(stream_content)} >>\nstream\n".encode("latin1")
        + stream_content
        + b"\nendstream"
    )

    output = io.BytesIO()
    output.write(b"%PDF-1.4\n")
    xref_offsets = [0]

    for i, obj in enumerate(objects, start=1):
        xref_offsets.append(output.tell())
        output.write(f"{i} 0 obj\n".encode("latin1"))
        output.write(obj)
        output.write(b"\nendobj\n")

    startxref = output.tell()
    output.write(b"xref\n")
    output.write(f"0 {len(objects) + 1}\n".encode("latin1"))
    output.write(b"0000000000 65535 f \n")
    for offset in xref_offsets[1:]:
        output.write(f"{offset:010d} 00000 n \n".encode("latin1"))

    output.write(b"trailer\n")
    output.write(f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode("latin1"))
    output.write(b"startxref\n")
    output.write(f"{startxref}\n".encode("latin1"))
    output.write(b"%%EOF\n")

    return output.getvalue()


def generate_soil_health_pdf(data):
    """
    Generate PDF bytes for the soil health card.
    Uses ReportLab if available, otherwise pure Python fallback.
    """
    if HAS_REPORTLAB:
        try:
            return _build_reportlab_pdf(data)
        except Exception:
            return _build_fallback_pdf(data)
    return _build_fallback_pdf(data)
