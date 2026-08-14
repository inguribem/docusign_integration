"""
Master Services Agreement (MSA) PDF Generator.
Variable fields: consultant_company, consultant_entity_type, consultant_address,
                 client_name, client_entity_type, client_address,
                 effective_day/month/year, payment_terms, late_fee_rate,
                 non_solicitation_term, agreement_term, governing_county.
Fixed content:   Sections 1–17 per TKSOLUTIONS-MSA-v2 template.
"""
from dataclasses import dataclass
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
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


@dataclass
class GenMSAData:
    # Service Provider (Consultant)
    consultant_company: str
    consultant_entity_type: str
    consultant_address: str
    # Client
    client_name: str
    client_entity_type: str
    client_address: str
    # Effective date
    effective_day: str
    effective_month: str
    effective_year: str
    # Variable commercial terms
    non_solicitation_term: str = "1 year"
    agreement_term: str = "1 year"
    governing_county: str = "Miami-Dade"
    # Signature block
    consultant_name: str = ""
    consultant_title: str = ""
    client_signer_name: str = ""
    client_signer_title: str = ""


def generate_gen_msa_pdf(data: GenMSAData) -> bytes:
    """Generate the Master Services Agreement and return its bytes."""
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


def _build_story(data: GenMSAData, S: dict) -> list:
    story = []

    # ── Title block ────────────────────────────────────────────────────────────
    story += [
        Paragraph("MASTER SERVICES AGREEMENT", S["doc_title"]),
        Paragraph(
            "IT Consulting · Software Development · Integrations &amp; Automations",
            S["subtitle"],
        ),
        Paragraph("Governed by the Laws of the State of Florida", S["subtitle2"]),
        HRFlowable(width="100%", thickness=1, color=DARK_BLUE, spaceAfter=10),
    ]

    # ── Preamble ───────────────────────────────────────────────────────────────
    story += [
        Paragraph(
            f'This Master Services Agreement (the "Agreement") is entered into as of this '
            f'<b>{data.effective_day}</b> day of <b>{data.effective_month}</b>, '
            f'<b>{data.effective_year}</b>, by and between:',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── Party table ────────────────────────────────────────────────────────────
    party_table = Table(
        [
            [
                Paragraph("<b>Service Provider /\nConsultant:</b>", S["td_label"]),
                Paragraph(
                    f'<b>{data.consultant_company}</b>, a Florida '
                    f'<b>{data.consultant_entity_type}</b>, with offices at '
                    f'<b>{data.consultant_address}</b> (the "Consultant").',
                    S["td"],
                ),
            ],
            [
                Paragraph("<b>Client:</b>", S["td_label"]),
                Paragraph(
                    f'<b>{data.client_name}</b>, a <b>{data.client_entity_type}</b>, '
                    f'with offices at <b>{data.client_address}</b> (the "Client").',
                    S["td"],
                ),
            ],
        ],
        colWidths=[1.6 * inch, 4.9 * inch],
    )
    party_table.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 0.75, GRID_COLOR),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5,  GRID_COLOR),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    story += [party_table, Spacer(1, 0.08 * inch)]

    story += [
        Paragraph(
            'Individually referred to as a "Party" and collectively as the "Parties".',
            S["body"],
        ),
        Spacer(1, 0.12 * inch),
    ]

    # ── § 1 Definitions ────────────────────────────────────────────────────────
    story += [
        _section_header("1. Definitions", S),
        Paragraph(
            '"<b>Statement of Work" (SOW)</b> means a written document executed by both '
            'Parties describing a specific engagement, including scope, deliverables, timeline, '
            'milestones, and fees. Each SOW is incorporated into and governed by this Agreement.',
            S["body"],
        ),
        Paragraph(
            '<b>"Deliverables"</b> means any software, code, integrations, automations, '
            'documentation, or other work product produced by Consultant specifically for Client '
            'under a SOW.',
            S["body"],
        ),
        Paragraph(
            '<b>"Pre-Existing IP"</b> means any intellectual property, tools, frameworks, '
            'libraries, or methodologies owned or developed by Consultant prior to or '
            'independently of this Agreement.',
            S["body"],
        ),
        Paragraph(
            '<b>"Confidential Information"</b> has the meaning set forth in Section 9 of this '
            'Agreement.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 2 Scope of Services ──────────────────────────────────────────────────
    story += [
        _section_header("2. Scope of Services", S),
        Paragraph(
            'Consultant agrees to provide IT consulting, software development, systems '
            'integration, and automation services (the "Services") as described in one or more '
            'Statements of Work. Each SOW shall specify the scope, deliverables, timeline, '
            'acceptance criteria, and applicable fees.',
            S["body"],
        ),
        Paragraph(
            'In the event of any conflict between this Agreement and a SOW, the terms of the '
            'SOW shall control with respect to that specific engagement only. Any services not '
            'described in a SOW are outside scope and subject to a Change Order or new SOW.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 3 Change Orders ──────────────────────────────────────────────────────
    story += [
        _section_header("3. Change Orders", S),
        Paragraph(
            'Either Party may request changes to the scope, timeline, or deliverables of an '
            'active SOW by submitting a written change request. No change shall be binding until '
            'both Parties execute a written Change Order. Consultant is not obligated to begin '
            'work on requested changes prior to execution of a Change Order.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 4 Fees and Payment ───────────────────────────────────────────────────
    story += [
        _section_header("4. Fees and Payment", S),
        Paragraph(
            'Fees for each engagement shall be set forth in the applicable SOW. Payment may be '
            'structured as: (a) a fixed monthly retainer billed on the first day of each '
            'service month; (b) milestone-based installments tied to defined deliverables; '
            '(c) a deposit of fifty percent (50%) of the total engagement fee due prior to '
            'commencement, with the remaining balance due upon final delivery; or (d) such other '
            'structure as mutually agreed in the applicable SOW. All invoices are due within '
            'fifteen (15) days of receipt unless otherwise specified. Accounts overdue by more '
            'than fifteen (15) days may incur a late fee of 1.5% per month.',
            S["body"],
        ),
        Paragraph(
            'Client shall reimburse Consultant for pre-approved, reasonable, and documented '
            'out-of-pocket expenses. Expenses exceeding $500 individually require prior written '
            'approval from Client.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 5 Acceptance of Deliverables ─────────────────────────────────────────
    story += [
        _section_header("5. Acceptance of Deliverables", S),
        Paragraph(
            'Upon completion of a milestone, Consultant shall notify Client in writing. Client '
            'shall have three (3) business days to provide written acceptance or written notice '
            'of specific deficiencies.',
            S["body"],
        ),
        Paragraph(
            'If Client does not respond within three (3) business days, the deliverable shall '
            'be deemed accepted. Cosmetic or subjective preferences that do not affect '
            'functionality do not constitute valid grounds for rejection.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 6 Intellectual Property and License ──────────────────────────────────
    story += [
        _section_header("6. Intellectual Property and License", S),
        Paragraph(
            '<b>Pre-Existing IP:</b> Consultant retains full ownership of all Pre-Existing IP. '
            'Nothing in this Agreement transfers ownership of Pre-Existing IP to Client.',
            S["body"],
        ),
        Paragraph(
            '<b>Deliverables License:</b> Upon receipt of full payment for the applicable SOW, '
            'Consultant grants Client a perpetual, irrevocable, worldwide, non-exclusive license '
            'to use, modify, and deploy the Deliverables for Client\'s internal business '
            'purposes.',
            S["body"],
        ),
        Paragraph(
            '<b>Third-Party Components:</b> Deliverables may incorporate open-source or '
            'third-party components subject to their own licenses. Client is responsible for '
            'compliance with such third-party license terms.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 7 Independent Contractor ─────────────────────────────────────────────
    story += [
        _section_header("7. Independent Contractor", S),
        Paragraph(
            'Consultant is an independent contractor and not an employee, partner, or agent of '
            'Client. Nothing in this Agreement creates an employment relationship, joint '
            'venture, or partnership. Consultant is solely responsible for all taxes, insurance, '
            'and benefits applicable to its personnel.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 8 Non-Solicitation ───────────────────────────────────────────────────
    non_sol = f"<b>{data.non_solicitation_term}</b>" if data.non_solicitation_term else "<b>______</b>"
    story += [
        _section_header("8. Non-Solicitation", S),
        Paragraph(
            f'During the term of this Agreement and for {non_sol} thereafter, neither Party '
            'shall directly solicit, recruit, or hire the employees, contractors, or consultants '
            'of the other Party who were involved in delivering or receiving Services, without '
            'prior written consent.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 9 Confidentiality ────────────────────────────────────────────────────
    story += [
        _section_header("9. Confidentiality", S),
        Paragraph(
            'All information shared between the Parties in connection with this Agreement and '
            'any SOW shall be presumed confidential regardless of how it is disclosed. Each '
            'Party shall protect the other\'s Confidential Information using commercially and '
            'technically reasonable measures, and shall not disclose it to third parties without '
            'prior written consent except as required by law.',
            S["body"],
        ),
        Paragraph(
            'This confidentiality obligation shall survive termination of this Agreement for a '
            'period of three (3) years, and indefinitely with respect to information that '
            'qualifies as a trade secret under Florida Statutes § 688.002.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 10 Data Security ─────────────────────────────────────────────────────
    story += [
        _section_header("10. Data Security", S),
        Paragraph(
            'To the extent Consultant accesses or processes Client\'s data or systems, '
            'Consultant shall implement commercially and technically reasonable security '
            'measures, including encryption in transit and at rest, and access controls limited '
            'to personnel with a legitimate need to know.',
            S["body"],
        ),
        Paragraph(
            'In the event of a confirmed or suspected data breach involving Client\'s '
            'information, Consultant shall notify Client in writing within forty-eight (48) '
            'hours of discovery and cooperate in good faith to contain and remediate the '
            'incident.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 11 Representations and Warranties ───────────────────────────────────
    story += [
        _section_header("11. Representations and Warranties", S),
        Paragraph(
            'Consultant represents and warrants that: (a) it has the right and authority to '
            'enter into this Agreement; (b) the Deliverables will materially conform to the '
            'specifications in the applicable SOW at the time of acceptance; and (c) to '
            'Consultant\'s knowledge, the Deliverables will not knowingly infringe any '
            'third-party intellectual property rights.',
            S["body"],
        ),
        Paragraph(
            'EXCEPT AS EXPRESSLY SET FORTH ABOVE, CONSULTANT PROVIDES THE SERVICES AND '
            'DELIVERABLES "AS IS" AND DISCLAIMS ALL OTHER WARRANTIES, EXPRESS OR IMPLIED.',
            S["caps"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 12 Limitation of Liability ───────────────────────────────────────────
    story += [
        _section_header("12. Limitation of Liability", S),
        Paragraph(
            'THE TOTAL CUMULATIVE LIABILITY OF EITHER PARTY FOR ANY AND ALL CLAIMS ARISING '
            'OUT OF OR RELATED TO THIS AGREEMENT OR ANY SOW — INCLUDING CLAIMS FOR BREACH OF '
            'CONFIDENTIALITY — SHALL NOT EXCEED TWO (2) TIMES THE TOTAL FEES PAID BY CLIENT '
            'TO CONSULTANT UNDER THE APPLICABLE ENGAGEMENT. THIS CAP APPLIES PER SOW.',
            S["caps"],
        ),
        Paragraph(
            'IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, '
            'PUNITIVE, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, LOSS OF DATA, OR '
            'BUSINESS INTERRUPTION, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. THE '
            'PARTIES ACKNOWLEDGE THAT THESE LIMITATIONS REFLECT A REASONABLE AND NEGOTIATED '
            'ALLOCATION OF RISK.',
            S["caps"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 13 Indemnification ───────────────────────────────────────────────────
    story += [
        _section_header("13. Indemnification", S),
        Paragraph(
            'Each Party ("Indemnifying Party") shall defend, indemnify, and hold harmless the '
            'other Party from third-party claims arising from: (a) material breach of this '
            'Agreement; (b) gross negligence or willful misconduct; or (c) in the case of '
            'Consultant, any claim that the Deliverables infringe a third party\'s intellectual '
            'property rights, provided such claim does not arise from Client\'s modifications or '
            'misuse.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 14 Term and Termination ──────────────────────────────────────────────
    term = f"<b>{data.agreement_term}</b>" if data.agreement_term else "<b>______</b>"
    story += [
        _section_header("14. Term and Termination", S),
        Paragraph(
            f'This Agreement shall commence on the date of execution and remain in effect for '
            f'{term}, automatically renewing for successive one-year terms unless either Party '
            'provides thirty (30) days written notice of non-renewal.',
            S["body"],
        ),
        Paragraph(
            'Either Party may terminate for cause upon written notice if the other Party '
            'materially breaches and fails to cure within fifteen (15) days. Client may '
            'terminate any SOW for convenience upon thirty (30) days written notice, paying for '
            'all Services performed through the termination date plus non-cancellable expenses.',
            S["body"],
        ),
        Paragraph(
            'Upon termination, Sections 6, 8, 9, 10, 12, and 13 shall survive.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 15 Support and Maintenance ───────────────────────────────────────────
    story += [
        _section_header("15. Support and Maintenance", S),
        Paragraph(
            'Ongoing support or maintenance after project acceptance is not included in this '
            'Agreement unless separately agreed in a Support SOW or Retainer Agreement. Bug '
            'fixes related to deficiencies identified within thirty (30) days of acceptance '
            'shall be addressed at no additional charge.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 16 Governing Law and Dispute Resolution ──────────────────────────────
    county = f"<b>{data.governing_county}</b>" if data.governing_county else "<b>______</b>"
    story += [
        _section_header("16. Governing Law and Dispute Resolution", S),
        Paragraph(
            'This Agreement shall be governed by the laws of the <b>State of Florida</b> '
            'without regard to conflict of law provisions. Disputes shall first be attempted to '
            'be resolved through good-faith negotiation within thirty (30) days. If unresolved, '
            f'disputes shall be adjudicated exclusively in the courts of {county} County, '
            'Florida.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 17 Miscellaneous ─────────────────────────────────────────────────────
    story += [
        _section_header("17. Miscellaneous", S),
        Paragraph(
            'This Agreement, together with all executed SOWs, constitutes the entire agreement '
            'between the Parties and supersedes all prior discussions. No amendment shall be '
            'valid unless in writing and signed by both Parties. If any provision is found '
            'unenforceable, the remaining provisions remain in full force. This Agreement may be '
            'executed in counterparts, including via electronic signature platforms. Neither '
            'Party may assign this Agreement without prior written consent, except in connection '
            'with a merger, acquisition, or sale of substantially all assets.',
            S["body"],
        ),
    ]

    # ── Signature block ─────────────────────────────────────────────────────────
    story += [PageBreak(), _signature_block(data, S)]

    return story


def _section_header(title: str, S: dict) -> Table:
    """Section heading with a blue left accent bar matching the PDF design."""
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


def _signature_block(data: GenMSAData, S: dict) -> Table:
    def _col(anchor: str, name_val: str, title_val: str) -> Paragraph:
        name_display  = name_val  or "________________________________"
        title_display = title_val or "________________________________"
        return Paragraph(
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


def _styles() -> dict:
    base = ParagraphStyle("base", fontName="Helvetica", fontSize=10, leading=14)
    return {
        "doc_title": ParagraphStyle(
            "doc_title", parent=base, fontSize=14, fontName="Helvetica-Bold",
            alignment=TA_CENTER, spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base, fontSize=10,
            alignment=TA_CENTER, spaceAfter=2,
        ),
        "subtitle2": ParagraphStyle(
            "subtitle2", parent=base, fontSize=10,
            alignment=TA_CENTER, spaceAfter=6,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base, fontSize=10, fontName="Helvetica-Bold",
            spaceBefore=0, spaceAfter=0,
        ),
        "body": ParagraphStyle(
            "body", parent=base, fontSize=9.5, leading=14,
            alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "caps": ParagraphStyle(
            "caps", parent=base, fontSize=9, leading=13,
            alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "caption": ParagraphStyle(
            "caption", parent=base, fontSize=8.5, leading=12,
            fontName="Helvetica-Oblique", alignment=TA_CENTER,
        ),
        "td_label": ParagraphStyle(
            "td_label", parent=base, fontSize=9.5, leading=14,
            fontName="Helvetica-Bold",
        ),
        "td": ParagraphStyle(
            "td", parent=base, fontSize=9.5, leading=14,
        ),
        "sig": ParagraphStyle(
            "sig", parent=base, fontSize=9.5, leading=18,
        ),
    }
