from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.repositories import job_application_repository
from app.models.enums import ApplicationStatus
from app.schemas.common import PaginatedResponse
from app.schemas.dashboard import ApplicationTimeline
from app.schemas.job_application import (
    JobApplicationDetail,
    JobApplicationRead,
    JobApplicationSummary,
    JobApplicationUpdate,
)
from app.services.dashboard_service import DashboardService


class ApplicationService:
    def __init__(self, dashboard_service: DashboardService | None = None) -> None:
        self._dashboard_service = dashboard_service or DashboardService()

    async def list_applications(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        page: int,
        page_size: int,
        status_filter: ApplicationStatus | None = None,
    ) -> PaginatedResponse[JobApplicationSummary]:
        items, total = await job_application_repository.list_applications_for_user(
            session,
            user_id=user_id,
            page=page,
            page_size=page_size,
            status_filter=status_filter,
        )
        return PaginatedResponse(
            items=[JobApplicationSummary.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_application(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        application_id: UUID,
    ) -> JobApplicationDetail:
        application = await job_application_repository.get_application_for_user(
            session,
            user_id=user_id,
            application_id=application_id,
            load_events=True,
        )
        if application is None:
            raise NotFoundError("Application not found")
        return JobApplicationDetail.model_validate(application)

    async def get_timeline(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        application_id: UUID,
    ) -> ApplicationTimeline:
        timeline = await self._dashboard_service.get_application_timeline(
            session,
            user_id,
            application_id,
        )
        if timeline is None:
            raise NotFoundError("Application not found")
        return timeline

    async def update_application(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        application_id: UUID,
        payload: JobApplicationUpdate,
    ) -> JobApplicationRead:
        application = await job_application_repository.get_application_for_user(
            session,
            user_id=user_id,
            application_id=application_id,
        )
        if application is None:
            raise NotFoundError("Application not found")

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(application, field, value)

        await session.flush()
        return JobApplicationRead.model_validate(application)
