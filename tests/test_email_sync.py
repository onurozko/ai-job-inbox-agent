from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.gmail.client import ParsedGmailMessage
from app.integrations.gmail.errors import GmailCredentialsMissingError
from app.models.application_event import ApplicationEvent
from app.models.email_message import EmailMessage
from app.models.enums import ApplicationStatus, EmailCategory, EventType
from app.models.job_application import JobApplication
from app.models.user import User
from app.schemas.email import EmailClassificationResult
from app.services.application_updater import ApplicationUpdater
from app.services.email_classifier import EmailClassifier
from app.services.email_sync import EmailSyncService
from app.services.gmail_credential_service import GmailTokenData, upsert_gmail_credential


def _parsed_message(
    message_id: str,
    *,
    subject: str,
    body: str = "body",
) -> ParsedGmailMessage:
    return ParsedGmailMessage(
        gmail_message_id=message_id,
        thread_id=f"thread-{message_id}",
        subject=subject,
        sender_email="jobs@shopify.com",
        raw_snippet=body[:100],
        body_text=body,
        received_at=datetime(2026, 6, 5, 12, 0, tzinfo=UTC),
    )


class MockGmailClient:
    def __init__(self, messages: list[ParsedGmailMessage]) -> None:
        self._messages = messages

    async def fetch_recent_messages_async(
        self, *, query: str, max_results: int
    ) -> list[ParsedGmailMessage]:
        return self._messages[:max_results]


class MockEmailClassifier(EmailClassifier):
    def __init__(self, classifications: dict[str, EmailClassificationResult]) -> None:
        self._classifications = classifications

    async def classify(self, email: EmailMessage) -> EmailClassificationResult:
        return self._classifications[email.gmail_message_id]


async def _seed_user_with_gmail(async_session: AsyncSession) -> User:
    user = User(email="sync@test.com", full_name="Sync Test")
    async_session.add(user)
    await async_session.flush()
    await upsert_gmail_credential(
        async_session,
        user_id=user.id,
        token_data=GmailTokenData(
            access_token="access-token",
            refresh_token="refresh-token",
            token_uri="https://oauth2.googleapis.com/token",
            client_id="client-id",
            client_secret="client-secret",
            scopes="https://www.googleapis.com/auth/gmail.readonly",
        ),
    )
    return user


@pytest.mark.asyncio
async def test_sync_raises_when_gmail_credentials_missing(async_session: AsyncSession) -> None:
    user = User(email="missing-creds@test.com", full_name="No Gmail")
    async_session.add(user)
    await async_session.flush()

    service = EmailSyncService()
    with pytest.raises(GmailCredentialsMissingError):
        await service.sync_user_emails(async_session, user=user)


@pytest.mark.asyncio
async def test_sync_skips_duplicate_gmail_messages(async_session: AsyncSession) -> None:
    user = await _seed_user_with_gmail(async_session)
    parsed = _parsed_message("gmail-001", subject="Application received")

    classifier = MockEmailClassifier(
        {
            "gmail-001": EmailClassificationResult(
                category=EmailCategory.APPLICATION_CONFIRMATION,
                company_name="Shopify",
                job_title="Software Engineer",
                summary="Application confirmed",
                confidence_score=0.9,
            )
        }
    )
    service = EmailSyncService(classifier=classifier)
    gmail_client = MockGmailClient([parsed])

    first = await service.sync_user_emails(async_session, user=user, gmail_client=gmail_client)
    second = await service.sync_user_emails(async_session, user=user, gmail_client=gmail_client)

    assert first.fetched_count == 1
    assert first.created_count == 1
    assert first.skipped_count == 0

    assert second.fetched_count == 1
    assert second.created_count == 0
    assert second.skipped_count == 1

    count_stmt = (
        select(func.count()).select_from(EmailMessage).where(EmailMessage.user_id == user.id)
    )
    assert (await async_session.execute(count_stmt)).scalar_one() == 1


