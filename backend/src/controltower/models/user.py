"""User: a single row ("me") until accounts arrive in Phase 6 (D1)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from controltower.models.base import Base, Timestamps, UUIDPrimaryKey

if TYPE_CHECKING:
    from controltower.models.trip import Trip


class User(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "user"

    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(320), unique=True)

    trips: Mapped[list[Trip]] = relationship(back_populates="owner")

    def __repr__(self) -> str:
        return f"User({self.name!r})"
