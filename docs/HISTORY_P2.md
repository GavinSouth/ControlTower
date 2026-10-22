# History — Phase 2 (context log)

Chronological log of every prompt/work item: what was asked, what was done, decisions, and what's next.
ROADMAP.md tracks feature completion; this file is the context a new session needs to pick up where we left off.
Phase 1 (tooling, scope resets, data model design) is in `HISTORY_P1.md`.

---

## 2026-10-21

### F2.1 — Database, models, migrations complete
- Asked: start F2.1. The design was settled in F1.2 (`docs/ARCHITECTURE.md`), so I went straight to implementing it.
- Done:
  - Deps: `sqlalchemy` 2.1.6, `alembic` 1.20.0.
  - `src/controltower/models/`: `types.py`, `base.py`, `enums.py`, `user.py`, `place.py`, `trip.py`, `item.py`, `log.py`.
  - `config.py` (`database_url()`), `db.py` (engine, sessions, owner seed).
  - Alembic: `alembic.ini`, `migrations/env.py`, mako template, initial migration `1f1c2a5323e6`.
  - Tests: `tests/conftest.py`, `test_models.py` (12), `test_migrations.py` (2). 16 pass in total.
  - `backend/data/` added to `.gitignore`.
  - Docs: ARCHITECTURE code map, CLAUDE.md commands, README.
- Decisions:
  - **Joined-table inheritance:** `Item` is `polymorphic_abstract`; Flight/Stay/Transport/Activity each join a `*_detail` table on the same UUID. `Note` has no extra fields, so it lives only in `item`. `select(Item)` returns the right subclasses.
  - **Custom types:**
    - `UTCDateTime` rejects naive datetimes, stores UTC, and returns aware UTC (SQLite would silently drop zones).
    - `TimeZoneName` validates IANA names via `zoneinfo`.
    - `Money` is exact Decimal (text on SQLite, NUMERIC on Postgres). It avoids SQLite float rounding and SQLAlchemy's Decimal warning.
    - Enums are stored as their string values with no CHECK constraint, so adding a member needs no migration.
  - `Base.type_annotation_map` maps every `Mapped[datetime]` to `UTCDateTime` automatically.
  - Constraint naming convention on `MetaData`, plus Alembic `render_as_batch=True`, because SQLite can only alter tables by rebuilding them.
  - `from __future__ import annotations` in model modules: Python 3.13 evaluates annotations eagerly, so `Mapped[list[Trip]]` with TYPE_CHECKING-only imports needs it.
  - Foreign keys: `PRAGMA foreign_keys=ON` on every SQLite connection via an engine event. Deleting a trip cascades to items, details, days, and log entries at the DB level. Deleting an item sets `log_entry.item_id` NULL (the minutes survive). Places are never cascaded.
  - Tests use a fresh SQLite file per test with `create_all`. A separate test runs the real migrations and asserts `compare_metadata` finds no diff, so any model change without a migration fails CI.
  - Migration files are auto-formatted then linted by ruff (Alembic post-write hooks, format before check).
- Verified: ruff, format, mypy strict (12 files), pytest 16 passed. Mutation check: with `foreign_keys=OFF`, exactly the 3 FK tests fail. `uv run alembic upgrade head` created `backend/data/controltower.db` at revision `1f1c2a5323e6`.

