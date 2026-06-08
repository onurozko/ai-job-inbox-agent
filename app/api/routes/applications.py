import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.enums import ApplicationStatus
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.dashboard import ApplicationTimeline
from app.schemas.job_application import (
    JobApplicationDetail,
    JobApplicationRead,
    JobApplicationSummary,
    JobApplicationUpdate,
)
from app.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=PaginatedResponse[JobApplicationSummary])
async def list_applications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: ApplicationStatus | None = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ApplicationService()
    return await service.list_applications(
        session,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
    )


@router.get("/{application_id}", response_model=JobApplicationDetail)
async def get_application(
    application_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobApplicationDetail:
    service = ApplicationService()
    return await service.get_application(
        session,
        user_id=current_user.id,
        application_id=application_id,
    )


@router.get("/{application_id}/timeline", response_model=ApplicationTimeline)
async def get_application_timeline(
    application_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationTimeline:
    service = ApplicationService()
    return await service.get_timeline(
        session,
        user_id=current_user.id,
        application_id=application_id,
    )


@router.patch("/{application_id}", response_model=JobApplicationRead)
async def update_application(
    application_id: uuid.UUID,
    payload: JobApplicationUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobApplicationRead:
    service = ApplicationService()
    return await service.update_application(
        session,
        user_id=current_user.id,
        application_id=application_id,
        payload=payload,
    )
