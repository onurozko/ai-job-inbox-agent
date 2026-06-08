from dataclasses import dataclass
from uuid import UUID

from google.oauth2.credentials import Credentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import GmailCredentialsMissingError
from app.integrations.gmail.client import DEFAULT_JOB_SEARCH_QUERY, GmailClient, ParsedGmailMessage
from app.models.email_message import EmailMessage
from app.models.enums import EmailCategory
from app.models.user import User
from app.services.application_updater import ApplicationUpdater
from app.services.email_classifier import EmailClassifier
from app.services.gmail_credential_service import (
    credentials_from_gmail_credential,
    get_user_gmail_credential,
)


@dataclass(frozen=True)
class EmailSyncSummary:
    fetched_count: int
    created_count: int
    skipped_count: int
    applications_updated_count: int


class EmailSyncService:
    def __init__(
        self,
        classifier: EmailClassifier | None = None,
        updater: ApplicationUpdater | None = None,
    ) -> None:
        self._classifier = classifier or EmailClassifier()
        self._updater = updater or ApplicationUpdater()

    async def sync_user_emails(
        self,
        session: AsyncSession,
        *,
        user: User,
        max_results: int = 50,
        query: str | None = None,
        gmail_client: GmailClient | None = None,
    ) -> EmailSyncSummary:
        credential = await get_user_gmail_credential(session, user.id)
        if credential is None:
            raise GmailCredentialsMissingError()

        search_query = query or DEFAULT_JOB_SEARCH_QUERY
        updated_application_ids: set[UUID] = set()

        if gmail_client is None:
            google_credentials = credentials_from_gmail_credential(credential)

            def on_token_refresh(refreshed_credentials: Credentials) -> None:
                credential.access_token = refreshed_credentials.token or credential.access_token
                if refreshed_credentials.refresh_token:
                    credential.refresh_token = refreshed_credentials.refresh_token
                credential.expiry = refreshed_credentials.expiry

            gmail_client = GmailClient(
                google_credentials,
                on_token_refresh=on_token_refresh,
            )

        parsed_messages = await gmail_client.fetch_recent_messages_async(
            query=search_query,
            max_results=max_results,
        )

        created_count = 0
        skipped_count = 0

        for parsed in parsed_messages:
            existing = await self._get_existing_message(session, user.id, parsed.gmail_message_id)
            if existing is not None:
                skipped_count += 1
                continue

            email = await self._create_email_message(session, user.id, parsed)
            created_count += 1

            try:
                classification = await self._classifier.classify(email)
                EmailClassifier.apply_to_email(email, classification)

                if classification.category == EmailCategory.IRRELEVANT:
                    continue

                application, _ = await self._updater.process_classified_email(
                    session,
                    email,
                    classification,
                )
                if application is not None:
                    updated_application_ids.add(application.id)
            except Exception as exc:
                email.processing_error = str(exc)
                await session.flush()

        await session.flush()
        return EmailSyncSummary(
            fetched_count=len(parsed_messages),
            created_count=created_count,
            skipped_count=skipped_count,
            applications_updated_count=len(updated_application_ids),
        )

    @staticmethod
    async def _get_existing_message(
        session: AsyncSession,
        user_id: UUID,
        gmail_message_id: str,
    ) -> EmailMessage | None:
        stmt = select(EmailMessage).where(
            EmailMessage.user_id == user_id,
            EmailMessage.gmail_message_id == gmail_message_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def _create_email_message(
        session: AsyncSession,
        user_id: UUID,
        parsed: ParsedGmailMessage,
    ) -> EmailMessage:
        email = EmailMessage(
            user_id=user_id,
            gmail_message_id=parsed.gmail_message_id,
            thread_id=parsed.thread_id,
            subject=parsed.subject,
            sender_email=parsed.sender_email,
            received_at=parsed.received_at,
            raw_snippet=parsed.raw_snippet,
            body_text=parsed.body_text,
        )
        session.add(email)
        await session.flush()
        return email
