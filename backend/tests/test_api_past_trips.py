"""Past trip record through HTTP (F3.4): reflection, item feedback, stats, favourites."""

from typing import Any

from fastapi.testclient import TestClient

LISBON = {
    "title": "Lisbon",
    "home_tz": "Europe/Lisbon",
    "start_date": "2025-05-10",
    "end_date": "2025-05-15",
}


def post(client: TestClient, url: str, body: dict[str, Any]) -> dict[str, Any]:
    response = client.post(url, json=body)
    assert response.status_code == 201, response.text
    data: dict[str, Any] = response.json()
    return data


def put(client: TestClient, url: str, body: dict[str, Any]) -> Any:
    response = client.put(url, json=body)
    assert response.status_code == 200, response.text
    return response.json()


def activity(client: TestClient, trip_id: str, title: str, **fields: Any) -> dict[str, Any]:
    body = {"kind": "activity", "title": title, "planned_start": "2025-05-12T12:00:00+01:00"}
    return post(client, f"/trips/{trip_id}/items", {**body, **fields})


# --- Reflection --------------------------------------------------------------


def test_reflection_put_replaces_and_shows_on_the_trip(client: TestClient) -> None:
    trip = post(client, "/trips", LISBON)
    url = f"/trips/{trip['id']}/reflection"
    assert trip["reflection"] is None
    assert client.get(url).status_code == 404

    body = {
        "rating": 5,
        "highlight": "Sunset at the miradouro",
        "would_return": True,
        "tags": [" Food ", "food", "Slow  travel", ""],
        "companions": ["Sam", "sam", " Alex "],
    }
    saved = put(client, url, body)
    assert saved["tags"] == ["food", "slow travel"]  # trimmed, lower-cased, deduped
    assert saved["companions"] == ["Sam", "Alex"]  # trimmed and deduped, case kept
    brief = {"rating": 5, "highlight": "Sunset at the miradouro"}
    assert client.get(f"/trips/{trip['id']}").json()["reflection"] == brief
    assert [t["reflection"] for t in client.get("/trips").json()] == [brief]

    # PUT replaces the whole reflection: fields left out are cleared.
    replaced = put(client, url, {"rating": 4})
    assert (replaced["rating"], replaced["highlight"], replaced["tags"]) == (4, None, [])

    assert client.delete(url).status_code == 204
    assert client.delete(url).status_code == 204  # idempotent
    assert client.get(url).status_code == 404


def test_reflection_validation(client: TestClient) -> None:
    trip = post(client, "/trips", LISBON)
    url = f"/trips/{trip['id']}/reflection"
    assert client.put(url, json={"rating": 0}).status_code == 422
    assert client.put(url, json={"rating": 6}).status_code == 422
    assert client.put(url, json={"mood": "great"}).status_code == 422  # unknown field
    assert client.put(url, json={}).status_code == 200  # everything is optional (P7)
    missing = "/trips/00000000-0000-0000-0000-000000000000/reflection"
    assert client.put(missing, json={}).status_code == 404


def test_deleting_a_trip_deletes_its_reflection_and_feedback(client: TestClient) -> None:
    trip = post(client, "/trips", LISBON)
    item = activity(client, trip["id"], "Pastéis")
    put(client, f"/trips/{trip['id']}/reflection", {"rating": 5})
    put(client, f"/items/{item['id']}/feedback", {"favourite": True})

    assert client.delete(f"/trips/{trip['id']}").status_code == 204
    assert client.get("/favourites").json() == []


# --- Item feedback -----------------------------------------------------------


