"""
SOW PDF Generator — generates a complete Statement of Work PDF
for the Teknowsolutions AppDev SOW template.
"""
from dataclasses import dataclass
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


# ── Fixed document content ─────────────────────────────────────────────────────

MILESTONE_NAMES = [
    "Discovery & Design",
    "Landing Page & Booking",
    "WhatsApp API & Tracking Automation",
    "Management WebApp",
    "QA, Testing & Launch",
]

MILESTONE_DELIVERABLES = [
    "UI/UX Wireframes/Mockups of the Landing Page and WebApp panels (Appointments and Tracking "
    "Log text view). Workflow architecture diagram for the WhatsApp provider automation.",
    "Fully functional and responsive Corporate Website integrated with the appointment booking "
    "form backend. Deployed to staging.",
    "WhatsApp Business API integration setup. Core automation backend capable of receiving "
    "messages, connecting with the tracking provider, and processing location data.",
    "Secure login portal with Section 1 (Appointments Dashboard) and Section 2 (Vehicle "
    "Tracking Text Log / Status History UI) fully connected to data sources.",
    "End-to-end testing (Form → WebApp; WhatsApp Request → Provider Data → WebApp Log), "
    "bug fixes, production deployment, and final launch sign-off.",
]

_SCOPE_ROWS = [
    ("Corporate Website",
     "Responsive Landing Page with an integrated booking form for scheduling appointments.",
     "Web (Desktop/Mobile)"),
    ("WhatsApp Business API",
     "Official WhatsApp Business API integration to handle incoming user communications.",
     "API / Webhooks"),
    ("Tracking Automation",
     "Automated workflow logic to process vehicle location requests received via WhatsApp "
     "messages. Tracking data will be pulled directly using WhatsApp messages from the "
     "designated provider.",
     "Backend / Automation"),
    ("Management WebApp",
     "Private panel with secure login containing two core sections:\n"
     "1. Appointments: View and manage scheduled customer slots.\n"
     "2. Vehicle Tracking Log: Text/Data-based visualization panel showing logs, history, "
     "and status of vehicle locations received via the WhatsApp provider.",
     "Web (Responsive)"),
    ("Database & Backend",
     "Core business logic, data models for appointments/tracking logs, and secure API layers.",
     "Cloud Infrastructure"),
]

_OUT_OF_SCOPE = [
    "third-party service fees (Meta WhatsApp API costs, provider tracking fees, cloud hosting, "
    "Google Workspace licenses);",
    "content creation, copywriting, or manual data migration;",
    "native mobile applications (iOS/Android apps on stores);",
    "interactive map interfaces, GIS mapping software, or geolocation APIs "
    "(e.g., Google Maps API, Leaflet);",
    "ongoing support or maintenance after the warranty period;",
    "procurement or physical installation of hardware/GPS tracking devices in vehicles.",
]

_CLIENT_RESPONSIBILITIES = [
    "provide timely feedback within three (3) business days of each deliverable submission;",
    "supply all required content, brand assets, credentials, and third-party access (such as "
    "Meta Business Manager verification, WhatsApp tracking provider API keys, Google Sheets "
    "API permissions, and Cloud hosting access) within three (3) business days of request;",
    "designate a single point of contact with authority to approve decisions;",
    "make milestone payments on time as specified in Section 4. Delays caused by Client may "
    "result in timeline adjustments at no additional cost to Consultant.",
]

_TECH_STACK_ROWS = [
    ("Frontend (Website & WebApp)", "React, Tailwind, Vite",
     "Modular, fast, and optimized production builds."),
    ("Automation / Workflow", "n8n, Custom Engine",
     "Workflow orchestration and event-driven automation."),
    ("Backend / API Layer", "Python, FastAPI",
     "High-performance, asynchronous REST API architecture."),
    ("Database & Data", "PostgreSQL, Google Sheets",
     "Relational storage for core data and flexible sync spreadsheets."),
    ("Cloud / Hosting", "Render, AWS, Cloudflare",
     "Reliable web hosting, compute resources, and secure CDN/DNS."),
    ("Integrations", "WhatsApp Business API",
     "Official Meta integration for text/data ingestion."),
]

