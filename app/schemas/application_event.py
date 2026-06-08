from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EventType


class ApplicationEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_application_id: UUID
    email_message_id: UUID | None
    event_type: EventType
    title: str
    description: str | None
    occurred_at: datetime
    metadata: dict[str, Any] | None = Field(default=None, validation_alias="metadata_")
    created_at: datetime
    updated_at: datetime
