from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class WeeklyApplicationTrendPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    week_start: date
    count: int


class AnalyticsSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_applications: int = 0
    active_applications: int = 0
    rejected_applications: int = 0
    offers: int = 0
    interviews: int = 0
    assessments: int = 0
    recruiter_outreach_count: int = 0
    response_rate: float = 0.0
    rejection_rate: float = 0.0
    interview_rate: float = 0.0
    offer_rate: float = 0.0
    average_response_time_days: float | None = None
    applications_by_status: dict[str, int] = Field(default_factory=dict)
    applications_by_company: dict[str, int] = Field(default_factory=dict)
    events_by_type: dict[str, int] = Field(default_factory=dict)
    weekly_application_trend: list[WeeklyApplicationTrendPoint] = Field(default_factory=list)
    recent_activity_count_7d: int = 0
    recent_activity_count_30d: int = 0
