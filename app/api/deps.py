from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import InvalidTokenError, decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.user_service import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)


async def get_settings_dep() -> Settings:
    return get_settings()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[User, None]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Not authenticated")

    try:
        token_payload = decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise UnauthorizedError("Invalid or expired access token") from exc

    user = await get_user_by_id(session, token_payload.sub)
    if user is None:
        raise UnauthorizedError("User not found")

    yield user
