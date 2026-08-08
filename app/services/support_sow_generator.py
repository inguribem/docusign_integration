"""
Support & Maintenance SOW PDF Generator.
Variable fields: consultant_company, client_name, sow_number, effective_date,
                 project_name, monthly_fee, included_hours, additional_hours_rate,
                 duration_months.
Fixed content:   scope of work, exclusions, deliverables, SLA, client obligations,
                 change order process.
"""
from dataclasses import dataclass
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
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

DARK_BLUE  = colors.HexColor("#1a3a6b")
ACCENT_BAR = colors.HexColor("#2563eb")
GRID_COLOR = colors.HexColor("#cccccc")
HEADER_BG  = colors.HexColor("#1e293b")
STRIPE     = colors.HexColor("#f5f7fa")


@dataclass
class SupportSOWData:
    # Parties
    consultant_company: str
    client_name: str
    # SOW metadata
    sow_number: str = "SOW-2026-001"
    effective_date: str = ""
    # Project
    project_name: str = "Automated Invoice Processing with AI"
    # Commercial terms
    monthly_fee: str = "250"
    included_hours: str = "3"
    additional_hours_rate: str = "75"
    duration_months: str = "12"
    # Signature block
    consultant_name: str = ""
    consultant_title: str = ""
    consultant_email: str = ""
    client_signer_name: str = ""
    client_signer_title: str = ""


def generate_support_sow_pdf(data: SupportSOWData) -> bytes:
    """Generate the Support & Maintenance SOW and return its bytes."""
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


