"""
Endpoints de contratos: NDA, MSA, SOW
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.services.docusign_service import (
    RecipientInfo,
    send_envelope_from_template,
    send_envelope_from_pdf,
    get_embedded_signing_url,
    get_envelope_status,
    list_envelopes,
    download_signed_document,
    send_sequential_envelope,
    send_sow_envelope,
)
from app.config.settings import get_settings

settings = get_settings()
router = APIRouter(prefix="/contracts", tags=["Contracts"])


# ─── Schemas ───────────────────────────────────────

class NDAFields(BaseModel):
    """
    Campos del NDA que cambian por contrato (solo datos del cliente).
    Los datos de tu empresa (Disclosing Party) se leen desde settings/.env.
    """
    # Cliente (Receiving Party) — cuerpo del documento
    client_entity_type: str = "Individual"      # tabLabel: client_entity_type
    client_address: str = ""                    # tabLabel: client_address
    # Fecha — tres tabs separados en el template
    effective_day: str                          # tabLabel: effective_day   (ej: "3")
    effective_month: str                        # tabLabel: effective_month (ej: "June")
    effective_year: str                         # tabLabel: effective_year  (ej: "2026")
    # Otros
    agreement_term: str = "2 years"             # tabLabel: agreement_term
    non_solicitation_term: str = "1 year"       # tabLabel: non_solicitation_term (§7)
    governing_county: str = "Miami-Dade"        # tabLabel: governing_county
    # Bloque de firma del cliente
    client_signer_name: str = ""               # tabLabel: client_full_name (persona que firma)
    client_title: str = ""                      # tabLabel: client_title (título del firmante)


class MSAFields(BaseModel):
    """
    Campos del MSA que cambian por contrato.
    Los datos de tu empresa se leen desde settings/.env.
    """
    # Cliente — cuerpo del documento
    client_entity_type: str = "Individual"      # tabLabel: client_entity_type
    client_address: str = ""                    # tabLabel: client_address
    # Fecha
    effective_day: str                          # tabLabel: effective_day
    effective_month: str                        # tabLabel: effective_month
    effective_year: str                         # tabLabel: effective_year
    # Términos comerciales
    payment_terms: str = "15"                   # tabLabel: payment_terms (días)
    late_fee_rate: str = "1.5"                  # tabLabel: late_fee_rate (% mensual)
    agreement_term: str = "1 year"              # tabLabel: agreement_term
    non_solicitation_term: str = "1 year"       # tabLabel: non_solicitation_term
    governing_county: str = "Miami-Dade"        # tabLabel: governing_county
    # Bloque de firma del cliente
    client_signer_name: str = ""               # tabLabel: client_full_name (persona que firma)
    client_title: str = ""                      # tabLabel: client_title (título del firmante)


class SOWFields(BaseModel):
    """
    Campos del SOW. El PDF se genera dinámicamente; no usa template de DocuSign.
    """
    # Firmante del cliente (para PDF y recipient de DocuSign)
    client_signer_name: str = ""
    client_title: str = ""
    # Proyecto
    project_description: str
    # Milestones variables (5 predefinidos en el template)
    m1_weeks: str = ""; m1_payment: str = ""
    m2_weeks: str = ""; m2_payment: str = ""
    m3_weeks: str = ""; m3_payment: str = ""
    m4_weeks: str = ""; m4_payment: str = ""
    m5_weeks: str = ""; m5_payment: str = ""
    total_price: str = ""
    # Términos (defaults desde settings si quedan vacíos)
    payment_due_days: str = ""
    late_fee_rate: str = ""
    warranty_days: str = ""
    governing_county: str = ""


class SendContractRequest(BaseModel):
    client_name: str
    client_email: EmailStr
    contract_type: str                          # "nda" | "msa" | "sow"
    template_id: Optional[str] = None          # Override del template por defecto
    nda_fields: Optional[NDAFields] = None     # Campos del NDA
    msa_fields: Optional[MSAFields] = None     # Campos del MSA
    sow_fields: Optional[SOWFields] = None     # Campos del SOW
    embedded: bool = False                      # True = firma dentro de tu app


class SendContractResponse(BaseModel):
    envelope_id: str
    status: str
    signing_url: Optional[str] = None  # Solo si embedded=True


class EnvelopeStatusResponse(BaseModel):
    envelope_id: str
    status: str
    sent_date: Optional[str] = None
    completed_date: Optional[str] = None
    decline_reason: Optional[str] = None


def get_contract_templates() -> dict[str, str]:
    """Lee los template IDs desde settings (cargados desde .env)."""
    return {
        "nda": settings.docusign_template_nda,
        "msa": settings.docusign_template_msa,
        "sow": settings.docusign_template_sow,
    }


# ─── Endpoints ─────────────────────────────────────

@router.get("", response_model=list[EnvelopeStatusResponse])
async def list_contracts(from_date: Optional[str] = None):
    """Lista los contratos recientes (últimos 30 días por defecto)."""
    try:
        envelopes = list_envelopes(from_date)
        return [EnvelopeStatusResponse(**e) for e in envelopes]
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/send", response_model=SendContractResponse)
async def send_contract(request: SendContractRequest):
    """
    Envía un contrato para firma al cliente.
    - embedded=False: el cliente recibe un email de DocuSign
    - embedded=True: retorna una URL para firmar dentro de tu app
    """
    contract_type = request.contract_type.lower()
    templates = get_contract_templates()
    if contract_type not in templates:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de contrato inválido. Opciones: {list(templates.keys())}"
        )

    # ── SOW: PDF generado dinámicamente, no usa template de DocuSign ────────
    if contract_type == "sow":
        if not request.sow_fields:
            raise HTTPException(status_code=400, detail="sow_fields requerido para type=sow")
        f = request.sow_fields
        from app.services.sow_generator import SOWData, generate_sow_pdf
        sow_data = SOWData(
            consultant_company=settings.company_name,
            client_name=request.client_name,
            project_description=f.project_description,
            m1_weeks=f.m1_weeks, m1_payment=f.m1_payment,
            m2_weeks=f.m2_weeks, m2_payment=f.m2_payment,
            m3_weeks=f.m3_weeks, m3_payment=f.m3_payment,
            m4_weeks=f.m4_weeks, m4_payment=f.m4_payment,
            m5_weeks=f.m5_weeks, m5_payment=f.m5_payment,
            total_price=f.total_price,
            payment_due_days=f.payment_due_days or settings.sow_payment_terms,
            late_fee_rate=f.late_fee_rate or settings.sow_late_fee_rate,
            warranty_days=f.warranty_days or settings.sow_warranty_days,
            governing_county=f.governing_county or settings.sow_governing_county,
            consultant_name=settings.consultant_name,
            consultant_title=settings.consultant_title,
            client_signer_name=f.client_signer_name or request.client_name,
            client_signer_title=f.client_title,
        )
        try:
            pdf_bytes = generate_sow_pdf(sow_data)
            consultant = RecipientInfo(name=settings.consultant_name, email=settings.consultant_email)
            client = RecipientInfo(
                name=f.client_signer_name or request.client_name,
                email=request.client_email,
            )
            result = send_sow_envelope(
                pdf_bytes=pdf_bytes,
                document_name=f"SOW — {request.client_name}",
                consultant=consultant,
                client=client,
                email_subject=f"Please sign your SOW — {request.client_name}",
            )
            return SendContractResponse(envelope_id=result.envelope_id, status=result.status)
        except RuntimeError as e:
            raise HTTPException(status_code=502, detail=str(e))

    template_id = request.template_id or templates[contract_type]

    # Tabs del bloque de firma del consultor (van al rol Consultant)
    consultant_sign_tabs = {
        "company_name":     settings.company_name,     # By
        "consultant_name":  settings.consultant_name,  # Name
        "consultant_title": settings.consultant_title, # Title
    }

    # Campos del cuerpo del documento (empresa — iguales en todos los contratos)
    base_doc = {
        "company_name":         settings.company_name,
        "company_entity_type":  settings.company_entity_type,
        "company_address":      settings.company_address,
    }

    # Tabs del bloque de firma del cliente (By = empresa; Name = auto desde recipient.name)
    document_tabs: dict[str, str] | None = None
    client_sign_tabs: dict[str, str] = {
        "client_name": request.client_name,  # By → empresa del cliente
    }

    # El nombre individual del firmante se usa como recipient.name en DocuSign.
    # Esto hace que el FullName tab del template se auto-llene con el nombre correcto.
    signer_name = request.client_name  # fallback si no hay campos específicos

    if contract_type == "nda" and request.nda_fields:
        f = request.nda_fields
        signer_name = f.client_signer_name or request.client_name
        client_sign_tabs["client_title"] = f.client_title  # Title
        document_tabs = {
            **base_doc,
            "client_entity_type":       f.client_entity_type,
            "client_address":           f.client_address,
            "effective_day":            f.effective_day,
            "effective_month":          f.effective_month,
            "effective_year":           f.effective_year,
            "agreement_term":           f.agreement_term,
            "non_solicitation_term":    f.non_solicitation_term,
            "governing_county":         f.governing_county,
        }

    elif contract_type == "msa" and request.msa_fields:
        f = request.msa_fields
        signer_name = f.client_signer_name or request.client_name
        client_sign_tabs["client_title"] = f.client_title  # Title
        document_tabs = {
            **base_doc,
            "client_entity_type":       f.client_entity_type,
            "client_address":           f.client_address,
            "effective_day":            f.effective_day,
            "effective_month":          f.effective_month,
            "effective_year":           f.effective_year,
            "payment_terms":            f.payment_terms,
            "late_fee_rate":            f.late_fee_rate,
            "agreement_term":           f.agreement_term,
            "non_solicitation_term":    f.non_solicitation_term,
            "governing_county":         f.governing_county,
        }

    # El recipient del cliente usa el nombre del firmante (no la empresa),
    # para que el FullName tab del template se llene con el nombre individual.
    recipient = RecipientInfo(name=signer_name, email=request.client_email)

    try:
        # Siempre firma secuencial: consultor (settings) → cliente
        consultant = RecipientInfo(
            name=settings.consultant_name,
            email=settings.consultant_email,
        )
        result = send_sequential_envelope(
            template_id=template_id,
            consultant=consultant,
            client=recipient,
            document_tabs=document_tabs,
            consultant_sign_tabs=consultant_sign_tabs,
            client_sign_tabs=client_sign_tabs,
            email_subject=f"Please sign your {contract_type.upper()} — {request.client_name}",
        )
        return SendContractResponse(
            envelope_id=result.envelope_id,
            status=result.status,
        )

    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{envelope_id}/status", response_model=EnvelopeStatusResponse)
async def check_contract_status(envelope_id: str):
    """Consulta el estado actual de un contrato enviado."""
    try:
        status = get_envelope_status(envelope_id)
        return EnvelopeStatusResponse(**status)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{envelope_id}/download")
async def download_contract(envelope_id: str, background_tasks: BackgroundTasks):
    """
    Descarga el PDF firmado con Certificate of Completion (audit trail).
    Solo disponible cuando status == 'completed'.
    """
    from fastapi.responses import FileResponse
    import tempfile, os

    # Verificar que esté firmado
    try:
        status_data = get_envelope_status(envelope_id)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    if status_data["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"El contrato aún no está firmado. Estado actual: {status_data['status']}"
        )

    try:
        tmp_path = os.path.join(tempfile.gettempdir(), f"{envelope_id}_signed.pdf")
        download_signed_document(envelope_id, tmp_path)

        # Eliminar el archivo temporal después de enviarlo
        background_tasks.add_task(os.unlink, tmp_path)

        return FileResponse(
            path=tmp_path,
            media_type="application/pdf",
            filename=f"contract_{envelope_id}_signed.pdf",
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/send-pdf", response_model=SendContractResponse)
async def send_contract_pdf(
    client_name: str = Form(...),
    client_email: EmailStr = Form(...),
    document_name: str = Form(...),
    sign_page: int = Form(1),
    sign_x_position: str = Form("100"),
    sign_y_position: str = Form("700"),
    file: UploadFile = File(..., description="PDF a enviar para firma"),
):
    """
    Envía un PDF generado dinámicamente para firma.
    El cliente recibe un email con el link para firmar.
    """
    import tempfile, os

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")

    try:
        contents = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        recipient = RecipientInfo(name=client_name, email=client_email)
        result = send_envelope_from_pdf(
            pdf_path=tmp_path,
            document_name=document_name,
            recipient=recipient,
            sign_page=sign_page,
            sign_x_position=sign_x_position,
            sign_y_position=sign_y_position,
        )
        return SendContractResponse(envelope_id=result.envelope_id, status=result.status)

    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        if "tmp_path" in locals():
            os.unlink(tmp_path)


@router.get("/signing-complete")
async def signing_complete(event: Optional[str] = None):
    """
    Redirect URL después de que el cliente firma en modo embedded.
    DocuSign redirige aquí con el parámetro ?event=signing_complete
    """
    return {
        "message": "Firma completada exitosamente.",
        "event": event,
        "next_step": "Recibirás una copia del documento firmado por email."
    }
