import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application_event import ApplicationEvent
from app.models.email_message import EmailMessage
from app.models.job_application import JobApplication
from app.services.application_updater import ApplicationUpdater
from app.services.email_classifier import EmailClassifier


class EmailPipeline:
    def __init__(
        self,
        classifier: EmailClassifier | None = None,
        updater: ApplicationUpdater | None = None,
    ) -> None:
        self._classifier = classifier or EmailClassifier()
        self._updater = updater or ApplicationUpdater()

    async def process_email_message(
        self,
        session: AsyncSession,
        email_id: uuid.UUID,
    ) -> tuple[EmailMessage, JobApplication, ApplicationEvent]:
        stmt = select(EmailMessage).where(EmailMessage.id == email_id)
        result = await session.execute(stmt)
        email = result.scalar_one_or_none()
        if email is None:
            raise ValueError(f"Email message {email_id} not found")

        try:
            classification = await self._classifier.classify(email)
            EmailClassifier.apply_to_email(email, classification)
            application, event = await self._updater.process_classified_email(
                session,
                email,
                classification,
            )
            if application is None or event is None:
                raise ValueError("Email classified as irrelevant; no application update performed")
            return email, application, event
        except Exception as exc:
            email.processing_error = str(exc)
            await session.flush()
            raise
