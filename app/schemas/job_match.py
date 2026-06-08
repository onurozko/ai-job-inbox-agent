from enum import Enum
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class MatchVerdict(str, Enum):
    STRONG_MATCH = "strong_match"
    MODERATE_MATCH = "moderate_match"
    WEAK_MATCH = "weak_match"
    UNCLEAR = "unclear"


class MatchJobRequest(BaseModel):
    job_application_id: UUID | None = None
    job_description: str | None = None

    @model_validator(mode="after")
    def require_job_input(self) -> Self:
        has_application = self.job_application_id is not None
        has_description = bool(self.job_description and self.job_description.strip())
        if not has_application and not has_description:
            raise ValueError("At least one of job_application_id or job_description is required")
        return self


class MatchJobResponse(BaseModel):
    match_score: int = Field(ge=0, le=100)
    verdict: MatchVerdict
    matched_skills: list[str]
    missing_skills: list[str]
    role_alignment_summary: str
    concerns: list[str] = Field(default_factory=list)
    suggested_resume_keywords: list[str] = Field(default_factory=list)
    suggested_next_steps: list[str] = Field(default_factory=list)
