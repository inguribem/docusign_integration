from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

# Ruta base del proyecto (donde está este archivo: app/config/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # → docusign_integration/

# Documentos locales en docs/
DOCS = {
    "nda": BASE_DIR / "docs" / "TKSOLUTIONS-NDA-v4.pdf",
    "msa": BASE_DIR / "docs" / "TKSOLUTIONS-MSA-v1.pdf",
}


class Settings(BaseSettings):
    # DocuSign
    docusign_integration_key: str
    docusign_user_id: str
    docusign_account_id: str
    docusign_private_key_path: str = "./private.key"
    docusign_environment: str = "sandbox"  # "sandbox" | "production"
    docusign_webhook_hmac_secret: str

    # App
    app_base_url: str = "http://localhost:8000"

    # Disclosing Party / Consultant (tu empresa — fija para todos los contratos)
    company_name: str = ""
    company_entity_type: str = "LLC"
    company_address: str = ""
    consultant_name: str = ""
    consultant_title: str = ""
    consultant_email: str = ""

    # DocuSign Template IDs
    docusign_template_nda: str = ""
    docusign_template_msa: str = ""
    docusign_template_sow: str = ""

    # Valores por defecto — NDA
    nda_agreement_term: str = "2 years"
    nda_non_solicitation_term: str = "1 year"
    nda_governing_county: str = "Miami-Dade"

    # Valores por defecto — MSA
    msa_payment_terms: str = "15"
    msa_late_fee_rate: str = "1.5"
    msa_agreement_term: str = "1 year"
    msa_non_solicitation_term: str = "1 year"
    msa_governing_county: str = "Miami-Dade"

    # Valores por defecto — SOW
    sow_warranty_days: str = "30"
    sow_payment_terms: str = "15"
    sow_late_fee_rate: str = "1.5"
    sow_governing_county: str = "Miami-Dade"

    @property
    def docusign_auth_url(self) -> str:
        if self.docusign_environment == "production":
            return "https://account.docusign.com"
        return "https://account-d.docusign.com"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
