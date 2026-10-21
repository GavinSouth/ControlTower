"""Shared helpers for the fare API experiments (standard library only).

Every numbered script imports from here so env loading, HTTP, raw saving, and the
normalized CSV schema live in one place. Keys are read from the repo-root `.env`
(or the real environment) and are scrubbed from anything written to disk.
"""

import csv
import json
import os
import re
import urllib.error
import urllib.request
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = ROOT.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

SECRET_VARS = ("SERPAPI_API_KEY", "DUFFEL_ACCESS_TOKEN")

# Routes under test: domestic trunk, transatlantic, short-haul.
ROUTES = [("JFK", "LAX"), ("LHR", "JFK"), ("SFO", "SEA")]
# Days ahead of today for departure; return trips come back 7 days later.
DATE_OFFSETS = [14, 60]
TRIP_LENGTH_DAYS = 7

# One row per bookable itinerary (not per segment), identical for both providers.
FARE_FIELDS = [
    "provider",
    "trip",  # one_way | round_trip
    "origin",
    "destination",
    "depart_date",
    "return_date",
    "price",
    "currency",
    "airlines",  # "|"-joined marketing carrier names
    "flight_numbers",  # "|"-joined, e.g. "AA 1|AA 2"
    "depart_time",  # first segment local departure
    "arrive_time",  # last segment local arrival (outbound)
    "stops",
    "duration_min",  # outbound journey duration
    "cabin",
    "baggage",  # whatever the provider says about bags, free text
    "booking_ref",  # token/offer id needed to book or deep-link
    "fetched_at",
]


def load_env() -> None:
    """Load KEY=VALUE lines from the repo-root .env into os.environ (no overrides)."""
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def require(var: str) -> str:
    """Return a required env var or exit with a hint (never echoes the value)."""
    load_env()
    value = os.environ.get(var, "")
    if not value:
        raise SystemExit(f"{var} is not set. Add it to {REPO_ROOT / '.env'} (see .env.example).")
    return value


def scrub(text: str) -> str:
    """Replace any known secret value in text with a placeholder."""
    for var in SECRET_VARS:
        value = os.environ.get(var)
        if value:
            text = text.replace(value, f"<{var}>")
    return re.sub(r"api_key=[^&\"\s]+", "api_key=<redacted>", text)


def request(
    method: str, url: str, headers: dict[str, str] | None = None, body: Any = None
) -> tuple[int, dict[str, str], bytes, float]:
    """Send a request. Returns (status, headers, body, seconds) without raising on 4xx/5xx."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    req.add_header("User-Agent", "ControlTower-research")
    start = datetime.now(UTC)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            status, resp_headers, payload = resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as err:
        status, resp_headers, payload = err.code, dict(err.headers), err.read()
    return status, resp_headers, payload, (datetime.now(UTC) - start).total_seconds()


def save_raw(name: str, payload: Any) -> Path:
    """Write a JSON response to data/raw/<name>.json with secrets scrubbed."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{name}.json"
    path.write_text(scrub(json.dumps(payload, indent=2)))
    return path


def load_raw(name: str) -> Any | None:
    """Return a previously saved raw response, or None (lets scripts skip paid calls)."""
    path = RAW_DIR / f"{name}.json"
    return json.loads(path.read_text()) if path.exists() else None


def write_csv(name: str, rows: list[dict[str, Any]], fields: list[str] | None = None) -> Path:
    """Write rows to data/<name>.csv; fields default to the keys of the first row."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{name}.csv"
    columns = fields or (list(rows[0]) if rows else [])
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def read_csv(name: str) -> list[dict[str, str]]:
    path = DATA_DIR / f"{name}.csv"
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def search_dates(today: date | None = None) -> list[tuple[str, str]]:
    """(depart, return) ISO dates for each offset in DATE_OFFSETS."""
    base = today or date.today()
    out = []
    for offset in DATE_OFFSETS:
        depart = base + timedelta(days=offset)
        out.append((depart.isoformat(), (depart + timedelta(days=TRIP_LENGTH_DAYS)).isoformat()))
    return out


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


PROVIDER_KEYS = {"serpapi": "SERPAPI_API_KEY", "duffel": "DUFFEL_ACCESS_TOKEN"}


def providers(argv: list[str]) -> list[str]:
    """Providers named on the command line (default: both) that have a key set."""
    load_env()
    wanted = [a for a in argv if a in PROVIDER_KEYS] or list(PROVIDER_KEYS)
    ready = []
    for name in wanted:
        if os.environ.get(PROVIDER_KEYS[name]):
            ready.append(name)
        else:
            print(f"skip {name}: {PROVIDER_KEYS[name]} not set in .env")
    return ready
