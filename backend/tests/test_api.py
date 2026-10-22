"""HTTP API behaviour (F2.2), exercised through real requests against a temp database."""

from typing import Any

from fastapi.testclient import TestClient

JAPAN = {"title": "Japan", "home_tz": "America/Los_Angeles"}


def create(client: TestClient, url: str, body: dict[str, Any]) -> dict[str, Any]:
    response = client.post(url, json=body)
    assert response.status_code == 201, response.text
    data: dict[str, Any] = response.json()
    return data


def new_trip(client: TestClient, **overrides: Any) -> dict[str, Any]:
    return create(client, "/trips", {**JAPAN, **overrides})


# --- Trips -----------------------------------------------------------------


def test_trip_crud(client: TestClient) -> None:
    trip = new_trip(client, notes="cherry blossoms")
    assert trip["phase"] == "unscheduled"  # no dates, no items yet
    url = f"/trips/{trip['id']}"

    assert client.get(url).json()["notes"] == "cherry blossoms"
    patched = client.patch(url, json={"start_date": "2027-04-05", "end_date": "2027-04-12"})
    assert patched.status_code == 200
    assert (patched.json()["first_day"], patched.json()["phase"]) == ("2027-04-05", "upcoming")

    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404


def test_trip_location_is_optional_free_text(client: TestClient) -> None:
    assert new_trip(client)["location"] is None
    trip = new_trip(client, location="Shinjuku, Japan")
    assert trip["location"] == "Shinjuku, Japan"
    url = f"/trips/{trip['id']}"
    assert client.patch(url, json={"location": "Japan"}).json()["location"] == "Japan"
    assert client.patch(url, json={"location": None}).json()["location"] is None
    assert client.patch(url, json={"location": "x" * 201}).status_code == 422


def test_trips_listed_soonest_first_and_filtered_by_phase(client: TestClient) -> None:
    new_trip(client, title="Later", start_date="2099-06-01", end_date="2099-06-05")
    new_trip(client, title="Sooner", start_date="2099-01-01", end_date="2099-01-05")
    new_trip(client, title="Done", start_date="2001-01-01", end_date="2001-01-05")
    new_trip(client, title="Someday")

    titles = [t["title"] for t in client.get("/trips").json()]
    assert titles == ["Done", "Sooner", "Later", "Someday"]
    upcoming = client.get("/trips", params={"phase": "upcoming"}).json()
    assert [t["title"] for t in upcoming] == ["Sooner", "Later"]


def test_trip_validation(client: TestClient) -> None:
    bad_zone = client.post("/trips", json={"title": "x", "home_tz": "Mars/Base"})
    assert bad_zone.status_code == 422
    assert "unknown time zone" in bad_zone.text
    typo = client.post("/trips", json={**JAPAN, "tittle": "typo"})
    assert typo.status_code == 422  # unknown fields are rejected, not ignored
    backwards = client.post(
        "/trips", json={**JAPAN, "start_date": "2027-04-10", "end_date": "2027-04-01"}
    )
    assert backwards.status_code == 422
    trip = new_trip(client)
    assert client.patch(f"/trips/{trip['id']}", json={"title": None}).status_code == 422


# --- Items -----------------------------------------------------------------


def test_every_item_kind_through_one_endpoint(client: TestClient) -> None:
    trip = new_trip(client)
    url = f"/trips/{trip['id']}/items"
    bodies = [
        {"kind": "flight", "title": "UA 837", "airline": "UA", "flight_number": "837"},
        {"kind": "stay", "title": "Hotel X", "check_in_after": "15:00"},
        {"kind": "transport", "title": "Monorail", "mode": "metro"},
        {"kind": "activity", "title": "Tsukiji", "category": "food"},
        {"kind": "note", "title": "Buy a Suica card"},
    ]
    for body in bodies:
        item = create(client, url, body)
        assert item["kind"] == body["kind"]
        assert item["status"] == "planned"

    items = client.get(url).json()
    by_kind = {i["kind"]: i for i in items}
    assert by_kind["flight"]["flight_number"] == "837"
    assert by_kind["stay"]["check_in_after"] == "15:00:00"
    assert by_kind["transport"]["mode"] == "metro"
    assert "airline" not in by_kind["note"]  # each kind returns only its own fields


