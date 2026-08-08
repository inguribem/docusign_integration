"""
Project Acceptance & Sign-Off Certificate PDF Generator.
Variable fields: consultant_company, consultant_name, client_name,
                 project_name, warranty_days, city, effective_date.
Fixed content:   deliverables table, conformity clauses, warranty text.
"""
from dataclasses import dataclass, field
from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Palette ─────────────────────────────────────────────────────────────────
DARK_BLUE  = colors.HexColor("#1a3a6b")
LIGHT_BLUE = colors.HexColor("#eef2f7")
STRIPE     = colors.HexColor("#f5f7fa")
GRID_COLOR = colors.HexColor("#cccccc")
GREEN_DARK = colors.HexColor("#166534")
GREEN_BG   = colors.HexColor("#dcfce7")
GREEN_TEXT = colors.HexColor("#15803d")

# ── Fixed deliverables ───────────────────────────────────────────────────────

_DELIVERABLES = [
    (
        "Corporate Website &\nBooking System",
        "Responsive landing page live at production URL; online booking form "
        "operational and storing appointment data in the designated database.",
    ),
    (
        "WhatsApp API\nIntegration",
        "Meta Business API webhooks configured and active; system successfully "
        "receiving, parsing, and acknowledging incoming WhatsApp traffic.",
    ),
    (
        "Tracking Automation\nBackend",
        "FastAPI application and n8n workflows processing inbound text and GPS "
        "location data from the designated tracking provider; automated log "
        "entries confirmed in the database.",
    ),
    (
        "Management\nWebApp Panel",
        "Secure authentication portal active; Appointments Dashboard displaying "
        "correct booking data; Vehicle Tracking Log reflecting real-time and "
        "historical location records.",
    ),
]

# ── Conformity clauses ────────────────────────────────────────────────────────

_CONFORMITY_CLAUSES = [
    "The Client has personally reviewed, accessed, and tested each of the "
    "deliverables listed in Section 2 of this Certificate.",
    "Each deliverable fully conforms to the specifications, functional "
    "requirements, and acceptance criteria defined in the original Application "
    "Development Statement of Work agreed between the Parties.",
    "As of the date of execution of this Certificate, no outstanding defects, "
    "omissions, functional failures, or non-conformities exist under the original "
    "development scope.",
    "The Client formally grants <b>Final Acceptance (Sign-Off)</b> of the complete "
    "platform as delivered, with no reservations.",
    "This Sign-Off conclusively concludes the Development Phase and extinguishes "
    "all milestone delivery obligations of the Consultant under the AppDev SOW, "
    "except for the Post-Launch Warranty described in Section 4 below.",
]


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class AcceptanceData:
    # Parties
    consultant_company: str
    client_name: str
    project_name: str
    warranty_days: str
    # Optional placement fields
    city: str = ""
    effective_date: str = ""   # auto-set to today if blank
    governing_county: str = "Orange"
    # Signature block
    consultant_name: str = ""
    consultant_title: str = ""
    client_signer_name: str = ""
    client_signer_title: str = ""

    def __post_init__(self):
        if not self.effective_date:
            self.effective_date = date.today().strftime("%B %d, %Y")


# ── Public API ────────────────────────────────────────────────────────────────

