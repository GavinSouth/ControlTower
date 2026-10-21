"""SerpApi Google Flights: request + normalize (https://serpapi.com/google-flights-api).

Each non-cached call costs one search from the monthly quota. SerpApi caches identical
queries for ~1 h and serves those free, unless `no_cache=true` is passed.
"""

import json
import urllib.parse
from typing import Any

from common import now_iso, request, require

BASE_URL = "https://serpapi.com"


def _get(path: str, params: dict[str, str]) -> tuple[int, dict[str, Any], float]:
    query = urllib.parse.urlencode({**params, "api_key": require("SERPAPI_API_KEY")})
    status, _, body, seconds = request("GET", f"{BASE_URL}/{path}?{query}")
    return status, json.loads(body or b"{}"), seconds


def account() -> dict[str, Any]:
    """Plan + searches left this month. Free; does not use quota."""
    return _get("account.json", {})[1]


def autocomplete(q: str) -> tuple[int, dict[str, Any], float]:
    return _get("search.json", {"engine": "google_flights_autocomplete", "q": q, "hl": "en"})


def search(
    origin: str,
    destination: str,
    depart: str,
    return_date: str | None = None,
    departure_token: str | None = None,
    no_cache: bool = False,
) -> tuple[int, dict[str, Any], float]:
    """One-way (type=2) or round trip (type=1). With departure_token, returns the return legs."""
    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": depart,
        "type": "1" if return_date else "2",
        "currency": "USD",
        "hl": "en",
        "gl": "us",
    }
    if return_date:
        params["return_date"] = return_date
    if departure_token:
        params["departure_token"] = departure_token
    if no_cache:
        params["no_cache"] = "true"
    return _get("search.json", params)


def itineraries(resp: dict[str, Any]) -> list[dict[str, Any]]:
    """best_flights + other_flights, tagged with which list they came from."""
    out = []
    for bucket in ("best_flights", "other_flights"):
        for item in resp.get(bucket, []):
            out.append({**item, "_bucket": bucket})
    return out


def normalize(
    resp: dict[str, Any], origin: str, destination: str, depart: str, return_date: str | None
) -> list[dict[str, Any]]:
    """Map SerpApi itineraries onto common.FARE_FIELDS."""
    fetched = now_iso()
    rows = []
    for it in itineraries(resp):
        segs = it.get("flights", [])
        if not segs:
            continue
        rows.append(
            {
                "provider": "serpapi",
                "trip": "round_trip" if return_date else "one_way",
                "origin": origin,
                "destination": destination,
                "depart_date": depart,
                "return_date": return_date or "",
                "price": it.get("price", ""),  # round trip: total for both legs
                "currency": "USD",
                "airlines": "|".join(dict.fromkeys(s.get("airline", "") for s in segs)),
                "flight_numbers": "|".join(s.get("flight_number", "") for s in segs),
                "depart_time": segs[0].get("departure_airport", {}).get("time", ""),
                "arrive_time": segs[-1].get("arrival_airport", {}).get("time", ""),
                "stops": len(segs) - 1,
                "duration_min": it.get("total_duration", ""),
                "cabin": segs[0].get("travel_class", ""),
                "baggage": "; ".join(
                    e for s in segs for e in s.get("extensions", []) if "bag" in e.lower()
                ),
                "booking_ref": "departure_token"
                if it.get("departure_token")
                else ("booking_token" if it.get("booking_token") else ""),
                "fetched_at": fetched,
            }
        )
    return rows
