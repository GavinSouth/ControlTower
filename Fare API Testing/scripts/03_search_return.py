"""Round-trip searches: same matrix as 02, returning TRIP_LENGTH_DAYS later.

Duffel returns combined outbound+return offers in one call. SerpApi (like the Google
Flights UI) returns outbound options first; picking one means a second call with its
`departure_token` to get the matching return flights and the final round-trip price.
We make that second call for the cheapest outbound on the first date of each route.

Usage: python 03_search_return.py [serpapi] [duffel]
SerpApi cost: 6 + 3 = 9 searches (0 on re-run).
Writes data/fares_return.csv, data/summary_return.csv, data/serpapi_return_legs.csv.
"""

import sys
from typing import Any

import fares
import serpapi_client
from common import FARE_FIELDS, ROUTES, load_raw, providers, save_raw, search_dates, write_csv


def serpapi_return_legs(
    resp: dict[str, Any], origin: str, destination: str, depart: str, ret: str
) -> list[dict[str, Any]]:
    """Follow the cheapest outbound's departure_token to its return-flight options."""
    outbound = [i for i in serpapi_client.itineraries(resp) if i.get("departure_token")]
    if not outbound:
        return []
    cheapest = min(outbound, key=lambda i: i.get("price", 1e9))
    name = f"serpapi_rt_{origin}-{destination}_{depart}_return_leg"
    cached = load_raw(name)
    if cached is None:
        status, body, seconds = serpapi_client.search(
            origin, destination, depart, ret, departure_token=cheapest["departure_token"]
        )
        cached = {"status": status, "seconds": seconds, "body": body}
        save_raw(name, cached)
    rows = serpapi_client.normalize(cached["body"], origin, destination, depart, ret)
    outbound_flights = "|".join(s.get("flight_number", "") for s in cheapest["flights"])
    for r in rows:
        r["outbound_flight_numbers"] = outbound_flights
        r["outbound_listed_price"] = cheapest.get("price")
    print(f"         return legs for {outbound_flights}: {len(rows)} options")
    return rows


def main() -> None:
    rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    legs: list[dict[str, Any]] = []
    for provider in providers(sys.argv[1:]):
        for origin, destination in ROUTES:
            for n, (depart, ret) in enumerate(search_dates()):
                resp, found, summary = fares.run(provider, origin, destination, depart, ret)
                rows += found
                summaries.append(summary)
                if provider == "serpapi" and n == 0 and summary["http_status"] == 200:
                    legs += serpapi_return_legs(resp, origin, destination, depart, ret)
    if summaries:
        print("wrote", write_csv("fares_return", rows, FARE_FIELDS))
        print("wrote", write_csv("summary_return", summaries))
    if legs:
        fields = [*FARE_FIELDS, "outbound_flight_numbers", "outbound_listed_price"]
        print("wrote", write_csv("serpapi_return_legs", legs, fields))


if __name__ == "__main__":
    main()
