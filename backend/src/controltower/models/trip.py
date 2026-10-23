"""Trip and TripDay.

Days are derived from item times (D2); a TripDay row exists only to hold per-day extras.
Whether a trip is past, current, or upcoming is computed, never stored.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from controltower.models.base import Base, Timestamps, UUIDPrimaryKey
from controltower.models.types import TimeZoneName

if TYPE_CHECKING:
    from controltower.models.item import Item
    from controltower.models.log import LogEntry
    from controltower.models.photo import Photo
    from controltower.models.user import User


class Trip(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "trip"

    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    # Free text at any level of detail ("Shinjuku, Japan", "Japan"); agents read it later.
    location: Mapped[str | None] = mapped_column(String(200))
    # Optional: when unset, the timeline computes the range from the items.
    start_date: Mapped[date | None]
    end_date: Mapped[date | None]
    home_tz: Mapped[str] = mapped_column(TimeZoneName())  # for days with no items
    cancelled: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    # The main photo (F3.5). SET NULL so deleting a photo row never breaks its trip.
    cover_photo_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("photo.id", ondelete="SET NULL")
    )

    owner: Mapped[User] = relationship(back_populates="trips")
    # passive_deletes: let the database's ON DELETE CASCADE remove children.
    items: Mapped[list[Item]] = relationship(
        back_populates="trip", cascade="all, delete-orphan", passive_deletes=True
    )
    days: Mapped[list[TripDay]] = relationship(
        back_populates="trip", cascade="all, delete-orphan", passive_deletes=True
    )
    log_entries: Mapped[list[LogEntry]] = relationship(
        back_populates="trip", cascade="all, delete-orphan", passive_deletes=True
    )
    cover_photo: Mapped[Photo | None] = relationship()

    def __repr__(self) -> str:
        return f"Trip({self.title!r})"


class TripDay(Base):
    """Per-day extras for one local date of a trip (title, city, summary)."""

    __tablename__ = "trip_day"

    trip_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("trip.id", ondelete="CASCADE"), primary_key=True
    )
    local_date: Mapped[date] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String(200))
    city: Mapped[str | None] = mapped_column(String(120))
    summary: Mapped[str | None] = mapped_column(Text)  # later written by the minutes agent

    trip: Mapped[Trip] = relationship(back_populates="days")

    def __repr__(self) -> str:
        return f"TripDay({self.local_date.isoformat()})"
