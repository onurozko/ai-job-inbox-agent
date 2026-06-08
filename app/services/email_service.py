import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    EmailProcessingError,
    ExternalServiceError,
    GmailCredentialsMissingError,
    NotFoundError,
)
from app.db.repositories import email_repository
from app.models.enums import EmailCategory
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.email import EmailMessageRead, EmailSyncRequest, EmailSyncResponse
from app.services.email_pipeline import EmailPipeline
from app.services.email_sync import EmailSyncService

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(
        self,
        sync_service: EmailSyncService | None = None,
        pipeline: EmailPipeline | None = None,
    ) -> None:
        self._sync_service = sync_service or EmailSyncService()
        self._pipeline = pipeline or EmailPipeline()

    async def list_emails(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        page: int,
        page_size: int,
        category: EmailCategory | None = None,
    ) -> PaginatedResponse[EmailMessageRead]:
        items, total = await email_repository.list_emails_for_user(
            session,
            user_id=user_id,
            page=page,
            page_size=page_size,
            category=category,
        )
        return PaginatedResponse(
            items=[EmailMessageRead.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_email(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        email_id: UUID,
    ) -> EmailMessageRead:
        email = await email_repository.get_email_for_user(
            session,
            user_id=user_id,
            email_id=email_id,
        )
        if email is None:
            raise NotFoundError("Email not found")
        return EmailMessageRead.model_validate(email)

    async def sync_emails(
        self,
        session: AsyncSession,
        *,
        user: User,
        payload: EmailSyncRequest,
    ) -> EmailSyncResponse:
        try:
            summary = await self._sync_service.sync_user_emails(
                session,
                user=user,
                max_results=payload.max_results,
                query=payload.query,
            )
        except GmailCredentialsMissingError:
            raise
        except Exception as exc:
            logger.exception("Gmail sync failed for user_id=%s", user.id)
            raise ExternalServiceError("Gmail sync failed") from exc

        logger.info(
            "Gmail sync completed user_id=%s fetched=%s created=%s skipped=%s",
            user.id,
            summary.fetched_count,
            summary.created_count,
            summary.skipped_count,
        )
        return EmailSyncResponse(
            message="Gmail sync completed",
            status="completed",
            fetched_count=summary.fetched_count,
            created_count=summary.created_count,
            skipped_count=summary.skipped_count,
            applications_updated_count=summary.applications_updated_count,
        )

    async def reprocess_email(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        email_id: UUID,
    ) -> EmailMessageRead:
        email = await email_repository.get_email_for_user(
            session,
            user_id=user_id,
            email_id=email_id,
        )
        if email is None:
            raise NotFoundError("Email not found")

        try:
            processed_email, _, _ = await self._pipeline.process_email_message(session, email.id)
        except Exception as exc:
            logger.exception("Email reprocess failed email_id=%s user_id=%s", email_id, user_id)
            raise EmailProcessingError("Failed to process email") from exc

        return EmailMessageRead.model_validate(processed_email)
