"""Provider interfaces ("ports").

The rest of the backend depends only on these Protocols, never on a concrete API. Swapping
OpenSky for a paid source (e.g. FlightAware AeroAPI) means writing one new class that satisfies
`StateProvider`; nothing else changes. Protocols are structural: a class satisfies one by having
the right methods, no inheritance needed.
"""

from dataclasses import dataclass
from typing import Protocol

from controltower.models import BoundingBox, Route, Snapshot, Track


class ProviderError(Exception):
    """A provider call failed (network, bad response, auth)."""


class RateLimitedError(ProviderError):
    """The provider refused the call for quota reasons; retry after `retry_after_s`."""

    def __init__(self, retry_after_s: int | None) -> None:
        super().__init__(f"rate limited; retry after {retry_after_s}s")
        self.retry_after_s = retry_after_s


@dataclass(frozen=True, slots=True)
class FetchResult:
    """A snapshot plus quota metadata, so the poller can budget its next call."""

    snapshot: Snapshot
    credits_remaining: int | None  # None if the provider doesn't report it


class StateProvider(Protocol):
    """Live aircraft positions."""

    @property
    def min_refresh_s(self) -> int:
        """Data resolution: polling faster than this returns duplicates and wastes quota."""
        ...

    def credit_cost(self, bbox: BoundingBox | None) -> int:
        """Quota cost of one `fetch_states` call for this area (None = global)."""
        ...

    async def fetch_states(self, bbox: BoundingBox | None = None) -> FetchResult: ...

    async def fetch_track(self, icao24: str) -> Track | None:
        """Live path of one aircraft, or None if the provider has none."""
        ...


class RouteProvider(Protocol):
    """Callsign -> scheduled origin/destination."""

    async def fetch_route(self, callsign: str) -> Route | None:
        """None means 'looked up, no route known' (cache it); errors raise ProviderError."""
        ...
