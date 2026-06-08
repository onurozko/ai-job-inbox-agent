import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.exceptions import GmailCredentialsMissingError
from app.db.session import get_session_factory
from app.models.user import User
from app.services.email_sync import EmailSyncService, EmailSyncSummary
from app.services.gmail_credential_service import list_user_ids_with_gmail_credentials

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScheduledSyncRunSummary:
    users_attempted: int
    users_succeeded: int
    users_failed: int


class ScheduledEmailSyncService:
    def __init__(
        self,
        sync_service: EmailSyncService | None = None,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._sync_service = sync_service or EmailSyncService()
        self._session_factory = session_factory
        self._settings = settings

    async def run_scheduled_sync(self) -> ScheduledSyncRunSummary:
        settings = self._settings or get_settings()
        session_factory = self._session_factory or get_session_factory()

        async with session_factory() as session:
            user_ids = await list_user_ids_with_gmail_credentials(session)

        if not user_ids:
            logger.info("Scheduled email sync skipped: no users with Gmail credentials")
            return ScheduledSyncRunSummary(users_attempted=0, users_succeeded=0, users_failed=0)

        logger.info("Scheduled email sync started user_count=%s", len(user_ids))

        succeeded = 0
        failed = 0

        for user_id in user_ids:
            try:
                summary = await self._sync_user(
                    session_factory,
                    user_id=user_id,
                    max_results=settings.background_sync_max_results,
                )
                succeeded += 1
                logger.info(
                    "Scheduled email sync completed user_id=%s fetched=%s created=%s "
                    "skipped=%s applications_updated=%s",
                    user_id,
                    summary.fetched_count,
                    summary.created_count,
                    summary.skipped_count,
                    summary.applications_updated_count,
                )
            except GmailCredentialsMissingError:
                failed += 1
                logger.warning(
                    "Scheduled email sync skipped user_id=%s reason=gmail_credentials_missing",
                    user_id,
                )
            except Exception:
                failed += 1
                logger.exception("Scheduled email sync failed user_id=%s", user_id)

        logger.info(
            "Scheduled email sync finished attempted=%s succeeded=%s failed=%s",
            len(user_ids),
            succeeded,
            failed,
        )
        return ScheduledSyncRunSummary(
            users_attempted=len(user_ids),
            users_succeeded=succeeded,
            users_failed=failed,
        )

    async def _sync_user(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        user_id: UUID,
        max_results: int,
    ) -> EmailSyncSummary:
        async with session_factory() as session:
            user = await session.get(User, user_id)
            if user is None:
                raise GmailCredentialsMissingError()

            summary = await self._sync_service.sync_user_emails(
                session,
                user=user,
                max_results=max_results,
            )
            await session.commit()
            return summary
