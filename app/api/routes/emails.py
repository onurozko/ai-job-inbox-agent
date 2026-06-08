import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.enums import EmailCategory
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.email import EmailMessageRead, EmailSyncRequest, EmailSyncResponse
from app.services.email_service import EmailService

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("", response_model=PaginatedResponse[EmailMessageRead])
async def list_emails(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: EmailCategory | None = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EmailService()
    return await service.list_emails(
        session,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        category=category,
    )


@router.get("/{email_id}", response_model=EmailMessageRead)
async def get_email(
    email_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EmailMessageRead:
    service = EmailService()
    return await service.get_email(session, user_id=current_user.id, email_id=email_id)


@router.post("/sync", response_model=EmailSyncResponse)
async def sync_emails(
    payload: EmailSyncRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EmailSyncResponse:
    service = EmailService()
    return await service.sync_emails(session, user=current_user, payload=payload)


@router.post("/{email_id}/reprocess", response_model=EmailMessageRead)
async def reprocess_email(
    email_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EmailMessageRead:
    service = EmailService()
    return await service.reprocess_email(
        session,
        user_id=current_user.id,
        email_id=email_id,
    )
