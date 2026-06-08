from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application_event import ApplicationEvent
from app.models.enums import ApplicationStatus, EventType
from app.models.job_application import JobApplication
from app.models.user import User
from app.services.analytics_service import AnalyticsService


async def _create_application(
    session: AsyncSession,
    *,
    user_id,
    company_name: str,
    status: ApplicationStatus,
    created_at: datetime | None = None,
) -> JobApplication:
    application = JobApplication(
        user_id=user_id,
        company_name=company_name,
        job_title="Software Engineer",
        company_name_normalized=company_name.lower(),
        job_title_normalized="software engineer",
        status=status,
    )
    if created_at is not None:
        application.created_at = created_at
        application.updated_at = created_at
    session.add(application)
    await session.flush()
    return application


async def _add_event(
    session: AsyncSession,
    *,
    application: JobApplication,
    event_type: EventType,
    occurred_at: datetime,
) -> ApplicationEvent:
    event = ApplicationEvent(
        job_application_id=application.id,
        event_type=event_type,
        title=f"{event_type.value} event",
        occurred_at=occurred_at,
    )
    session.add(event)
    await session.flush()
    return event


@pytest.mark.asyncio
async def test_analytics_returns_zero_values_for_user_with_no_applications(
    async_session: AsyncSession,
) -> None:
    user = User(email="empty-analytics@test.com", full_name="Empty Analytics")
    async_session.add(user)
    await async_session.flush()

    summary = await AnalyticsService().get_summary(async_session, user.id)

    assert summary.total_applications == 0
    assert summary.active_applications == 0
    assert summary.response_rate == 0.0
    assert summary.applications_by_status == {}
    assert summary.applications_by_company == {}
    assert summary.events_by_type == {}
    assert summary.weekly_application_trend == []
    assert summary.recent_activity_count_7d == 0
    assert summary.recent_activity_count_30d == 0
    assert summary.average_response_time_days is None


@pytest.mark.asyncio
async def test_analytics_counts_statuses_correctly(async_session: AsyncSession) -> None:
    user = User(email="status-analytics@test.com", full_name="Status Analytics")
    async_session.add(user)
    await async_session.flush()

    statuses = [
        ("Shopify", ApplicationStatus.INTERVIEW_SCHEDULED),
        ("Datadog", ApplicationStatus.ASSESSMENT),
        ("Stripe", ApplicationStatus.FOLLOW_UP),
        ("Meta", ApplicationStatus.REJECTED),
        ("Google", ApplicationStatus.OFFER_RECEIVED),
        ("Amazon", ApplicationStatus.APPLIED),
    ]
    for company, status in statuses:
        application = await _create_application(
            async_session,
            user_id=user.id,
            company_name=company,
            status=status,
        )
        await _add_event(
            async_session,
            application=application,
            event_type=EventType.STATUS_UPDATE,
            occurred_at=datetime(2026, 6, 5, 12, 0, tzinfo=UTC),
        )

    summary = await AnalyticsService().get_summary(async_session, user.id)

    assert summary.total_applications == 6
    assert summary.active_applications == 5
    assert summary.rejected_applications == 1
    assert summary.offers == 1
    assert summary.applications_by_status[ApplicationStatus.REJECTED.value] == 1
    assert summary.applications_by_status[ApplicationStatus.OFFER_RECEIVED.value] == 1
    assert summary.applications_by_company["Shopify"] == 1
    assert summary.applications_by_company["Meta"] == 1