DARK_BLUE = colors.HexColor("#1a3a6b")
LIGHT_BLUE = colors.HexColor("#eef2f7")
STRIPE = colors.HexColor("#f5f7fa")
GRID_COLOR = colors.HexColor("#cccccc")


# ── Data model ─────────────────────────────────────────────────────────────────

@dataclass
class SOWData:
    # Parties
    consultant_company: str
    client_name: str
    # Project
    project_description: str
    # Milestone variable fields (5 predefined milestones)
    m1_weeks: str = ""
    m1_payment: str = ""
    m2_weeks: str = ""
    m2_payment: str = ""
    m3_weeks: str = ""
    m3_payment: str = ""
    m4_weeks: str = ""
    m4_payment: str = ""
    m5_weeks: str = ""
    m5_payment: str = ""
    total_price: str = ""
    # Payment terms
    payment_due_days: str = "15"
    late_fee_rate: str = "1.5"
    warranty_days: str = "30"
    governing_county: str = "Orange"
    # Signature block
    consultant_name: str = ""
    consultant_title: str = ""
    client_signer_name: str = ""
    client_signer_title: str = ""


# ── Public API ──────────────────────────────────────────────────────────────────

def generate_sow_pdf(data: SOWData) -> bytes:
    """Generate the full SOW PDF and return its bytes."""
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


# ── Story builder ───────────────────────────────────────────────────────────────

