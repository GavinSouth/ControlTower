"""Place: a reusable location with its own time zone (D6)."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from controltower.models.base import Base, Timestamps, UUIDPrimaryKey
from controltower.models.types import TimeZoneName


class Place(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "place"

    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(String(400))
    city: Mapped[str | None] = mapped_column(String(120))
    country: Mapped[str | None] = mapped_column(String(2))  # ISO 3166-1 alpha-2, e.g. "JP"
    lat: Mapped[float | None]
    lon: Mapped[float | None]
    tz: Mapped[str] = mapped_column(TimeZoneName())
    iata_code: Mapped[str | None] = mapped_column(String(3), index=True)  # airports only

    def __repr__(self) -> str:
        return f"Place({self.name!r}, tz={self.tz!r})"
