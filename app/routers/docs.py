"""
Endpoints para gestionar los documentos template locales (docs/).
Permite listar, previsualizar y enviar PDFs directamente desde la carpeta docs/.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.config.settings import DOCS, get_settings
from app.services.docusign_service import (
    RecipientInfo,
    send_sequential_envelope,
)

settings = get_settings()
router = APIRouter(prefix="/docs", tags=["Documents"])


# ─── Schemas ───────────────────────────────────────

class SendDocRequest(BaseModel):
    client_name: str
    client_email: EmailStr
    doc_type: str                           # "nda" | "msa"
    tab_values: Optional[dict[str, str]] = None


class SendDocResponse(BaseModel):
    envelope_id: str
    status: str


# ─── Endpoints ─────────────────────────────────────

@router.get("", summary="Lista los documentos template disponibles")
async def list_docs():
    """Lista los PDFs disponibles en la carpeta docs/ con su estado."""
    result = []
    for doc_type, path in DOCS.items():
        result.append({
            "doc_type": doc_type,
            "filename": path.name,
            "exists": path.exists(),
            "size_kb": round(path.stat().st_size / 1024, 1) if path.exists() else None,
        })
    return result


@router.get("/{doc_type}/download", summary="Descarga el PDF template local")
async def download_doc(doc_type: str):
    """Descarga el PDF template desde docs/ para revisión."""
    path = DOCS.get(doc_type.lower())
    if not path:
        raise HTTPException(status_code=404, detail=f"Tipo de documento no reconocido: {doc_type}")
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {path.name}")
    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=path.name,
    )


@router.post("/{doc_type}/send", response_model=SendDocResponse,
             summary="Envía el PDF local directamente a DocuSign para firma")
async def send_doc(doc_type: str, request: SendDocRequest):
    """
    Envía el PDF de docs/ a DocuSign como envelope con firma secuencial.
    Útil antes de tener el template configurado en DocuSign, o para pruebas.

    Los tab_values se ignoran en este modo — el PDF se envía como está,
    con un campo SignHere posicionado en cada bloque de firma.
    """
    path = DOCS.get(doc_type.lower())
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail=f"Documento no encontrado: {doc_type}")

    from app.services.docusign_service import send_envelope_from_pdf

    # Posiciones de firma según el documento
    SIGN_POSITIONS = {
        "nda": {"page": 2, "consultant": ("100", "160"), "client": ("380", "160")},
        "msa": {"page": 2, "consultant": ("100", "160"), "client": ("380", "160")},
    }

    positions = SIGN_POSITIONS.get(doc_type.lower(), {"page": 2, "consultant": ("100", "700"), "client": ("380", "700")})

    try:
        consultant = RecipientInfo(
            name=settings.consultant_name,
            email=settings.consultant_email,
        )
        client = RecipientInfo(name=request.client_name, email=request.client_email)

        # Envío directo del PDF con dos campos SignHere
        from app.services.docusign_service import send_pdf_sequential
        result = send_pdf_sequential(
            pdf_path=str(path),
            document_name=path.stem,
            consultant=consultant,
            client=client,
            sign_page=positions["page"],
            consultant_sign_x=positions["consultant"][0],
            consultant_sign_y=positions["consultant"][1],
            client_sign_x=positions["client"][0],
            client_sign_y=positions["client"][1],
        )
        return SendDocResponse(envelope_id=result.envelope_id, status=result.status)

    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
