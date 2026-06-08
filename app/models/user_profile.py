from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class UserProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_profiles_user_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_text: Mapped[str] = mapped_column(Text, nullable=False)
    target_roles: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    target_locations: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    user: Mapped[User] = relationship(back_populates="profile")

    def __repr__(self) -> str:
        return f"UserProfile(id={self.id!r}, user_id={self.user_id!r})"
