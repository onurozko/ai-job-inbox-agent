from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import pg_enum
from app.models.enums import ApplicationStatus

if TYPE_CHECKING:
    from app.models.application_event import ApplicationEvent
    from app.models.user import User


class JobApplication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "job_applications"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "company_name_normalized",
            "job_title_normalized",
            name="uq_job_application_user_company_title",
        ),
        Index("ix_job_applications_user_status", "user_id", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_name_normalized: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title_normalized: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    status: Mapped[ApplicationStatus] = mapped_column(
        pg_enum(ApplicationStatus, name="application_status"),
        default=ApplicationStatus.UNKNOWN,
        nullable=False,
    )
    latest_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_email_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    action_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[User] = relationship(back_populates="job_applications")
    events: Mapped[list[ApplicationEvent]] = relationship(
        back_populates="job_application",
        cascade="all, delete-orphan",
        order_by="ApplicationEvent.occurred_at",
    )

    def __repr__(self) -> str:
        return f"JobApplication(id={self.id!r}, company={self.company_name!r})"
