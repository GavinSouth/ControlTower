# OpenSky API Testing

Exploratory research (2026-10-20/21) into whether the [OpenSky Network](https://opensky-network.org) REST API can power ControlTower. All tests were run **anonymously** (no account). This folder is a sandbox — not part of the backend package.

## TL;DR verdict
**Good enough for an MVP (Minimum Viable Product)**, with three conditions:
1. Create a free OpenSky account (10x credits, 5 s data, unlocks flight history).
2. Backend polls OpenSky **once** and caches/fans out to all users — users never hit OpenSky directly.
3. Add a second source for **origin -> destination** (adsbdb.com worked for 7/10 callsigns).

Keep the data source behind an interface so we can swap to a paid provider (e.g. FlightAware AeroAPI) if we need schedules, ETAs, or commercial rights.

## Folder layout
```
scripts/
  opensky.py              shared helpers: HTTP GET, field names, JSON->CSV
  01_snapshot.py          one live snapshot (global or NYC box) -> JSON + CSV
  02_analyze.py           stats on a saved snapshot (counts, freshness, completeness)
  03_poll_cadence.py      poll the NYC box repeatedly to measure refresh rate
  04_probe_endpoints.py   which endpoints work without an account
  05_route_lookup.py      callsign -> origin/destination via adsbdb.com
  convert_raw_to_csv.py   turn every data/raw/*.json into data/*.csv
data/
  raw/                    untouched API responses (JSON)
  *.csv                   the same data, flattened — open in Excel/Numbers
```

## How to run
Standard library only — no installs needed. From `scripts/`:
```bash
python3 01_snapshot.py --nyc                                  # 1 credit
python3 01_snapshot.py                                        # global, 4 credits
python3 02_analyze.py ../data/raw/states_global_1792561585.json
python3 03_poll_cadence.py 4 5                                # 4 polls, 5 s apart (4 credits)
python3 04_probe_endpoints.py
python3 05_route_lookup.py ../data/raw/poll_nyc_4.json 10     # uses adsbdb, not OpenSky credits
python3 convert_raw_to_csv.py
```
Every response prints/records `credits remaining`. Anonymous budget: **400/day**.

## The data files
| File | What it is |
|---|---|
| `states_global_1792561585.csv` | Every aircraft worldwide at 05:46:25 UTC (6,103 rows) |
| `poll_nyc_1..4.csv` | First cadence test: NYC box polled 4x, 5 s apart |
| `poll_summary_*.csv` / `poll_states_*.csv` | Second cadence test: 3 polls, 10 s apart |
| `states_nyc_*.csv` | A single NYC-box snapshot |
| `track_39de4f.csv` | Live flight path of one aircraft (TVF99PC departing Paris-Orly) |
| `endpoint_probe_*.csv` | HTTP status of each endpoint without an account |
| `routes_*.csv` | Callsign -> airline/origin/destination lookups |

Columns in the `states_*` CSVs (units matter!):
`icao24` unique transponder ID · `callsign` flight number-ish · `origin_country` country of **registration** (not departure) · `longitude`/`latitude` · `baro_altitude_m` meters · `velocity_mps` meters/second (x 1.944 = knots) · `true_track_deg` heading · `vertical_rate_mps` · `on_ground` · `last_contact` unix time · `position_source` 0=ADS-B.

## Results

### 1. What a snapshot contains (`02_analyze.py`)
- 6,103 aircraft; 5,431 airborne. (05:46 UTC is a quiet hour — expect ~2x at peak.)
- 97.5% have a callsign; 99% have a position.
- Freshness: median 0 s since last contact, p90 59 s, max 315 s. Stale aircraft (>60 s) should probably be hidden or faded in the UI.
- All positions were ADS-B.
- Global response is ~790 KB of JSON and took ~1.3 s.

### 2. Refresh cadence (`03_poll_cadence.py`)
- Polling every **5 s**: polls 2 and 3 returned the identical `time` -> wasted credit.
- Polling every **10 s**: no duplicates.
- => Anonymous data updates every ~10 s (docs: 10 s anonymous, 5 s authenticated). Never poll faster than the tier's resolution.

### 3. Credit costs (from docs, confirmed by `X-Rate-Limit-Remaining`)
| Query | Cost |
|---|---|
| Bounding box <= 25 sq deg | 1 |
| 25-100 sq deg | 2 |
| 100-400 sq deg | 3 |
| Global | 4 |

| Tier | Credits/day | Small box, continuous | Global, continuous |
|---|---|---|---|
| Anonymous | 400 | every ~3.6 min | every ~14 min |
| Free account | 4,000 | every ~22 s | every ~90 s |
| Account + own ADS-B receiver (feeder) | 8,000 | every ~11 s | every ~45 s |

### 4. Endpoint access (`04_probe_endpoints.py`)
| Endpoint | Anonymous | Notes |
|---|---|---|
| `/states/all` | ✅ 200 | Live positions. Main data source. |
| `/tracks/all?time=0` | ✅ 200 | Live flight path so far. Experimental. |
| `/flights/all`, `/arrival`, `/departure`, `/aircraft` | ❌ 403 "You cannot access historical flights" | Need account. Batched **nightly** — yesterday or older only. |

### 5. Origin/destination (`05_route_lookup.py`)
OpenSky has no live origin/destination. adsbdb.com (free, community-maintained) resolved **7/10** callsigns over NYC — e.g. `DAL2646` Delta PVD->ATL, `AAL174` RDU->LHR. All 3 misses were private `N...` registrations, which don't fly published routes. Caveat: community data can be stale or wrong for a given day.

## Gaps vs. project needs
| Need | OpenSky? | Plan |
|---|---|---|
| Live position, altitude, speed, heading | ✅ | Use `/states/all` |
| Flight path drawn on map | ✅ | `/tracks` (experimental) or accumulate our own from polls |
| Origin -> destination | ❌ | adsbdb lookup by callsign, cached |
| Schedules, ETA, delays | ❌ | Estimate ETA ourselves (distance / speed); paid API later if needed |
| Global coverage | ⚠️ | Strong US/EU/AU; weak over oceans and parts of Africa/Asia |
| Commercial use | ⚠️ | OpenSky terms are aimed at non-commercial/research use (not re-verified here) — **check before launch** |

## Open questions / next experiments
- With an account: confirm 5 s resolution, test `/flights/arrival` for real airport history, and how fresh "yesterday" really is.
- Peak-hour global snapshot (~15:00 UTC) for realistic size/latency.
- adsbdb rate limits and terms.
- OpenSky licence terms for a public app.
