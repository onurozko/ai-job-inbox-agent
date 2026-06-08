from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application_event import ApplicationEvent
from app.models.email_message import EmailMessage
from app.models.enums import ApplicationStatus, EmailCategory, EventType
from app.models.job_application import JobApplication
from app.schemas.email import EmailClassificationResult
from app.services.application_matcher import ApplicationMatcher

CATEGORY_TO_STATUS: dict[EmailCategory, ApplicationStatus] = {
    EmailCategory.APPLICATION_CONFIRMATION: ApplicationStatus.APPLIED,
    EmailCategory.REJECTION: ApplicationStatus.REJECTED,
    EmailCategory.INTERVIEW_INVITATION: ApplicationStatus.INTERVIEW_SCHEDULED,
    EmailCategory.ASSESSMENT: ApplicationStatus.ASSESSMENT,
    EmailCategory.RECRUITER_OUTREACH: ApplicationStatus.FOLLOW_UP,
    EmailCategory.OFFER: ApplicationStatus.OFFER_RECEIVED,
    EmailCategory.FOLLOW_UP_NEEDED: ApplicationStatus.FOLLOW_UP,
    EmailCategory.IRRELEVANT: ApplicationStatus.UNKNOWN,
}

CATEGORY_TO_EVENT_TYPE: dict[EmailCategory, EventType] = {
    EmailCategory.APPLICATION_CONFIRMATION: EventType.APPLICATION_CONFIRMATION,
    EmailCategory.REJECTION: EventType.REJECTION,
    EmailCategory.INTERVIEW_INVITATION: EventType.INTERVIEW_INVITATION,
    EmailCategory.ASSESSMENT: EventType.ASSESSMENT,
    EmailCategory.RECRUITER_OUTREACH: EventType.RECRUITER_OUTREACH,
    EmailCategory.OFFER: EventType.OFFER,
    EmailCategory.FOLLOW_UP_NEEDED: EventType.FOLLOW_UP_NEEDED,
    EmailCategory.IRRELEVANT: EventType.IRRELEVANT,
}

EVENT_TITLES: dict[EmailCategory, str] = {
    EmailCategory.APPLICATION_CONFIRMATION: "Application confirmed",
    EmailCategory.REJECTION: "Application rejected",
    EmailCategory.INTERVIEW_INVITATION: "Interview invitation received",
    EmailCategory.ASSESSMENT: "Assessment requested",
    EmailCategory.RECRUITER_OUTREACH: "Recruiter outreach",
    EmailCategory.OFFER: "Offer received",
    EmailCategory.FOLLOW_UP_NEEDED: "Follow-up needed",
    EmailCategory.IRRELEVANT: "Irrelevant email",
}


class ApplicationUpdater:
    def __init__(self, matcher: ApplicationMatcher | None = None) -> None:
        self._matcher = matcher or ApplicationMatcher()

    async def process_classified_email(
        self,
        session: AsyncSession,
        email: EmailMessage,
        classification: EmailClassificationResult,
    ) -> tuple[JobApplication | None, ApplicationEvent | None]:
        if classification.category == EmailCategory.IRRELEVANT:
            return None, None

        company_name = classification.company_name or "Unknown Company"
        job_title = classification.job_title
        new_status = CATEGORY_TO_STATUS.get(classification.category, ApplicationStatus.UNKNOWN)

        application = await self._matcher.find_or_create_application(
            session,
            user_id=email.user_id,
            company_name=company_name,
            job_title=job_title,
            status=new_status,
        )

        application.status = self._resolve_status(application.status, new_status)
        application.latest_summary = classification.summary or application.latest_summary
        application.last_email_at = email.received_at
        application.action_required = classification.action_required

        if job_title and not application.job_title:
            application.job_title = job_title

        event = ApplicationEvent(
            job_application_id=application.id,
            email_message_id=email.id,
            event_type=CATEGORY_TO_EVENT_TYPE[classification.category],
            title=EVENT_TITLES.get(classification.category, "Email processed"),
            description=classification.summary,
            occurred_at=email.received_at,
            metadata_={
                "deadline": classification.deadline.isoformat()
                if classification.deadline
                else None,
                "interview_date": (
                    classification.interview_date.isoformat()
                    if classification.interview_date
                    else None
                ),
                "confidence_score": classification.confidence_score,
                "category": classification.category.value,
            },
        )
        session.add(event)
        await session.flush()
        return application, event

    def _resolve_status(
        self,
        current: ApplicationStatus,
        incoming: ApplicationStatus,
    ) -> ApplicationStatus:
        priority = {
            ApplicationStatus.UNKNOWN: 0,
            ApplicationStatus.APPLIED: 1,
            ApplicationStatus.FOLLOW_UP: 2,
            ApplicationStatus.ASSESSMENT: 3,
            ApplicationStatus.INTERVIEW_SCHEDULED: 4,
            ApplicationStatus.OFFER_RECEIVED: 5,
            ApplicationStatus.REJECTED: 6,
        }
        if priority.get(incoming, 0) >= priority.get(current, 0):
            return incoming
        return current

    @staticmethod
    def utcnow() -> datetime:
        return datetime.now(UTC)
