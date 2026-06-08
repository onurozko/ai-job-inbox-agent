from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EmailCategory


class EmailClassificationResult(BaseModel):
    category: EmailCategory
    company_name: str | None = None
    job_title: str | None = None
    status: str | None = None
    sender_email: str | None = None
    received_at: datetime | None = None
    deadline: datetime | None = None
    interview_date: datetime | None = None
    action_required: bool = False
    summary: str | None = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class EmailMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    gmail_message_id: str
    thread_id: str | None
    subject: str
    sender_email: str
    received_at: datetime
    raw_snippet: str | None
    body_text: str | None
    category: EmailCategory | None
    company_name: str | None
    job_title: str | None
    deadline: datetime | None
    interview_date: datetime | None
    action_required: bool | None
    summary: str | None
    confidence_score: float | None
    processed_at: datetime | None
    processing_error: str | None
    created_at: datetime
    updated_at: datetime


class EmailSyncRequest(BaseModel):
    max_results: int = Field(default=50, ge=1, le=500)
    query: str | None = None


class EmailSyncResponse(BaseModel):
    message: str
    status: str = "completed"
    fetched_count: int = 0
    created_count: int = 0
    skipped_count: int = 0
    applications_updated_count: int = 0
