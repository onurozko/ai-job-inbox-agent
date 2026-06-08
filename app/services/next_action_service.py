from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.datetime_utils import parse_datetime
from app.integrations.ai.next_action_agent import generate_next_actions
from app.models.application_event import ApplicationEvent
from app.models.email_message import EmailMessage
from app.models.enums import ApplicationStatus
from app.models.job_application import JobApplication
from app.schemas.assistant import (
    ActionPriority,
    ApplicationActionContext,
    NextAction,
    NextActionAgentInput,
    NextActionsResponse,
)
from app.services.dashboard_service import DashboardService

PRIORITY_RANK = {
    ActionPriority.HIGH: 0,
    ActionPriority.MEDIUM: 1,
    ActionPriority.LOW: 2,
}


class NextActionService:
    def __init__(self, dashboard_service: DashboardService | None = None) -> None:
        self._dashboard_service = dashboard_service or DashboardService()

    async def get_next_actions(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> NextActionsResponse:
        contexts = await self._build_application_contexts(session, user_id)
        recent_events = await self._build_recent_event_summaries(session, user_id)

        agent_input = NextActionAgentInput(
            applications=contexts,
            recent_events=recent_events,
        )
        response = await generate_next_actions(agent_input)
        return self._post_process_actions(response, contexts)

    async def _build_application_contexts(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> list[ApplicationActionContext]:
        stmt = (
            select(JobApplication)
            .where(JobApplication.user_id == user_id)
            .options(selectinload(JobApplication.events))
        )
        applications = (await session.execute(stmt)).scalars().all()
        contexts: list[ApplicationActionContext] = []

        for application in applications:
            if application.status == ApplicationStatus.REJECTED:
                continue

            events = sorted(application.events, key=lambda event: event.occurred_at, reverse=True)
            recent_event_summaries = [
                f"{event.event_type.value}: {event.title}" for event in events[:5]
            ]

            deadlines: list[datetime] = []
            interview_dates: list[datetime] = []
            for event in events:
                metadata = event.metadata_ or {}
                deadline = parse_datetime(metadata.get("deadline"))
                interview = parse_datetime(metadata.get("interview_date"))
                if deadline:
                    deadlines.append(deadline)
                if interview:
                    interview_dates.append(interview)

            email_stmt = select(EmailMessage).where(
                EmailMessage.user_id == user_id,
                EmailMessage.company_name.is_not(None),
            )
            emails = (await session.execute(email_stmt)).scalars().all()
            company_normalized = application.company_name.strip().lower()
            for email in emails:
                if (email.company_name or "").strip().lower() != company_normalized:
                    continue
                if email.deadline:
                    deadlines.append(email.deadline)
                if email.interview_date:
                    interview_dates.append(email.interview_date)

            contexts.append(
                ApplicationActionContext(
                    application_id=application.id,
                    company_name=application.company_name,
                    job_title=application.job_title,
                    status=application.status.value,
                    action_required=application.action_required,
                    last_email_at=application.last_email_at,
                    recent_events=recent_event_summaries,
                    deadlines=sorted(deadlines),
                    interview_dates=sorted(interview_dates),
                )
            )

        return contexts

    async def _build_recent_event_summaries(
        self,
        session: AsyncSession,
        user_id: UUID,
        *,
        limit: int = 15,
    ) -> list[str]:
        stmt = (
            select(ApplicationEvent, JobApplication.company_name)
            .join(JobApplication, ApplicationEvent.job_application_id == JobApplication.id)
            .where(JobApplication.user_id == user_id)
            .order_by(ApplicationEvent.occurred_at.desc())
            .limit(limit)
        )
        rows = (await session.execute(stmt)).all()
        return [
            f"{company_name}: {event.event_type.value} - {event.title}"
            for event, company_name in rows
        ]

    @staticmethod
    def _post_process_actions(
        response: NextActionsResponse,
        contexts: list[ApplicationActionContext],
    ) -> NextActionsResponse:
        active_ids = {context.application_id for context in contexts}
        filtered_actions: list[NextAction] = []

        for action in response.actions:
            if action.application_id is not None and action.application_id not in active_ids:
                continue
            if action.action_type == "archive" and action.priority == ActionPriority.LOW:
                continue
            filtered_actions.append(action)

        filtered_actions.sort(
            key=lambda action: (
                PRIORITY_RANK.get(action.priority, 99),
                action.due_date or datetime.max.replace(tzinfo=UTC),
            )
        )

        summary = response.summary
        if not filtered_actions:
            summary = "No urgent actions at this time. Your active applications are up to date."

        return NextActionsResponse(summary=summary, actions=filtered_actions)
