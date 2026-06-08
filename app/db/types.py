from __future__ import annotations

import enum
from typing import TypeVar

from sqlalchemy import Enum

E = TypeVar("E", bound=enum.Enum)


def _enum_values(enum_class: type[E]) -> list[str]:
    return [member.value for member in enum_class]


def pg_enum(enum_class: type[E], *, name: str) -> Enum:
    """Map a Python enum to a PostgreSQL enum using member values."""
    return Enum(
        enum_class,
        values_callable=_enum_values,
        name=name,
        native_enum=True,
    )
