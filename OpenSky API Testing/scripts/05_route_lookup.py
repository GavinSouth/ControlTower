"""Experiment 5: fill OpenSky's biggest gap - origin and destination - via adsbdb.com.

OpenSky gives a callsign but not where the flight is going. adsbdb is a free
community API that maps callsign -> route. Does NOT use OpenSky credits.

Usage:
    python3 05_route_lookup.py ../data/raw/poll_nyc_4.json [max_lookups=10]
"""

import json
import sys
import time
from pathlib import Path

from opensky import DATA_DIR, get, states_to_rows, write_csv

snapshot = json.loads(Path(sys.argv[1]).read_text())
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
callsigns = [r["callsign"] for r in states_to_rows(snapshot) if r["callsign"]][:limit]

results = []
for cs in callsigns:
    status, _, body = get(f"https://api.adsbdb.com/v0/callsign/{cs}")
    row = {
        "callsign": cs,
        "found": False,
        "airline": None,
        "origin_iata": None,
        "origin_city": None,
        "destination_iata": None,
        "destination_city": None,
    }
    if status == 200:
        route = json.loads(body).get("response", {})
        if isinstance(route, dict) and "flightroute" in route:
            fr = route["flightroute"]
            row.update(
                found=True,
                airline=(fr.get("airline") or {}).get("name"),
                origin_iata=fr["origin"]["iata_code"],
                origin_city=fr["origin"]["municipality"],
                destination_iata=fr["destination"]["iata_code"],
                destination_city=fr["destination"]["municipality"],
            )
    results.append(row)
    print(cs, "->", f"{row['origin_iata']} -> {row['destination_iata']}" if row["found"] else "no route")
    time.sleep(0.5)  # be polite to a free community service

hits = sum(r["found"] for r in results)
print(f"routes found: {hits}/{len(results)}")
write_csv(results, DATA_DIR / f"routes_{snapshot['time']}.csv")