def _build_story(data: SOWData, S: dict) -> list:
    story = []

    # Header
    story += [
        Paragraph(data.consultant_company.upper(), S["company"]),
        Paragraph("STATEMENT OF WORK (SOW)", S["doc_title"]),
        HRFlowable(width="100%", thickness=1.5, color=DARK_BLUE, spaceAfter=8),
    ]

    # § 1 Purpose and Background
    story += [
        Paragraph("1. Purpose and Background", S["h1"]),
        Paragraph(
            f'This Statement of Work ("SOW") is entered into pursuant to the Master Services '
            f'Agreement ("MSA") between <b>{data.consultant_company}</b> ("Consultant") and '
            f'<b>{data.client_name}</b> ("Client"), and defines the scope, deliverables, '
            f'timeline, and compensation for the development of '
            f'<b>{data.project_description}</b> (the "Project"), a web application and '
            f'automation system described herein.',
            S["body"],
        ),
        Paragraph(
            "In the event of conflict between this SOW and the MSA, this SOW shall control "
            "for matters specific to this engagement.",
            S["body"],
        ),
        Spacer(1, 0.12 * inch),
    ]

    # § 2 Scope of Work
    story += [
        Paragraph("2. Scope of Work", S["h1"]),
        Paragraph("2.1 In-Scope", S["h2"]),
        Paragraph(
            "Consultant agrees to design, develop, test, and deploy the following components "
            "as part of the Project:",
            S["body"],
        ),
        Spacer(1, 0.04 * inch),
        _scope_table(S),
        Spacer(1, 0.12 * inch),
        Paragraph("2.2 Out of Scope", S["h2"]),
        Paragraph(
            "The following are explicitly excluded from this SOW unless added via a written "
            "Change Order:",
            S["body"],
        ),
    ]
    for i, item in enumerate(_OUT_OF_SCOPE):
        story.append(Paragraph(f"({chr(97+i)}) {item}", S["bullet"]))

    story += [
        Spacer(1, 0.08 * inch),
        Paragraph("2.3 Client Responsibilities", S["h2"]),
        Paragraph("Client agrees to:", S["body"]),
    ]
    for i, item in enumerate(_CLIENT_RESPONSIBILITIES):
        story.append(Paragraph(f"({chr(97+i)}) {item}", S["bullet"]))

    story.append(Spacer(1, 0.12 * inch))

    # § 3 Milestones
    story += [
        Paragraph("3. Milestones and Deliverables", S["h1"]),
        Paragraph(
            "The Project is organized into the following phases. Each milestone is subject "
            "to the acceptance process defined in Section 6.",
            S["body"],
        ),
        Spacer(1, 0.04 * inch),
        _milestones_table(data, S),
        Spacer(1, 0.04 * inch),
        Paragraph(
            "Duration per milestone is estimated from the start date of that phase. Actual "
            "start of each phase depends on timely delivery of Client responsibilities and "
            "payment of the preceding milestone.",
            S["caption"],
        ),
        Spacer(1, 0.12 * inch),
    ]

    # § 4 Payment Terms
    story += [
        Paragraph("4. Payment Terms", S["h1"]),
        Paragraph(
            f'The total fixed price for this SOW is <b>USD ${data.total_price}</b>, payable '
            f'in milestone installments as defined in Section 3. Invoices are due within '
            f'<b>{data.payment_due_days} days</b> of issuance. Payments not received by the '
            f'due date shall accrue interest at <b>{data.late_fee_rate}% per month</b>.',
            S["body"],
        ),
        Paragraph(
            "Consultant shall not begin a new milestone phase until the invoice for the "
            "preceding milestone has been paid in full. All prices are in USD and exclude "
            "applicable taxes. Pre-approved third-party expenses are billed at cost with "
            "supporting receipts.",
            S["body"],
        ),
        Spacer(1, 0.12 * inch),
    ]

    # § 5 Technology Stack
    story += [
        Paragraph("5. Technology Stack", S["h1"]),
        Paragraph(
            "The following technologies are proposed for this Project. Final selection is "
            "subject to mutual agreement prior to the start of Milestone 2.",
            S["body"],
        ),
        Spacer(1, 0.04 * inch),
        _tech_table(S),
        Spacer(1, 0.12 * inch),
    ]

    # § 6 Acceptance Criteria
    story += [
        Paragraph("6. Acceptance Criteria", S["h1"]),
        Paragraph(
            "Each deliverable shall be considered accepted when it: (a) meets the functional "
            "requirements described in Section 2.1; (b) passes the agreed test cases without "
            "critical or high-severity bugs; and (c) receives written approval from Client's "
            "designated point of contact.",
            S["body"],
        ),
        Paragraph(
            "Client shall review each deliverable within three (3) business days and provide "
            "either written acceptance or a written list of specific deficiencies. Silence "
            "within three (3) business days constitutes automatic acceptance. Consultant shall "
            "address documented deficiencies within a mutually agreed timeframe. Minor cosmetic "
            "preferences do not constitute grounds for rejection.",
            S["body"],
        ),
        Spacer(1, 0.12 * inch),
    ]

    # § 7 Post-Launch Warranty
    story += [
        Paragraph("7. Post-Launch Warranty", S["h1"]),
        Paragraph(
            f'Consultant warrants that the Deliverables will materially conform to the agreed '
            f'specifications for a period of <b>{data.warranty_days} days</b> following the '
            f'final launch acceptance ("Warranty Period"). During the Warranty Period, '
            f'Consultant shall correct any bugs or defects that prevent the application or '
            f'automation from functioning as specified, at no additional charge.',
            S["body"],
        ),
        Paragraph(
            "The Warranty Period does not cover: (a) issues caused by Client's modifications, "
            "custom metadata changes, Meta WhatsApp account suspensions, Google Sheet structure "
            "breakdown, or tracking provider API downtime/failures; (b) hosting or "
            "infrastructure failures outside Consultant's control; or (c) new feature requests.",
            S["body"],
        ),
        Spacer(1, 0.12 * inch),
    ]

    # § 8 Intellectual Property
    story += [
        Paragraph("8. Intellectual Property", S["h1"]),
        Paragraph(
            "Upon receipt of full payment for all milestones, Consultant grants Client a "
            "perpetual, irrevocable, worldwide, non-exclusive license to use, modify, and "
            "deploy the Deliverables for Client's business purposes, as defined in the MSA. "
            "Consultant retains ownership of all Pre-Existing IP and general-purpose "
            "components. Third-party open-source components are subject to their respective "
            "licenses.",
            S["body"],
        ),
        Spacer(1, 0.12 * inch),
    ]

    # § 9 Confidentiality and Governing Law
    story += [
        Paragraph("9. Confidentiality and Governing Law", S["h1"]),
        Paragraph(
            f'This SOW is subject to the confidentiality obligations and governing law '
            f'provisions of the MSA. All information shared in connection with this Project '
            f'is presumed confidential. This SOW shall be governed by the laws of the State '
            f'of Florida and any disputes shall be adjudicated in the courts of '
            f'<b>{data.governing_county} County</b>, Florida.',
            S["body"],
        ),
        Spacer(1, 0.12 * inch),
    ]

    # § 10 Amendments and Change Orders
    story += [
        Paragraph("10. Amendments and Change Orders", S["h1"]),
        Paragraph(
            "Any changes to the scope, timeline, or pricing defined in this SOW must be "
            "agreed upon in a written Change Order signed by both Parties. Consultant will "
            "provide a written estimate (effort, cost, and timeline impact) for any requested "
            "change within three (3) business days. Work on changes shall not begin until "
            "the Change Order is fully executed.",
            S["body"],
        ),
    ]

    # Signature block — forced to new page so coordinates are predictable
    story += [PageBreak(), _signature_block(data, S)]

    return story


