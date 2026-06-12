"""
DocuSign Service — lógica de negocio para envío y gestión de contratos.
Soporta: NDA, MSA, SOW via templates o PDFs dinámicos.
"""
import base64
from pathlib import Path
from typing import Optional

from docusign_esign import (
    EnvelopesApi,
    TemplatesApi,
    EnvelopeDefinition,
    Document,
    Signer,
    SignHere,
    DateSigned,
    Tabs,
    Recipients,
    TemplateRole,
    Text,
)
from docusign_esign.client.api_exception import ApiException

from app.config.settings import get_settings
from app.services.docusign_auth import get_api_client

settings = get_settings()


# ─────────────────────────────────────────────
# Modelos internos
# ─────────────────────────────────────────────

class RecipientInfo:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email


class EnvelopeResult:
    def __init__(self, envelope_id: str, status: str, redirect_url: Optional[str] = None):
        self.envelope_id = envelope_id
        self.status = status
        self.redirect_url = redirect_url  # Solo si es embedded signing


# ─────────────────────────────────────────────
# Opción A: Enviar via Template de DocuSign
# (Recomendado para NDA, MSA, SOW estandarizados)
# ─────────────────────────────────────────────

def send_envelope_from_template(
    template_id: str,
    recipient: RecipientInfo,
    role_name: str = "Client",
    tab_values: Optional[dict] = None,
    client_user_id: Optional[str] = None,
) -> EnvelopeResult:
    """
    Envía un envelope usando un template pre-configurado en DocuSign.
    El cliente recibe un email para firmar.

    tab_values: dict con los valores de los Text Tabs del template.
      La key debe coincidir exactamente con el tabLabel definido en DocuSign.
      Ejemplo para el NDA:
        {
          "company_name": "Acme IT Consulting LLC",
          "company_address": "123 Main St, Miami FL 33101",
          "effective_date": "June 3, 2026",
          "agreement_term": "2 years",
          "governing_county": "Miami-Dade",
        }

    client_user_id must be set for embedded signing (recipient view).
    """
    api_client = get_api_client()
    envelopes_api = EnvelopesApi(api_client)

    # Pre-llenar los Text Tabs del template con los valores proporcionados
    tabs = None
    if tab_values:
        text_tabs = [
            Text(tab_label=label, value=str(value))
            for label, value in tab_values.items()
        ]
        tabs = Tabs(text_tabs=text_tabs)

    template_role = TemplateRole(
        email=recipient.email,
        name=recipient.name,
        role_name=role_name,
        client_user_id=client_user_id,
        tabs=tabs,
    )

    envelope_definition = EnvelopeDefinition(
        status="sent",
        template_id=template_id,
        template_roles=[template_role],
    )

    try:
        result = envelopes_api.create_envelope(
            account_id=settings.docusign_account_id,
            envelope_definition=envelope_definition,
        )
        return EnvelopeResult(envelope_id=result.envelope_id, status=result.status)
    except ApiException as e:
        raise RuntimeError(f"DocuSign API error: {e.body}") from e


# ─────────────────────────────────────────────
# Opción B: Enviar PDF dinámico con firma embebida
# (Para cuando generas el PDF en tu sistema)
# ─────────────────────────────────────────────

def send_envelope_from_pdf(
    pdf_path: str,
    document_name: str,
    recipient: RecipientInfo,
    sign_page: int = 1,
    sign_x_position: str = "100",
    sign_y_position: str = "700",
) -> EnvelopeResult:
    """
    Envía un PDF generado por tu sistema para firma.
    El cliente recibe email con el link para firmar.
    """
    api_client = get_api_client()
    envelopes_api = EnvelopesApi(api_client)

    # Leer y encodear PDF en base64
    pdf_bytes = Path(pdf_path).read_bytes()
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

    document = Document(
        document_base64=pdf_b64,
        name=document_name,
        file_extension="pdf",
        document_id="1",
    )

    # Posición del campo de firma en el documento
    sign_here = SignHere(
        document_id="1",
        page_number=str(sign_page),
        recipient_id="1",
        x_position=sign_x_position,
        y_position=sign_y_position,
    )

    signer = Signer(
        email=recipient.email,
        name=recipient.name,
        recipient_id="1",
        routing_order="1",
        tabs=Tabs(sign_here_tabs=[sign_here]),
    )

    envelope_definition = EnvelopeDefinition(
        email_subject=f"Por favor firma: {document_name}",
        documents=[document],
        recipients=Recipients(signers=[signer]),
        status="sent",
    )

    try:
        result = envelopes_api.create_envelope(
            account_id=settings.docusign_account_id,
            envelope_definition=envelope_definition,
        )
        return EnvelopeResult(envelope_id=result.envelope_id, status=result.status)
    except ApiException as e:
        raise RuntimeError(f"DocuSign API error: {e.body}") from e


