"""
Run this once to get the DocuSign JWT consent URL.
Visit the URL in a browser while logged in as DOCUSIGN_USER_ID.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from urllib.parse import urlencode
from app.config.settings import get_settings

settings = get_settings()

REDIRECT_URI = "http://localhost:8000"

params = urlencode({
    "response_type": "code",
    "scope": "signature impersonation",
    "client_id": settings.docusign_integration_key,
    "redirect_uri": REDIRECT_URI,
})

consent_url = f"{settings.docusign_auth_url}/oauth/auth?{params}"

print(f"\nGrant consent by visiting this URL:\n\n{consent_url}\n")
print(f"Redirect URI used: {REDIRECT_URI}")
print(f"Make sure '{REDIRECT_URI}' is registered in apps-d.docusign.com exactly as shown above.")
