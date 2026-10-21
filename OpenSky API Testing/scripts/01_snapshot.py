"""Experiment 1: grab one snapshot of live aircraft and save it as JSON + CSV.

Usage:
    python3 01_snapshot.py            # whole world (costs 4 credits)
    python3 01_snapshot.py --nyc      # NYC box only (costs 1 credit)
"""

import sys

from opensky import DATA_DIR, NYC_BBOX, RAW_DIR, get_states, save_json, states_to_rows, write_csv

nyc = "--nyc" in sys.argv
snapshot, remaining = get_states(NYC_BBOX if nyc else None)
label = "nyc" if nyc else "global"
stamp = snapshot["time"]

save_json(snapshot, RAW_DIR / f"states_{label}_{stamp}.json")
write_csv(states_to_rows(snapshot), DATA_DIR / f"states_{label}_{stamp}.csv")
print(f"aircraft: {len(snapshot['states'] or [])} | credits remaining today: {remaining}")
