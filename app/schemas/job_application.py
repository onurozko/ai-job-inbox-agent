from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ApplicationStatus
from app.schemas.application_event import ApplicationEventRead


class JobApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    company_name: str
    job_title: str | None
    status: ApplicationStatus
    latest_summary: str | None
    last_email_at: datetime | None
    action_required: bool
    created_at: datetime
    updated_at: datetime


class JobApplicationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_name: str
    job_title: str | None
    status: ApplicationStatus
    last_email_at: datetime | None
    action_required: bool


class JobApplicationDetail(JobApplicationRead):
    events: list[ApplicationEventRead] = Field(default_factory=list)


class JobApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    latest_summary: str | None = None
    action_required: bool | None = None
