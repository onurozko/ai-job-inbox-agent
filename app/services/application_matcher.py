import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ApplicationStatus
from app.models.job_application import JobApplication

_LEGAL_SUFFIXES = re.compile(
    r"\b(inc\.?|incorporated|ltd\.?|limited|llc|corp\.?|corporation|co\.?|company)\b",
    re.IGNORECASE,
)


def normalize_company_name(name: str) -> str:
    cleaned = _LEGAL_SUFFIXES.sub("", name)
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip().lower()


def normalize_job_title(title: str | None) -> str:
    if not title:
        return ""
    cleaned = re.sub(r"[^\w\s]", " ", title)
    return re.sub(r"\s+", " ", cleaned).strip().lower()


class ApplicationMatcher:
    async def find_or_create_application(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        company_name: str,
        job_title: str | None,
        status: ApplicationStatus = ApplicationStatus.UNKNOWN,
    ) -> JobApplication:
        company_normalized = normalize_company_name(company_name)
        title_normalized = normalize_job_title(job_title)

        stmt = select(JobApplication).where(
            JobApplication.user_id == user_id,
            JobApplication.company_name_normalized == company_normalized,
            JobApplication.job_title_normalized == title_normalized,
        )
        result = await session.execute(stmt)
        application = result.scalar_one_or_none()

        if application is not None:
            return application

        application = JobApplication(
            user_id=user_id,
            company_name=company_name.strip(),
            job_title=job_title.strip() if job_title else None,
            company_name_normalized=company_normalized,
            job_title_normalized=title_normalized,
            status=status,
        )
        session.add(application)
        await session.flush()
        return application