def test_transport_mode_defaults_and_unknown_kind_is_rejected(client: TestClient) -> None:
    trip = new_trip(client)
    url = f"/trips/{trip['id']}/items"
    assert create(client, url, {"kind": "transport", "title": "Walk"})["mode"] == "other"
    assert client.post(url, json={"kind": "spaceship", "title": "x"}).status_code == 422
    flight_field_on_note = {"kind": "note", "title": "x", "airline": "UA"}
    assert client.post(url, json=flight_field_on_note).status_code == 422


def test_flight_times_zones_and_effective_time(client: TestClient) -> None:
    trip = new_trip(client)
    sfo = create(
        client, "/places", {"name": "SFO", "tz": "America/Los_Angeles", "iata_code": "SFO"}
    )
    hnd = create(client, "/places", {"name": "Haneda", "tz": "Asia/Tokyo", "iata_code": "HND"})
    flight = create(
        client,
        f"/trips/{trip['id']}/items",
        {
            "kind": "flight",
            "title": "UA 837",
            "planned_start": "2027-04-05T11:05:00-07:00",
            "planned_end": "2027-04-06T15:25:00+09:00",
            "place_id": sfo["id"],
            "to_place_id": hnd["id"],
        },
    )
    # Zones were filled from the places; times come back in UTC.
    assert (flight["start_tz"], flight["end_tz"]) == ("America/Los_Angeles", "Asia/Tokyo")
    assert flight["planned_start"].startswith("2027-04-05T18:05:00")
    assert flight["effective_start"] == flight["planned_start"]

    delayed = client.patch(
        f"/items/{flight['id']}",
        json={"kind": "flight", "actual_start": "2027-04-05T11:52:00-07:00", "status": "done"},
    ).json()
    assert delayed["effective_start"].startswith("2027-04-05T18:52:00")
    assert delayed["planned_start"] == flight["planned_start"]  # the plan is kept

    # The trip's range now comes from the flight: departs 5 Apr (SFO), lands 6 Apr (Tokyo).
    trip_now = client.get(f"/trips/{trip['id']}").json()
    assert (trip_now["first_day"], trip_now["last_day"]) == ("2027-04-05", "2027-04-06")


def test_timed_item_without_place_gets_trip_zone(client: TestClient) -> None:
    trip = new_trip(client)
    note = create(
        client,
        f"/trips/{trip['id']}/items",
        {"kind": "note", "title": "Call home", "planned_start": "2027-04-07T09:00:00+09:00"},
    )
    assert note["start_tz"] == "America/Los_Angeles"


def test_item_validation(client: TestClient) -> None:
    trip = new_trip(client)
    url = f"/trips/{trip['id']}/items"
    naive = {"kind": "note", "title": "x", "planned_start": "2027-04-07T09:00:00"}
    assert client.post(url, json=naive).status_code == 422
    backwards = {
        "kind": "stay",
        "title": "x",
        "planned_start": "2027-04-07T15:00:00+09:00",
        "planned_end": "2027-04-06T11:00:00+09:00",
    }
    response = client.post(url, json=backwards)
    assert response.status_code == 422
    assert "planned_end is before planned_start" in response.text
    ghost_place = {"kind": "stay", "title": "x", "place_id": "00000000-0000-0000-0000-000000000000"}
    assert client.post(url, json=ghost_place).status_code == 422
    assert (
        client.post(url, json={"kind": "stay", "title": "x", "cost_currency": "usd"}).status_code
        == 422
    )


def test_item_patch_rules(client: TestClient) -> None:
    trip = new_trip(client)
    stay = create(
        client, f"/trips/{trip['id']}/items", {"kind": "stay", "title": "Hotel X", "room": "1204"}
    )
    url = f"/items/{stay['id']}"

    renamed = client.patch(url, json={"kind": "stay", "title": "Hotel Y"}).json()
    assert (renamed["title"], renamed["room"]) == ("Hotel Y", "1204")  # untouched fields kept
    assert client.patch(url, json={"kind": "stay", "room": None}).json()["room"] is None
    assert client.patch(url, json={"kind": "stay", "title": None}).status_code == 422
    assert client.patch(url, json={"kind": "flight", "title": "x"}).status_code == 422

    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404


def test_cost_is_exact(client: TestClient) -> None:
    trip = new_trip(client)
    stay = create(
        client,
        f"/trips/{trip['id']}/items",
        {"kind": "stay", "title": "x", "cost_amount": "123.45", "cost_currency": "JPY"},
    )
    assert stay["cost_amount"] == "123.45"  # decimals are strings in JSON: no float rounding


