"""
DocuSign JWT Grant Authentication (server-to-server)
No user interaction required — ideal para backends automatizados.
"""
import time
import jwt
from pathlib import Path
from docusign_esign import ApiClient
from app.config.settings import get_settings

settings = get_settings()

# Token cache para no pedir uno nuevo en cada request
_token_cache: dict = {"access_token": None, "expires_at": 0}

# Cache del base_uri real de la cuenta (na1/na2/na3/na4/eu/...). DocuSign reparte
# las cuentas entre varios datacenters — nunca se debe asumir uno fijo, hay que
# resolverlo vía /oauth/userinfo. No expira mientras dure el proceso.
_account_cache: dict = {"base_uri": None}


def _load_private_key() -> str:
    key_path = Path(settings.docusign_private_key_path)
    if not key_path.exists():
        raise FileNotFoundError(
            f"DocuSign private key not found at: {key_path}\n"
            "Genera tu RSA key pair en DocuSign App Center y descarga la private key."
        )
    return key_path.read_text()


def get_access_token() -> str:
    """
    Retorna un access token válido. Usa cache para evitar llamadas innecesarias.
    El token de DocuSign dura 1 hora. Renovamos con 5 min de margen.
    """
    now = time.time()
    if _token_cache["access_token"] and now < _token_cache["expires_at"] - 300:
        return _token_cache["access_token"]

    private_key = _load_private_key()

    # Construir JWT payload
    payload = {
        "iss": settings.docusign_integration_key,
        "sub": settings.docusign_user_id,
        "aud": settings.docusign_auth_url.replace("https://", ""),
        "iat": int(now),
        "exp": int(now) + 3600,
        "scope": "signature impersonation",
    }

    # Firmar con RSA private key
    encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")

    # Intercambiar JWT por access token
    import httpx
    response = httpx.post(
        f"{settings.docusign_auth_url}/oauth/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": encoded_jwt,
        },
    )
    if response.status_code != 200:
        print(f"DocuSign token error: {response.status_code} — {response.text}")
        response.raise_for_status()
    data = response.json()

    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 3600)

    return _token_cache["access_token"]


def _get_account_base_uri(access_token: str) -> str:
    """
    Resuelve el host real (na1/na2/na3/na4/eu/...) de la cuenta configurada.
    Nunca se debe asumir un datacenter fijo: DocuSign reparte las cuentas
    (sobre todo en producción) entre varios hosts regionales.
    """
    if _account_cache["base_uri"]:
        return _account_cache["base_uri"]

    import httpx
    response = httpx.get(
        f"{settings.docusign_auth_url}/oauth/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    accounts = response.json().get("accounts", [])
    account = next(
        (a for a in accounts if a["account_id"] == settings.docusign_account_id),
        None,
    )
    if not account:
        raise RuntimeError(
            f"DOCUSIGN_ACCOUNT_ID={settings.docusign_account_id} no aparece entre las "
            "cuentas del usuario autenticado. Verifica el Account ID en settings."
        )

    _account_cache["base_uri"] = account["base_uri"]
    return account["base_uri"]


def get_api_client() -> ApiClient:
    """Retorna un ApiClient de DocuSign autenticado y listo para usar."""
    access_token = get_access_token()
    base_uri = _get_account_base_uri(access_token)

    api_client = ApiClient()
    api_client.host = f"{base_uri}/restapi"
    api_client.set_default_header(
        "Authorization", f"Bearer {access_token}"
    )
    return api_client
