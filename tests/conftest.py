import os

os.environ["APP_ENV"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-for-jwt-signing-min-32-bytes!!"
os.environ["DATABASE_URL"] = (
    "sqlite+aiosqlite:///file:jobinbox_test?mode=memory&cache=shared&uri=true"
)

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import Uuid

from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import close_db, get_db, init_db
from app.main import app
from app.models.user import User

get_settings.cache_clear()

TEST_DATABASE_URL = os.environ["DATABASE_URL"]


def _prepare_sqlite_metadata() -> None:
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, JSONB):
                column.type = JSON()
            if isinstance(column.type, PGUUID):
                column.type = Uuid(as_uuid=True)
            if hasattr(column.type, "native_enum"):
                column.type.native_enum = False


_prepare_sqlite_metadata()


@pytest.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False, "uri": True},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(async_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    await close_db()
    await init_db()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield async_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    await close_db()


async def create_test_user(
    session: AsyncSession,
    *,
    email: str,
    google_sub: str,
    full_name: str = "Test User",
) -> User:
    user = User(
        email=email,
        google_sub=google_sub,
        full_name=full_name,
    )
    session.add(user)
    await session.flush()
    return user


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(user_id=user.id, email=user.email)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def user_a(async_session: AsyncSession) -> User:
    return await create_test_user(
        async_session,
        email="usera@test.com",
        google_sub="google-sub-a",
        full_name="User A",
    )


@pytest.fixture
async def user_b(async_session: AsyncSession) -> User:
    return await create_test_user(
        async_session,
        email="userb@test.com",
        google_sub="google-sub-b",
        full_name="User B",
    )


@pytest.fixture
def user_a_headers(user_a: User) -> dict[str, str]:
    return auth_headers(user_a)


@pytest.fixture
def user_b_headers(user_b: User) -> dict[str, str]:
    return auth_headers(user_b)
