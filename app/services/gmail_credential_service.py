from datetime import datetime
from uuid import UUID

from google.oauth2.credentials import Credentials
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gmail_credential import GmailCredential


class GmailTokenData(BaseModel):
    access_token: str
    refresh_token: str
    token_uri: str
    client_id: str
    client_secret: str
    scopes: str
    expiry: datetime | None = None


async def get_user_gmail_credential(
    session: AsyncSession,
    user_id: UUID,
) -> GmailCredential | None:
    stmt = select(GmailCredential).where(GmailCredential.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_user_ids_with_gmail_credentials(session: AsyncSession) -> list[UUID]:
    stmt = select(GmailCredential.user_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def upsert_gmail_credential(
    session: AsyncSession,
    *,
    user_id: UUID,
    token_data: GmailTokenData,
) -> GmailCredential:
    credential = await get_user_gmail_credential(session, user_id)
    if credential is None:
        credential = GmailCredential(user_id=user_id)
        session.add(credential)

    credential.access_token = token_data.access_token
    credential.refresh_token = token_data.refresh_token
    credential.token_uri = token_data.token_uri
    credential.client_id = token_data.client_id
    credential.client_secret = token_data.client_secret
    credential.scopes = token_data.scopes
    credential.expiry = token_data.expiry
    await session.flush()
    return credential


async def update_gmail_credential_tokens(
    session: AsyncSession,
    credential: GmailCredential,
    google_credentials: Credentials,
) -> GmailCredential:
    credential.access_token = google_credentials.token or credential.access_token
    if google_credentials.refresh_token:
        credential.refresh_token = google_credentials.refresh_token
    credential.expiry = google_credentials.expiry
    await session.flush()
    return credential


def credentials_from_gmail_credential(credential: GmailCredential) -> Credentials:
    return Credentials(
        token=credential.access_token,
        refresh_token=credential.refresh_token,
        token_uri=credential.token_uri,
        client_id=credential.client_id,
        client_secret=credential.client_secret,
        scopes=credential.scopes.split(),
        expiry=credential.expiry,
    )
