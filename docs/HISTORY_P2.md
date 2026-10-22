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

### Next
- **F2.2 Trip API** (new session, plan mode): FastAPI + Pydantic schemas (separate from ORM models), CRUD for trips/items/places/log entries, dependency-injected sessions. Reviewable at `localhost:8000/docs`. Open: per-kind item create payloads (discriminated union on `kind`), and how a PATCH handles detail fields.
