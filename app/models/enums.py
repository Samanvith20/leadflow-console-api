"""Shared enum behaviour for values persisted to PostgreSQL."""

from __future__ import annotations

import enum
from typing import Self, TypeVar

EnumMember = TypeVar("EnumMember", bound="LowercaseEnum")


class LowercaseEnum(str, enum.Enum):
    """Store lowercase values and accept case-insensitive string input."""

    @classmethod
    def _missing_(cls, value: object) -> Self | None:
        if not isinstance(value, str):
            return None

        normalized_value = value.lower()
        return next(
            (member for member in cls if member.value == normalized_value),
            None,
        )


def enum_values(enum_class: type[LowercaseEnum]) -> list[str]:
    """Tell SQLAlchemy to persist enum values, never uppercase member names."""

    return [member.value for member in enum_class]
