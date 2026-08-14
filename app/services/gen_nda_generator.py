"""
Mutual Non-Disclosure Agreement (NDA) PDF Generator.
Variable fields: consultant_company, consultant_entity_type, consultant_address,
                 client_name, client_entity_type, client_address,
                 effective_day/month/year, agreement_term, non_solicitation_term,
                 governing_county.
Fixed content:   Sections 1–13 per TKSOLUTIONS-NDA_v4 template.
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
class GenNDAData:
    # Disclosing Party (Consultant)
    consultant_company: str
    consultant_entity_type: str
    consultant_address: str
    # Receiving Party (Client)
    client_name: str
    client_entity_type: str
    client_address: str
    # Effective date
    effective_day: str
    effective_month: str
    effective_year: str
    # Variable terms
    agreement_term: str = "2 years"
    non_solicitation_term: str = "1 year"
    governing_county: str = "Miami-Dade"
    # Signature block
    consultant_name: str = ""
    consultant_title: str = ""
    client_signer_name: str = ""
    client_signer_title: str = ""


def generate_gen_nda_pdf(data: GenNDAData) -> bytes:
    """Generate the Mutual NDA and return its bytes."""
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


def _build_story(data: GenNDAData, S: dict) -> list:
    story = []

    # ── Title block ────────────────────────────────────────────────────────────
    story += [
        Paragraph("MUTUAL NON-DISCLOSURE AGREEMENT", S["doc_title"]),
        Paragraph("Governed by the Laws of the State of Florida", S["subtitle"]),
        HRFlowable(width="100%", thickness=1, color=DARK_BLUE, spaceAfter=10),
    ]

    # ── Preamble ───────────────────────────────────────────────────────────────
    story += [
        Paragraph(
            f'This Non-Disclosure Agreement (the "Agreement") is entered into as of this '
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
                Paragraph("<b>Disclosing Party /\nConsultant:</b>", S["td_label"]),
                Paragraph(
                    f'<b>{data.consultant_company}</b>, a Florida '
                    f'<b>{data.consultant_entity_type}</b>, '
                    f'with offices at <b>{data.consultant_address}</b>.',
                    S["td"],
                ),
            ],
            [
                Paragraph("<b>Receiving Party /\nClient:</b>", S["td_label"]),
                Paragraph(
                    f'<b>{data.client_name}</b>, a <b>{data.client_entity_type}</b>, '
                    f'with offices at <b>{data.client_address}</b>.',
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

    # ── § 1 Purpose ────────────────────────────────────────────────────────────
    story += [
        _section_header("1. Purpose", S),
        Paragraph(
            'The Parties wish to explore a potential business relationship or engagement '
            '(the "Purpose"), including but not limited to the provision of IT consulting, '
            'software development, systems integration, or managed services, in connection with '
            'which either Party may disclose its Confidential Information to the other Party.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 2 Definition of Confidential Information ────────────────────────────
    story += [
        _section_header("2. Definition of Confidential Information", S),
        Paragraph(
            '"Confidential Information" means any non-public information, technical data, or '
            'know-how disclosed by one Party to the other in connection with the Purpose, '
            'including but not limited to: trade secrets; source code, object code, and software '
            'algorithms; system architecture, network configurations, and infrastructure designs; '
            'API keys, credentials, and access tokens; research, product plans, customer lists, '
            'pricing, financial data, and business strategies.',
            S["body"],
        ),
        Paragraph(
            '<b>Presumption of Confidentiality:</b> All information shared between the Parties '
            'in the context of the Purpose — whether disclosed in writing, orally, electronically, '
            'or by inspection — shall be presumed confidential and subject to the protections of '
            'this Agreement, unless the disclosing Party expressly indicates otherwise in writing '
            'at the time of disclosure.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 3 Non-Disclosure and Non-Use ─────────────────────────────────────────
    story += [
        _section_header("3. Non-Disclosure and Non-Use", S),
        Paragraph(
            'Each Party agrees not to use the Confidential Information of the other Party for '
            'any purpose other than evaluating or advancing the Purpose. Each Party shall protect '
            'such information using at least the same degree of care it uses to protect its own '
            'confidential information, but in no event less than reasonable care. Neither Party '
            'shall disclose Confidential Information to any third party without the prior written '
            'consent of the disclosing Party, except to its employees, contractors, or advisors '
            'who have a need to know and are bound by confidentiality obligations no less '
            'restrictive than those herein.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 4 Permitted Disclosures ───────────────────────────────────────────────
    story += [
        _section_header("4. Permitted Disclosures", S),
        Paragraph(
            'The obligations of Section 3 shall not apply to information that: (a) is or becomes '
            'publicly available through no fault of the receiving Party; (b) was rightfully known '
            'to the receiving Party prior to disclosure; (c) is independently developed by the '
            'receiving Party without use of Confidential Information; or (d) is required to be '
            'disclosed by law, regulation, or court order, provided the receiving Party gives '
            'prompt written notice to the disclosing Party and cooperates in seeking a protective '
            'order.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 5 Data Security and Breach Notification ──────────────────────────────
    story += [
        _section_header("5. Data Security and Breach Notification", S),
        Paragraph(
            'Each Party shall implement and maintain commercially and technically reasonable '
            'security measures appropriate to the nature and sensitivity of the Confidential '
            'Information, in order to protect it against unauthorized access, disclosure, '
            'alteration, or destruction. Such measures shall include, at minimum: (a) encryption '
            'of Confidential Information in transit and at rest; (b) access controls limiting '
            'disclosure to personnel with a legitimate need to know; and (c) reasonable '
            'precautions consistent with current industry practices for information of similar '
            'sensitivity.',
            S["body"],
        ),
        Paragraph(
            "In the event of a confirmed or reasonably suspected unauthorized access, disclosure, "
            "or breach involving the other Party's Confidential Information, the affected Party "
            "shall: (i) notify the other Party in writing within forty-eight (48) hours of "
            "discovery; (ii) provide a description of the nature of the breach, data involved, "
            "and likely impact; and (iii) promptly take all reasonable steps to contain, "
            "investigate, and remediate the breach at its own expense.",
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 6 Intellectual Property ───────────────────────────────────────────────
    story += [
        _section_header("6. Intellectual Property", S),
        Paragraph(
            "Nothing in this Agreement grants either Party any license, title, or ownership "
            "interest in the other Party's Confidential Information, intellectual property, "
            "source code, or proprietary technology. All pre-existing intellectual property "
            "remains the exclusive property of its owner. Any work product or developments "
            "created in connection with the Purpose shall be addressed in a separate written "
            "agreement.",
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 7 Return or Destruction of Information ───────────────────────────────
    story += [
        _section_header("7. Return or Destruction of Information", S),
        Paragraph(
            'Upon written request by the disclosing Party, or upon termination of this '
            'Agreement, the receiving Party shall promptly return or certifiably destroy all '
            'Confidential Information and any copies, notes, or summaries thereof, including '
            'data stored electronically. The receiving Party shall provide written certification '
            'of destruction within ten (10) business days of such request.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 8 Non-Solicitation ───────────────────────────────────────────────────
    non_sol = f"<b>{data.non_solicitation_term}</b>" if data.non_solicitation_term else "<b>______</b>"
    story += [
        _section_header("8. Non-Solicitation", S),
        Paragraph(
            f'During the term of this Agreement and for {non_sol} thereafter, neither '
            'Party shall directly solicit, recruit, or hire any employee, contractor, or '
            'consultant of the other Party who was involved in the Purpose, nor solicit the '
            'clients or customers of the other Party that were introduced through this '
            'engagement, without prior written consent. This restriction does not apply to '
            "general employment advertisements not targeted at the other Party's personnel.",
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 9 Limitation of Liability ────────────────────────────────────────────
    story += [
        _section_header("9. Limitation of Liability", S),
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

    # ── § 10 Injunctive Relief ─────────────────────────────────────────────────
    story += [
        _section_header("10. Injunctive Relief", S),
        Paragraph(
            'Each Party acknowledges that any breach or threatened breach of this Agreement may '
            'cause irreparable harm for which monetary damages would be an inadequate remedy. '
            'Accordingly, in addition to any other legal or equitable remedies available, and '
            'notwithstanding the limitations set forth in Section 9, either Party shall be '
            'entitled to seek immediate injunctive relief or specific performance in any court '
            'of competent jurisdiction without the requirement of posting a bond or proving '
            'actual damages. The pursuit of injunctive relief shall not be deemed a waiver of '
            'the monetary caps established in Section 9.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 11 Term and Termination ──────────────────────────────────────────────
    term = f"<b>{data.agreement_term}</b>" if data.agreement_term else "<b>______</b>"
    story += [
        _section_header("11. Term and Termination", S),
        Paragraph(
            f'This Agreement shall remain in effect for {term} from the date of execution. '
            'Either Party may terminate this Agreement upon thirty (30) days written notice. '
            'Upon termination, Sections 3, 5, 6, 7, 8, 9, and 10 shall survive. The obligations '
            'of confidentiality with respect to Trade Secrets shall survive termination '
            'indefinitely under Florida Statutes § 688.002.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 12 Governing Law and Dispute Resolution ──────────────────────────────
    county = f"<b>{data.governing_county}</b>" if data.governing_county else "<b>______</b>"
    story += [
        _section_header("12. Governing Law and Dispute Resolution", S),
        Paragraph(
            'This Agreement shall be governed by the laws of the <b>State of Florida</b> without '
            'regard to its conflict of law provisions, and shall apply to all Parties regardless '
            'of their jurisdiction of formation or principal place of business. Any disputes shall '
            'first be attempted to be resolved through good-faith negotiation within thirty (30) '
            f'days of written notice. If unresolved, disputes shall be adjudicated exclusively '
            f'in the state or federal courts of {county} County, Florida.',
            S["body"],
        ),
        Spacer(1, 0.1 * inch),
    ]

    # ── § 13 Miscellaneous ─────────────────────────────────────────────────────
    story += [
        _section_header("13. Miscellaneous", S),
        Paragraph(
            'This Agreement constitutes the entire agreement between the Parties with respect '
            'to its subject matter and supersedes all prior discussions or agreements. No '
            'amendment shall be valid unless in writing and signed by both Parties. If any '
            'provision is found unenforceable, the remaining provisions shall remain in full '
            'force. This Agreement may be executed in counterparts, including via electronic '
            'signature platforms (e.g., DocuSign), each of which shall constitute an original. '
            'Notices under this Agreement shall be delivered via email with read-receipt or '
            'certified mail to the addresses set forth above.',
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


def _signature_block(data: GenNDAData, S: dict) -> Table:
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
