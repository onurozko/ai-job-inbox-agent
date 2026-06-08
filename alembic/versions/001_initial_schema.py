"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

email_category_enum = postgresql.ENUM(
    "application_confirmation",
    "rejection",
    "interview_invitation",
    "assessment",
    "recruiter_outreach",
    "offer",
    "follow_up_needed",
    "irrelevant",
    name="email_category",
    create_type=False,
)
application_status_enum = postgresql.ENUM(
    "applied",
    "assessment",
    "interview_scheduled",
    "rejected",
    "offer_received",
    "follow_up",
    "unknown",
    name="application_status",
    create_type=False,
)
event_type_enum = postgresql.ENUM(
    "application_confirmation",
    "rejection",
    "interview_invitation",
    "assessment",
    "recruiter_outreach",
    "offer",
    "follow_up_needed",
    "irrelevant",
    "status_update",
    name="event_type",
    create_type=False,
)


def upgrade() -> None:
    email_category_enum.create(op.get_bind(), checkfirst=True)
    application_status_enum.create(op.get_bind(), checkfirst=True)
    event_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("gmail_refresh_token", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "email_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gmail_message_id", sa.String(length=255), nullable=False),
        sa.Column("thread_id", sa.String(length=255), nullable=True),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("sender_email", sa.String(length=320), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_snippet", sa.Text(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("category", email_category_enum, nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("job_title", sa.String(length=255), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("interview_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("action_required", sa.Boolean(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "gmail_message_id", name="uq_email_user_gmail_id"),
    )
    op.create_index(op.f("ix_email_messages_user_id"), "email_messages", ["user_id"], unique=False)
    op.create_index("ix_email_messages_user_received", "email_messages", ["user_id", "received_at"], unique=False)

    op.create_table(
        "job_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("job_title", sa.String(length=255), nullable=True),
        sa.Column("company_name_normalized", sa.String(length=255), nullable=False),
        sa.Column("job_title_normalized", sa.String(length=255), nullable=False),
        sa.Column("status", application_status_enum, nullable=False),
        sa.Column("latest_summary", sa.Text(), nullable=True),
        sa.Column("last_email_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("action_required", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "company_name_normalized",
            "job_title_normalized",
            name="uq_job_application_user_company_title",
        ),
    )
    op.create_index(op.f("ix_job_applications_user_id"), "job_applications", ["user_id"], unique=False)
    op.create_index("ix_job_applications_user_status", "job_applications", ["user_id", "status"], unique=False)

    op.create_table(
        "application_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email_message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", event_type_enum, nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["email_message_id"], ["email_messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_application_id"], ["job_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_application_events_email_message_id"),
        "application_events",
        ["email_message_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_application_events_job_application_id"),
        "application_events",
        ["job_application_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_application_events_job_application_id"), table_name="application_events")
    op.drop_index(op.f("ix_application_events_email_message_id"), table_name="application_events")
    op.drop_table("application_events")

    op.drop_index("ix_job_applications_user_status", table_name="job_applications")
    op.drop_index(op.f("ix_job_applications_user_id"), table_name="job_applications")
    op.drop_table("job_applications")

    op.drop_index("ix_email_messages_user_received", table_name="email_messages")
    op.drop_index(op.f("ix_email_messages_user_id"), table_name="email_messages")
    op.drop_table("email_messages")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    event_type_enum.drop(op.get_bind(), checkfirst=True)
    application_status_enum.drop(op.get_bind(), checkfirst=True)
    email_category_enum.drop(op.get_bind(), checkfirst=True)
