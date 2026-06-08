from dataclasses import dataclass

import httpx
from google_auth_oauthlib.flow import Flow

from app.core.config import get_settings
from app.core.security import create_oauth_state

GOOGLE_LOGIN_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


@dataclass(frozen=True)
class GoogleUserInfo:
    google_sub: str
    email: str
    full_name: str | None
    picture_url: str | None


@dataclass(frozen=True)
class GoogleLoginTokens:
    access_token: str


def _client_config(*, redirect_uri: str) -> dict:
    settings = get_settings()
    if not settings.gmail_client_id or not settings.gmail_client_secret:
        raise ValueError("Google OAuth credentials are not configured")
    return {
        "web": {
            "client_id": settings.gmail_client_id,
            "client_secret": settings.gmail_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }


def get_login_authorization_url() -> str:
    settings = get_settings()
    state = create_oauth_state(flow="login")
    flow = Flow.from_client_config(
        _client_config(redirect_uri=settings.gmail_redirect_uri),
        scopes=GOOGLE_LOGIN_SCOPES,
        redirect_uri=settings.gmail_redirect_uri,
    )
    auth_url, _ = flow.authorization_url(
        access_type="online",
        include_granted_scopes="false",
        prompt="select_account",
        state=state,
    )
    return auth_url


def exchange_login_code(code: str) -> GoogleLoginTokens:
    settings = get_settings()
    flow = Flow.from_client_config(
        _client_config(redirect_uri=settings.gmail_redirect_uri),
        scopes=GOOGLE_LOGIN_SCOPES,
        redirect_uri=settings.gmail_redirect_uri,
    )
    flow.fetch_token(code=code)
    credentials = flow.credentials
    if not credentials.token:
        raise ValueError("Google did not return an access token")
    return GoogleLoginTokens(access_token=credentials.token)


async def fetch_google_userinfo(access_token: str) -> GoogleUserInfo:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        payload = response.json()

    google_sub = payload.get("id")
    email = payload.get("email")
    if not google_sub or not email:
        raise ValueError("Google userinfo response missing id or email")

    return GoogleUserInfo(
        google_sub=str(google_sub),
        email=str(email),
        full_name=payload.get("name"),
        picture_url=payload.get("picture"),
    )
