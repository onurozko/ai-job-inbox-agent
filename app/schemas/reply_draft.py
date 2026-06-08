from uuid import UUID

from pydantic import BaseModel, Field


class DraftReplyRequest(BaseModel):
    email_id: UUID
    tone: str = Field(default="professional", min_length=1, max_length=50)
    extra_instructions: str | None = Field(default=None, max_length=2000)


class DraftReplyResponse(BaseModel):
    email_id: UUID
    subject: str
    recipient_email: str
    draft_body: str
    tone: str
    warnings: list[str] = Field(default_factory=list)
