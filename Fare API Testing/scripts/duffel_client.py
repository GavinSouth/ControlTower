"""Duffel Flights API: request + normalize (https://duffel.com/docs/api).

A test token (duffel_test_...) returns sandbox inventory; the `live_mode` field on each
response says which one we got. Searching is free; Duffel charges per booked order.
"""

import json
import re
import urllib.parse
from typing import Any

from common import now_iso, request, require

BASE_URL = "https://api.duffel.com"


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {require('DUFFEL_ACCESS_TOKEN')}",
        "Duffel-Version": "v2",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def place_suggestions(query: str) -> tuple[int, dict[str, Any], float]:
    url = f"{BASE_URL}/places/suggestions?{urllib.parse.urlencode({'query': query})}"
    status, _, body, seconds = request("GET", url, _headers())
    return status, json.loads(body or b"{}"), seconds


def search(
    origin: str, destination: str, depart: str, return_date: str | None = None
) -> tuple[int, dict[str, Any], float]:
    """Create an offer request and get its offers inline (return_offers=true)."""
    slices = [{"origin": origin, "destination": destination, "departure_date": depart}]
    if return_date:
        slices.append({"origin": destination, "destination": origin, "departure_date": return_date})
    body = {
        "data": {
            "slices": slices,
            "passengers": [{"type": "adult"}],
            "cabin_class": "economy",
        }
    }
    url = f"{BASE_URL}/air/offer_requests?return_offers=true&supplier_timeout=20000"
    status, _, payload, seconds = request("POST", url, _headers(), body)
    return status, json.loads(payload or b"{}"), seconds


def iso_minutes(duration: str | None) -> int | str:
    """ISO 8601 duration like 'P1DT2H30M' -> minutes."""
    if not duration:
        return ""
    m = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?)?", duration)
    if not m:
        return ""
    days, hours, mins = (int(g or 0) for g in m.groups())
    return days * 1440 + hours * 60 + mins


def _baggage(segment: dict[str, Any]) -> str:
    bags = (segment.get("passengers") or [{}])[0].get("baggages", [])
    return ", ".join(f"{b.get('quantity')}x {b.get('type')}" for b in bags)


def normalize(
    resp: dict[str, Any], origin: str, destination: str, depart: str, return_date: str | None
) -> list[dict[str, Any]]:
    """Map Duffel offers onto common.FARE_FIELDS (outbound slice for times/stops)."""
    fetched = now_iso()
    rows = []
    for offer in resp.get("data", {}).get("offers", []):
        out = offer["slices"][0]
        segs = out.get("segments", [])
        rows.append(
            {
                "provider": "duffel",
                "trip": "round_trip" if return_date else "one_way",
                "origin": origin,
                "destination": destination,
                "depart_date": depart,
                "return_date": return_date or "",
                "price": offer.get("total_amount", ""),
                "currency": offer.get("total_currency", ""),
                "airlines": "|".join(
                    dict.fromkeys(s.get("marketing_carrier", {}).get("name", "") for s in segs)
                ),
                "flight_numbers": "|".join(
                    f"{s.get('marketing_carrier', {}).get('iata_code', '')} "
                    f"{s.get('marketing_carrier_flight_number', '')}"
                    for s in segs
                ),
                "depart_time": segs[0].get("departing_at", "") if segs else "",
                "arrive_time": segs[-1].get("arriving_at", "") if segs else "",
                "stops": len(segs) - 1,
                "duration_min": iso_minutes(out.get("duration")),
                "cabin": (segs[0].get("passengers") or [{}])[0].get("cabin_class", "")
                if segs
                else "",
                "baggage": _baggage(segs[0]) if segs else "",
                "booking_ref": offer.get("id", ""),
                "fetched_at": fetched,
            }
        )
    return rows
