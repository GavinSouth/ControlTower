"""Run one fare search against a provider, cache the raw response, and summarize it.

Shared by 02 (one-way), 03 (round trip), and 04 (freshness). A raw file already on disk
is reused instead of calling the API again, so re-running a script costs nothing.
"""

from typing import Any

import duffel_client
import serpapi_client
from common import load_raw, save_raw


def run(
    provider: str,
    origin: str,
    destination: str,
    depart: str,
    return_date: str | None = None,
    tag: str = "",
    fresh: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """Return (raw response, normalized rows, one summary row)."""
    trip = "rt" if return_date else "ow"
    name = f"{provider}_{trip}_{origin}-{destination}_{depart}{tag}"
    cached = None if fresh else load_raw(name)
    if cached is not None:
        status, resp, seconds = cached["status"], cached["body"], cached["seconds"]
    else:
        if provider == "serpapi":
            status, resp, seconds = serpapi_client.search(
                origin, destination, depart, return_date, no_cache=fresh
            )
        else:
            status, resp, seconds = duffel_client.search(origin, destination, depart, return_date)
        save_raw(name, {"status": status, "seconds": seconds, "body": resp})

    client = serpapi_client if provider == "serpapi" else duffel_client
    rows = client.normalize(resp, origin, destination, depart, return_date) if status < 300 else []
    prices = [float(r["price"]) for r in rows if r["price"] != ""]
    summary = {
        "provider": provider,
        "trip": "round_trip" if return_date else "one_way",
        "route": f"{origin}-{destination}",
        "depart_date": depart,
        "return_date": return_date or "",
        "http_status": status,
        "results": len(rows),
        "cheapest": min(prices) if prices else "",
        "median": sorted(prices)[len(prices) // 2] if prices else "",
        "latency_s": round(seconds, 2),
        "from_cache": cached is not None,
        "live_mode": resp.get("data", {}).get("live_mode", "") if provider == "duffel" else "",
        "airlines_seen": len({a for r in rows for a in str(r["airlines"]).split("|")}),
        "error": "" if status < 300 else str(resp)[:200],
    }
    print(
        f"{provider:8} {summary['route']:8} {depart} {summary['trip']:10} HTTP {status} "
        f"{len(rows):3} results  cheapest {summary['cheapest']}  {seconds:.1f}s"
        + ("  (cached)" if cached is not None else "")
    )
    return resp, rows, summary
