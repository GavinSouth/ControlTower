# Project: ControlTower

## Purpose
ControlTower is a trip tracking app and system:
1. Records past and upcoming trips (single user first; accounts and shared trips later, ROADMAP Phase 6) in a backend database, organized as nodes: Trip → Days → Items (flights, stays, activities, transport, notes), so each trip breaks down day by day.
2. Later: an agent tracks where the traveller is and what they're doing, and keeps a running trip log ("minutes").

Low priority, last (ROADMAP Phase 7): automatic flight lookup via SerpApi (Google Flights) to fill in Flight items. Until then, flights are entered manually like any other item.

(Scope will increase in time)

## Environment
Backend:
- Python 3.13, managed by **uv** (deps + interpreter; lockfile `backend/uv.lock`)
- **ruff** (lint + format), **mypy** (strict, `src/`), **pytest**, **pre-commit**
- Database: SQLite (Postgres-ready) + SQLAlchemy 2.0 + Alembic; data model in `docs/ARCHITECTURE.md`
- Flight lookup (low priority, Phase 7): SerpApi Google Flights (`SERPAPI_API_KEY` in `.env`, see `.env.example`)

Frontend (`web/`):
- Node 24 LTS (user-level at `~/.local/share/node`, symlinked into `~/.local/bin`), npm
- React 19 + TypeScript 6 + Vite 8 + Tailwind 4; React Router; TanStack Query; `openapi-fetch` with types generated from the API (`openapi-typescript`); `@date-fns/tz` for zone conversion
- **oxlint** (lint), `tsc` (types), **Vitest** + Testing Library (tests)
- iOS later (SwiftUI or wrapped web app) on the same HTTP API

## Layout
- `backend/` — Python package (`src/controltower/`: `models/`, `api/`, `trips.py`, `db.py`, `config.py`), `migrations/` (Alembic), tests (`tests/`), `pyproject.toml` (tool config); local DB in `backend/data/` (git-ignored)
- `docs/` — `HISTORY_P<phase>.md` context log per phase; `ARCHITECTURE.md` (from F1.2); `python_research.md` (user's tooling notes)
- `.github/workflows/ci.yml` — CI: lint, format, types, tests on push/PR
- `.claude/` — project settings (permission allowlist) and skills (`/finish-feature`)
- `web/` — React app (`src/api`, `src/lib`, `src/components`, `src/pages`); `openapi.json` + generated types
- `ios/` — future

## Commands
Run from `backend/`:
- Setup: `uv sync`
- All checks: `uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest`
- Auto-fix: `uv run ruff check --fix . && uv run ruff format .`
- Hooks: `uv run pre-commit install` (once), `uv run pre-commit run --all-files`
- Run the API: `uv run uvicorn controltower.api.app:app --reload` → http://localhost:8000/docs
- DB migrate: `uv run alembic upgrade head` (creates/updates `backend/data/controltower.db`)
- New migration after a model change: `uv run alembic revision --autogenerate -m "<what>"`, then review the file; `tests/test_migrations.py` fails if models and migrations disagree
- Demo data: `uv run python -m controltower.demo` (adds "Japan (demo)" once)
- End of feature: `/finish-feature`

Run from `web/`:
- Setup: `npm install`
- Dev server: `npm run dev` → http://localhost:5173 (proxies `/api` to the API on :8000, so run both)
- All checks: `npm run lint && npm run typecheck && npm test && npm run build`
- After any API change: `npm run gen:api` and commit `openapi.json` + `src/api/schema.d.ts` (backend test `test_openapi.py` fails if stale)

## Rules
- Never paste credentials into CLAUDE.md or elsewhere.
- After each prompt take time to rewrite/update the project README.md and update new features, context, or information about the codebase. Each time there's a change. 

## Workflow
- The plan lives in ROADMAP.md; recent history in docs/HISTORY_Px.md. Read both at session start.
- I'll add updates to ROADMAP.md myself but if I prompt you for a feature or task, add it to the appropriate phase and describe it. Tasks and features are sequential so jump to the next unchecked feature or task if you're asked to resume work.
- Work one feature (e.g. F1.1) per session unless told otherwise. Then prompt for new session to start next feature.
- At the end of a feature: run lint + tests, tick the box in ROADMAP.md, then commit - I'll push.
- Any time work or something is prompted or done, add a concise but realistic update in the docs/HISTORY_Px.md. We're going to use this file as a context log and ROADMAP as a feature completion log. 
- After sessions end and feature development, inform me of the decisions and tooling very concisely and provide a path to the file where work was done. Then, prepare and anticipate to expound on code changes. I want to learn best practices and deepen my understanding.