from datetime import UTC, datetime

from app.integrations.ai.agent import classify_email
from app.models.email_message import EmailMessage
from app.schemas.email import EmailClassificationResult


class EmailClassifier:
    async def classify(self, email: EmailMessage) -> EmailClassificationResult:
        result = await classify_email(
            subject=email.subject,
            body=email.body_text or email.raw_snippet or "",
            sender=email.sender_email,
            received_at=email.received_at,
        )
        return result

    @staticmethod
    def apply_to_email(
        email: EmailMessage,
        classification: EmailClassificationResult,
    ) -> None:
        email.category = classification.category
        email.company_name = classification.company_name
        email.job_title = classification.job_title
        email.deadline = classification.deadline
        email.interview_date = classification.interview_date
        email.action_required = classification.action_required
        email.summary = classification.summary
        email.confidence_score = classification.confidence_score
        email.processed_at = datetime.now(UTC)
        email.processing_error = None
