"""F1.3 tests: the API contract (with a fake store), credit math, and model validation."""

import pytest
from fastapi.testclient import TestClient

from controltower.api import create_app
from controltower.models import (
    AircraftState,
    Airport,
    BoundingBox,
    Flight,
    Position,
    PositionSource,
    Route,
    Snapshot,
    Track,
)
from controltower.polling import poll_interval_s
from controltower.providers.opensky import credit_cost
from controltower.store import InMemoryFlightStore

NOW = 1_792_561_585

DAL = Flight(
    state=AircraftState(
        icao24="a1b2c3",
        callsign="DAL2646",
        origin_country="United States",
        last_contact=NOW,
        position=Position(NOW, 41.2, -72.9, 10_000.0, 225.0, on_ground=False),
        velocity_mps=230.0,
        vertical_rate_mps=0.0,
        geo_altitude_m=10_150.0,
        squawk="1234",
        position_source=PositionSource.ADSB,
    ),
    route=Route(
        callsign="DAL2646",
        airline="Delta Air Lines",
        origin=Airport("KPVD", "PVD", "Providence", 41.72, -71.43, "US"),
        destination=Airport("KATL", "ATL", "Atlanta", 33.64, -84.43, "US"),
    ),
)


class FakeStore:
    """Satisfies the FlightStore Protocol structurally (same methods, no inheritance)."""

    snapshot_time: int | None = NOW

    def put_snapshot(self, snapshot: Snapshot) -> None: ...

    def put_route(self, callsign: str, route: Route | None) -> None: ...

    def list_flights(
        self,
        bbox: BoundingBox | None = None,
        *,
        include_ground: bool = False,
        origin: str | None = None,
        destination: str | None = None,
    ) -> list[Flight]:
        return [DAL]

    def get_flight(self, icao24: str) -> Flight | None:
        return DAL if icao24 == DAL.state.icao24 else None

    def get_track(self, icao24: str) -> Track | None:
        pos = DAL.state.position
        assert pos is not None
        return Track(icao24, "DAL2646", (pos,)) if icao24 == DAL.state.icao24 else None


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(FakeStore()))


def test_openapi_lists_contract(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths) == {
        "/health",
        "/api/v1/flights",
        "/api/v1/flights/{icao24}",
        "/api/v1/flights/{icao24}/track",
    }


def test_list_flights_shape(client: TestClient) -> None:
    body = client.get("/api/v1/flights", params={"bbox": "39,-76,43,-71"}).json()
    assert body["count"] == 1
    assert body["snapshot_time"] == NOW
    assert body["flights"][0]["callsign"] == "DAL2646"
    assert body["flights"][0]["destination_icao"] == "KATL"


def test_bad_bbox_is_422(client: TestClient) -> None:
    assert client.get("/api/v1/flights", params={"bbox": "1,2,3"}).status_code == 422
    assert client.get("/api/v1/flights", params={"bbox": "43,-76,39,-71"}).status_code == 422


def test_flight_detail_and_404(client: TestClient) -> None:
    detail = client.get("/api/v1/flights/A1B2C3").json()  # icao24 is case-insensitive
    assert detail["route"]["origin"]["iata"] == "PVD"
    assert client.get("/api/v1/flights/ffffff").status_code == 404


def test_track(client: TestClient) -> None:
    assert len(client.get("/api/v1/flights/a1b2c3/track").json()["positions"]) == 1


def test_stub_store_returns_501() -> None:
    store = InMemoryFlightStore(stale_after_s=60, track_history_s=7200, route_ttl_s=86400)
    client = TestClient(create_app(store))
    assert client.get("/health").json() == {"status": "ok", "snapshot_time": None}
    assert client.get("/api/v1/flights").status_code == 501


@pytest.mark.parametrize(
    ("bbox", "cost"),
    [
        (BoundingBox(39, -76, 43, -71), 1),  # 20 sq deg (F1.2 NYC box)
        (BoundingBox(30, -80, 40, -70), 2),  # 100 sq deg, boundary is inclusive
        (BoundingBox(30, -90, 50, -70), 3),  # 400
        (BoundingBox(25, -125, 50, -65), 4),  # continental US, 1500
        (None, 4),  # global
    ],
)
def test_credit_cost(bbox: BoundingBox | None, cost: int) -> None:
    assert credit_cost(bbox) == cost


def test_poll_interval() -> None:
    # Free account, global: 4000 * 0.9 / 4 = 900 polls/day -> 96 s.
    assert poll_interval_s(daily_credits=4000, cost_per_poll=4, min_refresh_s=5) == 96
    # Small box: 3600 polls/day -> 24 s, so the 5 s resolution doesn't bind...
    assert poll_interval_s(daily_credits=4000, cost_per_poll=1, min_refresh_s=5) == 24
    # ...but with a huge budget the provider's resolution does.
    assert poll_interval_s(daily_credits=10**6, cost_per_poll=1, min_refresh_s=5) == 5
    with pytest.raises(ValueError):
        poll_interval_s(daily_credits=1, cost_per_poll=4, min_refresh_s=5)


def test_bbox_rejects_inverted_range() -> None:
    with pytest.raises(ValueError):
        BoundingBox(43, -76, 39, -71)
