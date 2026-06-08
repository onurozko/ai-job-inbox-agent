from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.ai.next_action_agent import generate_next_actions
from app.models.application_event import ApplicationEvent
from app.models.enums import ApplicationStatus, EventType
from app.models.job_application import JobApplication
from app.models.user import User
from app.schemas.assistant import ActionPriority, NextActionAgentInput
from app.services.next_action_service import NextActionService


async def _create_application(
    async_session: AsyncSession,
    user: User,
    *,
    company: str,
    status: ApplicationStatus,
    action_required: bool = False,
) -> JobApplication:
    application = JobApplication(
        user_id=user.id,
        company_name=company,
        job_title="Software Engineer",
        company_name_normalized=company.lower(),
        job_title_normalized="software engineer",
        status=status,
        action_required=action_required,
        last_email_at=datetime(2026, 6, 5, tzinfo=UTC),
    )
    async_session.add(application)
    await async_session.flush()
    return application


@pytest.mark.asyncio
async def test_next_actions_ignores_rejected_applications(async_session: AsyncSession) -> None:
    user = User(email="assistant@test.com", full_name="Assistant Test")
    async_session.add(user)
    await async_session.flush()

    await _create_application(
        async_session, user, company="Shopify", status=ApplicationStatus.REJECTED
    )
    await _create_application(
        async_session, user, company="Datadog", status=ApplicationStatus.ASSESSMENT
    )

    service = NextActionService()
    response = await service.get_next_actions(async_session, user.id)

    company_names = {action.company_name for action in response.actions}
    assert "Shopify" not in company_names
    assert "Datadog" in company_names
    assert all(action.application_id is not None for action in response.actions)


@pytest.mark.asyncio
async def test_next_actions_prioritizes_interview_and_assessment(
    async_session: AsyncSession,
) -> None:
    user = User(email="priority@test.com", full_name="Priority Test")
    async_session.add(user)
    await async_session.flush()

    applied = await _create_application(
        async_session, user, company="Amazon", status=ApplicationStatus.APPLIED
    )
    assessment = await _create_application(
        async_session,
        user,
        company="Datadog",
        status=ApplicationStatus.ASSESSMENT,
        action_required=True,
    )
    interview = await _create_application(
        async_session,
        user,
        company="Shopify",
        status=ApplicationStatus.INTERVIEW_SCHEDULED,
        action_required=True,
    )

    for application, event_type in (
        (applied, EventType.APPLICATION_CONFIRMATION),
        (assessment, EventType.ASSESSMENT),
        (interview, EventType.INTERVIEW_INVITATION),
    ):
        async_session.add(
            ApplicationEvent(
                job_application_id=application.id,
                event_type=event_type,
                title=f"{application.company_name} event",
                occurred_at=datetime(2026, 6, 5, tzinfo=UTC),
                metadata_={
                    "deadline": (datetime(2026, 6, 10, tzinfo=UTC).isoformat()),
                    "interview_date": (datetime(2026, 6, 7, tzinfo=UTC).isoformat()),
                },
            )
        )

    service = NextActionService()
    response = await service.get_next_actions(async_session, user.id)

    assert len(response.actions) >= 2
    priorities = [action.priority for action in response.actions]
    assert priorities[0] == ActionPriority.HIGH

    high_priority_companies = {
        action.company_name for action in response.actions if action.priority == ActionPriority.HIGH
    }
    assert "Shopify" in high_priority_companies
    assert "Datadog" in high_priority_companies

    low_priority = [action for action in response.actions if action.priority == ActionPriority.LOW]
    if low_priority:
        assert low_priority[0].company_name == "Amazon"


@pytest.mark.asyncio
async def test_mock_agent_returns_no_actions_when_no_active_applications() -> None:
    response = await generate_next_actions(NextActionAgentInput(applications=[]))
    assert "No urgent actions" in response.summary
    assert response.actions == []
