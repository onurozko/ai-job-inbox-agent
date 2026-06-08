from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_message import EmailMessage
from app.models.enums import EmailCategory
from app.models.user import User
from app.schemas.reply_draft import DraftReplyRequest
from app.services.reply_draft_service import ReplyDraftService


async def _create_email(
    session: AsyncSession,
    user: User,
    *,
    gmail_message_id: str,
    category: EmailCategory | None,
    subject: str = "Subject",
    body_text: str = "Body content that is long enough to avoid short-body warnings for testing.",
    sender_email: str = "recruiter@company.com",
    deadline: datetime | None = None,
    interview_date: datetime | None = None,
) -> EmailMessage:
    email = EmailMessage(
        user_id=user.id,
        gmail_message_id=gmail_message_id,
        subject=subject,
        sender_email=sender_email,
        received_at=datetime.now(UTC),
        body_text=body_text,
        category=category,
        company_name="Shopify",
        job_title="Software Engineer",
        deadline=deadline,
        interview_date=interview_date,
        confidence_score=0.9,
    )
    session.add(email)
    await session.flush()
    return email


@pytest.mark.asyncio
async def test_cannot_draft_reply_for_another_users_email(
    client: AsyncClient,
    async_session: AsyncSession,
    user_a: User,
    user_b: User,
    user_b_headers: dict[str, str],
) -> None:
    email = await _create_email(
        async_session,
        user_a,
        gmail_message_id="private-email",
        category=EmailCategory.INTERVIEW_INVITATION,
    )

    response = await client.post(
        "/api/v1/assistant/draft-reply",
        headers=user_b_headers,
        json={"email_id": str(email.id)},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_interview_invitation_creates_professional_scheduling_reply(
    async_session: AsyncSession,
    user_a: User,
) -> None:
    email = await _create_email(
        async_session,
        user_a,
        gmail_message_id="interview-email",
        category=EmailCategory.INTERVIEW_INVITATION,
        subject="Interview invitation from Shopify",
        body_text="We would like to invite you to interview for the Software Engineer role.",
    )

    service = ReplyDraftService()
    draft = await service.create_draft(
        async_session,
        user_id=user_a.id,
        request=DraftReplyRequest(email_id=email.id),
    )

    assert draft is not None
    assert "interview" in draft.draft_body.lower()
    assert "coordinate" in draft.draft_body.lower() or "availability" in draft.draft_body.lower()
    assert draft.recipient_email == "recruiter@company.com"
    assert draft.subject.startswith("Re:")


@pytest.mark.asyncio
async def test_assessment_email_acknowledges_deadline(
    async_session: AsyncSession,
    user_a: User,
) -> None:
    deadline = datetime.now(UTC) + timedelta(days=3)
    email = await _create_email(
        async_session,
        user_a,
        gmail_message_id="assessment-email",
        category=EmailCategory.ASSESSMENT,
        subject="Complete your assessment",
        body_text="Please complete the online assessment for the Software Engineer role.",
        deadline=deadline,
    )

    service = ReplyDraftService()
    draft = await service.create_draft(
        async_session,
        user_id=user_a.id,
        request=DraftReplyRequest(email_id=email.id),
    )

    assert draft is not None
    assert "assessment" in draft.draft_body.lower()
    assert deadline.strftime("%A, %B %d") in draft.draft_body


@pytest.mark.asyncio
async def test_rejection_email_includes_warning(
    async_session: AsyncSession,
    user_a: User,
) -> None:
    email = await _create_email(
        async_session,
        user_a,
        gmail_message_id="rejection-email",
        category=EmailCategory.REJECTION,
        subject="Update on your application",
        body_text=(
            "Thank you for your interest. "
            "We will not be moving forward with your application."
        ),
    )

    service = ReplyDraftService()
    draft = await service.create_draft(
        async_session,
        user_id=user_a.id,
        request=DraftReplyRequest(email_id=email.id),
    )

    assert draft is not None
    assert any("rejection" in warning.lower() for warning in draft.warnings)
    assert "thank you" in draft.draft_body.lower()


@pytest.mark.asyncio
async def test_irrelevant_email_includes_warning(
    async_session: AsyncSession,
    user_a: User,
) -> None:
    email = await _create_email(
        async_session,
        user_a,
        gmail_message_id="irrelevant-email",
        category=EmailCategory.IRRELEVANT,
        subject="Weekly newsletter",
        body_text="Here are this week's product updates and news from our team.",
    )

    service = ReplyDraftService()
    draft = await service.create_draft(
        async_session,
        user_id=user_a.id,
        request=DraftReplyRequest(email_id=email.id),
    )

    assert draft is not None
    assert any("irrelevant" in warning.lower() for warning in draft.warnings)


@pytest.mark.asyncio
async def test_draft_endpoint_never_sends_email(
    client: AsyncClient,
    async_session: AsyncSession,
    user_a: User,
    user_a_headers: dict[str, str],
) -> None:
    email = await _create_email(
        async_session,
        user_a,
        gmail_message_id="draft-only",
        category=EmailCategory.RECRUITER_OUTREACH,
    )

    with patch(
        "app.integrations.gmail.client.GmailClient.fetch_recent_messages_async",
        new=AsyncMock(),
    ) as fetch_mock:
        response = await client.post(
            "/api/v1/assistant/draft-reply",
            headers=user_a_headers,
            json={"email_id": str(email.id), "tone": "professional"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["draft_body"]
    assert payload["recipient_email"] == "recruiter@company.com"
    fetch_mock.assert_not_called()
