from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.demo.constants import (
    DEMO_GMAIL_ID_PREFIX,
    DEMO_RESUME_TEXT,
    DEMO_USER_EMAIL,
    DEMO_USER_FULL_NAME,
    DEMO_USER_GOOGLE_SUB,
)
from app.models.email_message import EmailMessage
from app.models.enums import EmailCategory
from app.models.job_application import JobApplication
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.email import EmailClassificationResult
from app.schemas.profile import ResumeProfileUpdate
from app.services.application_updater import ApplicationUpdater
from app.services.email_classifier import EmailClassifier
from app.services.profile_service import ProfileService


@dataclass(frozen=True)
class DemoEmailSpec:
    key: str
    company_name: str
    job_title: str
    category: EmailCategory
    subject: str
    sender_email: str
    body_text: str
    received_at: datetime
    summary: str
    action_required: bool = False
    deadline: datetime | None = None
    interview_date: datetime | None = None


@dataclass(frozen=True)
class DemoSeedResult:
    user_created: bool
    profile_created: bool
    emails_created: int
    emails_skipped: int
    applications_count: int
    events_count: int
    user_id: UUID


def build_demo_email_specs(*, now: datetime | None = None) -> list[DemoEmailSpec]:
    anchor = now or datetime.now(UTC)
    return [
        DemoEmailSpec(
            key="confirmation",
            company_name="Stripe",
            job_title="Backend Engineer",
            category=EmailCategory.APPLICATION_CONFIRMATION,
            subject="Application received - Backend Engineer at Stripe",
            sender_email="talent@stripe.com",
            body_text=(
                "Thank you for applying to the Backend Engineer role at Stripe. "
                "We have received your application and our recruiting team will review it soon."
            ),
            received_at=anchor - timedelta(days=14),
            summary="Stripe confirmed receipt of the backend engineer application.",
        ),
        DemoEmailSpec(
            key="assessment",
            company_name="Datadog",
            job_title="Software Engineer",
            category=EmailCategory.ASSESSMENT,
            subject="Complete your Datadog technical assessment",
            sender_email="recruiting@datadog.com",
            body_text=(
                "Please complete the online assessment for the Software Engineer role "
                "within the next few days so we can continue your application."
            ),
            received_at=anchor - timedelta(days=10),
            summary="Datadog requested a technical assessment with an upcoming deadline.",
            action_required=True,
            deadline=anchor + timedelta(days=3),
        ),
        DemoEmailSpec(
            key="interview",
            company_name="Shopify",
            job_title="Senior Backend Engineer",
            category=EmailCategory.INTERVIEW_INVITATION,
            subject="Interview invitation for Senior Backend Engineer at Shopify",
            sender_email="careers@shopify.com",
            body_text=(
                "We would like to invite you to a virtual interview for the "
                "Senior Backend Engineer position. Please confirm your availability."
            ),
            received_at=anchor - timedelta(days=5),
            summary="Shopify invited the candidate to a virtual interview.",
            action_required=True,
            interview_date=anchor + timedelta(days=2),
        ),
        DemoEmailSpec(
            key="rejection",
            company_name="Meta",
            job_title="Software Engineer",
            category=EmailCategory.REJECTION,
            subject="Update on your Meta application",
            sender_email="noreply@meta.com",
            body_text=(
                "Thank you for your interest in Meta. After careful review, we will not be "
                "moving forward with your application for the Software Engineer role."
            ),
            received_at=anchor - timedelta(days=7),
            summary="Meta sent a rejection for the software engineer application.",
        ),
        DemoEmailSpec(
            key="recruiter-outreach",
            company_name="Anthropic",
            job_title="Backend Engineer",
            category=EmailCategory.RECRUITER_OUTREACH,
            subject="Backend Engineer opportunity at Anthropic",
            sender_email="recruiting@anthropic.com",
            body_text=(
                "I came across your background and thought you might be a strong fit for a "
                "Backend Engineer role on our platform team. Would you be open to a brief chat?"
            ),
            received_at=anchor - timedelta(days=3),
            summary="Anthropic recruiter reached out about a backend engineer role.",
            action_required=True,
        ),
        DemoEmailSpec(
            key="offer",
            company_name="Figma",
            job_title="Software Engineer",
            category=EmailCategory.OFFER,
            subject="Offer letter for Software Engineer at Figma",
            sender_email="offers@figma.com",
            body_text=(
                "We are excited to extend an offer for the Software Engineer position at Figma. "
                "Please review the attached details and let us know if you have any questions."
            ),
            received_at=anchor - timedelta(days=1),
            summary="Figma extended an offer for the software engineer role.",
            action_required=True,
        ),
    ]


