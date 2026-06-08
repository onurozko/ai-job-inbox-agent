from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.demo.constants import DEMO_USER_EMAIL
from app.demo.seed import get_demo_user


class DemoUserNotFoundError(RuntimeError):
    pass


async def create_demo_user_token(session: AsyncSession) -> str:
    user = await get_demo_user(session)
    if user is None:
        raise DemoUserNotFoundError(
            f"Demo user {DEMO_USER_EMAIL!r} was not found. Run scripts/seed_demo_data.py first."
        )
    return create_access_token(user_id=user.id, email=user.email)
