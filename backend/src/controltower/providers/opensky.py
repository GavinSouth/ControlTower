"""OpenSky Network adapter (implements `StateProvider`).

Stub for F1.3: the credit math is real; network calls land in Phase 2.
Design notes:
- Auth is OAuth2 client credentials: POST client id/secret to the token endpoint, get a bearer
  token (~30 min), refresh before expiry. Anonymous mode (no credentials) is kept for local dev.
- `X-Rate-Limit-Remaining` is returned on every call and surfaced in `FetchResult`.
- HTTP 429 carries `X-Rate-Limit-Retry-After-Seconds` -> `RateLimitedError`.
- State vectors are positional arrays; parsing maps them to `AircraftState` (see
  `OpenSky API Testing/scripts/opensky.py` STATE_FIELDS for the index order).
"""

import httpx

from controltower.models import BoundingBox, Track
from controltower.providers.base import FetchResult

BASE_URL = "https://opensky-network.org/api"
TOKEN_URL = (
    "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
)

# (max area in sq deg, credits). Anything larger, or global, costs 4.
_CREDIT_TIERS = ((25.0, 1), (100.0, 2), (400.0, 3))
_GLOBAL_COST = 4


def credit_cost(bbox: BoundingBox | None) -> int:
    """Credits one /states/all call costs (OpenSky docs, confirmed in F1.2)."""
    if bbox is None:
        return _GLOBAL_COST
    for max_area, cost in _CREDIT_TIERS:
        if bbox.area_sq_deg <= max_area:
            return cost
    return _GLOBAL_COST


class OpenSkyProvider:
    def __init__(
        self,
        client: httpx.AsyncClient,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        self._client = client
        self._client_id = client_id
        self._client_secret = client_secret

    @property
    def authenticated(self) -> bool:
        return bool(self._client_id and self._client_secret)

    @property
    def min_refresh_s(self) -> int:
        return 5 if self.authenticated else 10

    def credit_cost(self, bbox: BoundingBox | None) -> int:
        return credit_cost(bbox)

    async def fetch_states(self, bbox: BoundingBox | None = None) -> FetchResult:
        raise NotImplementedError("Phase 2")

    async def fetch_track(self, icao24: str) -> Track | None:
        raise NotImplementedError("Phase 2")
