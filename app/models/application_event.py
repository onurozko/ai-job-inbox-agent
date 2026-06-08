from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import pg_enum
from app.models.enums import EventType

if TYPE_CHECKING:
    from app.models.email_message import EmailMessage
    from app.models.job_application import JobApplication


class ApplicationEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "application_events"

    job_application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[EventType] = mapped_column(
        pg_enum(EventType, name="event_type"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)

    job_application: Mapped[JobApplication] = relationship(back_populates="events")
    email_message: Mapped[EmailMessage | None] = relationship(back_populates="application_events")

    def __repr__(self) -> str:
        return f"ApplicationEvent(id={self.id!r}, type={self.event_type!r})"
