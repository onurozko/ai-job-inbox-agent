from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.datetime_utils import parse_datetime
from app.models.application_event import ApplicationEvent
from app.models.enums import ApplicationStatus, EventType
from app.models.job_application import JobApplication
from app.schemas.analytics import AnalyticsSummary, WeeklyApplicationTrendPoint

MEANINGFUL_RESPONSE_EVENT_TYPES = {
    EventType.REJECTION,
    EventType.INTERVIEW_INVITATION,
    EventType.ASSESSMENT,
    EventType.OFFER,
    EventType.RECRUITER_OUTREACH,
    EventType.FOLLOW_UP_NEEDED,
}


class AnalyticsService:
    async def get_summary(self, session: AsyncSession, user_id: UUID) -> AnalyticsSummary:
        applications = await self._load_user_applications(session, user_id)
        total = len(applications)

        if total == 0:
            return AnalyticsSummary()

        now = datetime.now(UTC)
        events = [event for application in applications for event in application.events]
        events_by_type = Counter(event.event_type.value for event in events)

        applications_by_status = Counter(app.status.value for app in applications)
        applications_by_company = Counter(app.company_name for app in applications)

        rejected = applications_by_status[ApplicationStatus.REJECTED.value]
        active = total - rejected
        offers = applications_by_status[ApplicationStatus.OFFER_RECEIVED.value]

        applications_with_interview = self._count_applications_with_event_type(
            applications,
            EventType.INTERVIEW_INVITATION,
        )
        applications_with_assessment = self._count_applications_with_event_type(
            applications,
            EventType.ASSESSMENT,
        )
        applications_with_response = self._count_applications_with_response_after_confirmation(
            applications
        )
        applications_with_offer = self._count_applications_with_offer(applications)

        weekly_trend = self._build_weekly_application_trend(applications)
        average_response_time_days = self._calculate_average_response_time_days(applications)

        return AnalyticsSummary(
            total_applications=total,
            active_applications=active,
            rejected_applications=rejected,
            offers=offers,
            interviews=applications_with_interview,
            assessments=applications_with_assessment,
            recruiter_outreach_count=events_by_type[EventType.RECRUITER_OUTREACH.value],
            response_rate=applications_with_response / total,
            rejection_rate=rejected / total,
            interview_rate=applications_with_interview / total,
            offer_rate=applications_with_offer / total,
            average_response_time_days=average_response_time_days,
            applications_by_status=dict(applications_by_status),
            applications_by_company=dict(applications_by_company),
            events_by_type=dict(events_by_type),
            weekly_application_trend=weekly_trend,
            recent_activity_count_7d=self._count_recent_events(events, now=now, days=7),
            recent_activity_count_30d=self._count_recent_events(events, now=now, days=30),
        )

    @staticmethod
    async def _load_user_applications(
        session: AsyncSession,
        user_id: UUID,
    ) -> list[JobApplication]:
        stmt = (
            select(JobApplication)
            .where(JobApplication.user_id == user_id)
            .options(selectinload(JobApplication.events))
            .order_by(JobApplication.created_at.asc())
        )
        return list((await session.execute(stmt)).scalars().all())

    @staticmethod
    def _count_applications_with_event_type(
        applications: list[JobApplication],
        event_type: EventType,
    ) -> int:
        return sum(
            1
            for application in applications
            if any(event.event_type == event_type for event in application.events)
        )

    @staticmethod
    def _count_applications_with_offer(applications: list[JobApplication]) -> int:
        return sum(
            1
            for application in applications
            if application.status == ApplicationStatus.OFFER_RECEIVED
            or any(event.event_type == EventType.OFFER for event in application.events)
        )

    @staticmethod
    def _count_applications_with_response_after_confirmation(
        applications: list[JobApplication],
    ) -> int:
        count = 0
        for application in applications:
            confirmation = AnalyticsService._first_event_of_type(
                application.events,
                EventType.APPLICATION_CONFIRMATION,
            )
            if confirmation is None:
                continue
            if AnalyticsService._has_event_after(application.events, confirmation.occurred_at):
                count += 1
        return count

    @staticmethod
    def _calculate_average_response_time_days(
        applications: list[JobApplication],
    ) -> float | None:
        response_times: list[float] = []

        for application in applications:
            confirmation = AnalyticsService._first_event_of_type(
                application.events,
                EventType.APPLICATION_CONFIRMATION,
            )
            if confirmation is None:
                continue

            confirmation_at = parse_datetime(confirmation.occurred_at)
            if confirmation_at is None:
                continue

            response_event = AnalyticsService._first_meaningful_response_after(
                application.events,
                confirmation_at,
            )
            if response_event is None:
                continue

            response_at = parse_datetime(response_event.occurred_at)
            if response_at is None:
                continue

            delta_days = (response_at - confirmation_at).total_seconds() / 86400
            if delta_days >= 0:
                response_times.append(delta_days)

        if not response_times:
            return None

        return sum(response_times) / len(response_times)

    @staticmethod
    def _build_weekly_application_trend(
        applications: list[JobApplication],
    ) -> list[WeeklyApplicationTrendPoint]:
        counts: dict[date, int] = defaultdict(int)

        for application in applications:
            created_at = parse_datetime(application.created_at)
            if created_at is None:
                continue
            week_start = AnalyticsService._week_start_date(created_at)
            counts[week_start] += 1

        return [
            WeeklyApplicationTrendPoint(week_start=week_start, count=count)
            for week_start, count in sorted(counts.items())
        ]

    @staticmethod
    def _week_start_date(value: datetime) -> date:
        localized = value.astimezone(UTC)
        return (localized - timedelta(days=localized.weekday())).date()

    @staticmethod
    def _count_recent_events(
        events: list[ApplicationEvent],
        *,
        now: datetime,
        days: int,
    ) -> int:
        cutoff = now - timedelta(days=days)
        return sum(
            1
            for event in events
            if (parsed := parse_datetime(event.occurred_at)) is not None and parsed >= cutoff
        )

    @staticmethod
    def _first_event_of_type(
        events: list[ApplicationEvent],
        event_type: EventType,
    ) -> ApplicationEvent | None:
        matching = [event for event in events if event.event_type == event_type]
        if not matching:
            return None
        return min(matching, key=lambda event: event.occurred_at)

    @staticmethod
    def _has_event_after(events: list[ApplicationEvent], occurred_at: datetime) -> bool:
        anchor = parse_datetime(occurred_at)
        if anchor is None:
            return False
        return any(
            (parsed := parse_datetime(event.occurred_at)) is not None and parsed > anchor
            for event in events
        )

    @staticmethod
    def _first_meaningful_response_after(
        events: list[ApplicationEvent],
        confirmation_at: datetime,
    ) -> ApplicationEvent | None:
        candidates: list[ApplicationEvent] = []
        for event in events:
            if event.event_type not in MEANINGFUL_RESPONSE_EVENT_TYPES:
                continue
            occurred_at = parse_datetime(event.occurred_at)
            if occurred_at is None or occurred_at <= confirmation_at:
                continue
            candidates.append(event)

        if not candidates:
            return None
        return min(candidates, key=lambda event: event.occurred_at)
