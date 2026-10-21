"""Experiment 2: summarize a saved snapshot - how much data, how fresh, how complete.

Usage:
    python3 02_analyze.py ../data/raw/states_global_1792561585.json
"""

import json
import sys
import time
from collections import Counter
from pathlib import Path

from opensky import states_to_rows

snapshot = json.loads(Path(sys.argv[1]).read_text())
rows = states_to_rows(snapshot)
now = snapshot["time"]

airborne = [r for r in rows if not r["on_ground"]]
ages = sorted(now - r["last_contact"] for r in rows)

print("snapshot:", time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now)))
print(f"aircraft: {len(rows)} | airborne: {len(airborne)} | on ground: {len(rows) - len(airborne)}")
print("with callsign:", sum(1 for r in rows if r["callsign"]))
print("with position:", sum(1 for r in rows if r["latitude"] is not None))
print(f"seconds since last contact: median {ages[len(ages) // 2]}, p90 {ages[int(len(ages) * 0.9)]}, max {ages[-1]}")
print("position source (0=ADS-B 1=ASTERIX 2=MLAT 3=FLARM):", dict(Counter(r["position_source"] for r in rows)))
print("top registration countries:", Counter(r["origin_country"] for r in rows).most_common(5))
