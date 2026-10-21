"""Cache between the poller (writer) and the API (reader).

The API never calls a provider directly: it reads whatever the poller last stored. MVP is a
single process with an in-memory store; a Redis-backed class with the same methods can replace
it if we ever run several API workers.
"""

from typing import Protocol

from controltower.models import BoundingBox, Flight, Route, Snapshot, Track


class FlightStore(Protocol):
    def put_snapshot(self, snapshot: Snapshot) -> None:
        """Replace current states and append each position to that aircraft's track history."""
        ...

    def put_route(self, callsign: str, route: Route | None) -> None:
        """Cache a lookup result. None is cached too, so we don't re-ask for unknown callsigns."""
        ...

    @property
    def snapshot_time(self) -> int | None:
        """Unix time of the data currently served, or None before the first poll."""
        ...

    def list_flights(
        self,
        bbox: BoundingBox | None = None,
        *,
        include_ground: bool = False,
        origin: str | None = None,
        destination: str | None = None,
    ) -> list[Flight]:
        """Non-stale flights, filtered. origin/destination (ICAO) match only known routes."""
        ...

    def get_flight(self, icao24: str) -> Flight | None: ...

    def get_track(self, icao24: str) -> Track | None:
        """Path accumulated from our own polls (no provider credits spent)."""
        ...


class InMemoryFlightStore:
    """Dicts keyed by icao24 / callsign, plus a time-bounded deque of positions per aircraft."""

    def __init__(self, *, stale_after_s: int, track_history_s: int, route_ttl_s: int) -> None:
        self._stale_after_s = stale_after_s
        self._track_history_s = track_history_s
        self._route_ttl_s = route_ttl_s
        self._snapshot_time: int | None = None

    def put_snapshot(self, snapshot: Snapshot) -> None:
        raise NotImplementedError("Phase 2")

    def put_route(self, callsign: str, route: Route | None) -> None:
        raise NotImplementedError("Phase 2")

    @property
    def snapshot_time(self) -> int | None:
        return self._snapshot_time

    def list_flights(
        self,
        bbox: BoundingBox | None = None,
        *,
        include_ground: bool = False,
        origin: str | None = None,
        destination: str | None = None,
    ) -> list[Flight]:
        raise NotImplementedError("Phase 2")

    def get_flight(self, icao24: str) -> Flight | None:
        raise NotImplementedError("Phase 2")

    def get_track(self, icao24: str) -> Track | None:
        raise NotImplementedError("Phase 2")
