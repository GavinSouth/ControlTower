"""Compare providers on the one-way results from 02 (no API calls).

For each route/date: result counts, cheapest price, how many flights both providers list,
and the price gap on those shared flights. Writes data/compare_oneway.csv.
"""

import re
from collections import defaultdict
from typing import Any

from common import read_csv, write_csv


def flight_key(row: dict[str, str]) -> str:
    """'UA 123|UA 0456' and 'UA123|UA456' -> 'UA123|UA456' (Duffel zero-pads numbers)."""
    return "|".join(
        re.sub(r"^([A-Z0-9]{2})0*(\d)", r"\1\2", f.replace(" ", ""))
        for f in row["flight_numbers"].split("|")
    )


def main() -> None:
    rows = read_csv("fares_oneway")
    if not rows:
        raise SystemExit("data/fares_oneway.csv missing; run 02_search_oneway.py first.")

    groups: dict[tuple[str, str], dict[str, dict[str, float]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    for r in rows:
        if not r["price"]:
            continue
        by_flight = groups[(f"{r['origin']}-{r['destination']}", r["depart_date"])][r["provider"]]
        key, price = flight_key(r), float(r["price"])
        by_flight[key] = min(price, by_flight.get(key, price))

    out: list[dict[str, Any]] = []
    for (route, depart), by_provider in sorted(groups.items()):
        serp, duff = by_provider.get("serpapi", {}), by_provider.get("duffel", {})
        shared = sorted(set(serp) & set(duff))
        gaps = [duff[k] - serp[k] for k in shared]
        out.append(
            {
                "route": route,
                "depart_date": depart,
                "serpapi_results": len(serp),
                "duffel_results": len(duff),
                "serpapi_cheapest": min(serp.values()) if serp else "",
                "duffel_cheapest": min(duff.values()) if duff else "",
                "shared_flights": len(shared),
                "avg_gap_duffel_minus_serpapi": round(sum(gaps) / len(gaps), 2) if gaps else "",
                "shared_examples": "; ".join(shared[:3]),
            }
        )
        print(out[-1])
    print("wrote", write_csv("compare_oneway", out))


if __name__ == "__main__":
    main()
