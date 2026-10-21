"""HTTP response models: the contract web and iOS code against.

Kept separate from `controltower.models` so internal refactors don't silently change the API.
FastAPI turns these into the OpenAPI schema at /docs, which frontends can generate clients from.
"""

from pydantic import BaseModel

from controltower import models


class AirportOut(BaseModel):
    icao: str
    iata: str | None
    name: str
    latitude: float
    longitude: float

    @classmethod
    def from_domain(cls, a: models.Airport) -> "AirportOut":
        return cls(
            icao=a.icao, iata=a.iata, name=a.name, latitude=a.latitude, longitude=a.longitude
        )


class RouteOut(BaseModel):
    airline: str | None
    origin: AirportOut
    destination: AirportOut

    @classmethod
    def from_domain(cls, r: models.Route) -> "RouteOut":
        return cls(
            airline=r.airline,
            origin=AirportOut.from_domain(r.origin),
            destination=AirportOut.from_domain(r.destination),
        )


class FlightSummary(BaseModel):
    """One map marker. Flat and small: a busy region can return thousands of these."""

    icao24: str
    callsign: str | None
    latitude: float
    longitude: float
    baro_altitude_m: float | None
    velocity_mps: float | None
    true_track_deg: float | None
    vertical_rate_mps: float | None
    on_ground: bool
    last_contact: int
    origin_icao: str | None  # from route, when known
    destination_icao: str | None

    @classmethod
    def from_domain(cls, f: models.Flight) -> "FlightSummary":
        s, p = f.state, f.state.position
        if p is None:
            raise ValueError(f"{s.icao24} has no position; store must filter these out")
        return cls(
            icao24=s.icao24,
            callsign=s.callsign,
            latitude=p.latitude,
            longitude=p.longitude,
            baro_altitude_m=p.baro_altitude_m,
            velocity_mps=s.velocity_mps,
            true_track_deg=p.true_track_deg,
            vertical_rate_mps=s.vertical_rate_mps,
            on_ground=p.on_ground,
            last_contact=s.last_contact,
            origin_icao=f.route.origin.icao if f.route else None,
            destination_icao=f.route.destination.icao if f.route else None,
        )


class FlightList(BaseModel):
    snapshot_time: int | None  # None before the first successful poll
    data_age_s: int | None  # now - snapshot_time; clients show "stale" when this grows
    count: int
    flights: list[FlightSummary]


class FlightDetail(FlightSummary):
    """Selected-aircraft panel: summary plus the fields a list doesn't need."""

    origin_country: str
    geo_altitude_m: float | None
    squawk: str | None
    route: RouteOut | None

    @classmethod
    def from_domain(cls, f: models.Flight) -> "FlightDetail":
        s = f.state
        return cls(
            **FlightSummary.from_domain(f).model_dump(),
            origin_country=s.origin_country,
            geo_altitude_m=s.geo_altitude_m,
            squawk=s.squawk,
            route=RouteOut.from_domain(f.route) if f.route else None,
        )


class PositionOut(BaseModel):
    time: int
    latitude: float
    longitude: float
    baro_altitude_m: float | None
    on_ground: bool


class TrackOut(BaseModel):
    icao24: str
    callsign: str | None
    positions: list[PositionOut]  # oldest first

    @classmethod
    def from_domain(cls, t: models.Track) -> "TrackOut":
        return cls(
            icao24=t.icao24,
            callsign=t.callsign,
            positions=[
                PositionOut(
                    time=p.time,
                    latitude=p.latitude,
                    longitude=p.longitude,
                    baro_altitude_m=p.baro_altitude_m,
                    on_ground=p.on_ground,
                )
                for p in t.positions
            ],
        )


class Health(BaseModel):
    status: str
    snapshot_time: int | None