def generate_acceptance_pdf(data: AcceptanceData) -> bytes:
    """Generate the Acceptance Certificate and return its bytes."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=1 * inch, rightMargin=1 * inch,
        topMargin=1 * inch, bottomMargin=1 * inch,
    )
    S = _styles()
    story = _build_story(data, S)
    doc.build(story)
    return buffer.getvalue()


# ── Story builder ─────────────────────────────────────────────────────────────

def _build_story(data: AcceptanceData, S: dict) -> list:
    story = []

    city_line = data.city if data.city else "__________________, Florida"

    # ── Header ────────────────────────────────────────────────────────────────
    story += [
        Paragraph(data.consultant_company.upper(), S["company"]),
        Paragraph("PROJECT ACCEPTANCE &amp; SIGN-OFF CERTIFICATE", S["doc_title"]),
        HRFlowable(width="100%", thickness=1.5, color=DARK_BLUE, spaceAfter=8),
    ]

    # ── § 1 Header and Context ────────────────────────────────────────────────
    story += [
        Paragraph("1. Header and Context", S["h1"]),
        Paragraph(
            f'This Project Acceptance and Sign-Off Certificate ("Certificate") is issued '
            f'in the city of <b>{city_line}</b>, on <b>{data.effective_date}</b>, by and '
            f'between <b>{data.consultant_company}</b> ("Consultant") and '
            f'<b>{data.client_name}</b> ("Client"), collectively referred to as the '
            f'"Parties."',
            S["body"],
        ),
        Paragraph(
            f'The purpose of this Certificate is to formally document the delivery, '
            f'closure, and final acceptance of all software development services '
            f'described in the Application Development Statement of Work for the '
            f'project known as <b>"{data.project_name}"</b> (the "Project"). '
            f'By executing this Certificate, the Parties confirm that all contracted '
            f'deliverables have been completed, delivered, and verified to their '
            f'mutual satisfaction.',
            S["body"],
        ),
        Spacer(1, 0.12 * inch),
    ]

    # ── § 2 Deliverables Compliance Declaration ───────────────────────────────
    story += [
        Paragraph("2. Deliverables Compliance Declaration", S["h1"]),
        Paragraph(
            "The Parties hereby certify that the following components have been "
            "successfully deployed to the agreed production environment, tested "
            "against the specified acceptance criteria, and confirmed as fully "
            "operational:",
            S["body"],
        ),
        Spacer(1, 0.04 * inch),
        _deliverables_table(S),
        Spacer(1, 0.12 * inch),
    ]

    # ── § 3 Client Conformity and Sign-Off ────────────────────────────────────
    story += [
        Paragraph("3. Client Conformity and Sign-Off Declaration", S["h1"]),
        Paragraph(
            f'The Client, <b>{data.client_name}</b>, hereby formally and irrevocably '
            f'declares the following:',
            S["body"],
        ),
    ]
    for i, clause in enumerate(_CONFORMITY_CLAUSES, start=1):
        story.append(Paragraph(f"({i})&nbsp;&nbsp;{clause}", S["clause"]))

    story.append(Spacer(1, 0.12 * inch))

    # ── § 4 Warranty Activation ───────────────────────────────────────────────
    story += [
        Paragraph("4. Warranty Activation", S["h1"]),
        Paragraph(
            f'Effective immediately upon execution of this Certificate by both Parties, '
            f'the <b>Post-Launch Warranty Period of {data.warranty_days} calendar days</b> '
            f'activates for the correction of unforeseen defects or regressions in the '
            f'delivered code base that prevent the system from operating in accordance '
            f'with the specifications accepted herein. The Warranty covers only '
            f'bug-correction work on the original deliverables; it does not cover new '
            f'feature requests, third-party API changes, or issues arising from '
            f'unauthorized modifications.',
            S["body"],
        ),
        Paragraph(
            "The separate Post-Launch Support and Maintenance Agreement, if executed "
            "between the Parties, activates concurrently with this Warranty Period and "
            "shall govern all ongoing support obligations once the Warranty Period "
            "expires.",
            S["body"],
        ),
        Spacer(1, 0.12 * inch),
    ]

    # ── § 5 Governing Law ─────────────────────────────────────────────────────
    story += [
        Paragraph("5. Governing Law", S["h1"]),
        Paragraph(
            f'This Certificate shall be governed by and construed in accordance with '
            f'the laws of the State of Florida. Any dispute arising from or related to '
            f'this Certificate shall be subject to the exclusive jurisdiction of the '
            f'courts of <b>{data.governing_county} County</b>, Florida.',
            S["body"],
        ),
    ]

    # ── Signature block ────────────────────────────────────────────────────────
    story += [PageBreak(), _signature_block(data, S)]

    return story


# ── Section helpers ────────────────────────────────────────────────────────────

def _deliverables_table(S: dict) -> Table:
    col_w = [0.28 * inch, 1.72 * inch, 3.5 * inch, 1.0 * inch]

    header = [Paragraph(h, S["th"]) for h in ("#", "Component", "Acceptance Criteria", "Status")]

    rows = [header]
    for i, (component, criteria) in enumerate(_DELIVERABLES, start=1):
        bg = STRIPE if i % 2 == 0 else colors.white
        rows.append([
            Paragraph(str(i), S["td_center"]),
            Paragraph(component, S["td_bold"]),
            Paragraph(criteria, S["td"]),
            Paragraph("<b>ACCEPTED</b>", S["accepted"]),
        ])

    t = Table(rows, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0),  (-1, 0),  DARK_BLUE),
        ("TEXTCOLOR",     (0, 0),  (-1, 0),  colors.white),
        ("GRID",          (0, 0),  (-1, -1), 0.5, GRID_COLOR),
        ("BACKGROUND",    (0, 2),  (-1, 2),  STRIPE),
        ("BACKGROUND",    (0, 4),  (-1, 4),  STRIPE),
        ("VALIGN",        (0, 0),  (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0),  (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0),  (-1, -1), 6),
        ("LEFTPADDING",   (0, 0),  (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0),  (-1, -1), 6),
        ("ALIGN",         (0, 1),  (0, -1),  "CENTER"),
        ("ALIGN",         (3, 1),  (3, -1),  "CENTER"),
    ]))
    return t


def _signature_block(data: AcceptanceData, S: dict) -> Table:
    def _col(anchor: str, role: str, name_val: str, title_val: str, entity: str) -> Paragraph:
        name_display  = name_val  or "________________________________"
        title_display = title_val or "________________________________"
        return Paragraph(
            f'<b>{role}</b><br/>'
            f'<font color="white" size="4">{anchor}</font><br/><br/>'
            '________________________________<br/>'
            'By (Signature):<br/><br/>'
            '________________________________<br/>'
            f'Name:&nbsp;&nbsp;<b>{name_display}</b><br/><br/>'
            '________________________________<br/>'
            f'Title:&nbsp;&nbsp;<b>{title_display}</b><br/><br/>'
            '________________________________<br/>'
            f'Entity:&nbsp;&nbsp;<b>{entity}</b><br/><br/>'
            '________________________________<br/>'
            'Date:',
            S["sig"],
        )

    left = _col(
        "TKSOL_CONSULTANT_SIG",
        "CONSULTANT",
        data.consultant_name,
        data.consultant_title,
        data.consultant_company,
    )
    right = _col(
        "TKSOL_CLIENT_SIG",
        "CLIENT",
        data.client_signer_name,
        data.client_signer_title,
        data.client_name,
    )

    note = Paragraph(
        "This Certificate is executed in two (2) counterpart originals, each of "
        "equal legal force and effect.",
        S["caption"],
    )

    outer = Table(
        [[left, right], [note, ""]],
        colWidths=[3.1 * inch, 3.1 * inch],
        style=TableStyle([
            ("VALIGN",        (0, 0), (-1, 0), "TOP"),
            ("SPAN",          (0, 1), (1, 1)),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ]),
    )
    return outer


# ── Styles ─────────────────────────────────────────────────────────────────────

def _styles() -> dict:
    base = ParagraphStyle("base", fontName="Helvetica", fontSize=10, leading=14)
    return {
        "company": ParagraphStyle(
            "company", parent=base, fontSize=13, fontName="Helvetica-Bold",
            alignment=TA_CENTER, spaceAfter=2,
        ),
        "doc_title": ParagraphStyle(
            "doc_title", parent=base, fontSize=14, fontName="Helvetica-Bold",
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base, fontSize=11, fontName="Helvetica-Bold",
            spaceBefore=8, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body", parent=base, fontSize=9.5, leading=14,
            alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "clause": ParagraphStyle(
            "clause", parent=base, fontSize=9.5, leading=14,
            leftIndent=20, spaceAfter=5, alignment=TA_JUSTIFY,
        ),
        "caption": ParagraphStyle(
            "caption", parent=base, fontSize=8.5, leading=12,
            fontName="Helvetica-Oblique", alignment=TA_CENTER, spaceBefore=8,
        ),
        "th": ParagraphStyle(
            "th", parent=base, fontSize=9, fontName="Helvetica-Bold",
            alignment=TA_CENTER, textColor=colors.white,
        ),
        "td": ParagraphStyle(
            "td", parent=base, fontSize=8.5, leading=12,
        ),
        "td_bold": ParagraphStyle(
            "td_bold", parent=base, fontSize=8.5, leading=12,
            fontName="Helvetica-Bold",
        ),
        "td_center": ParagraphStyle(
            "td_center", parent=base, fontSize=8.5, leading=12,
            alignment=TA_CENTER,
        ),
        "accepted": ParagraphStyle(
            "accepted", parent=base, fontSize=8.5, fontName="Helvetica-Bold",
            alignment=TA_CENTER, textColor=GREEN_TEXT,
        ),
        "sig": ParagraphStyle(
            "sig", parent=base, fontSize=9.5, leading=20,
        ),
    }
