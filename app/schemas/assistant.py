from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ActionPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NextAction(BaseModel):
    priority: ActionPriority
    application_id: UUID | None = None
    company_name: str
    job_title: str | None = None
    action_type: str
    reason: str
    suggested_next_step: str
    due_date: datetime | None = None


class NextActionsResponse(BaseModel):
    summary: str
    actions: list[NextAction] = Field(default_factory=list)


class ApplicationActionContext(BaseModel):
    application_id: UUID
    company_name: str
    job_title: str | None = None
    status: str
    action_required: bool
    last_email_at: datetime | None = None
    recent_events: list[str] = Field(default_factory=list)
    deadlines: list[datetime] = Field(default_factory=list)
    interview_dates: list[datetime] = Field(default_factory=list)


class NextActionAgentInput(BaseModel):
    applications: list[ApplicationActionContext]
    recent_events: list[str] = Field(default_factory=list)
