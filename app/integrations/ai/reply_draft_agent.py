from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel

from app.core.config import get_settings
from app.models.enums import EmailCategory

SUPPORTED_REPLY_CATEGORIES = {
    EmailCategory.RECRUITER_OUTREACH,
    EmailCategory.INTERVIEW_INVITATION,
    EmailCategory.ASSESSMENT,
    EmailCategory.OFFER,
    EmailCategory.FOLLOW_UP_NEEDED,
    EmailCategory.APPLICATION_CONFIRMATION,
    EmailCategory.REJECTION,
    EmailCategory.IRRELEVANT,
}

SYSTEM_PROMPT = """You write professional email reply drafts for job-search correspondence.

Rules:
- Keep replies concise, natural, and professional.
- Do NOT invent availability, salary expectations, phone numbers, or personal details.
- If scheduling is involved and no clear time slots were provided, express willingness
  to coordinate and ask for available times.
- If an assessment has a deadline, acknowledge it.
- For rejections, write a brief polite thank-you. Do not sound desperate.
- For irrelevant emails, keep the draft minimal.
- Never claim the email was sent. This is only a draft.
- Match the requested tone when possible.
"""


class ReplyDraftAgentOutput(BaseModel):
    subject: str
    draft_body: str
    uncertain: bool = False


@dataclass(frozen=True)
class ReplyDraftContext:
    email_subject: str
    sender_email: str
    body_text: str
    category: EmailCategory | None
    company_name: str | None
    job_title: str | None
    deadline: datetime | None
    interview_date: datetime | None
    summary: str | None
    confidence_score: float | None
    application_company: str | None
    application_job_title: str | None
    application_status: str | None
    tone: str
    extra_instructions: str | None


def _reply_subject(original_subject: str) -> str:
    if original_subject.lower().startswith("re:"):
        return original_subject
    return f"Re: {original_subject}"


def _mock_reply_draft(context: ReplyDraftContext) -> ReplyDraftAgentOutput:
    company = context.company_name or context.application_company or "your team"
    role = context.job_title or context.application_job_title or "the role"
    category = context.category

    if category == EmailCategory.INTERVIEW_INVITATION:
        if context.interview_date:
            scheduling = (
                f"I am happy to confirm my availability for the interview on "
                f"{context.interview_date.strftime('%A, %B %d at %I:%M %p UTC')}."
            )
        else:
            scheduling = "I am happy to coordinate and would appreciate your available time slots."
        body = (
            f"Hi,\n\n"
            f"Thank you for the interview invitation for the {role} position at {company}. "
            f"{scheduling}\n\n"
            f"Please let me know if you need anything else from me beforehand.\n\n"
            f"Best regards"
        )
        return ReplyDraftAgentOutput(subject=_reply_subject(context.email_subject), draft_body=body)

    if category == EmailCategory.ASSESSMENT:
        deadline_text = ""
        if context.deadline:
            deadline_text = (
                f" I understand the assessment deadline is "
                f"{context.deadline.strftime('%A, %B %d')}, and I will complete it by then."
            )
        body = (
            f"Hi,\n\n"
            f"Thank you for sharing the assessment for the {role} position at {company}."
            f"{deadline_text} Please let me know if you have any questions.\n\n"
            f"Best regards"
        )
        return ReplyDraftAgentOutput(subject=_reply_subject(context.email_subject), draft_body=body)

    if category == EmailCategory.REJECTION:
        body = (
            f"Hi,\n\n"
            f"Thank you for the update regarding the {role} position at {company}. "
            f"I appreciate the time your team spent reviewing my application.\n\n"
            f"Best regards"
        )
        return ReplyDraftAgentOutput(
            subject=_reply_subject(context.email_subject),
            draft_body=body,
            uncertain=True,
        )

    if category == EmailCategory.IRRELEVANT:
        return ReplyDraftAgentOutput(
            subject=_reply_subject(context.email_subject),
            draft_body="Hi,\n\nThank you for your email.\n\nBest regards",
            uncertain=True,
        )

    if category == EmailCategory.RECRUITER_OUTREACH:
        body = (
            f"Hi,\n\n"
            f"Thank you for reaching out about the {role} opportunity at {company}. "
            f"I am interested in learning more and would be happy to continue the conversation.\n\n"
            f"Best regards"
        )
        return ReplyDraftAgentOutput(subject=_reply_subject(context.email_subject), draft_body=body)

    if category == EmailCategory.OFFER:
        body = (
            f"Hi,\n\n"
            f"Thank you for sharing the offer details for the {role} position at {company}. "
            f"I appreciate the opportunity and will review the information carefully.\n\n"
            f"Best regards"
        )
        return ReplyDraftAgentOutput(subject=_reply_subject(context.email_subject), draft_body=body)

    if category == EmailCategory.FOLLOW_UP_NEEDED:
        body = (
            f"Hi,\n\n"
            f"Thank you for your message regarding my application for the {role} "
            f"position at {company}. "
            f"I wanted to follow up and see whether there are any updates you can share.\n\n"
            f"Best regards"
        )
        return ReplyDraftAgentOutput(subject=_reply_subject(context.email_subject), draft_body=body)

    body = (
        f"Hi,\n\n"
        f"Thank you for your email regarding my application for the {role} position at {company}. "
        f"I appreciate the update.\n\n"
        f"Best regards"
    )
    return ReplyDraftAgentOutput(subject=_reply_subject(context.email_subject), draft_body=body)


async def generate_reply_draft(context: ReplyDraftContext) -> ReplyDraftAgentOutput:
    settings = get_settings()
    if not settings.openai_api_key:
        return _mock_reply_draft(context)

    try:
        from pydantic_ai import Agent

        agent = Agent(
            model="openai:gpt-4o-mini",
            output_type=ReplyDraftAgentOutput,
            system_prompt=SYSTEM_PROMPT,
        )
        prompt = (
            f"Tone: {context.tone}\n"
            f"Extra instructions: {context.extra_instructions or 'None'}\n"
            f"Original subject: {context.email_subject}\n"
            f"Sender: {context.sender_email}\n"
            f"Category: {context.category.value if context.category else 'unknown'}\n"
            f"Company: {context.company_name or context.application_company or 'Unknown'}\n"
            f"Job title: {context.job_title or context.application_job_title or 'Unknown'}\n"
            f"Application status: {context.application_status or 'Unknown'}\n"
            f"Deadline: {context.deadline.isoformat() if context.deadline else 'None'}\n"
            f"Interview date: "
            f"{context.interview_date.isoformat() if context.interview_date else 'None'}\n"
            f"Summary: {context.summary or 'None'}\n\n"
            f"Original email body:\n{context.body_text[:8000]}"
        )
        result = await agent.run(prompt)
        output = result.output
        if not output.subject.strip():
            output.subject = _reply_subject(context.email_subject)
        return output
    except Exception:
        return _mock_reply_draft(context)
