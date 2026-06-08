from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ApplicationStatus
from app.schemas.application_event import ApplicationEventRead
from app.schemas.email import EmailMessageRead
from app.schemas.job_application import JobApplicationRead


class UpcomingDeadline(BaseModel):
    application_id: UUID
    company_name: str
    job_title: str | None
    deadline: datetime
    deadline_type: str


class DashboardSummary(BaseModel):
    total_applications: int
    active_applications: int
    rejected_applications: int
    interviews_scheduled: int
    assessments_pending: int
    offers: int
    follow_ups_needed: int
    upcoming_deadlines: list[UpcomingDeadline]
    recent_events: list[ApplicationEventRead]


class ApplicationTimeline(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application: JobApplicationRead
    current_status: ApplicationStatus
    emails: list[EmailMessageRead]
    events: list[ApplicationEventRead]
    next_deadline: datetime | None = None
    next_interview_date: datetime | None = None
