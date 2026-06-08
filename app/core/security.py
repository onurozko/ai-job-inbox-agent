from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from pydantic import BaseModel

from app.core.config import get_settings

JWT_ALGORITHM = "HS256"


class TokenPayload(BaseModel):
    sub: UUID
    email: str
    exp: datetime
    type: str


class InvalidTokenError(Exception):
    pass


def create_access_token(*, user_id: UUID, email: str) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def create_oauth_state(*, flow: str, user_id: UUID | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.oauth_state_expire_minutes)
    payload: dict[str, str | datetime] = {
        "flow": flow,
        "exp": expire,
        "type": "oauth_state",
    }
    if user_id is not None:
        payload["user_id"] = str(user_id)
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    payload = _decode_token(token, expected_type="access")
    return TokenPayload(
        sub=UUID(payload["sub"]),
        email=payload["email"],
        exp=datetime.fromtimestamp(payload["exp"], tz=UTC),
        type=payload["type"],
    )


def decode_oauth_state(state: str) -> dict[str, str]:
    return _decode_token(state, expected_type="oauth_state")


def _decode_token(token: str, *, expected_type: str) -> dict[str, str | int | float]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Invalid token") from exc

    if payload.get("type") != expected_type:
        raise InvalidTokenError("Invalid token type")

    return payload