@pytest.mark.asyncio
async def test_irrelevant_emails_do_not_create_job_applications(
    async_session: AsyncSession,
) -> None:
    user = await _seed_user_with_gmail(async_session)
    parsed = _parsed_message("gmail-irrelevant", subject="Newsletter")

    classifier = MockEmailClassifier(
        {
            "gmail-irrelevant": EmailClassificationResult(
                category=EmailCategory.IRRELEVANT,
                company_name="Shopify",
                summary="Not job related",
                confidence_score=0.95,
            )
        }
    )
    service = EmailSyncService(classifier=classifier)
    summary = await service.sync_user_emails(
        async_session,
        user=user,
        gmail_client=MockGmailClient([parsed]),
    )

    assert summary.created_count == 1
    assert summary.applications_updated_count == 0

    app_count = (
        select(func.count()).select_from(JobApplication).where(JobApplication.user_id == user.id)
    )
    assert (await async_session.execute(app_count)).scalar_one() == 0


@pytest.mark.asyncio
async def test_shopify_timeline_updates_one_application_with_three_events(
    async_session: AsyncSession,
) -> None:
    user = await _seed_user_with_gmail(async_session)
    messages = [
        _parsed_message(
            "shopify-1", subject="Application confirmation", body="Your application was received"
        ),
        _parsed_message(
            "shopify-2", subject="Assessment invitation", body="Complete this assessment"
        ),
        _parsed_message(
            "shopify-3", subject="Interview invitation", body="We would like to interview you"
        ),
    ]
    classifier = MockEmailClassifier(
        {
            "shopify-1": EmailClassificationResult(
                category=EmailCategory.APPLICATION_CONFIRMATION,
                company_name="Shopify",
                job_title="Software Engineer",
                summary="Application confirmed",
                confidence_score=0.9,
            ),
            "shopify-2": EmailClassificationResult(
                category=EmailCategory.ASSESSMENT,
                company_name="Shopify",
                job_title="Software Engineer",
                summary="Assessment requested",
                action_required=True,
                confidence_score=0.9,
            ),
            "shopify-3": EmailClassificationResult(
                category=EmailCategory.INTERVIEW_INVITATION,
                company_name="Shopify",
                job_title="Software Engineer",
                summary="Interview scheduled",
                action_required=True,
                confidence_score=0.9,
            ),
        }
    )
    service = EmailSyncService(classifier=classifier)
    summary = await service.sync_user_emails(
        async_session,
        user=user,
        gmail_client=MockGmailClient(messages),
    )

    assert summary.created_count == 3
    assert summary.applications_updated_count == 1

    applications = (
        (
            await async_session.execute(
                select(JobApplication).where(JobApplication.user_id == user.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(applications) == 1
    assert applications[0].company_name == "Shopify"
    assert applications[0].status == ApplicationStatus.INTERVIEW_SCHEDULED

    events = (
        (
            await async_session.execute(
                select(ApplicationEvent).where(
                    ApplicationEvent.job_application_id == applications[0].id
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(events) == 3
    assert {event.event_type for event in events} == {
        EventType.APPLICATION_CONFIRMATION,
        EventType.ASSESSMENT,
        EventType.INTERVIEW_INVITATION,
    }


@pytest.mark.asyncio
async def test_irrelevant_classification_skips_application_updater(
    async_session: AsyncSession,
) -> None:
    user = User(email="irrelevant@test.com", full_name="Irrelevant Test")
    async_session.add(user)
    await async_session.flush()

    email = EmailMessage(
        user_id=user.id,
        gmail_message_id="local-1",
        subject="Newsletter",
        sender_email="news@example.com",
        received_at=datetime(2026, 6, 5, tzinfo=UTC),
    )
    async_session.add(email)
    await async_session.flush()

    updater = ApplicationUpdater()
    application, event = await updater.process_classified_email(
        async_session,
        email,
        EmailClassificationResult(
            category=EmailCategory.IRRELEVANT,
            summary="Not relevant",
            confidence_score=0.99,
        ),
    )

    assert application is None
    assert event is None
