"""Experiment 4: which endpoints work without an account?

Hits the flights + tracks endpoints anonymously and records the HTTP status.

Usage:
    python3 04_probe_endpoints.py [icao24=39de4f]
"""

import sys
import time

from opensky import BASE_URL, DATA_DIR, get, write_csv

icao24 = sys.argv[1] if len(sys.argv) > 1 else "39de4f"
end = int(time.time()) - 86_400  # flights data is batched nightly, so look at yesterday
begin = end - 7_200  # /flights/all allows at most a 2-hour window

endpoints = [
    f"/flights/all?begin={begin}&end={end}",
    f"/flights/arrival?airport=KJFK&begin={begin}&end={end}",
    f"/flights/departure?airport=KJFK&begin={begin}&end={end}",
    f"/flights/aircraft?icao24={icao24}&begin={begin}&end={end}",
    f"/tracks/all?icao24={icao24}&time=0",
]

results = []
for path in endpoints:
    status, _, body = get(BASE_URL + path)
    results.append({"endpoint": path, "status": status, "body_preview": body[:120].decode(errors="replace")})
    print(status, path)

write_csv(results, DATA_DIR / f"endpoint_probe_{int(time.time())}.csv")
