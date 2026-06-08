import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ApplicationStatus
from app.models.user import User
from app.services.application_matcher import (
    ApplicationMatcher,
    normalize_company_name,
    normalize_job_title,
)


def test_normalize_company_name_strips_legal_suffixes() -> None:
    assert normalize_company_name("Shopify Inc.") == "shopify"
    assert normalize_company_name("Acme Corporation") == "acme"


def test_normalize_job_title_handles_empty() -> None:
    assert normalize_job_title(None) == ""
    assert normalize_job_title("  Senior   Engineer  ") == "senior engineer"


@pytest.mark.asyncio
async def test_find_or_create_application_reuses_existing(async_session: AsyncSession) -> None:
    user = User(email="matcher@test.com", full_name="Matcher Test")
    async_session.add(user)
    await async_session.flush()

    matcher = ApplicationMatcher()
    first = await matcher.find_or_create_application(
        async_session,
        user_id=user.id,
        company_name="Shopify Inc.",
        job_title="Software Engineer",
        status=ApplicationStatus.APPLIED,
    )
    second = await matcher.find_or_create_application(
        async_session,
        user_id=user.id,
        company_name="Shopify",
        job_title="Software Engineer",
        status=ApplicationStatus.ASSESSMENT,
    )

    assert first.id == second.id
    assert first.company_name_normalized == "shopify"
