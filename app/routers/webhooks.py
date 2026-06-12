"""
Webhook handler para eventos de DocuSign.
DocuSign llama a este endpoint cada vez que cambia el estado de un envelope.

SETUP en DocuSign:
  App Center → Connect → Add Configuration → URL: https://tuapp.com/webhooks/docusign
  Events: envelope-sent, envelope-delivered, envelope-completed, envelope-declined, envelope-voided
  Include: envelope data, recipients data
  HMAC: habilitar y copiar el secret a DOCUSIGN_WEBHOOK_HMAC_SECRET en .env
"""
import hashlib
import hmac
import base64
import logging
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional

from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# ─── HMAC Verification ─────────────────────────────

def verify_docusign_hmac(payload: bytes, hmac_header: str) -> bool:
    """
    Verifica que el webhook realmente venga de DocuSign.
    DocuSign firma el payload con tu HMAC secret.
    """
    expected = base64.b64encode(
        hmac.new(
            settings.docusign_webhook_hmac_secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).digest()
    ).decode("utf-8")
    return hmac.compare_digest(expected, hmac_header)


# ─── Webhook Endpoint ──────────────────────────────

@router.post("/docusign")
async def docusign_webhook(
    request: Request,
    x_docusign_signature_1: Optional[str] = Header(None),
):
    """
    Recibe eventos de DocuSign y ejecuta acciones según el estado del envelope.
    """
    payload = await request.body()

    # Verificar HMAC si está configurado
    if settings.docusign_webhook_hmac_secret and x_docusign_signature_1:
        if not verify_docusign_hmac(payload, x_docusign_signature_1):
            logger.warning("DocuSign webhook HMAC verification failed")
            raise HTTPException(status_code=401, detail="Invalid HMAC signature")

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = data.get("event")
    envelope_id = data.get("data", {}).get("envelopeId")
    envelope_summary = data.get("data", {}).get("envelopeSummary", {})

    logger.info(f"DocuSign event received: {event} | envelope: {envelope_id}")

    # ─── Dispatch por evento ───────────────────────
    handlers = {
        "envelope-sent":      _on_envelope_sent,
        "envelope-delivered": _on_envelope_delivered,
        "envelope-completed": _on_envelope_completed,
        "envelope-declined":  _on_envelope_declined,
        "envelope-voided":    _on_envelope_voided,
    }

    handler = handlers.get(event)
    if handler:
        await handler(envelope_id, envelope_summary)
    else:
        logger.debug(f"No handler for event: {event}")

    # DocuSign espera 200 OK. Si retornamos error, reintenta el webhook.
    return {"received": True}


# ─── Event Handlers ────────────────────────────────

async def _on_envelope_sent(envelope_id: str, data: dict):
    """Contrato enviado al cliente. Registrar timestamp en tu DB."""
    logger.info(f"[SENT] Envelope {envelope_id} enviado al cliente")
    # TODO: actualizar estado en tu base de datos
    # await db.contracts.update(envelope_id=envelope_id, status="sent")


async def _on_envelope_delivered(envelope_id: str, data: dict):
    """Cliente abrió el email. Útil para seguimiento comercial."""
    logger.info(f"[DELIVERED] Envelope {envelope_id} visto por el cliente")
    # TODO: registrar que el cliente vio el documento
    # await db.contracts.update(envelope_id=envelope_id, status="viewed")


async def _on_envelope_completed(envelope_id: str, data: dict):
    """
    ¡Contrato firmado! Aquí va la lógica más importante:
    - Descargar PDF firmado
    - Activar onboarding del cliente
    - Enviar notificación interna
    - Guardar en S3/Drive
    """
    logger.info(f"[COMPLETED] Envelope {envelope_id} firmado exitosamente")

    recipients = data.get("recipients", {}).get("signers", [])
    for signer in recipients:
        logger.info(f"  Firmado por: {signer.get('name')} <{signer.get('email')}>")

    # TODO: implementar tu lógica de negocio aquí
    # pdf_path = await storage.save_signed_contract(envelope_id)
    # await db.contracts.update(envelope_id=envelope_id, status="completed", pdf_path=pdf_path)
    # await notifications.send_internal_alert(f"Contrato {envelope_id} firmado")
    # await onboarding.activate_client(envelope_id)


async def _on_envelope_declined(envelope_id: str, data: dict):
    """Cliente rechazó firmar. Alertar al equipo comercial."""
    decline_reason = data.get("declineReason", "No especificado")
    logger.warning(f"[DECLINED] Envelope {envelope_id} rechazado. Razón: {decline_reason}")

    # TODO: alertar equipo
    # await notifications.send_alert(f"Contrato rechazado: {envelope_id}. Razón: {decline_reason}")
    # await db.contracts.update(envelope_id=envelope_id, status="declined", reason=decline_reason)


async def _on_envelope_voided(envelope_id: str, data: dict):
    """Contrato anulado. Marcar como inválido."""
    void_reason = data.get("voidedReason", "No especificado")
    logger.warning(f"[VOIDED] Envelope {envelope_id} anulado. Razón: {void_reason}")

    # TODO:
    # await db.contracts.update(envelope_id=envelope_id, status="voided")
