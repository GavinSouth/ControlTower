"""Experiment 3: poll a small area repeatedly to learn how often data actually refreshes.

If two polls return the same `time`, we polled faster than OpenSky updates
(and wasted a credit). Each poll costs 1 credit.

Usage:
    python3 03_poll_cadence.py [polls=4] [interval_seconds=5]
"""

import sys
import time

from opensky import DATA_DIR, NYC_BBOX, RAW_DIR, get_states, save_json, states_to_rows, write_csv

polls = int(sys.argv[1]) if len(sys.argv) > 1 else 4
interval = float(sys.argv[2]) if len(sys.argv) > 2 else 5

summary, all_rows, previous = [], [], None
for i in range(1, polls + 1):
    snapshot, remaining = get_states(NYC_BBOX)
    rows = states_to_rows(snapshot)
    for r in rows:
        r["poll"] = i
    all_rows += rows
    save_json(snapshot, RAW_DIR / f"poll_nyc_{snapshot['time']}_{i}.json")

    same = previous is not None and snapshot["time"] == previous
    summary.append(
        {
            "poll": i,
            "data_time": snapshot["time"],
            "aircraft": len(rows),
            "credits_remaining": remaining,
            "duplicate_of_previous": same,
        }
    )
    print(summary[-1])
    previous = snapshot["time"]
    if i < polls:
        time.sleep(interval)

stamp = summary[0]["data_time"]
write_csv(summary, DATA_DIR / f"poll_summary_{stamp}.csv")
write_csv(all_rows, DATA_DIR / f"poll_states_{stamp}.csv")