def test_deleting_a_trip_removes_its_items(client: TestClient) -> None:
    trip = new_trip(client)
    note = create(client, f"/trips/{trip['id']}/items", {"kind": "note", "title": "x"})
    client.delete(f"/trips/{trip['id']}")
    assert client.get(f"/items/{note['id']}").status_code == 404


# --- Places, days, log -----------------------------------------------------


def test_place_search(client: TestClient) -> None:
    create(client, "/places", {"name": "Haneda", "tz": "Asia/Tokyo", "iata_code": "HND"})
    create(client, "/places", {"name": "Hotel X", "city": "Tokyo", "tz": "Asia/Tokyo"})
    create(client, "/places", {"name": "SFO", "tz": "America/Los_Angeles", "iata_code": "SFO"})

    def names(q: str) -> list[str]:
        return [p["name"] for p in client.get("/places", params={"q": q}).json()]

    assert names("tokyo") == ["Hotel X"]
    assert names("hnd") == ["Haneda"]
    assert len(client.get("/places").json()) == 3
    assert (
        client.post(
            "/places", json={"name": "x", "tz": "Asia/Tokyo", "country": "Japan"}
        ).status_code
        == 422
    )


def test_day_extras_upsert(client: TestClient) -> None:
    trip = new_trip(client)
    url = f"/trips/{trip['id']}/days/2027-04-06"
    assert client.put(url, json={"title": "Arrival", "city": "Tokyo"}).status_code == 200
    replaced = client.put(url, json={"title": "Arrival day"}).json()
    assert (replaced["title"], replaced["city"]) == ("Arrival day", None)
    assert [d["local_date"] for d in client.get(f"/trips/{trip['id']}/days").json()] == [
        "2027-04-06"
    ]
    assert client.delete(url).status_code == 204
    assert client.delete(url).status_code == 404


def test_log_entries(client: TestClient) -> None:
    trip = new_trip(client)
    other = new_trip(client, title="Other")
    stay = create(client, f"/trips/{trip['id']}/items", {"kind": "stay", "title": "Hotel X"})
    url = f"/trips/{trip['id']}/log"
    base = {"tz": "Asia/Tokyo", "kind": "note"}

    create(client, url, {**base, "occurred_at": "2027-04-06T20:00:00+09:00", "text": "dinner"})
    create(
        client,
        url,
        {
            **base,
            "occurred_at": "2027-04-06T15:10:00+09:00",
            "kind": "check_in",
            "item_id": stay["id"],
        },
    )
    entries = client.get(url).json()
    assert [e["kind"] for e in entries] == ["check_in", "note"]  # oldest first
    assert entries[0]["source"] == "manual"

    wrong_trip = {**base, "occurred_at": "2027-04-06T15:10:00+09:00", "item_id": stay["id"]}
    assert client.post(f"/trips/{other['id']}/log", json=wrong_trip).status_code == 422
    assert client.delete(f"/log/{entries[0]['id']}").status_code == 204
    assert len(client.get(url).json()) == 1


def test_docs_and_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/docs").status_code == 200
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/trips", "/trips/{trip_id}/items", "/items/{item_id}", "/places"} <= set(paths)


def test_log_entry_patch(client: TestClient) -> None:
    trip = new_trip(client)
    other = new_trip(client, title="Other")
    stay = create(client, f"/trips/{trip['id']}/items", {"kind": "stay", "title": "Hotel X"})
    elsewhere = create(client, f"/trips/{other['id']}/items", {"kind": "note", "title": "n"})
    entry = create(
        client,
        f"/trips/{trip['id']}/log",
        {"occurred_at": "2027-04-06T20:00:00+09:00", "tz": "Asia/Tokyo", "kind": "note"},
    )
    url = f"/log/{entry['id']}"

    patched = client.patch(url, json={"text": "ramen", "kind": "check_in", "item_id": stay["id"]})
    assert patched.status_code == 200, patched.text
    body = patched.json()
    assert (body["text"], body["kind"], body["item_id"]) == ("ramen", "check_in", stay["id"])
    assert body["occurred_at"] == "2027-04-06T11:00:00Z"  # untouched fields are kept

    assert client.patch(url, json={"item_id": None}).json()["item_id"] is None
    assert client.patch(url, json={"item_id": elsewhere["id"]}).status_code == 422
    assert client.patch(url, json={"kind": None}).status_code == 422
    assert client.patch(url, json={"tz": "Mars/Base"}).status_code == 422
    assert client.patch("/log/00000000-0000-0000-0000-000000000000", json={}).status_code == 404
