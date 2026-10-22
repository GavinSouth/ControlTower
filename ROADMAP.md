# Roadmap

ControlTower is a **trip tracker**. It keeps past and upcoming trips organized as a tree: **Trip → Days → Items** (flights, stays, activities, transport, notes), so every trip can be read day by day.
Flights are entered like any other item. Automatic flight lookup (SerpApi / Google Flights) is low priority and comes last (Phase 6).
Later, an agent keeps a running **trip log ("minutes")** of where you are and what you're doing.

Earlier scopes (live flight tracking via OpenSky; fare comparison via SerpApi/Duffel) were removed on 2026-10-21. Their research and code can be recovered from commit `2580a78`.

## Phase 1 — Foundation & Design  [IN PROGRESS]
- [x] F1.1 Tooling: uv + Python 3.13 package in `backend/`, ruff/mypy/pytest, pre-commit, GitHub Actions CI, Claude allowlist + `/finish-feature` skill.
- [ ] F1.2 Trip domain model & data design. Define the entities and how they relate: Trip, Day, Item nodes (Flight, Stay, Activity, Transport, Note), and LogEntry for the minutes. Cover:
  - Items that span days (a 4-night stay, an overnight flight) and time zones (store UTC + the local zone).
  - Past vs upcoming trips, and planned vs actual (what was booked vs what happened).
  - Choice of database + ORM + migrations (proposal: SQLite to start, Postgres-ready; SQLAlchemy 2.0; Alembic).
  - Output: `docs/ARCHITECTURE.md` with an entity diagram, decisions, and the first API resource list.
- [ ] F1.3 Agentic trip log research. Which signals can feed the minutes (manual check-ins, phone location, calendar, booking emails, photos); how an LLM agent turns them into a daily log; privacy and consent. Research only.

## Phase 2 — Backend Core  [NOT STARTED]
- [ ] F2.1 Database, models, and migrations (from F1.2).
- [ ] F2.2 Trip API: create/read/update/delete trips, days, and items.
- [ ] F2.3 Day-by-day timeline endpoint (a trip's items grouped per local day).

## Phase 3 — Web Frontend  [NOT STARTED]
- [ ] F3.1 TBD: trip list, trip timeline view, add/edit items.

## Phase 4 — Agentic Trip Log  [NOT STARTED]
- [ ] F4.1 TBD (scoped after F1.3).

## Phase 5 — iOS  [LATER]
- [ ] F5.1 TBD: SwiftUI or wrapped web app on the same API.

## Phase 6 — Flight Lookup  [LOW PRIORITY]
Optional convenience: find a flight and fill in a Flight item instead of typing it in. Free tier is 250 searches/mo, so use it on demand and cache results.
- [ ] F6.1 SerpApi flight lookup spike: a few real searches; how one result maps onto a Flight item. Research only.
- [ ] F6.2 Flight search & attach: SerpApi adapter behind a provider interface, cached.
