from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application_event import ApplicationEvent
from app.models.email_message import EmailMessage
from app.models.enums import ApplicationStatus, EventType
from app.models.job_application import JobApplication
from app.models.user import User
from app.services.dashboard_service import DashboardService


async def _seed_dashboard_data(async_session: AsyncSession) -> User:
    user = User(email="dashboard@test.com", full_name="Dashboard Test")
    async_session.add(user)
    await async_session.flush()

    apps = [
        ("Shopify", ApplicationStatus.INTERVIEW_SCHEDULED),
        ("Datadog", ApplicationStatus.ASSESSMENT),
        ("Stripe", ApplicationStatus.FOLLOW_UP),
        ("Meta", ApplicationStatus.REJECTED),
        ("Google", ApplicationStatus.OFFER_RECEIVED),
        ("Amazon", ApplicationStatus.APPLIED),
    ]
    for company, status in apps:
        application = JobApplication(
            user_id=user.id,
            company_name=company,
            job_title="Software Engineer",
            company_name_normalized=company.lower(),
            job_title_normalized="software engineer",
            status=status,
            action_required=status in {ApplicationStatus.FOLLOW_UP, ApplicationStatus.ASSESSMENT},
            last_email_at=datetime(2026, 6, 5, tzinfo=UTC),
        )
        async_session.add(application)
        await async_session.flush()

        event = ApplicationEvent(
            job_application_id=application.id,
            event_type=EventType.STATUS_UPDATE,
            title=f"{company} update",
            occurred_at=datetime(2026, 6, 5, 12, 0, tzinfo=UTC),
        )
        async_session.add(event)

    return user


@pytest.mark.asyncio
async def test_dashboard_summary_counts_statuses_correctly(async_session: AsyncSession) -> None:
    user = await _seed_dashboard_data(async_session)
    service = DashboardService()

    summary = await service.get_summary(async_session, user.id)

    assert summary.total_applications == 6
    assert summary.active_applications == 5
    assert summary.rejected_applications == 1
    assert summary.interviews_scheduled == 1
    assert summary.assessments_pending == 1
    assert summary.offers == 1
    assert summary.follow_ups_needed == 2
    assert len(summary.recent_events) == 6


@pytest.mark.asyncio
async def test_timeline_returns_events_in_chronological_order(async_session: AsyncSession) -> None:
    user = User(email="timeline@test.com", full_name="Timeline Test")
    async_session.add(user)
    await async_session.flush()

    application = JobApplication(
        user_id=user.id,
        company_name="Shopify",
        job_title="Software Engineer",
        company_name_normalized="shopify",
        job_title_normalized="software engineer",
        status=ApplicationStatus.INTERVIEW_SCHEDULED,
    )
    async_session.add(application)
    await async_session.flush()

    now = datetime.now(UTC)
    dates = [
        now - timedelta(days=10),
        now - timedelta(days=5),
        now - timedelta(days=1),
    ]
    emails: list[EmailMessage] = []
    for index, received_at in enumerate(dates, start=1):
        email = EmailMessage(
            user_id=user.id,
            gmail_message_id=f"gmail-{index}",
            subject=f"Event {index}",
            sender_email="jobs@shopify.com",
            received_at=received_at,
            company_name="Shopify",
            deadline=now + timedelta(days=3) if index == 2 else None,
            interview_date=now + timedelta(days=2) if index == 3 else None,
        )
        async_session.add(email)
        await async_session.flush()
        emails.append(email)

        async_session.add(
            ApplicationEvent(
                job_application_id=application.id,
                email_message_id=email.id,
                event_type=EventType.APPLICATION_CONFIRMATION,
                title=f"Event {index}",
                occurred_at=received_at,
                metadata_={"deadline": (now + timedelta(days=3)).isoformat()}
                if index == 2
                else None,
            )
        )

    service = DashboardService()
    timeline = await service.get_application_timeline(async_session, user.id, application.id)

    assert timeline is not None
    assert timeline.current_status == ApplicationStatus.INTERVIEW_SCHEDULED
    assert [event.title for event in timeline.events] == ["Event 1", "Event 2", "Event 3"]
    assert (
        timeline.events[0].occurred_at
        <= timeline.events[1].occurred_at
        <= timeline.events[2].occurred_at
    )
    assert len(timeline.emails) == 3
    assert timeline.next_deadline is not None
    assert timeline.next_interview_date is not None
