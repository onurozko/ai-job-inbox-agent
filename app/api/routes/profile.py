from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.profile import ResumeProfileRead, ResumeProfileUpdate
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


@router.put("/resume", response_model=ResumeProfileRead)
async def upsert_resume_profile(
    payload: ResumeProfileUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeProfileRead:
    service = ProfileService()
    return await service.upsert_resume(session, user_id=current_user.id, payload=payload)


@router.get("/resume", response_model=ResumeProfileRead)
async def get_resume_profile(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeProfileRead:
    service = ProfileService()
    return await service.get_resume(session, user_id=current_user.id)