def test_feedback_shows_on_the_timeline_and_empty_feedback_is_deleted(client: TestClient) -> None:
    trip = post(client, "/trips", LISBON)
    item = activity(client, trip["id"], "Pastéis de Belém")
    url = f"/items/{item['id']}/feedback"

    saved = put(client, url, {"verdict": "up", "favourite": True, "review": "Worth the queue"})
    assert (saved["verdict"], saved["favourite"]) == ("up", True)

    timeline = client.get(f"/trips/{trip['id']}/timeline").json()
    [listing] = [li for day in timeline["days"] for li in day["items"]]
    assert listing["item"]["feedback"]["review"] == "Worth the queue"

    assert put(client, url, {}) is None  # nothing left to keep → row deleted
    timeline = client.get(f"/trips/{trip['id']}/timeline").json()
    [listing] = [li for day in timeline["days"] for li in day["items"]]
    assert listing["item"]["feedback"] is None
    assert put(client, url, {}) is None  # and an empty first PUT stores nothing
    assert client.delete(url).status_code == 204


def test_feedback_validation(client: TestClient) -> None:
    trip = post(client, "/trips", LISBON)
    item = activity(client, trip["id"], "Tram 28")
    url = f"/items/{item['id']}/feedback"
    assert client.put(url, json={"verdict": "meh"}).status_code == 422
    assert client.put(url, json={"review": "x" * 2001}).status_code == 422
    missing = "/items/00000000-0000-0000-0000-000000000000/feedback"
    assert client.put(missing, json={"verdict": "up"}).status_code == 404


# --- Stats and favourites ----------------------------------------------------


def test_stats_endpoint(client: TestClient) -> None:
    trip = post(client, "/trips", LISBON)
    place = post(
        client,
        "/places",
        {"name": "Pena", "city": "Sintra", "country": "PT", "lat": 38.8, "tz": "Europe/Lisbon"},
    )
    cost = {"cost_amount": "14", "cost_currency": "EUR"}
    liked = activity(client, trip["id"], "Pena", place_id=place["id"], **cost)
    activity(client, trip["id"], "Fado night")
    activity(client, trip["id"], "Museum", status="skipped")
    put(client, f"/items/{liked['id']}/feedback", {"verdict": "up"})

    stats = client.get(f"/trips/{trip['id']}/stats").json()

    assert stats["nights"] == 5
    assert (stats["cities"], stats["countries"]) == (["Sintra"], ["PT"])
    assert stats["spend"] == {"EUR": "14"}
    assert stats["season"] == "spring"
    assert stats["feedback"] == {"up": 1, "down": 0, "favourite": 0, "skipped": 1, "pending": 1}
    missing = "/trips/00000000-0000-0000-0000-000000000000/stats"
    assert client.get(missing).status_code == 404


def test_favourites_across_trips_with_filters(client: TestClient) -> None:
    lisbon = post(client, "/trips", LISBON)
    japan = post(client, "/trips", {"title": "Japan", "home_tz": "Asia/Tokyo"})
    tokyo = post(client, "/places", {"name": "Sushi bar", "country": "JP", "tz": "Asia/Tokyo"})
    sushi = activity(client, japan["id"], "Sushi", category="food", place_id=tokyo["id"])
    temple = activity(client, japan["id"], "Temple", category="sight", place_id=tokyo["id"])
    tart = activity(client, lisbon["id"], "Pastéis", category="food")
    meh = activity(client, lisbon["id"], "Tram")
    for item in (sushi, temple, tart):
        put(client, f"/items/{item['id']}/feedback", {"favourite": True})
    put(client, f"/items/{meh['id']}/feedback", {"verdict": "down"})  # not a favourite

    def titles(**params: str) -> list[str]:
        favourites = client.get("/favourites", params=params).json()
        return sorted(f["item"]["title"] for f in favourites)

    assert titles() == ["Pastéis", "Sushi", "Temple"]
    assert titles(country="jp", category="food") == ["Sushi"]  # "favourite food spots in Japan"
    assert titles(kind="stay") == []

    [fav] = client.get("/favourites", params={"category": "food", "country": "JP"}).json()
    assert (fav["trip_title"], fav["place"]["name"]) == ("Japan", "Sushi bar")
    assert fav["item"]["feedback"]["favourite"] is True
