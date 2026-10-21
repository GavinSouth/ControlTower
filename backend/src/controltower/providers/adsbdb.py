"""adsbdb.com adapter (implements `RouteProvider`).

Stub for F1.3; implemented in Phase 2. Endpoint: GET https://api.adsbdb.com/v0/callsign/{callsign}
-> `response.flightroute` with `origin`/`destination` airports, or an "unknown callsign" body,
which maps to None. Rate limits/terms are unverified (open question from F1.2).
"""

import httpx

from controltower.models import Route

BASE_URL = "https://api.adsbdb.com/v0"


class AdsbdbRouteProvider:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def fetch_route(self, callsign: str) -> Route | None:
        raise NotImplementedError("Phase 2")
