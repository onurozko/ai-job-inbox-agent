from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import ApplicationStatus
from app.models.job_application import JobApplication


async def get_application_for_user(
    session: AsyncSession,
    *,
    user_id: UUID,
    application_id: UUID,
    load_events: bool = False,
) -> JobApplication | None:
    stmt = select(JobApplication).where(
        JobApplication.id == application_id,
        JobApplication.user_id == user_id,
    )
    if load_events:
        stmt = stmt.options(selectinload(JobApplication.events))
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_applications_for_user(
    session: AsyncSession,
    *,
    user_id: UUID,
    page: int,
    page_size: int,
    status_filter: ApplicationStatus | None = None,
) -> tuple[list[JobApplication], int]:
    filters = [JobApplication.user_id == user_id]
    if status_filter is not None:
        filters.append(JobApplication.status == status_filter)

    count_stmt = select(func.count()).select_from(JobApplication).where(*filters)
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = (
        select(JobApplication)
        .where(*filters)
        .order_by(JobApplication.last_email_at.desc().nullslast(), JobApplication.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list((await session.execute(stmt)).scalars().all())
    return items, total
