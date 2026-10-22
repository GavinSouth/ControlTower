"""Items: anything on a trip's itinerary (D3, D4, D5).

`item` holds the fields every kind shares (times, place, status, cost). Each kind with
extra fields gets its own detail table joined on the same id (joined-table inheritance):
querying `Item` returns Flight/Stay/Transport/Activity/Note objects automatically.

Times are UTC with an IANA zone per end, because a flight leaves in one zone and lands
in another. "Effective" time = actual if recorded, else planned.
"""

from __future__ import annotations

import uuid
from datetime import datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from controltower.models.base import Base, Timestamps, UUIDPrimaryKey
from controltower.models.enums import ItemKind, ItemStatus, TransportMode
from controltower.models.types import Money, TimeZoneName, str_enum

if TYPE_CHECKING:
    from controltower.models.place import Place
    from controltower.models.trip import Trip


class Item(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "item"

    trip_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("trip.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[ItemKind] = mapped_column(str_enum(ItemKind))
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[ItemStatus] = mapped_column(str_enum(ItemStatus), default=ItemStatus.PLANNED)

    # Plan vs actual (D3). Ideas may have no times; notes/moments have no end.
    planned_start: Mapped[datetime | None]
    planned_end: Mapped[datetime | None]
    actual_start: Mapped[datetime | None]
    actual_end: Mapped[datetime | None]
    start_tz: Mapped[str | None] = mapped_column(TimeZoneName())
    end_tz: Mapped[str | None] = mapped_column(TimeZoneName())  # defaults to start_tz

    # Where it happens / departs from, and where it arrives (flights, transport).
    place_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("place.id", ondelete="SET NULL"))
    to_place_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("place.id", ondelete="SET NULL")
    )

    confirmation_code: Mapped[str | None] = mapped_column(String(64))
    cost_amount: Mapped[Decimal | None] = mapped_column(Money())
    cost_currency: Mapped[str | None] = mapped_column(String(3))  # ISO 4217, e.g. "JPY"
    notes: Mapped[str | None] = mapped_column(Text)

    trip: Mapped[Trip] = relationship(back_populates="items")
    place: Mapped[Place | None] = relationship(foreign_keys=[place_id])
    to_place: Mapped[Place | None] = relationship(foreign_keys=[to_place_id])

    __mapper_args__ = {"polymorphic_on": "kind", "polymorphic_abstract": True}

    @property
    def effective_start(self) -> datetime | None:
        return self.actual_start or self.planned_start

    @property
    def effective_end(self) -> datetime | None:
        return self.actual_end or self.planned_end

    @property
    def effective_end_tz(self) -> str | None:
        return self.end_tz or self.start_tz

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.title!r})"


def _detail_pk() -> Mapped[uuid.UUID]:
    """Primary key of a detail table: the same id as its `item` row."""
    return mapped_column(ForeignKey("item.id", ondelete="CASCADE"), primary_key=True)


class Flight(Item):
    __tablename__ = "flight_detail"
    __mapper_args__ = {"polymorphic_identity": ItemKind.FLIGHT}

    id: Mapped[uuid.UUID] = _detail_pk()
    airline: Mapped[str | None] = mapped_column(String(3))  # IATA code, e.g. "UA"
    flight_number: Mapped[str | None] = mapped_column(String(8))  # e.g. "837"
    seat: Mapped[str | None] = mapped_column(String(8))
    cabin: Mapped[str | None] = mapped_column(String(32))
    terminal_from: Mapped[str | None] = mapped_column(String(16))
    terminal_to: Mapped[str | None] = mapped_column(String(16))
    gate: Mapped[str | None] = mapped_column(String(16))
    aircraft: Mapped[str | None] = mapped_column(String(64))
    booking_source: Mapped[str | None] = mapped_column(String(64))  # "manual", later "serpapi"


class Stay(Item):
    __tablename__ = "stay_detail"
    __mapper_args__ = {"polymorphic_identity": ItemKind.STAY}

    id: Mapped[uuid.UUID] = _detail_pk()
    property_name: Mapped[str | None] = mapped_column(String(200))
    room: Mapped[str | None] = mapped_column(String(64))
    check_in_after: Mapped[time | None]  # local wall-clock policy, e.g. 15:00
    check_out_before: Mapped[time | None]
    host_contact: Mapped[str | None] = mapped_column(String(200))


class Transport(Item):
    __tablename__ = "transport_detail"
    __mapper_args__ = {"polymorphic_identity": ItemKind.TRANSPORT}

    id: Mapped[uuid.UUID] = _detail_pk()
    mode: Mapped[TransportMode] = mapped_column(
        str_enum(TransportMode), default=TransportMode.OTHER
    )
    carrier: Mapped[str | None] = mapped_column(String(120))
    vehicle_ref: Mapped[str | None] = mapped_column(String(64))  # train number, plate...
    seat: Mapped[str | None] = mapped_column(String(16))


class Activity(Item):
    __tablename__ = "activity_detail"
    __mapper_args__ = {"polymorphic_identity": ItemKind.ACTIVITY}

    id: Mapped[uuid.UUID] = _detail_pk()
    category: Mapped[str | None] = mapped_column(String(32))  # food, sight, event, work...
    booking_url: Mapped[str | None] = mapped_column(String(1000))
    ticket_ref: Mapped[str | None] = mapped_column(String(64))


class Note(Item):
    """No extra fields, so no detail table: lives entirely in `item` (single-table)."""

    __mapper_args__ = {"polymorphic_identity": ItemKind.NOTE}
