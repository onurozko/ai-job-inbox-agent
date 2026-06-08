from uuid import UUID

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from app.core.config import get_settings
from app.core.security import create_oauth_state
from app.services.gmail_credential_service import GmailTokenData

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def _client_config(*, redirect_uri: str) -> dict:
    settings = get_settings()
    if not settings.gmail_client_id or not settings.gmail_client_secret:
        raise ValueError("Gmail OAuth credentials are not configured")
    return {
        "web": {
            "client_id": settings.gmail_client_id,
            "client_secret": settings.gmail_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }


def get_gmail_connect_authorization_url(*, user_id: UUID) -> str:
    settings = get_settings()
    state = create_oauth_state(flow="gmail", user_id=user_id)
    flow = Flow.from_client_config(
        _client_config(redirect_uri=settings.gmail_connect_redirect_uri),
        scopes=GMAIL_SCOPES,
        redirect_uri=settings.gmail_connect_redirect_uri,
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return auth_url


def exchange_gmail_code(code: str) -> GmailTokenData:
    settings = get_settings()
    flow = Flow.from_client_config(
        _client_config(redirect_uri=settings.gmail_connect_redirect_uri),
        scopes=GMAIL_SCOPES,
        redirect_uri=settings.gmail_connect_redirect_uri,
    )
    flow.fetch_token(code=code)
    credentials = flow.credentials
    return GmailTokenData(
        access_token=credentials.token or "",
        refresh_token=credentials.refresh_token or "",
        token_uri=credentials.token_uri or "https://oauth2.googleapis.com/token",
        client_id=credentials.client_id or settings.gmail_client_id or "",
        client_secret=credentials.client_secret or settings.gmail_client_secret or "",
        scopes=" ".join(credentials.scopes or GMAIL_SCOPES),
        expiry=credentials.expiry,
    )


def build_credentials(refresh_token: str) -> Credentials:
    settings = get_settings()
    if not settings.gmail_client_id or not settings.gmail_client_secret:
        raise ValueError("Gmail OAuth credentials are not configured")
    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.gmail_client_id,
        client_secret=settings.gmail_client_secret,
        scopes=GMAIL_SCOPES,
    )