### F2.2 — Trip API complete
- Asked: start F2.2. The design and the resource list were already in ARCHITECTURE.md, and the two open questions from F2.1 were settled while building (below).
- Done:
  - Deps: `fastapi` 0.159.1, `uvicorn` 0.54.0. Dev: `httpx2` 2.16.0 (Starlette 1.9's TestClient deprecates `httpx`; with `httpx2` the warning is gone).
  - `src/controltower/trips.py`: computed date range and phase.
  - `src/controltower/api/`: `app.py` (`create_app`), `deps.py`, `schemas.py`, `routes/{trips,items,places,days,log}.py`.
  - Tests: `tests/test_api.py` (15 HTTP tests), `tests/test_trips.py` (3). `conftest.py` gained a `client` fixture. **34 tests pass.**
  - pytest now turns `SAWarning` into errors.
  - Docs: ARCHITECTURE API section + code map, README "Run the API", CLAUDE.md run command.
- Decisions:
  - **Item bodies are a discriminated union on `kind`:** one `POST /trips/{id}/items` and the docs show all five shapes. Field sets are defined once as mixins (`FlightFields`, …) and reused across Create/Patch/Read.
  - **PATCH** = `kind` + only the changed fields (`exclude_unset`). `null` clears an optional field; `PatchSchema.NOT_NULL` blocks nulling required ones. A kind mismatch is a 422 (kind can't change).
  - **Create** uses `exclude_none`, so DB defaults (status, transport mode) apply.
  - All inputs use `extra="forbid"`: a typo or a flight field on a note is a 422.
  - **Times:** `UTCDatetime` = aware datetime normalized to UTC at validation. Naive times are a 422; responses are always UTC.
  - **Rules run after every item create/update** (`apply_item_rules`): places must exist (422), zones are filled from place → trip `home_tz`, and an end can't precede its start.
  - Trip `first_day`/`last_day`/`phase` are computed per response (stored dates win; cancelled items are ignored; local days per item zone).
  - Every lookup is owner-scoped through `deps.py`, so accounts only change `get_owner`.
  - ORM → response for items goes through an explicit `TypeAdapter(ItemRead)` (typed, no `type: ignore`).
- Bugs caught by tests while building:
  1. Responses echoed the input offset instead of UTC: with `expire_on_commit=False` objects aren't reloaded. Fixed by normalizing to UTC in the schema.
  2. A `SAWarning`: in SQLAlchemy 2.x, `Item(trip=trip)` no longer cascades the item into the session. Fixed with `session.add(item)` first.
  3. That fix made the place lookup autoflush an item with a bad `place_id`, giving an FK error instead of a 422. Fixed with `session.no_autoflush` around the lookups.
- Verified: ruff, format, mypy strict (23 files), pytest 34 passed. Ran real uvicorn on the migrated DB: create trip → create stay (times returned in UTC) → trip shows 2027-04-06..10 "upcoming" → `/docs` 200 → delete 204. The smoke-test trip was deleted; the "Me" user remains in `backend/data/controltower.db`.

### F2.3 — Day-by-day timeline complete
- Asked: start F2.3.
- Done:
  - `src/controltower/timeline.py`: the pure `build_timeline(trip) -> Timeline` (Day, Listing, Role, `TimelineTooLongError`).
  - `api/routes/timeline.py`: `GET /trips/{trip_id}/timeline`.
  - Schemas `ListingRead`, `DayRead`, `TimelineRead`. `item_read()` moved into `schemas.py` to be shared.
  - `GET /trips/{id}/items` now eager-loads detail columns too.
  - Tests: `tests/test_timeline.py` (10 unit tests), `tests/test_api_timeline.py` (3). **47 pass.**
  - ARCHITECTURE timeline section + code map, README walkthrough step, ROADMAP: Phase 2 **[DONE]**, Phase 3 **[NEXT]**.
- Decisions (edge cases the design hadn't covered):
  - The range is stored dates, else timed items, widened by log entries and day extras. Every date is a day, including empty ones, numbered from 1.
  - Clipped items keep their true role: a stay that began before the trip's stored start shows `continues` on day 1.
  - Cancelled items are listed but never widen the range. Untimed items go to `unscheduled`.
  - Day order: `continues` first, then by the moment that matters that day (start for starts/single, end for ends).
  - Each listing carries the full item, so a multi-day stay repeats per day. That's simpler for the frontend; the payload is still small.
  - More than 366 days → 422 (guards against a wrong-year typo).
  - `build_timeline` reads everything from the trip (`trip.items`, `log_entries`, `days`), so there's one source of truth instead of separate arguments.
  - **N+1 guard:** the route uses `selectinload(Trip.items).selectin_polymorphic([Flight, Stay, Transport, Activity])` plus selectinloads for log and days. A test counts SELECTs and asserts 5 vs 50 items cost the same. Mutation check: without `selectin_polymorphic` it was **45 vs 9** SELECTs.
- Test fix: my first endpoint test had a hotel check-in (15:00) before the flight landed (15:25), so the rule correctly sorted the hotel first. I fixed the test data, not the rule.
- Verified: ruff, format, mypy strict (25 files), pytest 47 passed. Real uvicorn: a stay 6–8 Apr gave days 1–3 as starts/continues/ends; the smoke trip was deleted.

### Next
- **F3.1 Web frontend** (new session, plan mode): first reviewable app. Decide the stack first, e.g. a React/TypeScript SPA in `web/` (Vite) vs server-rendered pages (FastAPI + Jinja/HTMX). Plus CORS or a dev proxy, the trip list, the timeline view, and add/edit item forms. Phase 3 is logged in `docs/HISTORY_P3.md`.
- Phase 2 closed. Continued in `docs/HISTORY_P3.md`.
