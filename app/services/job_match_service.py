from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.repositories import job_application_repository
from app.integrations.ai.job_match_agent import JobMatchContext, generate_job_match
from app.models.job_application import JobApplication
from app.schemas.job_match import MatchJobRequest, MatchJobResponse
from app.services.profile_service import ProfileService


class JobMatchService:
    def __init__(self, profile_service: ProfileService | None = None) -> None:
        self._profile_service = profile_service or ProfileService()

    async def match_job(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        request: MatchJobRequest,
    ) -> MatchJobResponse:
        profile = await self._profile_service.get_profile_for_user(session, user_id)
        if profile is None:
            raise NotFoundError("Resume profile not found")

        application = None
        if request.job_application_id is not None:
            application = await job_application_repository.get_application_for_user(
                session,
                user_id=user_id,
                application_id=request.job_application_id,
            )
            if application is None:
                raise NotFoundError("Job application not found")

        job_description = self._build_job_description(
            application_summary=self._application_context(application),
            pasted_description=request.job_description,
        )

        context = JobMatchContext(
            resume_text=profile.resume_text,
            target_roles=profile.target_roles,
            target_locations=profile.target_locations,
            company_name=application.company_name if application else None,
            job_title=application.job_title if application else None,
            application_status=application.status.value if application else None,
            job_description=job_description,
        )
        return await generate_job_match(context)

    @staticmethod
    def _application_context(application: JobApplication | None) -> str | None:
        if application is None:
            return None
        parts = [
            f"Company: {application.company_name}",
            f"Job title: {application.job_title or 'Unknown'}",
            f"Status: {application.status.value}",
        ]
        if application.latest_summary:
            parts.append(f"Latest summary: {application.latest_summary}")
        return "\n".join(parts)

    @staticmethod
    def _build_job_description(
        *,
        application_summary: str | None,
        pasted_description: str | None,
    ) -> str:
        sections: list[str] = []
        if application_summary:
            sections.append("Application context:\n" + application_summary)
        if pasted_description and pasted_description.strip():
            sections.append("Job description:\n" + pasted_description.strip())
        return "\n\n".join(sections)
