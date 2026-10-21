"""Shared helpers for the OpenSky experiments (standard library only).

Every numbered script imports from here so the HTTP + CSV logic lives in one place.
"""

import csv
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BASE_URL = "https://opensky-network.org/api"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"

# Index -> name for each entry in a state vector (see OpenSky REST docs).
STATE_FIELDS = [
    "icao24",  # unique 24-bit transponder address (hex)
    "callsign",  # e.g. "DAL2646", may be null
    "origin_country",  # country of registration, NOT where the flight departed
    "time_position",  # unix time of last position update
    "last_contact",  # unix time of last message of any kind
    "longitude",
    "latitude",
    "baro_altitude_m",  # barometric altitude, meters
    "on_ground",
    "velocity_mps",  # ground speed, meters/second
    "true_track_deg",  # heading, degrees clockwise from north
    "vertical_rate_mps",  # + climbing, - descending
    "sensors",
    "geo_altitude_m",  # GPS altitude, meters
    "squawk",  # transponder code
    "spi",  # special purpose indicator
    "position_source",  # 0=ADS-B 1=ASTERIX 2=MLAT 3=FLARM
    "category",  # only present with extended=1
]

TRACK_FIELDS = ["time", "latitude", "longitude", "baro_altitude_m", "true_track_deg", "on_ground"]

# A ~20 square-degree box around New York (<=25 sq deg costs 1 credit).
NYC_BBOX = {"lamin": 39, "lomin": -76, "lamax": 43, "lomax": -71}


def get(url: str) -> tuple[int, dict[str, str], bytes]:
    """GET a URL. Returns (status, headers, body) without raising on 4xx/5xx."""
    req = urllib.request.Request(url, headers={"User-Agent": "ControlTower-research"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as err:
        return err.code, dict(err.headers), err.read()


def get_states(bbox: dict[str, float] | None = None) -> tuple[dict[str, Any], int | None]:
    """Fetch live state vectors. Returns (json, credits_remaining)."""
    url = f"{BASE_URL}/states/all"
    if bbox:
        url += "?" + "&".join(f"{k}={v}" for k, v in bbox.items())
    status, headers, body = get(url)
    if status != 200:
        raise RuntimeError(f"HTTP {status}: {body[:200]!r}")
    remaining = headers.get("X-Rate-Limit-Remaining") or headers.get("x-rate-limit-remaining")
    return json.loads(body), int(remaining) if remaining else None


def save_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def states_to_rows(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """Turn OpenSky's positional arrays into named dicts (one per aircraft)."""
    rows = []
    for state in snapshot.get("states") or []:
        row = dict(zip(STATE_FIELDS, state, strict=False))
        if isinstance(row.get("callsign"), str):
            row["callsign"] = row["callsign"].strip()  # OpenSky pads to 8 chars
        row["snapshot_time"] = snapshot["time"]
        rows.append(row)
    return rows


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        fieldnames += [k for k in row if k not in fieldnames]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows -> {path.relative_to(DATA_DIR.parent)}")
