from __future__ import annotations

import enum

from sqlalchemy import Enum


def _enum_values[E: enum.Enum](enum_class: type[E]) -> list[str]:
    return [member.value for member in enum_class]


def pg_enum[E: enum.Enum](enum_class: type[E], *, name: str) -> Enum:
    """Map a Python enum to a PostgreSQL enum using member values."""
    return Enum(
        enum_class,
        values_callable=_enum_values,
        name=name,
        native_enum=True,
    )
