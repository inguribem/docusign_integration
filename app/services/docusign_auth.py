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


def get_api_client() -> ApiClient:
    """Retorna un ApiClient de DocuSign autenticado y listo para usar."""
    api_client = ApiClient()
    api_client.host = settings.docusign_base_url
    api_client.set_default_header(
        "Authorization", f"Bearer {get_access_token()}"
    )
    return api_client