def _build_story(data: SupportSOWData, S: dict) -> list:
    story = []

    # ── Header ─────────────────────────────────────────────────────────────────
    story += [
        Paragraph(data.consultant_company.upper(), S["company"]),
        Paragraph(
            f'STATEMENT OF WORK — {data.client_name.upper()}',
            S["doc_title"],
        ),
        Paragraph("Standard Plan — Maintenance &amp; Support", S["subtitle"]),
        Paragraph(f'<b>{data.project_name}</b>', S["project_name"]),
        HRFlowable(width="100%", thickness=1, color=DARK_BLUE, spaceAfter=6),
    ]

    # ── SOW metadata line ──────────────────────────────────────────────────────
    eff = data.effective_date or "_________________, 2026"
    story += [
        Paragraph(
            f'SOW No.: <b>{data.sow_number}</b>&nbsp;&nbsp;|&nbsp;&nbsp;'
            f'Effective Date: <b>{eff}</b>',
            S["meta"],
        ),
        Spacer(1, 0.08 * inch),
    ]

    # ── Plan summary banner ────────────────────────────────────────────────────
    banner = Table(
        [[
            Paragraph(
                "STANDARD PLAN — Maintenance &amp; Support",
                S["banner_left"],
            ),
            Paragraph(
                f'<b>${data.monthly_fee}/month · Fixed rate</b>',
                S["banner_right"],
            ),
        ]],
        colWidths=[3.8 * inch, 2.7 * inch],
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), ACCENT_BAR),
        ("TEXTCOLOR",     (0, 0), (-1, -1), colors.white),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (0, 0),   14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("ALIGN",         (1, 0), (1, 0),   "RIGHT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story += [banner, Spacer(1, 0.18 * inch)]

    # ── § 1 Overview ───────────────────────────────────────────────────────────
    story += [
        _section_header("1. OVERVIEW", S),
        Paragraph(
            f'This Statement of Work ("<b>SOW</b>") is entered into pursuant to the Master '
            f'Services Agreement ("<b>MSA</b>") dated <b>{eff}</b> between '
            f'<b>{data.consultant_company}</b> ("<b>Service Provider</b>") and '
            f'<b>{data.client_name}</b> ("<b>Client</b>"). In the event of any conflict between '
            f'this SOW and the MSA, the MSA shall control except where this SOW expressly states '
            f'otherwise.',
            S["body"],
        ),
        Paragraph(
            f'This SOW governs the delivery of <b>Standard Plan — Maintenance &amp; Support</b> '
            f'services for the <b>{data.project_name}</b> platform.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 2 Points of Contact ──────────────────────────────────────────────────
    story += [
        _section_header("2. POINTS OF CONTACT", S),
        _contacts_table(data, S),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 3 Scope of Work ─────────────────────────────────────────────────────
    story += [
        _section_header("3. SCOPE OF WORK", S),
        Paragraph(
            "Service Provider will perform the following services under the Standard Plan:",
            S["body"],
        ),
    ]
    scope_items = [
        "24/7 automated monitoring of all platform components (WhatsApp webhook, OpenAI API, "
        "Google Drive sync, PostgreSQL database).",
        "Critical error alerts via email and/or WhatsApp notification upon detection of system "
        "failures, processing errors, or API disruptions.",
        "Monthly status report delivered by the 5th business day of each month, covering: "
        "system uptime, invoice processing volume, errors detected, API health, support hours "
        "used, and recommendations.",
        "Third-party API and dependency changelog tracking with proactive compatibility updates "
        "applied before breaking changes affect production.",
        f'Up to <b>{data.included_hours} hours per month</b> of remote technical support, '
        f'applicable to: error diagnosis and resolution, system configuration adjustments, '
        f'notification routing changes, and data validation rule updates.',
        "Monthly support hour utilization report included in the status report.",
    ]
    for i, item in enumerate(scope_items, 1):
        story.append(Paragraph(f'<b>{i}.</b> {item}', S["numbered"]))
    story.append(Spacer(1, 0.1 * inch))

    # ── § 4 Exclusions ─────────────────────────────────────────────────────────
    story += [
        _section_header("4. EXCLUSIONS — NOT IN SCOPE", S),
        Paragraph(
            "The following are expressly excluded from this SOW. Any out-of-scope work requires "
            "a written Change Order signed by both parties.",
            S["body"],
        ),
    ]
    exclusions = [
        f'Support hours in excess of {data.included_hours} per month '
        f'(billed at ${data.additional_hours_rate}/hr with prior written approval).',
        "Minor or major workflow changes, new logic, or structural modifications.",
        "AI prompt review or optimization.",
        "New feature development or new integrations.",
        "On-site support of any kind.",
    ]
    for item in exclusions:
        story.append(Paragraph(f'● {item}', S["bullet"]))
    story.append(Spacer(1, 0.1 * inch))

    # ── § 5 Deliverables ───────────────────────────────────────────────────────
    story += [
        _section_header("5. DELIVERABLES", S),
        _deliverables_table(S),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 6 Service Level Agreement ────────────────────────────────────────────
    story += [
        _section_header("6. SERVICE LEVEL AGREEMENT (SLA)", S),
        _sla_table(S),
        Spacer(1, 0.04 * inch),
        Paragraph(
            "Response times are measured from the moment the issue is reported or detected by "
            "monitoring. Response time constitutes acknowledgment and initiation of "
            "investigation, not resolution.",
            S["caption"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 7 Fees and Payment ───────────────────────────────────────────────────
    story += [
        _section_header("7. FEES AND PAYMENT", S),
        _fees_table(data, S),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 8 Term and Termination ───────────────────────────────────────────────
    dur = data.duration_months or "twelve (12)"
    story += [
        _section_header("8. TERM AND TERMINATION", S),
        Paragraph(
            f'This SOW is effective as of <b>{eff}</b> and continues for an initial term of '
            f'<b>{dur} months</b>, after which it automatically renews on a month-to-month '
            f'basis unless either Party provides thirty (30) days written notice of '
            f'non-renewal. Termination for convenience or cause is governed by the MSA.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 9 Client Obligations ─────────────────────────────────────────────────
    story += [
        _section_header("9. CLIENT OBLIGATIONS", S),
    ]
    obligations = [
        "Maintain active and valid accounts for all third-party services used by the platform "
        "(WhatsApp Business API, OpenAI, Google Drive).",
        "Provide Service Provider with continued access to all systems, credentials, and "
        "environments required to perform the Services.",
        "Designate a primary point of contact responsible for approving Change Orders and "
        "responding to Service Provider inquiries within 2 business days.",
        "Promptly notify Service Provider of any platform changes, credential rotations, or "
        "business process modifications that may affect platform operation.",
        "Pay all invoices in accordance with Section 7.",
    ]
    for i, item in enumerate(obligations, 1):
        story.append(Paragraph(f'<b>{i}.</b> {item}', S["numbered"]))
    story.append(Spacer(1, 0.1 * inch))

    # ── § 10 Change Order Process ──────────────────────────────────────────────
    story += [
        _section_header("10. CHANGE ORDER PROCESS", S),
        Paragraph(
            "Any work outside the scope defined in Section 3 must be formalized through a "
            "written Change Order prior to commencement. Change Orders must specify: description "
            "of work, estimated hours, additional fees, and revised timeline. Both parties must "
            "sign the Change Order before Service Provider begins out-of-scope work.",
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── Signature block ─────────────────────────────────────────────────────────
    story += [
        HRFlowable(width="100%", thickness=0.5, color=GRID_COLOR, spaceAfter=6),
        Paragraph("SIGNATURES", S["sig_header"]),
        Paragraph(
            "By signing below, both parties agree to the terms and conditions of this "
            "Statement of Work.",
            S["body"],
        ),
        Spacer(1, 0.12 * inch),
        _signature_block(data, S),
        Spacer(1, 0.3 * inch),
        Paragraph(
            f'{data.consultant_company} — Confidential · {data.sow_number} · teknowsolutions.com',
            S["footer"],
        ),
    ]

    return story


# ── Section helpers ─────────────────────────────────────────────────────────────

def _section_header(title: str, S: dict) -> Table:
    t = Table(
        [[Paragraph("", S["body"]), Paragraph(title, S["h1"])]],
        colWidths=[0.1 * inch, 5.9 * inch],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0), ACCENT_BAR),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (1, 0), (1, 0), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _contacts_table(data: SupportSOWData, S: dict) -> Table:
    header = [Paragraph(h, S["th"]) for h in ("Role", "Party", "Name", "Email")]
    rows = [
        header,
        [
            Paragraph("Service Manager", S["td"]),
            Paragraph(data.consultant_company, S["td"]),
            Paragraph(data.consultant_name or "___________________", S["td"]),
            Paragraph(data.consultant_email or "___________________", S["td"]),
        ],
        [
            Paragraph("Client Contact", S["td"]),
            Paragraph(data.client_name, S["td"]),
            Paragraph(data.client_signer_name or "___________________", S["td"]),
            Paragraph("___________________", S["td"]),
        ],
    ]
    t = Table(rows, colWidths=[1.3 * inch, 1.7 * inch, 1.5 * inch, 2.0 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  HEADER_BG),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("GRID",          (0, 0), (-1, -1), 0.5, GRID_COLOR),
        ("BACKGROUND",    (0, 2), (-1, 2),  STRIPE),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return t


def _deliverables_table(S: dict) -> Table:
    header = [Paragraph(h, S["th"]) for h in ("Deliverable", "Frequency", "Format")]
    rows = [
        header,
        [
            Paragraph("Monthly Status Report", S["td_bold"]),
            Paragraph("Monthly, by the 5th business day", S["td"]),
            Paragraph("Email (PDF)", S["td"]),
        ],
        [
            Paragraph("Alert Notifications", S["td_bold"]),
            Paragraph("Upon detection", S["td"]),
            Paragraph("Email / WhatsApp", S["td"]),
        ],
        [
            Paragraph("Support Hour Usage Summary", S["td_bold"]),
            Paragraph("Included in monthly report", S["td"]),
            Paragraph("Email (PDF)", S["td"]),
        ],
    ]
    t = Table(rows, colWidths=[2.2 * inch, 2.2 * inch, 2.1 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  HEADER_BG),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("GRID",          (0, 0), (-1, -1), 0.5, GRID_COLOR),
        ("BACKGROUND",    (0, 2), (-1, 2),  STRIPE),
        ("BACKGROUND",    (0, 4), (-1, 4),  STRIPE),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return t


def _sla_table(S: dict) -> Table:
    header = [Paragraph(h, S["th"]) for h in ("Severity", "Description", "Response Time")]
    rows = [
        header,
        [
            Paragraph("<b>Critical</b>", S["td_bold"]),
            Paragraph("Platform down or invoices not processing", S["td"]),
            Paragraph("<b>24–48 hours</b>", S["td_center"]),
        ],
        [
            Paragraph("<b>High</b>", S["td_bold"]),
            Paragraph("Data extraction errors / notification failures", S["td"]),
            Paragraph("48 hours", S["td_center"]),
        ],
        [
            Paragraph("<b>Medium</b>", S["td_bold"]),
            Paragraph("Minor adjustments / technical inquiries", S["td"]),
            Paragraph("72 hours", S["td_center"]),
        ],
        [
            Paragraph("<b>Low</b>", S["td_bold"]),
            Paragraph("Requested improvements or changes", S["td"]),
            Paragraph("N/A", S["td_center"]),
        ],
    ]
    t = Table(rows, colWidths=[1.1 * inch, 3.4 * inch, 2.0 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  HEADER_BG),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("GRID",          (0, 0), (-1, -1), 0.5, GRID_COLOR),
        ("BACKGROUND",    (0, 2), (-1, 2),  STRIPE),
        ("BACKGROUND",    (0, 4), (-1, 4),  STRIPE),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("ALIGN",         (2, 1), (2, -1),  "CENTER"),
    ]))
    return t


def _fees_table(data: SupportSOWData, S: dict) -> Table:
    rows = [
        [Paragraph("<b>Monthly Service Fee</b>", S["td_bold"]),
         Paragraph(f'${data.monthly_fee}/month, fixed rate', S["td"])],
        [Paragraph("<b>Billing Cycle</b>", S["td_bold"]),
         Paragraph("Monthly, invoiced in advance on the 1st of each month", S["td"])],
        [Paragraph("<b>Payment Due</b>", S["td_bold"]),
         Paragraph("Within 5 business days of invoice date", S["td"])],
        [Paragraph("<b>Payment Method</b>", S["td_bold"]),
         Paragraph("Bank transfer (ACH) or corporate credit card", S["td"])],
        [Paragraph("<b>Additional Hours</b>", S["td_bold"]),
         Paragraph(
             f'${data.additional_hours_rate}/hr — requires written pre-approval before work begins',
             S["td"],
         )],
        [Paragraph("<b>Third-Party API Costs</b>", S["td_bold"]),
         Paragraph(
             "Billed separately and are Client's responsibility "
             "(OpenAI, WhatsApp Business, Google)",
             S["td"],
         )],
    ]
    t = Table(rows, colWidths=[2.0 * inch, 4.5 * inch])
    t.setStyle(TableStyle([
        ("GRID",          (0, 0), (-1, -1), 0.5, GRID_COLOR),
        ("BACKGROUND",    (0, 1), (-1, 1),  STRIPE),
        ("BACKGROUND",    (0, 3), (-1, 3),  STRIPE),
        ("BACKGROUND",    (0, 5), (-1, 5),  STRIPE),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    return t


def _signature_block(data: SupportSOWData, S: dict) -> Table:
    def _col(anchor: str, name_val: str, title_val: str) -> Paragraph:
        name_display  = name_val  or "________________________________"
        title_display = title_val or "________________________________"
        return Paragraph(
            f'<font color="white" size="4">{anchor}</font><br/><br/>'
            '________________________________<br/>'
            'Authorized Signature<br/><br/>'
            '________________________________<br/>'
            f'Name:&nbsp;&nbsp;<b>{name_display}</b><br/><br/>'
            '________________________________<br/>'
            f'Title:&nbsp;&nbsp;<b>{title_display}</b><br/><br/>'
            '________________________________<br/>'
            'Date:',
            S["sig"],
        )

    left  = _col("TKSOL_CONSULTANT_SIG", data.consultant_name,  data.consultant_title)
    right = _col("TKSOL_CLIENT_SIG",     data.client_signer_name, data.client_signer_title)

    return Table(
        [[left, right]],
        colWidths=[3.1 * inch, 3.1 * inch],
        style=TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ]),
    )


# ── Styles ──────────────────────────────────────────────────────────────────────

def _styles() -> dict:
    base = ParagraphStyle("base", fontName="Helvetica", fontSize=10, leading=14)
    return {
        "company": ParagraphStyle(
            "company", parent=base, fontSize=11, fontName="Helvetica-Bold",
            alignment=TA_LEFT, spaceAfter=1,
        ),
        "doc_title": ParagraphStyle(
            "doc_title", parent=base, fontSize=13, fontName="Helvetica-Bold",
            alignment=TA_LEFT, spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base, fontSize=10,
            alignment=TA_LEFT, spaceAfter=2,
        ),
        "project_name": ParagraphStyle(
            "project_name", parent=base, fontSize=10,
            alignment=TA_LEFT, spaceAfter=6,
        ),
        "meta": ParagraphStyle(
            "meta", parent=base, fontSize=9, leading=13,
            alignment=TA_LEFT, spaceAfter=4,
        ),
        "banner_left": ParagraphStyle(
            "banner_left", parent=base, fontSize=10, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_LEFT,
        ),
        "banner_right": ParagraphStyle(
            "banner_right", parent=base, fontSize=11, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_RIGHT,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base, fontSize=10, fontName="Helvetica-Bold",
            spaceBefore=0, spaceAfter=0,
        ),
        "body": ParagraphStyle(
            "body", parent=base, fontSize=9.5, leading=14,
            alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "numbered": ParagraphStyle(
            "numbered", parent=base, fontSize=9.5, leading=14,
            leftIndent=16, spaceAfter=4, alignment=TA_JUSTIFY,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base, fontSize=9.5, leading=14,
            leftIndent=16, spaceAfter=3,
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
        "td_bold": ParagraphStyle(
            "td_bold", parent=base, fontSize=8.5, leading=12,
            fontName="Helvetica-Bold",
        ),
        "td_center": ParagraphStyle(
            "td_center", parent=base, fontSize=8.5, leading=12,
            alignment=TA_CENTER,
        ),
        "sig_header": ParagraphStyle(
            "sig_header", parent=base, fontSize=9, fontName="Helvetica-Bold",
            spaceAfter=4, textColor=colors.HexColor("#64748b"),
        ),
        "sig": ParagraphStyle(
            "sig", parent=base, fontSize=9.5, leading=18,
        ),
        "footer": ParagraphStyle(
            "footer", parent=base, fontSize=8, leading=11,
            fontName="Helvetica-Oblique", alignment=TA_CENTER,
            textColor=colors.HexColor("#94a3b8"),
        ),
    }
