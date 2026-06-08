from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.user_profile import UserProfile
from app.schemas.profile import ResumeProfileRead, ResumeProfileUpdate


def _to_profile_read(profile: UserProfile) -> ResumeProfileRead:
    return ResumeProfileRead(
        id=profile.id,
        user_id=profile.user_id,
        resume_text=profile.resume_text,
        target_roles=profile.target_roles,
        target_locations=profile.target_locations,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


class ProfileService:
    async def upsert_resume(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        payload: ResumeProfileUpdate,
    ) -> ResumeProfileRead:
        profile = await self._get_profile(session, user_id)
        if profile is None:
            profile = UserProfile(user_id=user_id, resume_text=payload.resume_text)
            session.add(profile)
        else:
            profile.resume_text = payload.resume_text

        profile.target_roles = payload.target_roles
        profile.target_locations = payload.target_locations
        await session.flush()
        await session.refresh(profile)
        return _to_profile_read(profile)

    async def get_resume(self, session: AsyncSession, *, user_id: UUID) -> ResumeProfileRead:
        profile = await self.get_profile_for_user(session, user_id)
        if profile is None:
            raise NotFoundError("Resume profile not found")
        return _to_profile_read(profile)

    @staticmethod
    async def get_profile_for_user(session: AsyncSession, user_id: UUID) -> UserProfile | None:
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_profile(session: AsyncSession, user_id: UUID) -> UserProfile | None:
        return await ProfileService.get_profile_for_user(session, user_id)
