"""Core domain models.

Plain frozen dataclasses with no framework dependency: providers, cache, and poller all speak
these types. The HTTP layer (`controltower.api.schemas`) converts them to Pydantic models at the
edge. Units are SI and carried in field names (`_m`, `_mps`, `_deg`) to match OpenSky; frontends
convert for display (m -> ft x 3.281, m/s -> kt x 1.944).
"""

from dataclasses import dataclass
from enum import IntEnum


class PositionSource(IntEnum):
    """How a position was obtained (OpenSky `position_source`)."""

    ADSB = 0
    ASTERIX = 1
    MLAT = 2
    FLARM = 3


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """A lat/lon rectangle. OpenSky charges credits by its area in square degrees."""

    lat_min: float
    lon_min: float
    lat_max: float
    lon_max: float

    def __post_init__(self) -> None:
        if not (-90 <= self.lat_min < self.lat_max <= 90):
            raise ValueError(f"invalid latitude range {self.lat_min}..{self.lat_max}")
        if not (-180 <= self.lon_min < self.lon_max <= 180):
            raise ValueError(f"invalid longitude range {self.lon_min}..{self.lon_max}")

    @property
    def area_sq_deg(self) -> float:
        return (self.lat_max - self.lat_min) * (self.lon_max - self.lon_min)

    def contains(self, lat: float, lon: float) -> bool:
        return self.lat_min <= lat <= self.lat_max and self.lon_min <= lon <= self.lon_max


@dataclass(frozen=True, slots=True)
class Position:
    """One point on a flight path."""

    time: int  # unix seconds
    latitude: float
    longitude: float
    baro_altitude_m: float | None
    true_track_deg: float | None
    on_ground: bool


@dataclass(frozen=True, slots=True)
class AircraftState:
    """Latest known state of one aircraft (one OpenSky state vector, cleaned)."""

    icao24: str  # 24-bit transponder address, lowercase hex; the stable aircraft key
    callsign: str | None  # stripped; None if not broadcast
    origin_country: str  # country of registration, NOT departure country
    last_contact: int  # unix seconds, last message of any kind
    position: Position | None  # None if no position yet
    velocity_mps: float | None
    vertical_rate_mps: float | None
    geo_altitude_m: float | None
    squawk: str | None
    position_source: PositionSource


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Every aircraft returned by one provider poll."""

    time: int  # unix seconds the data is valid for (OpenSky `time`)
    aircraft: tuple[AircraftState, ...]


@dataclass(frozen=True, slots=True)
class Airport:
    icao: str  # e.g. "KJFK"; primary key
    iata: str | None  # e.g. "JFK"
    name: str
    latitude: float
    longitude: float
    country_iso: str | None


@dataclass(frozen=True, slots=True)
class Route:
    """Scheduled origin -> destination for a callsign (from a route provider, e.g. adsbdb).

    Community data: may be stale or wrong for a given day. Treat as a best guess.
    """

    callsign: str
    airline: str | None
    origin: Airport
    destination: Airport


@dataclass(frozen=True, slots=True)
class Track:
    """An aircraft's path, oldest point first."""

    icao24: str
    callsign: str | None
    positions: tuple[Position, ...]


@dataclass(frozen=True, slots=True)
class Flight:
    """What the API serves for one aircraft: live state plus best-effort route."""

    state: AircraftState
    route: Route | None
