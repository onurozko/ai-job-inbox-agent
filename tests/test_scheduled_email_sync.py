from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.scheduler import (
    create_background_sync_scheduler,
    get_scheduler,
    shutdown_background_sync_scheduler,
    start_background_sync_scheduler,
)
from app.models.enums import EmailCategory
from app.models.user import User
from app.schemas.email import EmailClassificationResult
from app.services.email_sync import EmailSyncService, EmailSyncSummary
from app.services.gmail_credential_service import GmailTokenData, upsert_gmail_credential
from app.services.scheduled_email_sync_service import ScheduledEmailSyncService
from tests.test_email_sync import MockEmailClassifier, MockGmailClient, _parsed_message


@pytest.fixture(autouse=True)
def reset_scheduler_state() -> None:
    shutdown_background_sync_scheduler()
    yield
    shutdown_background_sync_scheduler()


def test_scheduler_does_not_start_when_background_sync_disabled() -> None:
    settings = Settings(enable_background_sync=False)

    assert create_background_sync_scheduler(settings) is None
    assert start_background_sync_scheduler(settings) is None
    assert get_scheduler() is None


@pytest.mark.asyncio
async def test_scheduler_starts_when_background_sync_enabled() -> None:
    settings = Settings(enable_background_sync=True, background_sync_interval_minutes=15)

    scheduler = start_background_sync_scheduler(settings)

    assert scheduler is not None
    assert get_scheduler() is scheduler
    assert scheduler.running is True
    job = scheduler.get_job("background_email_sync")
    assert job is not None
    assert job.trigger.interval.total_seconds() == 15 * 60


def _session_factory(session: AsyncSession) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(session.bind, class_=AsyncSession, expire_on_commit=False)


async def _seed_user_with_gmail(session: AsyncSession, *, email: str) -> User:
    user = User(email=email, full_name="Scheduled Sync User")
    session.add(user)
    await session.flush()
    await upsert_gmail_credential(
        session,
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
    await session.commit()
    return user


@pytest.mark.asyncio
async def test_scheduled_sync_processes_users_with_gmail_credentials(
    async_session: AsyncSession,
) -> None:
    user = await _seed_user_with_gmail(async_session, email="scheduled@test.com")

    mock_sync_service = AsyncMock()
    mock_sync_service.sync_user_emails.return_value = EmailSyncSummary(
        fetched_count=3,
        created_count=2,
        skipped_count=1,
        applications_updated_count=1,
    )

    service = ScheduledEmailSyncService(
        sync_service=mock_sync_service,
        session_factory=_session_factory(async_session),
        settings=Settings(enable_background_sync=True, background_sync_max_results=25),
    )

    summary = await service.run_scheduled_sync()

    assert summary.users_attempted == 1
    assert summary.users_succeeded == 1
    assert summary.users_failed == 0
    mock_sync_service.sync_user_emails.assert_awaited_once()
    call_kwargs = mock_sync_service.sync_user_emails.await_args.kwargs
    assert call_kwargs["user"].id == user.id
    assert call_kwargs["max_results"] == 25


@pytest.mark.asyncio
async def test_one_failed_user_does_not_stop_syncing_other_users(
    async_session: AsyncSession,
) -> None:
    await _seed_user_with_gmail(async_session, email="scheduled-a@test.com")
    await _seed_user_with_gmail(async_session, email="scheduled-b@test.com")

    mock_sync_service = AsyncMock()
    mock_sync_service.sync_user_emails.side_effect = [
        RuntimeError("Gmail API unavailable"),
        EmailSyncSummary(
            fetched_count=2,
            created_count=1,
            skipped_count=1,
            applications_updated_count=1,
        ),
    ]

    service = ScheduledEmailSyncService(
        sync_service=mock_sync_service,
        session_factory=_session_factory(async_session),
        settings=Settings(enable_background_sync=True),
    )

    summary = await service.run_scheduled_sync()

    assert summary.users_attempted == 2
    assert summary.users_succeeded == 1
    assert summary.users_failed == 1
    assert mock_sync_service.sync_user_emails.await_count == 2


@pytest.mark.asyncio
async def test_scheduled_sync_uses_existing_email_sync_service(async_session: AsyncSession) -> None:
    await _seed_user_with_gmail(async_session, email="workflow@test.com")

    parsed = _parsed_message("workflow-001", subject="Interview invite")
    classifier = MockEmailClassifier(
        {
            "workflow-001": EmailClassificationResult(
                category=EmailCategory.INTERVIEW_INVITATION,
                company_name="Acme",
                job_title="Engineer",
                summary="Interview scheduled",
                confidence_score=0.9,
            )
        }
    )

    service = ScheduledEmailSyncService(
        sync_service=EmailSyncService(classifier=classifier),
        session_factory=_session_factory(async_session),
        settings=Settings(background_sync_max_results=10),
    )

    with patch(
        "app.services.email_sync.GmailClient",
        side_effect=lambda *args, **kwargs: MockGmailClient([parsed]),
    ):
        summary = await service.run_scheduled_sync()

    assert summary.users_succeeded == 1
    assert summary.users_failed == 0
