from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.models.enums import ApplicationStatus
from app.schemas.assistant import (
    ActionPriority,
    NextAction,
    NextActionAgentInput,
    NextActionsResponse,
)

SYSTEM_PROMPT = """You are a job-search assistant that recommends practical next actions.

Rules:
- Do NOT recommend actions for rejected applications unless giving brief archival advice.
- Prioritize interviews and assessments over passive applications.
- Include due_date when a deadline or interview date is available.
- If there are no urgent actions, say so clearly in the summary.
- Keep suggested_next_step concise and actionable.
- action_type examples: prepare_interview, complete_assessment, follow_up, review_offer, archive
- priority must be one of: high, medium, low
"""


class NextActionAgentOutput(BaseModel):
    summary: str
    actions: list[NextAction] = Field(default_factory=list)


def _priority_rank(priority: ActionPriority) -> int:
    return {ActionPriority.HIGH: 0, ActionPriority.MEDIUM: 1, ActionPriority.LOW: 2}[priority]


def _mock_next_actions(agent_input: NextActionAgentInput) -> NextActionsResponse:
    actions: list[NextAction] = []
    now = datetime.now(UTC)

    for application in agent_input.applications:
        if application.status == ApplicationStatus.REJECTED.value:
            continue

        if application.status == ApplicationStatus.INTERVIEW_SCHEDULED.value:
            due_date = application.interview_dates[0] if application.interview_dates else None
            actions.append(
                NextAction(
                    priority=ActionPriority.HIGH,
                    application_id=application.application_id,
                    company_name=application.company_name,
                    job_title=application.job_title,
                    action_type="prepare_interview",
                    reason="An interview is scheduled for this application.",
                    suggested_next_step=(
                        f"Prepare for {application.company_name} interview"
                        + (f" on {due_date.date()}" if due_date else " soon")
                        + "."
                    ),
                    due_date=due_date,
                )
            )
        elif application.status == ApplicationStatus.ASSESSMENT.value:
            due_date = application.deadlines[0] if application.deadlines else None
            actions.append(
                NextAction(
                    priority=ActionPriority.HIGH,
                    application_id=application.application_id,
                    company_name=application.company_name,
                    job_title=application.job_title,
                    action_type="complete_assessment",
                    reason="An assessment is pending for this application.",
                    suggested_next_step=(
                        f"Complete assessment for {application.company_name}"
                        + (f" before {due_date.date()}" if due_date else "")
                        + "."
                    ),
                    due_date=due_date,
                )
            )
        elif application.status == ApplicationStatus.FOLLOW_UP.value or application.action_required:
            due_date = now + timedelta(days=3)
            actions.append(
                NextAction(
                    priority=ActionPriority.MEDIUM,
                    application_id=application.application_id,
                    company_name=application.company_name,
                    job_title=application.job_title,
                    action_type="follow_up",
                    reason="This application needs follow-up.",
                    suggested_next_step=(
                        f"Follow up with {application.company_name} about your application."
                    ),
                    due_date=due_date,
                )
            )
        elif application.status == ApplicationStatus.APPLIED.value:
            actions.append(
                NextAction(
                    priority=ActionPriority.LOW,
                    application_id=application.application_id,
                    company_name=application.company_name,
                    job_title=application.job_title,
                    action_type="monitor",
                    reason="Application submitted; no urgent action yet.",
                    suggested_next_step=(
                        f"Monitor inbox for updates from {application.company_name}."
                    ),
                    due_date=None,
                )
            )

    actions.sort(key=lambda action: _priority_rank(action.priority))

    if not actions:
        return NextActionsResponse(
            summary="No urgent actions at this time. Your active applications are up to date.",
            actions=[],
        )

    return NextActionsResponse(
        summary=(
            f"You have {len(actions)} recommended action(s). "
            "Focus on high-priority items first."
        ),
        actions=actions,
    )


async def generate_next_actions(agent_input: NextActionAgentInput) -> NextActionsResponse:
    settings = get_settings()
    if not settings.openai_api_key or not agent_input.applications:
        return _mock_next_actions(agent_input)

    try:
        from pydantic_ai import Agent

        agent = Agent(
            model="openai:gpt-4o-mini",
            output_type=NextActionAgentOutput,
            system_prompt=SYSTEM_PROMPT,
        )
        prompt = agent_input.model_dump_json(indent=2)
        result = await agent.run(prompt)
        return NextActionsResponse(
            summary=result.output.summary,
            actions=result.output.actions,
        )
    except Exception:
        return _mock_next_actions(agent_input)
