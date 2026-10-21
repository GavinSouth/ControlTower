"""FastAPI app: the HTTP contract (v1) both frontends consume.

Endpoints are read-only and served from the store, so request volume never costs provider
credits. Clients poll `GET /api/v1/flights` at roughly the backend's poll interval and
dead-reckon markers in between (position + velocity + heading); SSE/WebSocket push is a later
upgrade that doesn't change these shapes.

Stub for F1.3: store methods raise NotImplementedError, which is returned as HTTP 501.
"""

import time
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from controltower import __version__
from controltower.api.schemas import FlightDetail, FlightList, FlightSummary, Health, TrackOut
from controltower.config import Settings
from controltower.models import BoundingBox
from controltower.store import FlightStore, InMemoryFlightStore

API_PREFIX = "/api/v1"


def parse_bbox(raw: str | None) -> BoundingBox | None:
    """'lat_min,lon_min,lat_max,lon_max' -> BoundingBox (None if absent)."""
    if not raw:
        return None
    try:
        lat_min, lon_min, lat_max, lon_max = (float(v) for v in raw.split(","))
        return BoundingBox(lat_min, lon_min, lat_max, lon_max)
    except ValueError as err:
        raise HTTPException(422, f"bbox must be 'lat_min,lon_min,lat_max,lon_max': {err}") from err


def get_store(request: Request) -> FlightStore:
    store: FlightStore = request.app.state.store
    return store


StoreDep = Annotated[FlightStore, Depends(get_store)]


def create_app(store: FlightStore | None = None) -> FastAPI:
    """App factory: tests pass a fake store; production builds one from Settings."""
    if store is None:
        settings = Settings()
        store = InMemoryFlightStore(
            stale_after_s=settings.stale_after_s,
            track_history_s=settings.track_history_s,
            route_ttl_s=settings.route_cache_ttl_s,
        )

    app = FastAPI(title="ControlTower API", version=__version__)
    app.state.store = store

    @app.exception_handler(NotImplementedError)
    async def not_implemented(_: Request, exc: NotImplementedError) -> JSONResponse:
        return JSONResponse(status_code=501, content={"detail": f"not implemented: {exc}"})

    @app.get("/health")
    def health(store: StoreDep) -> Health:
        return Health(status="ok", snapshot_time=store.snapshot_time)

    @app.get(f"{API_PREFIX}/flights")
    def list_flights(
        store: StoreDep,
        bbox: Annotated[
            str | None, Query(description="lat_min,lon_min,lat_max,lon_max (map viewport)")
        ] = None,
        include_ground: bool = False,
        origin: Annotated[str | None, Query(description="Origin airport ICAO, e.g. KJFK")] = None,
        destination: Annotated[str | None, Query(description="Destination ICAO")] = None,
    ) -> FlightList:
        flights = store.list_flights(
            parse_bbox(bbox),
            include_ground=include_ground,
            origin=origin.upper() if origin else None,
            destination=destination.upper() if destination else None,
        )
        snap = store.snapshot_time
        return FlightList(
            snapshot_time=snap,
            data_age_s=int(time.time()) - snap if snap is not None else None,
            count=len(flights),
            flights=[FlightSummary.from_domain(f) for f in flights],
        )

    @app.get(f"{API_PREFIX}/flights/{{icao24}}")
    def get_flight(store: StoreDep, icao24: str) -> FlightDetail:
        flight = store.get_flight(icao24.lower())
        if flight is None:
            raise HTTPException(404, f"no live aircraft {icao24}")
        return FlightDetail.from_domain(flight)

    @app.get(f"{API_PREFIX}/flights/{{icao24}}/track")
    def get_track(store: StoreDep, icao24: str) -> TrackOut:
        track = store.get_track(icao24.lower())
        if track is None:
            raise HTTPException(404, f"no track for {icao24}")
        return TrackOut.from_domain(track)

    return app
