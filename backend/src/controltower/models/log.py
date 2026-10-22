"""LogEntry: the trip "minutes" (D7).

A timestamped observation from some source (manual, agent, location...). It can point at
an item or place but never changes them; an agent may later *propose* actual times.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from controltower.models.base import Base, Timestamps, UUIDPrimaryKey
from controltower.models.enums import LogKind, LogSource
from controltower.models.types import TimeZoneName, str_enum

if TYPE_CHECKING:
    from controltower.models.item import Item
    from controltower.models.place import Place
    from controltower.models.trip import Trip


class LogEntry(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "log_entry"

    trip_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("trip.id", ondelete="CASCADE"), index=True
    )
    occurred_at: Mapped[datetime]
    tz: Mapped[str] = mapped_column(TimeZoneName())  # decides which local day it lands on
    source: Mapped[LogSource] = mapped_column(str_enum(LogSource))
    kind: Mapped[LogKind] = mapped_column(str_enum(LogKind))
    text: Mapped[str | None] = mapped_column(Text)
    item_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("item.id", ondelete="SET NULL"))
    place_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("place.id", ondelete="SET NULL"))
    lat: Mapped[float | None]
    lon: Mapped[float | None]
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSON)  # original signal, for reprocessing

    trip: Mapped[Trip] = relationship(back_populates="log_entries")
    item: Mapped[Item | None] = relationship()
    place: Mapped[Place | None] = relationship()

    def __repr__(self) -> str:
        return f"LogEntry({self.kind}, {self.occurred_at.isoformat()})"
