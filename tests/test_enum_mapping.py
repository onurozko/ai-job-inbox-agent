import enum

import pytest
from sqlalchemy.dialects import postgresql

from app.models.application_event import ApplicationEvent
from app.models.email_message import EmailMessage
from app.models.enums import ApplicationStatus, EmailCategory, EventType
from app.models.job_application import JobApplication


@pytest.mark.parametrize(
    ("model", "column_name", "enum_class"),
    [
        (EmailMessage, "category", EmailCategory),
        (JobApplication, "status", ApplicationStatus),
        (ApplicationEvent, "event_type", EventType),
    ],
)
def test_postgres_enum_columns_use_enum_values(
    model: type,
    column_name: str,
    enum_class: type[enum.Enum],
) -> None:
    column = model.__table__.c[column_name]
    expected = [member.value for member in enum_class]
    assert list(column.type.enums) == expected


@pytest.mark.parametrize(
    ("model", "column_name", "enum_member"),
    [
        (EmailMessage, "category", EmailCategory.APPLICATION_CONFIRMATION),
        (JobApplication, "status", ApplicationStatus.APPLIED),
        (ApplicationEvent, "event_type", EventType.STATUS_UPDATE),
    ],
)
def test_postgres_enum_bind_processor_persists_values(
    model: type,
    column_name: str,
    enum_member: enum.Enum,
) -> None:
    column = model.__table__.c[column_name]
    bind = column.type.bind_processor(postgresql.dialect())
    assert bind is not None
    assert bind(enum_member) == enum_member.value
