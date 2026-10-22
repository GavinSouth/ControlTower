# Roadmap

ControlTower is a **trip tracker**. It keeps past and upcoming trips organized as a tree: **Trip → Days → Items** (flights, stays, activities, transport, notes), so every trip can be read day by day.
Flights are entered like any other item. Automatic flight lookup (SerpApi / Google Flights) is low priority and comes last (Phase 7).
Later, an agent keeps a running **trip log ("minutes")** of where you are and what you're doing.

Earlier scopes (live flight tracking via OpenSky; fare comparison via SerpApi/Duffel) were removed on 2026-10-21. Their research and code can be recovered from commit `2580a78`.

## Phase 1 — Foundation & Design  [DONE]
- [x] F1.1 Tooling: uv + Python 3.13 package in `backend/`, ruff/mypy/pytest, pre-commit, GitHub Actions CI, Claude allowlist + `/finish-feature` skill.
- [x] F1.2 Trip domain model & data design. Define the entities and how they relate: Trip, Day, Item nodes (Flight, Stay, Activity, Transport, Note), and LogEntry for the minutes. Cover:
  - Items that span days (a 4-night stay, an overnight flight) and time zones (store UTC + the local zone).
  - Past vs upcoming trips, and planned vs actual (what was booked vs what happened).
  - Choice of database + ORM + migrations (proposal: SQLite to start, Postgres-ready; SQLAlchemy 2.0; Alembic).
  - Output: `docs/ARCHITECTURE.md` with an entity diagram, decisions, and the first API resource list.

## Phase 2 — Backend Core  [DONE]
- [x] F2.1 Database, models, and migrations (from F1.2). SQLAlchemy 2.1 models in `backend/src/controltower/models/`, Alembic initial migration, single-user seed, 16 tests.
- [x] F2.2 Trip API: create/read/update/delete trips, days, and items. FastAPI app in `backend/src/controltower/api/` (trips, items, places, day extras, log); interactive docs at `localhost:8000/docs`; 34 tests.
- [x] F2.3 Day-by-day timeline endpoint (a trip's items grouped per local day). `GET /trips/{id}/timeline` built on the pure `build_timeline()`; 47 tests.

## Phase 3 — Web Frontend  [NEXT]
- [ ] F3.1 TBD: trip list, trip timeline view, add/edit items. **First reviewable local web app.** (From F2.2 on, the interactive API page at `localhost:8000/docs` is reviewable.)

## Phase 4 — Agentic Trip Log  [NOT STARTED]
- [ ] F4.1 Agentic trip log research. Which signals can feed the minutes (manual check-ins, phone location, calendar, booking emails, photos); how an LLM agent turns them into a daily log; privacy and consent. Research only. (Moved from F1.3 so the web app comes first; the `log_entry` table already exists in the design.)
- [ ] F4.2 TBD: build the trip log (scoped after F4.1).

## Phase 5 — iOS  [LATER]
- [ ] F5.1 TBD: SwiftUI or wrapped web app on the same API.

## Phase 6 — Accounts & Sharing  [LATER]
Starts single-user; the data model is ready for these (see `docs/ARCHITECTURE.md`, *Scaling up later*).
- [ ] F6.1 Accounts: login, and each user sees only their own trips.
- [ ] F6.2 Shared trips: trip members with roles (owner/editor/viewer), per-traveller items.

## Phase 7 — Flight Lookup  [LOW PRIORITY]
Optional convenience: find a flight and fill in a Flight item instead of typing it in. Free tier is 250 searches/mo, so use it on demand and cache results.
- [ ] F7.1 SerpApi flight lookup spike: a few real searches; how one result maps onto a Flight item. Research only.
- [ ] F7.2 Flight search & attach: SerpApi adapter behind a provider interface, cached.