# ─────────────────────────────────────────────
# Envío de PDF local con firma secuencial (sin template en DocuSign)
# ─────────────────────────────────────────────

def send_pdf_sequential(
    pdf_path: str,
    document_name: str,
    consultant: RecipientInfo,
    client: RecipientInfo,
    sign_page: int = 2,
    consultant_sign_x: str = "100",
    consultant_sign_y: str = "160",
    client_sign_x: str = "380",
    client_sign_y: str = "160",
) -> EnvelopeResult:
    """
    Envía un PDF local a DocuSign con firma secuencial:
      1. Consultant firma primero (routing_order=1)
      2. Client firma después (routing_order=2)
    No requiere template configurado en DocuSign.
    """
    api_client = get_api_client()
    envelopes_api = EnvelopesApi(api_client)

    pdf_b64 = base64.b64encode(Path(pdf_path).read_bytes()).decode("utf-8")
    document = Document(
        document_base64=pdf_b64,
        name=document_name,
        file_extension="pdf",
        document_id="1",
    )

    consultant_signer = Signer(
        email=consultant.email,
        name=consultant.name,
        recipient_id="1",
        routing_order="1",
        tabs=Tabs(sign_here_tabs=[SignHere(
            document_id="1",
            page_number=str(sign_page),
            recipient_id="1",
            x_position=consultant_sign_x,
            y_position=consultant_sign_y,
        )]),
    )

    client_signer = Signer(
        email=client.email,
        name=client.name,
        recipient_id="2",
        routing_order="2",
        tabs=Tabs(sign_here_tabs=[SignHere(
            document_id="1",
            page_number=str(sign_page),
            recipient_id="2",
            x_position=client_sign_x,
            y_position=client_sign_y,
        )]),
    )

    envelope_definition = EnvelopeDefinition(
        email_subject=f"Please sign: {document_name}",
        documents=[document],
        recipients=Recipients(signers=[consultant_signer, client_signer]),
        status="sent",
    )

    try:
        result = envelopes_api.create_envelope(
            account_id=settings.docusign_account_id,
            envelope_definition=envelope_definition,
        )
        return EnvelopeResult(envelope_id=result.envelope_id, status=result.status)
    except ApiException as e:
        raise RuntimeError(f"DocuSign API error: {e.body}") from e


# ─────────────────────────────────────────────
# Opción C: Firma secuencial (Consultant → Client)
# El consultor firma primero; DocuSign envía al cliente
# automáticamente cuando el consultor completa su firma.
# ─────────────────────────────────────────────

def send_sequential_envelope(
    template_id: str,
    consultant: RecipientInfo,
    client: RecipientInfo,
    consultant_role: str = "Consultant",
    client_role: str = "Client",
    document_tabs: Optional[dict] = None,
    consultant_sign_tabs: Optional[dict] = None,
    client_sign_tabs: Optional[dict] = None,
    email_subject: Optional[str] = None,
) -> EnvelopeResult:
    """
    Crea un envelope con dos firmantes en orden secuencial:
      1. Consultant (routing_order=1) — firma primero
      2. Client     (routing_order=2) — firma después

    document_tabs:      campos del cuerpo del documento (van al rol Client como locked)
    consultant_sign_tabs: campos del bloque de firma del consultor (van al rol Consultant)
    client_sign_tabs:     campos del bloque de firma del cliente (van al rol Client, locked)
    """
    api_client = get_api_client()
    envelopes_api = EnvelopesApi(api_client)

    # Tabs del bloque de firma del consultor (pre-llenados, no bloqueados)
    consultant_tabs = Tabs(text_tabs=[
        Text(tab_label=k, value=str(v))
        for k, v in (consultant_sign_tabs or {}).items()
    ])

    # Cuerpo del documento → bloqueados (el cliente no puede editar los términos)
    doc_text_tabs = [
        Text(tab_label=k, value=str(v), locked="true")
        for k, v in (document_tabs or {}).items()
    ]
    # Bloque de firma del cliente → pre-llenados pero SIN bloquear.
    # DocuSign ignora locked="true" en signature-area tabs; sin bloqueo
    # el valor se pre-llena y el signer puede confirmarlo o corregirlo.
    sign_text_tabs = [
        Text(tab_label=k, value=str(v))
        for k, v in (client_sign_tabs or {}).items()
    ]
    client_tabs = Tabs(text_tabs=doc_text_tabs + sign_text_tabs)

    consultant_role_obj = TemplateRole(
        email=consultant.email,
        name=consultant.name,
        role_name=consultant_role,
        routing_order="1",
        tabs=consultant_tabs,
    )

    client_role_obj = TemplateRole(
        email=client.email,
        name=client.name,
        role_name=client_role,
        routing_order="2",
        tabs=client_tabs,
    )

    envelope_definition = EnvelopeDefinition(
        status="sent",
        template_id=template_id,
        template_roles=[consultant_role_obj, client_role_obj],
        email_subject=email_subject,
    )

    try:
        result = envelopes_api.create_envelope(
            account_id=settings.docusign_account_id,
            envelope_definition=envelope_definition,
        )
        return EnvelopeResult(envelope_id=result.envelope_id, status=result.status)
    except ApiException as e:
        raise RuntimeError(f"DocuSign API error: {e.body}") from e