@pytest.mark.asyncio
async def test_analytics_computes_rates_correctly(async_session: AsyncSession) -> None:
    user = User(email="rates-analytics@test.com", full_name="Rates Analytics")
    async_session.add(user)
    await async_session.flush()

    base = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)

    responded = await _create_application(
        async_session,
        user_id=user.id,
        company_name="Responded Co",
        status=ApplicationStatus.ASSESSMENT,
    )
    await _add_event(
        async_session,
        application=responded,
        event_type=EventType.APPLICATION_CONFIRMATION,
        occurred_at=base,
    )
    await _add_event(
        async_session,
        application=responded,
        event_type=EventType.ASSESSMENT,
        occurred_at=base + timedelta(days=1),
    )

    interviewed = await _create_application(
        async_session,
        user_id=user.id,
        company_name="Interview Co",
        status=ApplicationStatus.INTERVIEW_SCHEDULED,
    )
    await _add_event(
        async_session,
        application=interviewed,
        event_type=EventType.INTERVIEW_INVITATION,
        occurred_at=base + timedelta(days=2),
    )

    rejected = await _create_application(
        async_session,
        user_id=user.id,
        company_name="Rejected Co",
        status=ApplicationStatus.REJECTED,
    )
    await _add_event(
        async_session,
        application=rejected,
        event_type=EventType.REJECTION,
        occurred_at=base + timedelta(days=3),
    )

    offered = await _create_application(
        async_session,
        user_id=user.id,
        company_name="Offer Co",
        status=ApplicationStatus.OFFER_RECEIVED,
    )
    await _add_event(
        async_session,
        application=offered,
        event_type=EventType.OFFER,
        occurred_at=base + timedelta(days=4),
    )

    await _create_application(
        async_session,
        user_id=user.id,
        company_name="Silent Co",
        status=ApplicationStatus.APPLIED,
    )

    summary = await AnalyticsService().get_summary(async_session, user.id)

    assert summary.total_applications == 5
    assert summary.response_rate == pytest.approx(0.2)
    assert summary.rejection_rate == pytest.approx(0.2)
    assert summary.interview_rate == pytest.approx(0.2)
    assert summary.offer_rate == pytest.approx(0.2)
    assert summary.interviews == 1
    assert summary.assessments == 1


@pytest.mark.asyncio
async def test_analytics_computes_average_response_time_days_correctly(
    async_session: AsyncSession,
) -> None:
    user = User(email="response-time@test.com", full_name="Response Time")
    async_session.add(user)
    await async_session.flush()

    base = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)

    first = await _create_application(
        async_session,
        user_id=user.id,
        company_name="Fast Co",
        status=ApplicationStatus.ASSESSMENT,
    )
    await _add_event(
        async_session,
        application=first,
        event_type=EventType.APPLICATION_CONFIRMATION,
        occurred_at=base,
    )
    await _add_event(
        async_session,
        application=first,
        event_type=EventType.ASSESSMENT,
        occurred_at=base + timedelta(days=2),
    )

    second = await _create_application(
        async_session,
        user_id=user.id,
        company_name="Slow Co",
        status=ApplicationStatus.INTERVIEW_SCHEDULED,
    )
    await _add_event(
        async_session,
        application=second,
        event_type=EventType.APPLICATION_CONFIRMATION,
        occurred_at=base,
    )
    await _add_event(
        async_session,
        application=second,
        event_type=EventType.INTERVIEW_INVITATION,
        occurred_at=base + timedelta(days=6),
    )

    summary = await AnalyticsService().get_summary(async_session, user.id)

    assert summary.average_response_time_days == pytest.approx(4.0)


@pytest.mark.asyncio
async def test_user_cannot_see_other_users_analytics(
    client: AsyncClient,
    async_session: AsyncSession,
    user_a: User,
    user_b: User,
    user_b_headers: dict[str, str],
) -> None:
    application = await _create_application(
        async_session,
        user_id=user_a.id,
        company_name="Private Co",
        status=ApplicationStatus.APPLIED,
    )
    await _add_event(
        async_session,
        application=application,
        event_type=EventType.APPLICATION_CONFIRMATION,
        occurred_at=datetime(2026, 6, 5, 12, 0, tzinfo=UTC),
    )
    await async_session.commit()

    response = await client.get("/api/v1/analytics/summary", headers=user_b_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_applications"] == 0
    assert payload["applications_by_company"] == {}


@pytest.mark.asyncio
async def test_weekly_trend_groups_applications_correctly(async_session: AsyncSession) -> None:
    user = User(email="weekly-analytics@test.com", full_name="Weekly Analytics")
    async_session.add(user)
    await async_session.flush()

    week_one = datetime(2026, 6, 2, 10, 0, tzinfo=UTC)
    week_two = datetime(2026, 6, 9, 10, 0, tzinfo=UTC)

    await _create_application(
        async_session,
        user_id=user.id,
        company_name="Week One A",
        status=ApplicationStatus.APPLIED,
        created_at=week_one,
    )
    await _create_application(
        async_session,
        user_id=user.id,
        company_name="Week One B",
        status=ApplicationStatus.APPLIED,
        created_at=week_one + timedelta(days=1),
    )
    await _create_application(
        async_session,
        user_id=user.id,
        company_name="Week Two",
        status=ApplicationStatus.APPLIED,
        created_at=week_two,
    )

    summary = await AnalyticsService().get_summary(async_session, user.id)

    assert [point.model_dump(mode="json") for point in summary.weekly_application_trend] == [
        {"week_start": "2026-06-01", "count": 2},
        {"week_start": "2026-06-08", "count": 1},
    ]
