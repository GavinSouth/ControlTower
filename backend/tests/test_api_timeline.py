"""GET /trips/{trip_id}/timeline through HTTP (F2.3)."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, event

JAPAN = {"title": "Japan", "home_tz": "Asia/Tokyo"}


def post(client: TestClient, url: str, body: dict[str, Any]) -> dict[str, Any]:
    response = client.post(url, json=body)
    assert response.status_code == 201, response.text
    data: dict[str, Any] = response.json()
    return data


@contextmanager
def count_queries(engine: Engine) -> Iterator[list[str]]:
    statements: list[str] = []

    def record(*args: Any) -> None:
        statements.append(args[2])  # (conn, cursor, statement, ...)

    event.listen(engine, "before_cursor_execute", record)
    try:
        yield statements
    finally:
        event.remove(engine, "before_cursor_execute", record)


def test_timeline_end_to_end(client: TestClient) -> None:
    trip = post(client, "/trips", JAPAN)
    items_url = f"/trips/{trip['id']}/items"
    post(
        client,
        items_url,
        {
            "kind": "flight",
            "title": "UA 837",
            "planned_start": "2027-04-05T11:05:00-07:00",
            "planned_end": "2027-04-06T15:25:00+09:00",
            "start_tz": "America/Los_Angeles",
            "end_tz": "Asia/Tokyo",
        },
    )
    stay = post(
        client,
        items_url,
        {
            "kind": "stay",
            "title": "Hotel X",
            "planned_start": "2027-04-06T17:00:00+09:00",  # after landing at 15:25
            "planned_end": "2027-04-08T11:00:00+09:00",
        },
    )
    post(client, items_url, {"kind": "note", "title": "Maybe: teamLab", "status": "idea"})
    client.put(f"/trips/{trip['id']}/days/2027-04-06", json={"title": "Arrival", "city": "Tokyo"})
    post(
        client,
        f"/trips/{trip['id']}/log",
        {
            "occurred_at": "2027-04-06T17:40:00+09:00",
            "tz": "Asia/Tokyo",
            "kind": "check_in",
            "item_id": stay["id"],
        },
    )

    response = client.get(f"/trips/{trip['id']}/timeline")
    assert response.status_code == 200
    timeline = response.json()

    assert (timeline["first_day"], timeline["last_day"]) == ("2027-04-05", "2027-04-08")
    summary = [
        (d["local_date"], d["number"], [(i["item"]["title"], i["role"]) for i in d["items"]])
        for d in timeline["days"]
    ]
    assert summary == [
        ("2027-04-05", 1, [("UA 837", "starts")]),
        ("2027-04-06", 2, [("UA 837", "ends"), ("Hotel X", "starts")]),
        ("2027-04-07", 3, [("Hotel X", "continues")]),
        ("2027-04-08", 4, [("Hotel X", "ends")]),
    ]
    arrival = timeline["days"][1]
    assert (arrival["title"], arrival["city"]) == ("Arrival", "Tokyo")
    assert [e["kind"] for e in arrival["log"]] == ["check_in"]
    assert arrival["items"][0]["item"]["kind"] == "flight"  # full item, kind-specific fields
    assert [i["title"] for i in timeline["unscheduled"]] == ["Maybe: teamLab"]


def test_timeline_errors(client: TestClient) -> None:
    missing = "/trips/00000000-0000-0000-0000-000000000000/timeline"
    assert client.get(missing).status_code == 404
    trip = post(client, "/trips", {**JAPAN, "start_date": "2027-01-01", "end_date": "2029-01-01"})
    too_long = client.get(f"/trips/{trip['id']}/timeline")
    assert too_long.status_code == 422
    assert "maximum is 366" in too_long.text


def test_timeline_query_count_does_not_grow_with_items(client: TestClient, engine: Engine) -> None:
    """Guards against N+1 queries: 10x the items, same number of SELECTs."""
    trip = post(client, "/trips", JAPAN)
    url = f"/trips/{trip['id']}/items"
    kinds = ["flight", "stay", "transport", "activity", "note"]

    def add(n: int) -> None:
        for k in range(n):
            post(
                client,
                url,
                {
                    "kind": kinds[k % len(kinds)],
                    "title": f"item {k}",
                    "planned_start": f"2027-04-{6 + k % 5:02d}T09:00:00+09:00",
                },
            )

    def selects() -> int:
        with count_queries(engine) as statements:
            assert client.get(f"/trips/{trip['id']}/timeline").status_code == 200
        return sum(s.lstrip().upper().startswith("SELECT") for s in statements)

    add(5)
    few = selects()
    add(45)
    assert selects() == few
