from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.google.oauth import GoogleLoginTokens, GoogleUserInfo
from app.models.email_message import EmailMessage
from app.models.enums import ApplicationStatus
from app.models.gmail_credential import GmailCredential
from app.models.job_application import JobApplication
from app.models.user import User
from app.services.email_sync import EmailSyncService


@pytest.mark.asyncio
async def test_unauthenticated_users_cannot_access_protected_routes(client: AsyncClient) -> None:
    protected_paths = [
        "/api/v1/emails",
        "/api/v1/applications",
        "/api/v1/dashboard/summary",
        "/api/v1/assistant/next-actions",
        "/api/v1/auth/me",
    ]
    for path in protected_paths:
        response = await client.get(path)
        assert response.status_code == 401, path


@pytest.mark.asyncio
async def test_authenticated_users_can_access_their_dashboard(
    client: AsyncClient,
    user_a: User,
    user_a_headers: dict[str, str],
) -> None:
    response = await client.get("/api/v1/dashboard/summary", headers=user_a_headers)
    assert response.status_code == 200
    assert response.json()["total_applications"] == 0


@pytest.mark.asyncio
async def test_user_cannot_access_other_users_application(
    client: AsyncClient,
    async_session: AsyncSession,
    user_a: User,
    user_b: User,
    user_b_headers: dict[str, str],
) -> None:
    application = JobApplication(
        user_id=user_a.id,
        company_name="Shopify",
        job_title="Engineer",
        company_name_normalized="shopify",
        job_title_normalized="engineer",
        status=ApplicationStatus.APPLIED,
    )
    async_session.add(application)
    await async_session.flush()

    response = await client.get(
        f"/api/v1/applications/{application.id}",
        headers=user_b_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_user_cannot_access_other_users_email(
    client: AsyncClient,
    async_session: AsyncSession,
    user_a: User,
    user_b: User,
    user_b_headers: dict[str, str],
) -> None:
    email = EmailMessage(
        user_id=user_a.id,
        gmail_message_id="private-email",
        subject="Private",
        sender_email="jobs@shopify.com",
        received_at=datetime.now(UTC),
    )
    async_session.add(email)
    await async_session.flush()

    response = await client.get(
        f"/api/v1/emails/{email.id}",
        headers=user_b_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_google_login_callback_creates_or_updates_user(
    client: AsyncClient,
    async_session: AsyncSession,
) -> None:
    google_user = GoogleUserInfo(
        google_sub="google-sub-new",
        email="newuser@gmail.com",
        full_name="New User",
        picture_url="https://example.com/avatar.png",
    )

    with (
        patch("app.services.auth_service.decode_oauth_state", return_value={"flow": "login"}),
        patch(
            "app.services.auth_service.exchange_login_code",
            return_value=GoogleLoginTokens(access_token="token"),
        ),
        patch(
            "app.services.auth_service.fetch_google_userinfo",
            new=AsyncMock(return_value=google_user),
        ),
    ):
        response = await client.get(
            "/api/v1/auth/google/callback",
            params={"code": "test-code", "state": "signed-state", "response_format": "json"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["user"]["email"] == "newuser@gmail.com"
    assert payload["user"]["google_sub"] == "google-sub-new"

    stored_user = (
        await async_session.execute(select(User).where(User.google_sub == "google-sub-new"))
    ).scalar_one()
    assert stored_user.full_name == "New User"


@pytest.mark.asyncio
async def test_gmail_sync_uses_current_user_id(
    async_session: AsyncSession,
    user_a: User,
) -> None:
    credential = GmailCredential(
        user_id=user_a.id,
        access_token="access",
        refresh_token="refresh",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="client-id",
        client_secret="client-secret",
        scopes="https://www.googleapis.com/auth/gmail.readonly",
    )
    async_session.add(credential)
    await async_session.flush()

    class MockGmailClient:
        async def fetch_recent_messages_async(self, *, query: str, max_results: int):
            from app.integrations.gmail.client import ParsedGmailMessage

            return [
                ParsedGmailMessage(
                    gmail_message_id=f"sync-{uuid4()}",
                    thread_id="thread-1",
                    subject="Application received",
                    sender_email="jobs@shopify.com",
                    raw_snippet="Thanks for applying",
                    body_text="Thanks for applying to Shopify",
                    received_at=datetime.now(UTC),
                )
            ]

    service = EmailSyncService()
    summary = await service.sync_user_emails(
        async_session,
        user=user_a,
        gmail_client=MockGmailClient(),
    )

    assert summary.created_count == 1
    emails = (
        (await async_session.execute(select(EmailMessage).where(EmailMessage.user_id == user_a.id)))
        .scalars()
        .all()
    )
    assert len(emails) == 1
    assert emails[0].user_id == user_a.id


@pytest.mark.asyncio
async def test_auth_me_returns_current_user(
    client: AsyncClient,
    user_a: User,
    user_a_headers: dict[str, str],
) -> None:
    response = await client.get("/api/v1/auth/me", headers=user_a_headers)
    assert response.status_code == 200
    assert response.json()["email"] == user_a.email


@pytest.mark.asyncio
async def test_logout_requires_authentication(
    client: AsyncClient, user_a_headers: dict[str, str]
) -> None:
    unauthenticated = await client.post("/api/v1/auth/logout")
    assert unauthenticated.status_code == 401

    authenticated = await client.post("/api/v1/auth/logout", headers=user_a_headers)
    assert authenticated.status_code == 200
    assert authenticated.json()["message"] == "Logged out successfully"
