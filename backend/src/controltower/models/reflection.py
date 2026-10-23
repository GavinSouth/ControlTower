"""Opinions about a past trip (ARCHITECTURE.md: Past trip record, P2-P5).

Keyed by (trip or item, user), not stored as trip/item columns, because opinions belong
to a person: with shared trips (Phase 6) two travellers can rate the same dinner
differently. Every field is optional (P7). Rows go away with their trip or item
(ON DELETE CASCADE in the database).
"""

from __future__ import annotations

import uuid

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from controltower.models.base import Base, Timestamps
from controltower.models.enums import Verdict
from controltower.models.types import str_enum


class TripReflection(Timestamps, Base):
    __tablename__ = "trip_reflection"
    __table_args__ = (CheckConstraint("rating BETWEEN 1 AND 5", name="rating_1_to_5"),)

    trip_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("trip.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), primary_key=True)
    rating: Mapped[int | None]  # 1-5 stars
    highlight: Mapped[str | None] = mapped_column(Text)
    would_return: Mapped[bool | None]  # None = unsure
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)  # trimmed, lower-cased
    companions: Mapped[list[str]] = mapped_column(JSON, default=list)
    notes: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"TripReflection(rating={self.rating})"


class ItemFeedback(Timestamps, Base):
    """👍/👎 + ♥ + a short review. An all-empty row is deleted, never kept."""

    __tablename__ = "item_feedback"

    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("item.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), primary_key=True)
    verdict: Mapped[Verdict | None] = mapped_column(str_enum(Verdict))
    favourite: Mapped[bool] = mapped_column(default=False)
    review: Mapped[str | None] = mapped_column(Text)

    @property
    def is_empty(self) -> bool:
        return self.verdict is None and not self.favourite and not self.review

    def __repr__(self) -> str:
        return f"ItemFeedback({self.verdict}, favourite={self.favourite})"
