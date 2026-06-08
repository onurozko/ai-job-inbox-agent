from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    return await session.get(User, user_id)


async def get_user_by_google_sub(session: AsyncSession, google_sub: str) -> User | None:
    stmt = select(User).where(User.google_sub == google_sub)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_or_update_user_from_google(
    session: AsyncSession,
    *,
    google_sub: str,
    email: str,
    full_name: str | None,
    picture_url: str | None,
) -> User:
    user = await get_user_by_google_sub(session, google_sub)
    if user is None:
        email_stmt = select(User).where(User.email == email)
        existing_by_email = (await session.execute(email_stmt)).scalar_one_or_none()
        if existing_by_email is not None:
            user = existing_by_email
            user.google_sub = google_sub
        else:
            user = User(
                google_sub=google_sub,
                email=email,
                full_name=full_name,
                picture_url=picture_url,
            )
            session.add(user)

    user.email = email
    user.full_name = full_name
    user.picture_url = picture_url
    await session.flush()
    return user
