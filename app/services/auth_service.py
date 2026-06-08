import asyncio
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import BadRequestError, InvalidOAuthStateError, OAuthConfigError
from app.core.security import InvalidTokenError, create_access_token, decode_oauth_state
from app.integrations.gmail.oauth import exchange_gmail_code, get_gmail_connect_authorization_url
from app.integrations.google.oauth import (
    exchange_login_code,
    fetch_google_userinfo,
    get_login_authorization_url,
)
from app.schemas.auth import GmailConnectResponse, UserRead
from app.services.gmail_credential_service import upsert_gmail_credential
from app.services.user_service import create_or_update_user_from_google

logger = logging.getLogger(__name__)


class AuthService:
    async def get_google_login_url(self) -> str:
        try:
            return await asyncio.to_thread(get_login_authorization_url)
        except ValueError as exc:
            raise OAuthConfigError(str(exc)) from exc

    async def complete_google_login(
        self,
        session: AsyncSession,
        *,
        code: str,
        state: str,
    ) -> tuple[str, UserRead]:
        self._validate_login_state(state)

        try:
            login_tokens = await asyncio.to_thread(exchange_login_code, code)
            google_user = await fetch_google_userinfo(login_tokens.access_token)
        except ValueError as exc:
            raise BadRequestError(f"Failed to complete Google login: {exc}") from exc
        except Exception as exc:
            logger.exception("Google login failed during token exchange or userinfo fetch")
            raise BadRequestError("Failed to complete Google login") from exc

        user = await create_or_update_user_from_google(
            session,
            google_sub=google_user.google_sub,
            email=google_user.email,
            full_name=google_user.full_name,
            picture_url=google_user.picture_url,
        )
        access_token = create_access_token(user_id=user.id, email=user.email)
        logger.info("Google login completed user_id=%s", user.id)
        return access_token, UserRead.model_validate(user)

    def build_login_redirect_url(self, access_token: str) -> str:
        settings = get_settings()
        return (
            f"{settings.auth_frontend_redirect_url}?access_token={access_token}&token_type=bearer"
        )

    async def get_gmail_connect_url(self, *, user_id: UUID) -> str:
        try:
            return await asyncio.to_thread(get_gmail_connect_authorization_url, user_id=user_id)
        except ValueError as exc:
            raise OAuthConfigError(str(exc)) from exc

    async def complete_gmail_connect(
        self,
        session: AsyncSession,
        *,
        code: str,
        state: str,
    ) -> GmailConnectResponse:
        user_id = self._validate_gmail_state(state)

        try:
            token_data = await asyncio.to_thread(exchange_gmail_code, code)
        except ValueError as exc:
            raise BadRequestError(f"Failed to exchange Gmail OAuth code: {exc}") from exc
        except Exception as exc:
            logger.exception("Gmail connect failed during token exchange user_id=%s", user_id)
            raise BadRequestError("Failed to exchange Gmail OAuth code") from exc

        await upsert_gmail_credential(session, user_id=user_id, token_data=token_data)
        logger.info("Gmail connected user_id=%s", user_id)
        return GmailConnectResponse(message="Gmail connected successfully", user_id=user_id)

    @staticmethod
    def _validate_login_state(state: str) -> None:
        try:
            oauth_state = decode_oauth_state(state)
        except InvalidTokenError as exc:
            raise InvalidOAuthStateError() from exc

        if oauth_state.get("flow") != "login":
            raise BadRequestError("Invalid OAuth flow")

    @staticmethod
    def _validate_gmail_state(state: str) -> UUID:
        try:
            oauth_state = decode_oauth_state(state)
        except InvalidTokenError as exc:
            raise InvalidOAuthStateError() from exc

        if oauth_state.get("flow") != "gmail":
            raise BadRequestError("Invalid OAuth flow")

        user_id_raw = oauth_state.get("user_id")
        if not user_id_raw:
            raise BadRequestError("OAuth state missing user id")

        try:
            return UUID(str(user_id_raw))
        except ValueError as exc:
            raise BadRequestError("Invalid OAuth state user id") from exc
