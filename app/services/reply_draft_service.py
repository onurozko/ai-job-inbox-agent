import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.db.repositories import email_repository
from app.integrations.ai.reply_draft_agent import (
    SUPPORTED_REPLY_CATEGORIES,
    ReplyDraftContext,
    generate_reply_draft,
)
from app.models.application_event import ApplicationEvent
from app.models.email_message import EmailMessage
from app.models.enums import EmailCategory
from app.models.job_application import JobApplication
from app.schemas.reply_draft import DraftReplyRequest, DraftReplyResponse

MIN_BODY_LENGTH = 50
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")


class ReplyDraftService:
    async def create_draft(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        request: DraftReplyRequest,
    ) -> DraftReplyResponse:
        email = await email_repository.get_email_for_user(
            session,
            user_id=user_id,
            email_id=request.email_id,
        )
        if email is None:
            raise NotFoundError("Email not found")

        application = await self._load_related_application(session, user_id, email)
        body_text = (email.body_text or email.raw_snippet or "").strip()
        warnings = self._build_warnings(email, body_text)

        context = ReplyDraftContext(
            email_subject=email.subject,
            sender_email=email.sender_email,
            body_text=body_text,
            category=email.category,
            company_name=email.company_name,
            job_title=email.job_title,
            deadline=email.deadline,
            interview_date=email.interview_date,
            summary=email.summary,
            confidence_score=email.confidence_score,
            application_company=application.company_name if application else None,
            application_job_title=application.job_title if application else None,
            application_status=application.status.value if application else None,
            tone=request.tone,
            extra_instructions=request.extra_instructions,
        )

        draft = await generate_reply_draft(context)
        warnings.extend(self._post_generation_warnings(email, draft.uncertain))

        recipient_email = self._resolve_recipient_email(email.sender_email)
        if not recipient_email:
            warnings.append("Recipient email could not be determined from the sender address.")

        return DraftReplyResponse(
            email_id=email.id,
            subject=draft.subject,
            recipient_email=recipient_email or email.sender_email,
            draft_body=draft.draft_body.strip(),
            tone=request.tone,
            warnings=_dedupe_warnings(warnings),
        )

    @staticmethod
    async def _load_related_application(
        session: AsyncSession,
        user_id: UUID,
        email: EmailMessage,
    ) -> JobApplication | None:
        event_stmt = (
            select(ApplicationEvent)
            .where(ApplicationEvent.email_message_id == email.id)
            .options(selectinload(ApplicationEvent.job_application))
        )
        event = (await session.execute(event_stmt)).scalar_one_or_none()
        if event is not None and event.job_application.user_id == user_id:
            return event.job_application

        if not email.company_name:
            return None

        app_stmt = select(JobApplication).where(
            JobApplication.user_id == user_id,
            JobApplication.company_name == email.company_name,
        )
        return (await session.execute(app_stmt)).scalar_one_or_none()

    @staticmethod
    def _build_warnings(email: EmailMessage, body_text: str) -> list[str]:
        warnings: list[str] = []

        if email.category == EmailCategory.REJECTION:
            warnings.append("This email appears to be a rejection. A reply may not be necessary.")

        if email.category == EmailCategory.IRRELEVANT:
            warnings.append(
                "This email appears to be irrelevant to your job search. Review before sending."
            )

        if email.category not in SUPPORTED_REPLY_CATEGORIES and email.category is not None:
            warnings.append(f"No specialized reply template for category '{email.category.value}'.")

        if len(body_text) < MIN_BODY_LENGTH:
            warnings.append("Original email body is very short; the draft may lack context.")

        if not ReplyDraftService._resolve_recipient_email(email.sender_email):
            warnings.append("Sender email address appears to be missing or invalid.")

        if email.confidence_score is not None and email.confidence_score < 0.5:
            warnings.append("Email classification confidence is low; review the draft carefully.")

        return warnings

    @staticmethod
    def _post_generation_warnings(email: EmailMessage, uncertain: bool) -> list[str]:
        warnings: list[str] = []
        if uncertain:
            warnings.append("The assistant is uncertain about this draft; review before sending.")
        return warnings

    @staticmethod
    def _resolve_recipient_email(sender_email: str) -> str | None:
        if not sender_email or not sender_email.strip():
            return None
        match = EMAIL_PATTERN.search(sender_email)
        return match.group(0) if match else None


def _dedupe_warnings(warnings: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for warning in warnings:
        if warning not in seen:
            seen.add(warning)
            unique.append(warning)
    return unique