async def get_demo_user(session: AsyncSession) -> User | None:
    stmt = select(User).where(User.email == DEMO_USER_EMAIL)
    return (await session.execute(stmt)).scalar_one_or_none()


async def seed_demo_data(session: AsyncSession) -> DemoSeedResult:
    user, user_created = await _get_or_create_demo_user(session)
    profile_created = await _ensure_demo_profile(session, user.id)

    updater = ApplicationUpdater()
    emails_created = 0
    emails_skipped = 0

    for spec in build_demo_email_specs():
        created = await _seed_demo_email(session, user=user, spec=spec, updater=updater)
        if created:
            emails_created += 1
        else:
            emails_skipped += 1

    applications_count = await _count_user_applications(session, user.id)
    events_count = await _count_user_events(session, user.id)

    return DemoSeedResult(
        user_created=user_created,
        profile_created=profile_created,
        emails_created=emails_created,
        emails_skipped=emails_skipped,
        applications_count=applications_count,
        events_count=events_count,
        user_id=user.id,
    )


async def _get_or_create_demo_user(session: AsyncSession) -> tuple[User, bool]:
    existing = await get_demo_user(session)
    if existing is not None:
        if existing.full_name != DEMO_USER_FULL_NAME:
            existing.full_name = DEMO_USER_FULL_NAME
        if existing.google_sub != DEMO_USER_GOOGLE_SUB:
            existing.google_sub = DEMO_USER_GOOGLE_SUB
        await session.flush()
        return existing, False

    user = User(
        email=DEMO_USER_EMAIL,
        full_name=DEMO_USER_FULL_NAME,
        google_sub=DEMO_USER_GOOGLE_SUB,
    )
    session.add(user)
    await session.flush()
    return user, True


async def _ensure_demo_profile(session: AsyncSession, user_id: UUID) -> bool:
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        await ProfileService().upsert_resume(
            session,
            user_id=user_id,
            payload=ResumeProfileUpdate(
                resume_text=DEMO_RESUME_TEXT,
                target_roles=["Backend Engineer", "Software Engineer"],
                target_locations=["Remote", "Toronto"],
            ),
        )
        return False

    await ProfileService().upsert_resume(
        session,
        user_id=user_id,
        payload=ResumeProfileUpdate(
            resume_text=DEMO_RESUME_TEXT,
            target_roles=["Backend Engineer", "Software Engineer"],
            target_locations=["Remote", "Toronto"],
        ),
    )
    return True


async def _seed_demo_email(
    session: AsyncSession,
    *,
    user: User,
    spec: DemoEmailSpec,
    updater: ApplicationUpdater,
) -> bool:
    gmail_message_id = f"{DEMO_GMAIL_ID_PREFIX}{spec.key}"
    existing_stmt = select(EmailMessage).where(
        EmailMessage.user_id == user.id,
        EmailMessage.gmail_message_id == gmail_message_id,
    )
    if (await session.execute(existing_stmt)).scalar_one_or_none() is not None:
        return False

    email = EmailMessage(
        user_id=user.id,
        gmail_message_id=gmail_message_id,
        thread_id=f"demo-thread-{spec.key}",
        subject=spec.subject,
        sender_email=spec.sender_email,
        received_at=spec.received_at,
        raw_snippet=spec.body_text[:160],
        body_text=spec.body_text,
        processed_at=spec.received_at,
    )
    session.add(email)
    await session.flush()

    classification = EmailClassificationResult(
        category=spec.category,
        company_name=spec.company_name,
        job_title=spec.job_title,
        summary=spec.summary,
        confidence_score=0.95,
        action_required=spec.action_required,
        deadline=spec.deadline,
        interview_date=spec.interview_date,
    )
    EmailClassifier.apply_to_email(email, classification)
    await updater.process_classified_email(session, email, classification)
    return True


async def _count_user_applications(session: AsyncSession, user_id: UUID) -> int:
    stmt = select(func.count()).select_from(JobApplication).where(JobApplication.user_id == user_id)
    return (await session.execute(stmt)).scalar_one()


async def _count_user_events(session: AsyncSession, user_id: UUID) -> int:
    from app.models.application_event import ApplicationEvent

    stmt = (
        select(func.count())
        .select_from(ApplicationEvent)
        .join(JobApplication, ApplicationEvent.job_application_id == JobApplication.id)
        .where(JobApplication.user_id == user_id)
    )
    return (await session.execute(stmt)).scalar_one()


def demo_email_keys() -> list[str]:
    return [spec.key for spec in build_demo_email_specs()]
