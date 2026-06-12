from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import contracts, webhooks, templates, docs

app = FastAPI(
    title="Consulting Corp — Contract API",
    description="API para gestión de contratos NDA, MSA y SOW via DocuSign",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restringir en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contracts.router)
app.include_router(webhooks.router)
app.include_router(templates.router)
app.include_router(docs.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/config/defaults", tags=["Config"],
         summary="Valores por defecto de cada tipo de contrato")
async def get_contract_defaults():
    """
    Retorna los valores por defecto leídos desde .env para pre-llenar
    el formulario del frontend (template IDs incluidos, no se exponen credenciales).
    """
    from app.config.settings import get_settings
    s = get_settings()
    return {
        "nda": {
            "template_id":           s.docusign_template_nda,
            "agreement_term":        s.nda_agreement_term,
            "non_solicitation_term": s.nda_non_solicitation_term,
            "governing_county":      s.nda_governing_county,
        },
        "msa": {
            "template_id":           s.docusign_template_msa,
            "payment_terms":         s.msa_payment_terms,
            "late_fee_rate":         s.msa_late_fee_rate,
            "agreement_term":        s.msa_agreement_term,
            "non_solicitation_term": s.msa_non_solicitation_term,
            "governing_county":      s.msa_governing_county,
        },
        "sow": {
            "template_id":           s.docusign_template_sow,
            "warranty_days":         s.sow_warranty_days,
            "payment_terms":         s.sow_payment_terms,
            "late_fee_rate":         s.sow_late_fee_rate,
            "governing_county":      s.sow_governing_county,
        },
    }
