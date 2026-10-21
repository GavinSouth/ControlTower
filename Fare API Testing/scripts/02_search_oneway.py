"""One-way searches: every route in ROUTES x every date in DATE_OFFSETS, per provider.

Usage: python 02_search_oneway.py [serpapi] [duffel]
SerpApi cost: 6 searches (0 on re-run; raw responses are reused).
Writes data/fares_oneway.csv (one row per itinerary) and data/summary_oneway.csv.
"""

import sys
from typing import Any

import fares
from common import FARE_FIELDS, ROUTES, providers, search_dates, write_csv


def main() -> None:
    rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for provider in providers(sys.argv[1:]):
        for origin, destination in ROUTES:
            for depart, _ in search_dates():
                _, found, summary = fares.run(provider, origin, destination, depart)
                rows += found
                summaries.append(summary)
    if summaries:
        print("wrote", write_csv("fares_oneway", rows, FARE_FIELDS))
        print("wrote", write_csv("summary_oneway", summaries))


if __name__ == "__main__":
    main()
