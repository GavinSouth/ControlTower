# Live tracking architecture (F4.2, parked)

> **Parked.** Written for live flight tracking, before the product focus moved to fare search (see ROADMAP). Not being built now. The typed stubs it describes ("Code map") were removed from `backend/`; recover them with `git show 3459315`.

Design for the Phase 2 backend. Typed stubs for everything below live in `backend/src/controltower/`; `backend/tests/test_design.py` pins the contract. Inputs: the F1.2 findings in `OpenSky API Testing/README.md`.

## 1. Shape

```
         OpenSky /states/all            adsbdb /callsign/{cs}
                 │                               │
     ┌───────────▼──────────┐       ┌────────────▼─────────┐
     │ OpenSkyProvider      │       │ AdsbdbRouteProvider  │   providers/  ("adapters")
     │  : StateProvider     │       │  : RouteProvider     │
     └───────────┬──────────┘       └────────────┬─────────┘
                 │  Snapshot                     │  Route | None
            ┌────▼───────────────────────────────▼────┐
            │ Poller (one background task)            │   polling.py
            │  budget-paced, demand-driven, backoff   │
            └────────────────────┬────────────────────┘
                                 │ put_snapshot / put_route
                       ┌─────────▼─────────┐
                       │ FlightStore       │   store.py  (in-memory; Redis later)
                       │ states, tracks,   │
                       │ route cache       │
                       └─────────▲─────────┘
                                 │ read only
                       ┌─────────┴─────────┐
                       │ FastAPI /api/v1   │   api/
                       └─────────▲─────────┘
                                 │ JSON over HTTP
                         web (Phase 3), iOS
```

Rule: **user requests never reach a provider.** One poller spends the credits, so cost grows with time, not users.

## 2. Decisions

| # | Decision | Why |
|---|---|---|
| D1 | Providers sit behind `typing.Protocol` interfaces (`StateProvider`, `RouteProvider`). | Swap OpenSky for a paid API by adding one class. Protocols are structural: any class with the right methods qualifies. Tests use fakes the same way. |
| D2 | Domain models are frozen stdlib dataclasses (`models.py`); API models are separate Pydantic classes (`api/schemas.py`). | The core doesn't depend on a web framework. An internal rename can't silently break the frontends' contract. Frozen = safe to share between the poller and request handlers. |
| D3 | SI units, carried in field names (`baro_altitude_m`, `velocity_mps`). | Matches OpenSky, no conversion bugs in the backend. Frontends convert for display. |
| D4 | `icao24` (transponder hex) is the aircraft key; callsign is an attribute. | Stable and always present. Callsigns can be missing (2.5%) or reused. |
| D5 | Single process, in-memory `FlightStore`. | Simplest thing that works for an MVP. The Protocol leaves room for Redis if we run several workers. |
| D6 | FastAPI + httpx (async), pydantic-settings for config. | FastAPI generates OpenAPI docs at `/docs` that web/iOS can generate clients from. httpx is the async HTTP client FastAPI's ecosystem uses. Settings are validated at startup. |
| D7 | Clients poll `GET /api/v1/flights` and **dead-reckon** between updates (position + speed + heading). | Backend data updates every ~24–96 s, so polling HTTP is enough. Markers move smoothly anyway. SSE/WebSocket later, same payload shapes. |
| D8 | Track history built from **our own polls**, not `/tracks`. | Free, and covers every aircraft. `/tracks` is experimental and costs credits. It can backfill tracks for aircraft we only just started seeing. |
| D9 | Route lookups are lazy, cached 24 h, **misses cached too**. | adsbdb is free and community-run, so we're polite. Private `N…` callsigns never resolve, so don't keep asking. |
| D10 | Unimplemented endpoints return **501**, not 500. | The contract can be exercised end to end before Phase 2 fills it in. |

## 3. Polling strategy

`poll_interval_s()` = the slower of the provider's resolution (5 s with an account, 10 s anonymous) and `86400 / (daily_credits × (1 − reserve) / cost_per_poll)`. By default 10% of credits are kept in reserve for retries and on-demand calls.

| Area polled | Credits/poll | Free account (4,000/day) | Anonymous (400/day) |
|---|---|---|---|
| ≤ 25 sq° (one metro, e.g. NYC) | 1 | every **24 s** | every 4 min |
| ≤ 100 sq° | 2 | 48 s | 8 min |
| ≤ 400 sq° | 3 | 72 s | 12 min |
| > 400 sq° or global | 4 | **96 s** | 16 min |

