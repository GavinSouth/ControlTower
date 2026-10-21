"""Convert every saved raw JSON response in data/raw/ into a CSV in data/.

Usage:
    python3 convert_raw_to_csv.py
"""

import json

from opensky import DATA_DIR, RAW_DIR, TRACK_FIELDS, states_to_rows, write_csv

for path in sorted(RAW_DIR.glob("*.json")):
    data = json.loads(path.read_text())
    if "path" in data:  # a /tracks response
        rows = [dict(zip(TRACK_FIELDS, p, strict=True)) for p in data["path"]]
    else:  # a /states response
        rows = states_to_rows(data)
    write_csv(rows, DATA_DIR / f"{path.stem}.csv")