# ─────────────────────────────────────────────
# Opción D: Embedded Signing
# (El cliente firma dentro de tu plataforma)
# ─────────────────────────────────────────────

def get_embedded_signing_url(
    template_id: str,
    recipient: RecipientInfo,
    return_url: str,
    role_name: str = "Client",
    tab_values: Optional[dict] = None,
) -> EnvelopeResult:
    """
    Crea un envelope y retorna una URL para que el cliente firme
    embebido dentro de tu app (en un iframe o redirect).
    """
    # client_user_id must match between TemplateRole and RecipientViewRequest
    client_user_id = recipient.email
    result = send_envelope_from_template(
        template_id, recipient, role_name,
        tab_values=tab_values,
        client_user_id=client_user_id,
    )

    api_client = get_api_client()
    envelopes_api = EnvelopesApi(api_client)

    from docusign_esign import RecipientViewRequest
    view_request = RecipientViewRequest(
        authentication_method="none",
        client_user_id=client_user_id,
        recipient_id="1",
        return_url=return_url,
        user_name=recipient.name,
        email=recipient.email,
    )

    try:
        view_result = envelopes_api.create_recipient_view(
            account_id=settings.docusign_account_id,
            envelope_id=result.envelope_id,
            recipient_view_request=view_request,
        )
        result.redirect_url = view_result.url
        return result
    except ApiException as e:
        raise RuntimeError(f"DocuSign API error: {e.body}") from e


# ─────────────────────────────────────────────
# Opción E: SOW — PDF generado dinámicamente
# ─────────────────────────────────────────────

def send_sow_envelope(
    pdf_bytes: bytes,
    document_name: str,
    consultant: RecipientInfo,
    client: RecipientInfo,
    email_subject: Optional[str] = None,
) -> EnvelopeResult:
    """
    Envía un SOW generado dinámicamente para firma secuencial.

    El PDF debe contener las cadenas ancla:
      TKSOL_CONSULTANT_SIG  — línea de firma del consultor
      TKSOL_CLIENT_SIG      — línea de firma del cliente
    DocuSign coloca los tabs SignHere y DateSigned en esas posiciones.
    """
    api_client = get_api_client()
    envelopes_api = EnvelopesApi(api_client)

    document = Document(
        document_base64=base64.b64encode(pdf_bytes).decode("utf-8"),
        name=document_name,
        file_extension="pdf",
        document_id="1",
    )

    def _sign_tabs(sign_anchor: str) -> Tabs:
        return Tabs(
            sign_here_tabs=[SignHere(
                anchor_string=sign_anchor,
                anchor_y_offset="-5",
                anchor_units="pixels",
            )],
            date_signed_tabs=[DateSigned(
                anchor_string=sign_anchor,
                anchor_x_offset="0",
                anchor_y_offset="60",
                anchor_units="pixels",
            )],
        )

    consultant_signer = Signer(
        email=consultant.email,
        name=consultant.name,
        recipient_id="1",
        routing_order="1",
        tabs=_sign_tabs("TKSOL_CONSULTANT_SIG"),
    )
    client_signer = Signer(
        email=client.email,
        name=client.name,
        recipient_id="2",
        routing_order="2",
        tabs=_sign_tabs("TKSOL_CLIENT_SIG"),
    )

    envelope = EnvelopeDefinition(
        email_subject=email_subject or f"Please sign: {document_name}",
        documents=[document],
        recipients=Recipients(signers=[consultant_signer, client_signer]),
        status="sent",
    )

    try:
        result = envelopes_api.create_envelope(
            account_id=settings.docusign_account_id,
            envelope_definition=envelope,
        )
        return EnvelopeResult(envelope_id=result.envelope_id, status=result.status)
    except ApiException as e:
        raise RuntimeError(f"DocuSign API error: {e.body}") from e


# ─────────────────────────────────────────────
# Consultar estado de un envelope
# ─────────────────────────────────────────────

