"""
Endpoints para explorar y gestionar Templates de DocuSign.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.services.docusign_service import list_templates, get_template_details

router = APIRouter(prefix="/templates", tags=["Templates"])


# ─── Schemas ───────────────────────────────────────

class TemplateSummary(BaseModel):
    template_id: str
    name: str
    description: Optional[str] = None
    shared: Optional[str] = None
    last_modified: Optional[str] = None
    page_count: Optional[int] = None


class TemplateRole(BaseModel):
    role_name: str
    recipient_type: Optional[str] = None


class TemplateDocument(BaseModel):
    document_id: str
    name: str
    file_extension: Optional[str] = None


class TemplateDetail(BaseModel):
    template_id: str
    name: str
    description: Optional[str] = None
    email_subject: Optional[str] = None
    roles: list[TemplateRole]
    documents: list[TemplateDocument]
    last_modified: Optional[str] = None


# ─── Endpoints ─────────────────────────────────────

@router.get("", response_model=list[TemplateSummary])
async def get_templates(
    search: Optional[str] = Query(None, description="Filtrar por nombre de template"),
):
    """Lista todos los templates disponibles en la cuenta de DocuSign."""
    try:
        return list_templates(search_text=search)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{template_id}", response_model=TemplateDetail)
async def get_template(template_id: str):
    """Retorna detalles de un template: roles, documentos y campos."""
    try:
        return get_template_details(template_id)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
