"""Can each API power an airport search box? Query by city/airport name, flatten results.

Usage: python 01_airport_lookup.py [serpapi] [duffel]
SerpApi cost: one search per query (4 total).
"""

import sys
from typing import Any

import duffel_client
import serpapi_client
from common import load_raw, providers, save_raw, write_csv

QUERIES = ["london", "new york", "san fran", "heathrow"]


def flatten_serpapi(q: str, resp: dict[str, Any], seconds: float) -> list[dict[str, Any]]:
    rows = []
    for rank, s in enumerate(resp.get("suggestions", []), 1):
        rows.append(
            {
                "provider": "serpapi",
                "query": q,
                "rank": rank,
                "kind": s.get("type"),
                "name": s.get("name"),
                "code": s.get("id"),
                "city": s.get("description", ""),
                "latency_s": round(seconds, 2),
            }
        )
        for a in s.get("airports", []):
            rows.append(
                {
                    "provider": "serpapi",
                    "query": q,
                    "rank": rank,
                    "kind": "airport (nested)",
                    "name": a.get("name"),
                    "code": a.get("id"),
                    "city": a.get("city", ""),
                    "latency_s": round(seconds, 2),
                }
            )
    return rows


def flatten_duffel(q: str, resp: dict[str, Any], seconds: float) -> list[dict[str, Any]]:
    rows = []
    for rank, p in enumerate(resp.get("data", []), 1):
        rows.append(
            {
                "provider": "duffel",
                "query": q,
                "rank": rank,
                "kind": p.get("type"),
                "name": p.get("name"),
                "code": p.get("iata_code"),
                "city": p.get("city_name") or "",
                "latency_s": round(seconds, 2),
            }
        )
        for a in p.get("airports") or []:
            rows.append(
                {
                    "provider": "duffel",
                    "query": q,
                    "rank": rank,
                    "kind": "airport (nested)",
                    "name": a.get("name"),
                    "code": a.get("iata_code"),
                    "city": a.get("city_name") or "",
                    "latency_s": round(seconds, 2),
                }
            )
    return rows


def main() -> None:
    rows: list[dict[str, Any]] = []
    for provider in providers(sys.argv[1:]):
        for q in QUERIES:
            name = f"lookup_{provider}_{q.replace(' ', '_')}"
            cached = load_raw(name)
            if cached is not None:
                status, resp, seconds = cached["status"], cached["body"], cached["seconds"]
            elif provider == "serpapi":
                status, resp, seconds = serpapi_client.autocomplete(q)
            else:
                status, resp, seconds = duffel_client.place_suggestions(q)
            if cached is None:
                save_raw(name, {"status": status, "seconds": seconds, "body": resp})
            flat = flatten_serpapi if provider == "serpapi" else flatten_duffel
            found = flat(q, resp, seconds)
            print(f"{provider:8} {q!r:12} HTTP {status}  {len(found)} rows  {seconds:.2f}s")
            if status != 200:
                print(f"         error: {str(resp)[:200]}")
            rows += found
    if rows:
        print("wrote", write_csv("airport_lookup", rows))


if __name__ == "__main__":
    main()