**MVP default: global every ~96 s** (`POLL_BBOX` empty). A region costs as much as the whole world once it's bigger than about 20°×20°, so global wins unless we focus on a single metro. Set `POLL_BBOX` to a ≤25 sq° box for 24 s freshness over one area.

The poller loop (Phase 2, documented in `polling.py`):
1. **Demand-driven:** if no API request has arrived in `IDLE_PAUSE_S` (10 min), skip polling. Overnight idle time costs nothing.
2. Successful fetch → `store.put_snapshot()`. Record `X-Rate-Limit-Remaining`.
3. 429 → wait `X-Rate-Limit-Retry-After-Seconds`. Other errors → exponential backoff. Keep serving the last snapshot; `data_age_s` in responses tells clients it's stale.
4. Credits below the reserve → stretch the interval for the rest of the UTC day.
5. New callsigns → queue rate-limited route lookups.

Staleness: aircraft not heard from in `STALE_AFTER_S` (60 s; F1.2 p90 was 59 s) are left out of responses.

## 4. HTTP contract (v1)

All responses are JSON. Times are unix seconds (UTC). Interactive schema at `/docs` once running.

| Method & path | Query | Returns |
|---|---|---|
| `GET /health` | — | `{status, snapshot_time}` |
| `GET /api/v1/flights` | `bbox=lat_min,lon_min,lat_max,lon_max` (viewport), `include_ground=false`, `origin=KJFK`, `destination=EGLL` | `FlightList` |
| `GET /api/v1/flights/{icao24}` | — | `FlightDetail`, or 404 if not live |
| `GET /api/v1/flights/{icao24}/track` | — | `TrackOut` (oldest first), or 404 |

`origin`/`destination` give us "flights between locations". They only match flights whose route is already known (D9). Coverage grows as the poller enriches callsigns.

```jsonc
// GET /api/v1/flights?bbox=39,-76,43,-71
{
  "snapshot_time": 1792561585,
  "data_age_s": 12,
  "count": 1,
  "flights": [{
    "icao24": "a1b2c3", "callsign": "DAL2646",
    "latitude": 41.2, "longitude": -72.9, "baro_altitude_m": 10000.0,
    "velocity_mps": 230.0, "true_track_deg": 225.0, "vertical_rate_mps": 0.0,
    "on_ground": false, "last_contact": 1792561585,
    "origin_icao": "KPVD", "destination_icao": "KATL"
  }]
}
// GET /api/v1/flights/a1b2c3 adds: origin_country, geo_altitude_m, squawk,
//   route: {airline, origin: {icao, iata, name, latitude, longitude}, destination: {...}}
```

Errors: `422` bad query (e.g. inverted bbox), `404` unknown aircraft, `501` not yet implemented.

## 5. Code map

| File | Role | F1.3 status |
|---|---|---|
| `models.py` | Domain dataclasses: `BoundingBox`, `Position`, `AircraftState`, `Snapshot`, `Airport`, `Route`, `Track`, `Flight` | done |
| `providers/base.py` | `StateProvider`, `RouteProvider` Protocols; `ProviderError`, `RateLimitedError`, `FetchResult` | done |
| `providers/opensky.py` | OpenSky adapter: `credit_cost()` real; OAuth2 + fetch stubbed | stub |
| `providers/adsbdb.py` | adsbdb route adapter | stub |
| `polling.py` | `poll_interval_s()` real; `Poller` loop stubbed | partial |
| `store.py` | `FlightStore` Protocol + `InMemoryFlightStore` stub | stub |
| `config.py` | `Settings` from env / `.env` | done |
| `api/schemas.py`, `api/app.py` | Response models, `create_app()` factory, endpoints | contract done; data via store |

## 6. Open questions (carry into Phase 2)
- **Not yet verified with an account** (no `.env` yet): 5 s resolution, OAuth2 token flow, `/flights/*` freshness.
- OpenSky licence for a public app; adsbdb rate limits and terms.
- Peak-hour global payload (~2× the 790 KB quiet-hour snapshot): parse cost and memory.
- If we focus on one metro, which one? (Changes the default from global/96 s to box/24 s.)
- Starlette now warns that `TestClient` on `httpx` is deprecated in favour of `httpx2`. Harmless for now; revisit when FastAPI's docs settle.
