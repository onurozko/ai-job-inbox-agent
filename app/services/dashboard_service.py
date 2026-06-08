from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.datetime_utils import parse_datetime
from app.models.application_event import ApplicationEvent
from app.models.email_message import EmailMessage
from app.models.enums import ApplicationStatus
from app.models.job_application import JobApplication
from app.schemas.application_event import ApplicationEventRead
from app.schemas.dashboard import ApplicationTimeline, DashboardSummary, UpcomingDeadline
from app.schemas.email import EmailMessageRead
from app.schemas.job_application import JobApplicationRead


class DashboardService:
    async def get_summary(self, session: AsyncSession, user_id: UUID) -> DashboardSummary:
        applications = (
            (await session.execute(select(JobApplication).where(JobApplication.user_id == user_id)))
            .scalars()
            .all()
        )

        total = len(applications)
        rejected = sum(1 for app in applications if app.status == ApplicationStatus.REJECTED)
        active = sum(1 for app in applications if app.status != ApplicationStatus.REJECTED)
        interviews = sum(
            1 for app in applications if app.status == ApplicationStatus.INTERVIEW_SCHEDULED
        )
        assessments = sum(1 for app in applications if app.status == ApplicationStatus.ASSESSMENT)
        offers = sum(1 for app in applications if app.status == ApplicationStatus.OFFER_RECEIVED)
        follow_ups = sum(
            1
            for app in applications
            if app.status == ApplicationStatus.FOLLOW_UP
            or (app.action_required and app.status != ApplicationStatus.REJECTED)
        )

        recent_events = await self._get_recent_events(session, user_id, limit=10)
        upcoming_deadlines = await self._get_upcoming_deadlines(session, user_id, applications)

        return DashboardSummary(
            total_applications=total,
            active_applications=active,
            rejected_applications=rejected,
            interviews_scheduled=interviews,
            assessments_pending=assessments,
            offers=offers,
            follow_ups_needed=follow_ups,
            upcoming_deadlines=upcoming_deadlines,
            recent_events=recent_events,
        )

    async def get_application_timeline(
        self,
        session: AsyncSession,
        user_id: UUID,
        application_id: UUID,
    ) -> ApplicationTimeline | None:
        stmt = (
            select(JobApplication)
            .where(
                JobApplication.id == application_id,
                JobApplication.user_id == user_id,
            )
            .options(
                selectinload(JobApplication.events).selectinload(ApplicationEvent.email_message),
            )
        )
        application = (await session.execute(stmt)).scalar_one_or_none()
        if application is None:
            return None

        events = sorted(application.events, key=lambda event: event.occurred_at)
        email_ids = {
            event.email_message_id for event in events if event.email_message_id is not None
        }

        emails: list[EmailMessage] = []
        if email_ids:
            email_stmt = select(EmailMessage).where(
                EmailMessage.user_id == user_id,
                EmailMessage.id.in_(email_ids),
            )
            emails = list((await session.execute(email_stmt)).scalars().all())
            emails.sort(key=lambda email: email.received_at)

        next_deadline, next_interview_date = self._extract_next_dates(events, emails)

        return ApplicationTimeline(
            application=JobApplicationRead.model_validate(application),
            current_status=application.status,
            emails=[EmailMessageRead.model_validate(email) for email in emails],
            events=[ApplicationEventRead.model_validate(event) for event in events],
            next_deadline=next_deadline,
            next_interview_date=next_interview_date,
        )

    async def _get_recent_events(
        self,
        session: AsyncSession,
        user_id: UUID,
        *,
        limit: int,
    ) -> list[ApplicationEventRead]:
        stmt = (
            select(ApplicationEvent)
            .join(JobApplication, ApplicationEvent.job_application_id == JobApplication.id)
            .where(JobApplication.user_id == user_id)
            .order_by(ApplicationEvent.occurred_at.desc())
            .limit(limit)
        )
        events = (await session.execute(stmt)).scalars().all()
        return [ApplicationEventRead.model_validate(event) for event in events]

    async def _get_upcoming_deadlines(
        self,
        session: AsyncSession,
        user_id: UUID,
        applications: list[JobApplication],
    ) -> list[UpcomingDeadline]:
        now = datetime.now(UTC)
        deadlines: list[UpcomingDeadline] = []
        app_by_id = {app.id: app for app in applications}

        email_stmt = select(EmailMessage).where(
            EmailMessage.user_id == user_id,
            EmailMessage.deadline.is_not(None),
        )
        for email in (await session.execute(email_stmt)).scalars().all():
            if email.deadline and email.deadline >= now:
                application = self._find_application_for_email(applications, email.company_name)
                if application is None:
                    continue
                deadlines.append(
                    UpcomingDeadline(
                        application_id=application.id,
                        company_name=application.company_name,
                        job_title=application.job_title,
                        deadline=email.deadline,
                        deadline_type="deadline",
                    )
                )

        event_stmt = (
            select(ApplicationEvent)
            .join(JobApplication, ApplicationEvent.job_application_id == JobApplication.id)
            .where(JobApplication.user_id == user_id)
        )
        for event in (await session.execute(event_stmt)).scalars().all():
            application = app_by_id.get(event.job_application_id)
            if application is None:
                continue
            metadata = event.metadata_ or {}
            for key, deadline_type in (
                ("deadline", "assessment"),
                ("interview_date", "interview"),
            ):
                raw_value = metadata.get(key)
                if not raw_value:
                    continue
                parsed = parse_datetime(raw_value)
                if parsed is None or parsed < now:
                    continue
                deadlines.append(
                    UpcomingDeadline(
                        application_id=application.id,
                        company_name=application.company_name,
                        job_title=application.job_title,
                        deadline=parsed,
                        deadline_type=deadline_type,
                    )
                )

        deadlines.sort(key=lambda item: item.deadline)
        return deadlines[:20]

    @staticmethod
    def _find_application_for_email(
        applications: list[JobApplication],
        company_name: str | None,
    ) -> JobApplication | None:
        if not company_name:
            return None
        normalized = company_name.strip().lower()
        for application in applications:
            if application.company_name.strip().lower() == normalized:
                return application
        return None

    @staticmethod
    def _extract_next_dates(
        events: list[ApplicationEvent],
        emails: list[EmailMessage],
    ) -> tuple[datetime | None, datetime | None]:
        now = datetime.now(UTC)
        deadlines: list[datetime] = []
        interviews: list[datetime] = []

        for email in emails:
            if email.deadline and email.deadline >= now:
                deadlines.append(email.deadline)
            if email.interview_date and email.interview_date >= now:
                interviews.append(email.interview_date)

        for event in events:
            metadata = event.metadata_ or {}
            deadline = parse_datetime(metadata.get("deadline"))
            interview = parse_datetime(metadata.get("interview_date"))
            if deadline and deadline >= now:
                deadlines.append(deadline)
            if interview and interview >= now:
                interviews.append(interview)

        next_deadline = min(deadlines) if deadlines else None
        next_interview = min(interviews) if interviews else None
        return next_deadline, next_interview
