from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_message import EmailMessage
from app.models.enums import ApplicationStatus, EmailCategory, EventType
from app.models.user import User
from app.schemas.email import EmailClassificationResult
from app.services.application_updater import ApplicationUpdater


@pytest.mark.asyncio
async def test_process_classified_email_updates_status_and_event(
    async_session: AsyncSession,
) -> None:
    user = User(email="updater@test.com", full_name="Updater Test")
    async_session.add(user)
    await async_session.flush()

    received_at = datetime(2026, 6, 5, 12, 0, tzinfo=UTC)
    email = EmailMessage(
        user_id=user.id,
        gmail_message_id="msg-001",
        subject="Interview invitation from Shopify",
        sender_email="recruiting@shopify.com",
        received_at=received_at,
        raw_snippet="We would like to invite you to an interview.",
    )
    async_session.add(email)
    await async_session.flush()

    classification = EmailClassificationResult(
        category=EmailCategory.INTERVIEW_INVITATION,
        company_name="Shopify",
        job_title="Software Engineer",
        summary="Interview scheduled for next week",
        action_required=True,
        confidence_score=0.9,
    )

    updater = ApplicationUpdater()
    application, event = await updater.process_classified_email(
        async_session, email, classification
    )

    assert application.status == ApplicationStatus.INTERVIEW_SCHEDULED
    assert application.company_name == "Shopify"
    assert application.action_required is True
    assert event.event_type == EventType.INTERVIEW_INVITATION
    assert event.email_message_id == email.id


@pytest.mark.asyncio
async def test_multiple_emails_share_one_application(async_session: AsyncSession) -> None:
    user = User(email="timeline@test.com", full_name="Timeline Test")
    async_session.add(user)
    await async_session.flush()

    updater = ApplicationUpdater()
    received_at = datetime(2026, 6, 5, tzinfo=UTC)

    categories = [
        (EmailCategory.APPLICATION_CONFIRMATION, ApplicationStatus.APPLIED),
        (EmailCategory.ASSESSMENT, ApplicationStatus.ASSESSMENT),
        (EmailCategory.INTERVIEW_INVITATION, ApplicationStatus.INTERVIEW_SCHEDULED),
    ]

    application_ids: set[str] = set()
    for index, (category, expected_status) in enumerate(categories, start=1):
        email = EmailMessage(
            user_id=user.id,
            gmail_message_id=f"msg-{index}",
            subject=f"{category.value} from Shopify",
            sender_email="jobs@shopify.com",
            received_at=received_at,
        )
        async_session.add(email)
        await async_session.flush()

        classification = EmailClassificationResult(
            category=category,
            company_name="Shopify",
            job_title="Software Engineer",
            summary=f"Event {index}",
            confidence_score=0.8,
        )
        application, _ = await updater.process_classified_email(
            async_session, email, classification
        )
        application_ids.add(str(application.id))
        assert application.status == expected_status

    assert len(application_ids) == 1
