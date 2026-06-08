from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.common import HealthResponse


class HealthService:
    @staticmethod
    async def check_health(session: AsyncSession) -> HealthResponse:
        db_status = "connected"
        try:
            await session.execute(text("SELECT 1"))
        except Exception:
            db_status = "disconnected"
        return HealthResponse(status="ok", db=db_status)