# ── Section helpers ─────────────────────────────────────────────────────────────

def _scope_table(S: dict) -> Table:
    col_w = [1.35 * inch, 3.65 * inch, 1.3 * inch]
    header = [Paragraph(h, S["th"]) for h in ("Component", "Description / Features", "Platform")]
    rows = [header]
    for name, desc, platform in _SCOPE_ROWS:
        rows.append([
            Paragraph(f"<b>{name}</b>", S["td"]),
            Paragraph(desc.replace("\n", "<br/>"), S["td"]),
            Paragraph(platform, S["td"]),
        ])
    return _styled_table(rows, col_w)


def _milestones_table(data: SOWData, S: dict) -> Table:
    col_w = [0.25 * inch, 1.35 * inch, 3.0 * inch, 0.85 * inch, 0.85 * inch]
    header = [Paragraph(h, S["th"]) for h in ("#", "Milestone", "Deliverables", "Duration", "Payment")]
    weeks_payments = [
        (data.m1_weeks, data.m1_payment),
        (data.m2_weeks, data.m2_payment),
        (data.m3_weeks, data.m3_payment),
        (data.m4_weeks, data.m4_payment),
        (data.m5_weeks, data.m5_payment),
    ]
    rows = [header]
    for i, (name, deliverables) in enumerate(zip(MILESTONE_NAMES, MILESTONE_DELIVERABLES)):
        wk, pay = weeks_payments[i]
        rows.append([
            Paragraph(str(i + 1), S["td_center"]),
            Paragraph(f"<b>{name}</b>", S["td"]),
            Paragraph(deliverables, S["td"]),
            Paragraph(f"{wk} wks" if wk else "—", S["td_center"]),
            Paragraph(f"${pay}" if pay else "—", S["td_center"]),
        ])
    rows.append([
        Paragraph("", S["td"]),
        Paragraph("", S["td"]),
        Paragraph("<b>TOTAL</b>", S["td"]),
        Paragraph("", S["td"]),
        Paragraph(f"<b>${data.total_price}</b>", S["td_center"]),
    ])

    t = Table(rows, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0),  (-1, 0),  DARK_BLUE),
        ("TEXTCOLOR",     (0, 0),  (-1, 0),  colors.white),
        ("GRID",          (0, 0),  (-1, -1), 0.5, GRID_COLOR),
        ("ROWBACKGROUNDS",(0, 1),  (-1, -2), [colors.white, STRIPE]),
        ("BACKGROUND",    (0, -1), (-1, -1), LIGHT_BLUE),
        ("VALIGN",        (0, 0),  (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0),  (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0),  (-1, -1), 5),
        ("LEFTPADDING",   (0, 0),  (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0),  (-1, -1), 4),
        ("ALIGN",         (0, 0),  (0, -1),  "CENTER"),
    ]))
    return t


