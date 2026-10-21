"""Freshness: repeat one identical search several times and diff the prices per flight.

SerpApi is called with no_cache=true so every run is a real (billed) Google Flights fetch.
Usage: python 04_freshness.py [serpapi] [duffel] [--runs N] [--interval SECONDS]
Defaults: 3 runs, 600 s apart (~20 min). SerpApi cost: N searches.
Writes data/freshness.csv (price per flight per run) and prints changes.
"""

import argparse
import time
from collections import defaultdict
from typing import Any

import fares
from common import ROUTES, now_iso, providers, search_dates, write_csv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("provider", nargs="*")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--interval", type=int, default=600)
    args = parser.parse_args()

    origin, destination = ROUTES[0]
    depart = search_dates()[0][0]
    stamp = now_iso().replace(":", "")
    rows: list[dict[str, Any]] = []
    for run in range(1, args.runs + 1):
        for provider in providers(args.provider):
            _, found, _ = fares.run(
                provider, origin, destination, depart, tag=f"_fresh{stamp}_{run}", fresh=True
            )
            for r in found:
                rows.append(
                    {
                        "run": run,
                        "provider": provider,
                        "fetched_at": r["fetched_at"],
                        "flight_numbers": r["flight_numbers"],
                        "depart_time": r["depart_time"],
                        "price": r["price"],
                        "currency": r["currency"],
                    }
                )
        write_csv("freshness", rows)  # after every run, so a cancelled run keeps data
        if run < args.runs:
            time.sleep(args.interval)

    prices: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for r in rows:
        prices[(r["provider"], r["flight_numbers"], r["depart_time"])].append(str(r["price"]))
    for provider in sorted({k[0] for k in prices}):
        keys = [k for k in prices if k[0] == provider]
        changed = [k for k in keys if len(set(prices[k])) > 1]
        print(f"{provider}: {len(keys)} distinct flights, {len(changed)} changed price")
        for k in changed[:10]:
            print(f"   {k[1]:24} {' -> '.join(prices[k])}")


if __name__ == "__main__":
    main()
