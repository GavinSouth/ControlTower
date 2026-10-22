"""Portable column types (ARCHITECTURE.md D10).

SQLite has no time-zone-aware datetime, no exact decimal, and no enum type. These
TypeDecorators make every column behave the same on SQLite now and Postgres later.
Migrations import this module, so keep the class names stable.
"""

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import DateTime, Dialect, Enum, Numeric, String
from sqlalchemy.types import TypeDecorator, TypeEngine


class UTCDateTime(TypeDecorator[datetime]):
    """Aware datetimes only; stored as UTC, returned as UTC-aware.

    Rejects naive datetimes on write, because a time without a zone can't be placed on a
    local day. SQLite stores the UTC value as naive text; Postgres uses timestamptz.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"naive datetime not allowed: {value!r} (attach a time zone)")
        value = value.astimezone(UTC)
        return value.replace(tzinfo=None) if dialect.name == "sqlite" else value

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class TimeZoneName(TypeDecorator[str]):
    """An IANA zone name such as 'Asia/Tokyo', validated against the tz database on write."""

    impl = String(64)
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect: Dialect) -> str | None:
        if value is None:
            return None
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as err:
            raise ValueError(f"unknown time zone: {value!r}") from err
        return value


class Money(TypeDecorator[Decimal]):
    """Exact decimal amounts: NUMERIC on Postgres, text on SQLite (which would use floats)."""

    impl = Numeric(14, 4)
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(32))
        return dialect.type_descriptor(Numeric(14, 4))

    def process_bind_param(self, value: Decimal | None, dialect: Dialect) -> Any:
        if value is None:
            return None
        return str(value) if dialect.name == "sqlite" else value

    def process_result_value(self, value: Any, dialect: Dialect) -> Decimal | None:
        return None if value is None else Decimal(str(value))


def str_enum(enum_cls: type[StrEnum]) -> Enum:
    """Store a StrEnum by its value ('in_progress'), as VARCHAR, never a native DB enum.

    No CHECK constraint and a fixed length, so adding a member later needs no migration.
    """
    return Enum(
        enum_cls,
        native_enum=False,
        create_constraint=False,
        length=32,
        values_callable=lambda cls: [m.value for m in cls],
        validate_strings=True,
    )