def _tech_table(S: dict) -> Table:
    col_w = [1.6 * inch, 1.9 * inch, 2.8 * inch]
    header = [Paragraph(h, S["th"]) for h in ("Layer", "Technology", "Notes")]
    rows = [header]
    for layer, tech, notes in _TECH_STACK_ROWS:
        rows.append([Paragraph(layer, S["td"]), Paragraph(tech, S["td"]), Paragraph(notes, S["td"])])
    return _styled_table(rows, col_w)


def _styled_table(rows: list, col_widths: list) -> Table:
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, GRID_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, STRIPE]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def _signature_block(data: SOWData, S: dict) -> Table:
    """Two-column signature block with invisible DocuSign anchor strings."""

    def _col(anchor: str, name_val: str, title_val: str) -> Paragraph:
        name_display = name_val or "________________________________"
        title_display = title_val or "________________________________"
        return Paragraph(
            # Invisible anchor text for DocuSign anchor-tab detection
            f'<font color="white" size="4">{anchor}</font><br/><br/>'
            '________________________________<br/>'
            'By:<br/><br/>'
            '________________________________<br/>'
            f'Name:&nbsp;&nbsp;<b>{name_display}</b><br/><br/>'
            '________________________________<br/>'
            f'Title:&nbsp;&nbsp;<b>{title_display}</b><br/><br/>'
            '________________________________<br/>'
            'Date:',
            S["sig"],
        )

    left = _col("TKSOL_CONSULTANT_SIG", data.consultant_name, data.consultant_title)
    right = _col("TKSOL_CLIENT_SIG", data.client_signer_name, data.client_signer_title)

    return Table(
        [[left, right]],
        colWidths=[3.1 * inch, 3.1 * inch],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ]),
    )


# ── Styles ──────────────────────────────────────────────────────────────────────

def _styles() -> dict:
    base = ParagraphStyle("base", fontName="Helvetica", fontSize=10, leading=14)
    return {
        "company": ParagraphStyle(
            "company", parent=base, fontSize=13, fontName="Helvetica-Bold",
            alignment=TA_CENTER, spaceAfter=2,
        ),
        "doc_title": ParagraphStyle(
            "doc_title", parent=base, fontSize=16, fontName="Helvetica-Bold",
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base, fontSize=11, fontName="Helvetica-Bold",
            spaceBefore=8, spaceAfter=4,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base, fontSize=10, fontName="Helvetica-Bold",
            spaceBefore=6, spaceAfter=3, leftIndent=12,
        ),
        "body": ParagraphStyle(
            "body", parent=base, fontSize=9.5, leading=14,
            alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base, fontSize=9.5, leading=14,
            leftIndent=20, spaceAfter=3,
        ),
        "caption": ParagraphStyle(
            "caption", parent=base, fontSize=8.5, leading=12,
            fontName="Helvetica-Oblique", alignment=TA_JUSTIFY,
        ),
        "th": ParagraphStyle(
            "th", parent=base, fontSize=9, fontName="Helvetica-Bold",
            alignment=TA_CENTER, textColor=colors.white,
        ),
        "td": ParagraphStyle(
            "td", parent=base, fontSize=8.5, leading=12,
        ),
        "td_center": ParagraphStyle(
            "td_center", parent=base, fontSize=8.5, leading=12,
            alignment=TA_CENTER,
        ),
        "sig": ParagraphStyle(
            "sig", parent=base, fontSize=9.5, leading=18,
        ),
    }
