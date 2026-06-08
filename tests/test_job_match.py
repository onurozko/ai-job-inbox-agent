import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ApplicationStatus
from app.models.job_application import JobApplication
from app.models.user import User
from app.schemas.job_match import MatchVerdict
from app.schemas.profile import ResumeProfileUpdate
from app.services.profile_service import ProfileService

SAMPLE_RESUME = (
    "Software Engineer with experience in Python, FastAPI, SQLAlchemy, PostgreSQL, and Docker. "
    "Built backend APIs and async data pipelines."
)
FULL_JOB_DESCRIPTION = (
    "We are hiring a backend engineer with Python, FastAPI, PostgreSQL, and Docker experience. "
    "You will build APIs, work with SQLAlchemy, and deploy services in production."
)
SHORT_JOB_DESCRIPTION = "Backend engineer role."


@pytest.mark.asyncio
async def test_user_can_create_and_update_resume_profile(
    client: AsyncClient,
    user_a: User,
    user_a_headers: dict[str, str],
) -> None:
    create_response = await client.put(
        "/api/v1/profile/resume",
        headers=user_a_headers,
        json={
            "resume_text": SAMPLE_RESUME,
            "target_roles": ["Backend Engineer"],
            "target_locations": ["Remote"],
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["user_id"] == str(user_a.id)
    assert created["resume_text"] == SAMPLE_RESUME
    assert created["target_roles"] == ["Backend Engineer"]

    update_response = await client.put(
        "/api/v1/profile/resume",
        headers=user_a_headers,
        json={
            "resume_text": SAMPLE_RESUME + " Added Kubernetes experience.",
            "target_roles": ["Platform Engineer"],
            "target_locations": ["Toronto"],
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["id"] == created["id"]
    assert "Kubernetes" in updated["resume_text"]
    assert updated["target_roles"] == ["Platform Engineer"]

    get_response = await client.get("/api/v1/profile/resume", headers=user_a_headers)
    assert get_response.status_code == 200
    assert get_response.json()["target_locations"] == ["Toronto"]


@pytest.mark.asyncio
async def test_user_cannot_access_another_users_profile(
    client: AsyncClient,
    async_session: AsyncSession,
    user_a: User,
    user_b: User,
    user_b_headers: dict[str, str],
) -> None:
    service = ProfileService()
    await service.upsert_resume(
        async_session,
        user_id=user_a.id,
        payload=ResumeProfileUpdate(resume_text=SAMPLE_RESUME),
    )
    await async_session.commit()

    get_response = await client.get("/api/v1/profile/resume", headers=user_b_headers)
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_match_job_requires_resume_profile(
    client: AsyncClient,
    user_a_headers: dict[str, str],
) -> None:
    response = await client.post(
        "/api/v1/assistant/match-job",
        headers=user_a_headers,
        json={"job_description": FULL_JOB_DESCRIPTION},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Resume profile not found"


@pytest.mark.asyncio
async def test_match_job_requires_job_application_id_or_job_description(
    client: AsyncClient,
    user_a_headers: dict[str, str],
) -> None:
    create_response = await client.put(
        "/api/v1/profile/resume",
        headers=user_a_headers,
        json={"resume_text": SAMPLE_RESUME},
    )
    assert create_response.status_code == 200

    response = await client.post(
        "/api/v1/assistant/match-job",
        headers=user_a_headers,
        json={"job_application_id": None, "job_description": None},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_user_cannot_match_against_another_users_job_application(
    client: AsyncClient,
    async_session: AsyncSession,
    user_a: User,
    user_b: User,
    user_b_headers: dict[str, str],
) -> None:
    service = ProfileService()
    await service.upsert_resume(
        async_session,
        user_id=user_b.id,
        payload=ResumeProfileUpdate(resume_text=SAMPLE_RESUME),
    )

    application = JobApplication(
        user_id=user_a.id,
        company_name="Shopify",
        job_title="Software Engineer",
        company_name_normalized="shopify",
        job_title_normalized="software engineer",
        status=ApplicationStatus.APPLIED,
    )
    async_session.add(application)
    await async_session.commit()

    response = await client.post(
        "/api/v1/assistant/match-job",
        headers=user_b_headers,
        json={"job_application_id": str(application.id)},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Job application not found"


@pytest.mark.asyncio
async def test_short_job_description_returns_unclear_verdict(
    client: AsyncClient,
    user_a_headers: dict[str, str],
) -> None:
    create_response = await client.put(
        "/api/v1/profile/resume",
        headers=user_a_headers,
        json={"resume_text": SAMPLE_RESUME},
    )
    assert create_response.status_code == 200

    response = await client.post(
        "/api/v1/assistant/match-job",
        headers=user_a_headers,
        json={"job_description": SHORT_JOB_DESCRIPTION},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["verdict"] == MatchVerdict.UNCLEAR.value
    assert payload["match_score"] == 0
    assert any("too short" in concern.lower() for concern in payload["concerns"])


@pytest.mark.asyncio
async def test_mock_agent_returns_deterministic_match_output(
    client: AsyncClient,
    user_a_headers: dict[str, str],
) -> None:
    create_response = await client.put(
        "/api/v1/profile/resume",
        headers=user_a_headers,
        json={"resume_text": SAMPLE_RESUME},
    )
    assert create_response.status_code == 200

    response = await client.post(
        "/api/v1/assistant/match-job",
        headers=user_a_headers,
        json={"job_description": FULL_JOB_DESCRIPTION},
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["match_score"] == 100
    assert payload["verdict"] == MatchVerdict.STRONG_MATCH.value
    assert set(payload["matched_skills"]) == {
        "python",
        "fastapi",
        "postgresql",
        "docker",
        "sqlalchemy",
    }
    assert payload["role_alignment_summary"]
    assert payload["suggested_next_steps"]
