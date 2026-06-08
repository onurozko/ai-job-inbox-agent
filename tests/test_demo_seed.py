import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.demo.constants import (
    DEMO_GMAIL_ID_PREFIX,
    DEMO_USER_EMAIL,
    DEMO_USER_FULL_NAME,
    DEMO_USER_GOOGLE_SUB,
)
from app.demo.guard import DemoScriptsNotAllowedError, ensure_demo_scripts_allowed
from app.demo.seed import build_demo_email_specs, demo_email_keys, get_demo_user, seed_demo_data
from app.demo.token import DemoUserNotFoundError, create_demo_user_token
from app.models.email_message import EmailMessage
from app.models.enums import EmailCategory
from app.models.user_profile import UserProfile


@pytest.fixture
def demo_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_seed_script_creates_demo_user_and_data(
    async_session: AsyncSession,
    demo_environment: None,
) -> None:
    ensure_demo_scripts_allowed()

    result = await seed_demo_data(async_session)
    await async_session.commit()

    user = await get_demo_user(async_session)
    assert user is not None
    assert user.email == DEMO_USER_EMAIL
    assert user.full_name == DEMO_USER_FULL_NAME
    assert user.google_sub == DEMO_USER_GOOGLE_SUB

    profile = (
        await async_session.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    ).scalar_one_or_none()
    assert profile is not None
    assert "FastAPI" in profile.resume_text

    emails = (
        (
            await async_session.execute(
                select(EmailMessage).where(
                    EmailMessage.user_id == user.id,
                    EmailMessage.gmail_message_id.like(f"{DEMO_GMAIL_ID_PREFIX}%"),
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(emails) == len(build_demo_email_specs())
    categories = {email.category for email in emails}
    assert EmailCategory.APPLICATION_CONFIRMATION in categories
    assert EmailCategory.ASSESSMENT in categories
    assert EmailCategory.INTERVIEW_INVITATION in categories
    assert EmailCategory.REJECTION in categories
    assert EmailCategory.RECRUITER_OUTREACH in categories
    assert EmailCategory.OFFER in categories

    assert result.emails_created == len(demo_email_keys())
    assert result.applications_count == len(demo_email_keys())
    assert result.events_count == len(demo_email_keys())


@pytest.mark.asyncio
async def test_seed_script_is_idempotent(
    async_session: AsyncSession,
    demo_environment: None,
) -> None:
    ensure_demo_scripts_allowed()

    first = await seed_demo_data(async_session)
    await async_session.commit()
    second = await seed_demo_data(async_session)
    await async_session.commit()

    assert first.emails_created == len(demo_email_keys())
    assert second.emails_created == 0
    assert second.emails_skipped == len(demo_email_keys())
    assert second.applications_count == first.applications_count
    assert second.events_count == first.events_count


def test_production_environment_blocks_demo_seeding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    get_settings.cache_clear()

    with pytest.raises(DemoScriptsNotAllowedError, match="production"):
        ensure_demo_scripts_allowed()


@pytest.mark.asyncio
async def test_demo_token_script_creates_valid_token_for_demo_user(
    async_session: AsyncSession,
    demo_environment: None,
) -> None:
    ensure_demo_scripts_allowed()
    await seed_demo_data(async_session)
    await async_session.commit()

    token = await create_demo_user_token(async_session)
    payload = decode_access_token(token)

    user = await get_demo_user(async_session)
    assert user is not None
    assert payload.sub == user.id
    assert payload.email == DEMO_USER_EMAIL


@pytest.mark.asyncio
async def test_demo_token_requires_seeded_user(
    async_session: AsyncSession, demo_environment: None
) -> None:
    ensure_demo_scripts_allowed()

    with pytest.raises(DemoUserNotFoundError, match=DEMO_USER_EMAIL):
        await create_demo_user_token(async_session)
