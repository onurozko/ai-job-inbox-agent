from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_message import EmailMessage
from app.models.enums import EmailCategory


async def get_email_for_user(
    session: AsyncSession,
    *,
    user_id: UUID,
    email_id: UUID,
) -> EmailMessage | None:
    stmt = select(EmailMessage).where(
        EmailMessage.id == email_id,
        EmailMessage.user_id == user_id,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_emails_for_user(
    session: AsyncSession,
    *,
    user_id: UUID,
    page: int,
    page_size: int,
    category: EmailCategory | None = None,
) -> tuple[list[EmailMessage], int]:
    filters = [EmailMessage.user_id == user_id]
    if category is not None:
        filters.append(EmailMessage.category == category)

    count_stmt = select(func.count()).select_from(EmailMessage).where(*filters)
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = (
        select(EmailMessage)
        .where(*filters)
        .order_by(EmailMessage.received_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list((await session.execute(stmt)).scalars().all())
    return items, total
