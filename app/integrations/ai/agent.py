from datetime import datetime

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.models.enums import EmailCategory
from app.schemas.email import EmailClassificationResult

SYSTEM_PROMPT = """You classify job-search related emails and extract structured data.
Return accurate category, company, role, dates, and a concise summary.
Confidence should reflect how certain you are (0.0 to 1.0)."""


class ClassificationOutput(BaseModel):
    category: EmailCategory
    company_name: str | None = None
    job_title: str | None = None
    deadline: datetime | None = None
    interview_date: datetime | None = None
    action_required: bool = False
    summary: str | None = None
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)


def _mock_classification(
    subject: str,
    body: str,
    sender: str,
    received_at: datetime | None,
) -> EmailClassificationResult:
    lowered = f"{subject} {body}".lower()
    if "reject" in lowered:
        category = EmailCategory.REJECTION
    elif "interview" in lowered:
        category = EmailCategory.INTERVIEW_INVITATION
    elif "assessment" in lowered or "test" in lowered:
        category = EmailCategory.ASSESSMENT
    elif "offer" in lowered:
        category = EmailCategory.OFFER
    elif "application" in lowered or "applied" in lowered:
        category = EmailCategory.APPLICATION_CONFIRMATION
    elif "recruiter" in lowered:
        category = EmailCategory.RECRUITER_OUTREACH
    else:
        category = EmailCategory.IRRELEVANT

    company = None
    for token in subject.split():
        if token.endswith(".com") or "@" in token:
            continue
        if token[0:1].isupper() and len(token) > 2:
            company = token.strip(",:")
            break

    return EmailClassificationResult(
        category=category,
        company_name=company,
        job_title=None,
        sender_email=sender,
        received_at=received_at,
        action_required=category
        in {
            EmailCategory.ASSESSMENT,
            EmailCategory.INTERVIEW_INVITATION,
            EmailCategory.FOLLOW_UP_NEEDED,
        },
        summary=f"Mock classification for: {subject[:120]}",
        confidence_score=0.3,
    )


async def classify_email(
    *,
    subject: str,
    body: str,
    sender: str,
    received_at: datetime | None = None,
) -> EmailClassificationResult:
    settings = get_settings()
    if not settings.openai_api_key:
        return _mock_classification(subject, body, sender, received_at)

    try:
        from pydantic_ai import Agent

        agent = Agent(
            model="openai:gpt-4o-mini",
            output_type=ClassificationOutput,
            system_prompt=SYSTEM_PROMPT,
        )
        prompt = (
            f"Subject: {subject}\n"
            f"From: {sender}\n"
            f"Received: {received_at.isoformat() if received_at else 'unknown'}\n\n"
            f"Body:\n{body[:8000]}"
        )
        result = await agent.run(prompt)
        output = result.output
        return EmailClassificationResult(
            category=output.category,
            company_name=output.company_name,
            job_title=output.job_title,
            sender_email=sender,
            received_at=received_at,
            deadline=output.deadline,
            interview_date=output.interview_date,
            action_required=output.action_required,
            summary=output.summary,
            confidence_score=output.confidence_score,
        )
    except Exception:
        return _mock_classification(subject, body, sender, received_at)
