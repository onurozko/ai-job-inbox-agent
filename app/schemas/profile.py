from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ResumeProfileUpdate(BaseModel):
    resume_text: str = Field(min_length=1)
    target_roles: list[str] | None = None
    target_locations: list[str] | None = None


class ResumeProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    resume_text: str
    target_roles: list[str] | None
    target_locations: list[str] | None
    created_at: datetime
    updated_at: datetime
