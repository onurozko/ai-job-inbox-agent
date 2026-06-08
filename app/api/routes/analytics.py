from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.analytics import AnalyticsSummary
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyticsSummary:
    service = AnalyticsService()
    return await service.get_summary(session, current_user.id)