def list_envelopes(from_date: Optional[str] = None) -> list[dict]:
    """Lists recent envelopes from DocuSign (last 30 days by default)."""
    from datetime import datetime, timedelta
    api_client = get_api_client()
    envelopes_api = EnvelopesApi(api_client)

    if not from_date:
        from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    try:
        result = envelopes_api.list_status_changes(
            account_id=settings.docusign_account_id,
            from_date=from_date,
        )
        envelopes = result.envelopes or []
        return [
            {
                "envelope_id": e.envelope_id,
                "status": e.status,
                "email_subject": e.email_subject,
                "sent_date": e.sent_date_time,
                "completed_date": e.completed_date_time,
                "last_modified": e.last_modified_date_time,
            }
            for e in envelopes
        ]
    except ApiException as e:
        raise RuntimeError(f"DocuSign API error: {e.body}") from e


def get_envelope_status(envelope_id: str) -> dict:
    """Retorna el estado actual de un envelope."""
    api_client = get_api_client()
    envelopes_api = EnvelopesApi(api_client)

    try:
        envelope = envelopes_api.get_envelope(
            account_id=settings.docusign_account_id,
            envelope_id=envelope_id,
        )
        return {
            "envelope_id": envelope.envelope_id,
            "status": envelope.status,
            "sent_date": envelope.sent_date_time,
            "completed_date": envelope.completed_date_time,
            "decline_reason": getattr(envelope, "decline_reason", None),
        }
    except ApiException as e:
        raise RuntimeError(f"DocuSign API error: {e.body}") from e


# ─────────────────────────────────────────────
# Descargar documento firmado
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# Templates
# ─────────────────────────────────────────────

def list_templates(search_text: Optional[str] = None) -> list[dict]:
    """Lista los templates disponibles en la cuenta de DocuSign."""
    api_client = get_api_client()
    templates_api = TemplatesApi(api_client)

    try:
        kwargs = {}
        if search_text:
            kwargs["search_text"] = search_text
        result = templates_api.list_templates(
            account_id=settings.docusign_account_id,
            **kwargs,
        )
        templates = result.envelope_templates or []
        return [
            {
                "template_id": t.template_id,
                "name": t.name,
                "description": t.description,
                "shared": t.shared,
                "last_modified": t.last_modified,
                "page_count": t.page_count,
            }
            for t in templates
        ]
    except ApiException as e:
        raise RuntimeError(f"DocuSign API error: {e.body}") from e


def get_template_details(template_id: str) -> dict:
    """Retorna detalles de un template: roles, documentos, campos de firma y tab labels."""
    api_client = get_api_client()
    templates_api = TemplatesApi(api_client)

    try:
        t = templates_api.get(
            account_id=settings.docusign_account_id,
            template_id=template_id,
        )

        def extract_tabs(signer) -> dict:
            """Extrae todos los tab labels y sus tipos para un signer."""
            tabs_info = {}
            if not signer.tabs:
                return tabs_info
            tab_types = {
                "text_tabs":      "text",
                "sign_here_tabs": "sign_here",
                "full_name_tabs": "full_name",
                "title_tabs":     "title",
                "date_signed_tabs": "date_signed",
                "checkbox_tabs":  "checkbox",
            }
            for attr, tab_type in tab_types.items():
                tabs = getattr(signer.tabs, attr, None) or []
                for tab in tabs:
                    label = getattr(tab, "tab_label", None) or getattr(tab, "name", "unnamed")
                    tabs_info[label] = {
                        "type": tab_type,
                        "required": getattr(tab, "required", None),
                        "locked": getattr(tab, "locked", None),
                        "value": getattr(tab, "value", None),
                    }
            return tabs_info

        roles = [
            {
                "role_name": r.role_name,
                "recipient_type": r.recipient_type,
                "routing_order": r.routing_order,
                "tabs": extract_tabs(r),
            }
            for r in (t.recipients.signers or [])
        ] if t.recipients else []

        documents = [
            {"document_id": d.document_id, "name": d.name, "file_extension": d.file_extension}
            for d in (t.documents or [])
        ]

        return {
            "template_id": t.template_id,
            "name": t.name,
            "description": t.description,
            "email_subject": t.email_subject,
            "roles": roles,
            "documents": documents,
            "last_modified": t.last_modified,
        }
    except ApiException as e:
        raise RuntimeError(f"DocuSign API error: {e.body}") from e


def download_signed_document(envelope_id: str, output_path: str) -> str:
    """
    Descarga el PDF firmado con audit trail incluido.
    Retorna el path del archivo guardado.
    """
    api_client = get_api_client()
    envelopes_api = EnvelopesApi(api_client)

    try:
        # "combined" incluye el documento + el Certificate of Completion (audit trail)
        pdf_bytes = envelopes_api.get_document(
            account_id=settings.docusign_account_id,
            envelope_id=envelope_id,
            document_id="combined",
        )
        Path(output_path).write_bytes(pdf_bytes)
        return output_path
    except ApiException as e:
        raise RuntimeError(f"DocuSign API error: {e.body}") from e
