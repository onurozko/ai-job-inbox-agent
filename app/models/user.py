from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.email_message import EmailMessage
    from app.models.gmail_credential import GmailCredential
    from app.models.job_application import JobApplication
    from app.models.user_profile import UserProfile


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_sub: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    picture_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    email_messages: Mapped[list[EmailMessage]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    job_applications: Mapped[list[JobApplication]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    gmail_credential: Mapped[GmailCredential | None] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    profile: Mapped[UserProfile | None] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r})"
