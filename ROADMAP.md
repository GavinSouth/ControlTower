# Roadmap

ControlTower is a **trip tracker**. It keeps past and upcoming trips organized as a tree: **Trip → Days → Items** (flights, stays, activities, transport, notes), so every trip can be read day by day.
Flight search through SerpApi (Google Flights) is used **occasionally**, to find a flight and attach it to a trip, not as the core product.
Later, an agent keeps a running **trip log ("minutes")** of where you are and what you're doing.

Earlier scopes (live flight tracking via OpenSky; fare comparison via SerpApi/Duffel) were removed on 2026-10-21. Their research and code can be recovered from commit `2580a78`.

## Phase 1 — Foundation & Design  [IN PROGRESS]
- [x] F1.1 Tooling: uv + Python 3.13 package in `backend/`, ruff/mypy/pytest, pre-commit, GitHub Actions CI, Claude allowlist + `/finish-feature` skill.
- [ ] F1.2 Trip domain model & data design. Define the entities and how they relate: Trip, Day, Item nodes (Flight, Stay, Activity, Transport, Note), and LogEntry for the minutes. Cover:
  - Items that span days (a 4-night stay, an overnight flight) and time zones (store UTC + the local zone).
  - Past vs upcoming trips, and planned vs actual (what was booked vs what happened).
  - Choice of database + ORM + migrations (proposal: SQLite to start, Postgres-ready; SQLAlchemy 2.0; Alembic).
  - Output: `docs/ARCHITECTURE.md` with an entity diagram, decisions, and the first API resource list.
- [ ] F1.3 SerpApi flight lookup spike. A few real searches (free tier: 250/mo). How one result maps onto a Flight item; budget rules (on-demand only, cache results). Research only, no backend code.
- [ ] F1.4 Agentic trip log research. Which signals can feed the minutes (manual check-ins, phone location, calendar, booking emails, photos); how an LLM agent turns them into a daily log; privacy and consent. Research only.

## Phase 2 — Backend Core  [NOT STARTED]
- [ ] F2.1 Database, models, and migrations (from F1.2).
- [ ] F2.2 Trip API: create/read/update/delete trips, days, and items.
- [ ] F2.3 Day-by-day timeline endpoint (a trip's items grouped per local day).
- [ ] F2.4 Flight search & attach: SerpApi adapter behind a provider interface, cached.

## Phase 3 — Web Frontend  [NOT STARTED]
- [ ] F3.1 TBD: trip list, trip timeline view, add/edit items.

## Phase 4 — Agentic Trip Log  [NOT STARTED]
- [ ] F4.1 TBD (scoped after F1.4).

## Phase 5 — iOS  [LATER]
- [ ] F5.1 TBD: SwiftUI or wrapped web app on the same API.
