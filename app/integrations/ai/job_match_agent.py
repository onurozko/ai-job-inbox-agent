from dataclasses import dataclass

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.schemas.job_match import MatchJobResponse, MatchVerdict

MIN_JOB_DESCRIPTION_LENGTH = 80

SYSTEM_PROMPT = """You compare a candidate resume against a job description for job-search planning.

Rules:
- Do NOT invent experience, skills, or qualifications not present in the resume.
- Be honest about gaps and weak alignment.
- Prefer practical advice over generic encouragement.
- If the job description is too short or vague, set verdict to unclear and explain why.
- Keep suggestions focused on improving applications and resume presentation,
  not fabricating qualifications.
- match_score must be an integer from 0 to 100 reflecting honest fit based on
  evidence in the resume.
- verdict must be one of: strong_match, moderate_match, weak_match, unclear
"""

TRACKED_SKILLS = (
    "python",
    "fastapi",
    "sqlalchemy",
    "postgresql",
    "docker",
    "aws",
    "react",
    "typescript",
    "kubernetes",
    "redis",
)


class JobMatchAgentOutput(BaseModel):
    match_score: int = Field(ge=0, le=100)
    verdict: MatchVerdict
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    role_alignment_summary: str
    concerns: list[str] = Field(default_factory=list)
    suggested_resume_keywords: list[str] = Field(default_factory=list)
    suggested_next_steps: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class JobMatchContext:
    resume_text: str
    target_roles: list[str] | None
    target_locations: list[str] | None
    company_name: str | None
    job_title: str | None
    application_status: str | None
    job_description: str


def _score_to_verdict(score: int) -> MatchVerdict:
    if score >= 75:
        return MatchVerdict.STRONG_MATCH
    if score >= 50:
        return MatchVerdict.MODERATE_MATCH
    if score >= 25:
        return MatchVerdict.WEAK_MATCH
    return MatchVerdict.WEAK_MATCH


def _mock_job_match(context: JobMatchContext) -> JobMatchAgentOutput:
    description = context.job_description.strip()
    if len(description) < MIN_JOB_DESCRIPTION_LENGTH:
        return JobMatchAgentOutput(
            match_score=0,
            verdict=MatchVerdict.UNCLEAR,
            matched_skills=[],
            missing_skills=[],
            role_alignment_summary=(
                "The job description is too short to assess fit reliably against the resume."
            ),
            concerns=["Job description is too short for a reliable match assessment."],
            suggested_resume_keywords=[],
            suggested_next_steps=["Provide a fuller job description before retrying the match."],
        )

    resume_lower = context.resume_text.lower()
    description_lower = description.lower()

    resume_skills = [skill for skill in TRACKED_SKILLS if skill in resume_lower]
    job_skills = [skill for skill in TRACKED_SKILLS if skill in description_lower]
    matched_skills = [skill for skill in job_skills if skill in resume_skills]
    missing_skills = [skill for skill in job_skills if skill not in resume_skills]

    if not job_skills:
        score = 45
        matched_skills = resume_skills[:3]
        missing_skills = []
        summary = (
            "The job description does not mention common technical keywords, "
            "so the match is based on limited evidence."
        )
        concerns = ["Job description lacks specific skill requirements for a precise comparison."]
        keywords = resume_skills[:5]
        next_steps = ["Ask for or locate a fuller job description with explicit requirements."]
    else:
        score = int(round((len(matched_skills) / len(job_skills)) * 100))
        role = context.job_title or "the role"
        company = context.company_name or "the company"
        summary = (
            f"The resume aligns with {len(matched_skills)} of {len(job_skills)} "
            f"tracked requirements for {role} at {company}."
        )
        concerns = []
        if missing_skills:
            concerns.append(
                "Some listed job requirements do not appear in the resume: "
                + ", ".join(missing_skills[:5])
            )
        keywords = missing_skills[:5]
        next_steps = []
        if missing_skills:
            next_steps.append(
                "Highlight adjacent experience for missing requirements "
                "instead of inventing skills."
            )
        if context.target_roles and not any(
            role.lower() in description_lower for role in context.target_roles
        ):
            next_steps.append(
                "Confirm this role aligns with your target roles before applying."
            )
        if not next_steps:
            next_steps.append("Tailor the resume summary to mirror the strongest matched skills.")

    return JobMatchAgentOutput(
        match_score=score,
        verdict=_score_to_verdict(score),
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        role_alignment_summary=summary,
        concerns=concerns,
        suggested_resume_keywords=keywords,
        suggested_next_steps=next_steps,
    )


async def generate_job_match(context: JobMatchContext) -> MatchJobResponse:
    settings = get_settings()
    if not settings.openai_api_key:
        return MatchJobResponse.model_validate(_mock_job_match(context).model_dump())

    try:
        from pydantic_ai import Agent

        agent = Agent(
            model="openai:gpt-4o-mini",
            output_type=JobMatchAgentOutput,
            system_prompt=SYSTEM_PROMPT,
        )
        prompt = (
            f"Target roles: {', '.join(context.target_roles or []) or 'None'}\n"
            f"Target locations: {', '.join(context.target_locations or []) or 'None'}\n"
            f"Company: {context.company_name or 'Unknown'}\n"
            f"Job title: {context.job_title or 'Unknown'}\n"
            f"Application status: {context.application_status or 'Unknown'}\n\n"
            f"Resume:\n{context.resume_text[:12000]}\n\n"
            f"Job description:\n{context.job_description[:12000]}"
        )
        result = await agent.run(prompt)
        return MatchJobResponse.model_validate(result.output.model_dump())
    except Exception:
        return MatchJobResponse.model_validate(_mock_job_match(context).model_dump())
