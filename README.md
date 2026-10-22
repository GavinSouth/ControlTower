# ControlTower

A trip tracking app. ControlTower keeps your past and upcoming trips organized and broken down day by day: each **trip** holds **days**, and each day holds **items** such as flights, stays, activities, transport, and notes. Later, an agent will keep a running **trip log** ("minutes") of where you are and what you're doing. Automatic flight lookup (SerpApi) is a low-priority extra at the end of the roadmap; flights are entered by hand until then.

**Status:** Phase 2 in progress. Tooling (F1.1), data model design (F1.2), database (F2.1), and **trip API (F2.2)** done. You can create trips, items, places, day extras, and log entries from the interactive API page (see *Run the API*). Design: see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (entities, day-by-day timeline rule, DB conventions, API draft). Next: F2.3 day-by-day timeline, then the web app (F3.1). See [ROADMAP.md](ROADMAP.md) and [docs/](docs/).

## How a trip is organized (planned)
```
Trip  "Japan, Apr 2027"
├── Day 1  (Tue 6 Apr, Tokyo)
│   ├── Flight  SFO → HND  UA 837
│   ├── Transport  HND → hotel
│   └── Stay  Hotel X (4 nights, spans Day 1–5)
├── Day 2
│   ├── Activity  Tsukiji market
│   └── Log  "09:40 arrived at the market, ..."   ← agentic minutes (later)
└── ...
```
Items that span days (stays, overnight flights) are stored once and appear on every day they touch; days are derived, not stored. Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Architecture (planned)
- **Backend** (`backend/`): Python 3.13 FastAPI HTTP API over a SQLite database of trips, items, places, day extras, and log entries.
- **Agentic trip log** (Phase 4): turns signals (check-ins, location, bookings) into a daily log.
- **Web frontend** (`web/`, Phase 3): trip list and day-by-day timeline.
- **iOS** (Phase 5): SwiftUI app or wrapped web app on the same API.
- **Accounts & sharing** (Phase 6): single-user until then; the model already has trip owners.
- **Flight lookup** (Phase 7, low priority): SerpApi adapter, on demand and cached.

## Tech stack
| Concern | Tool |
|---|---|
| Python + dependencies | [uv](https://docs.astral.sh/uv/) (`backend/uv.lock`) |
| Lint + format | ruff |
| Type checking | mypy (strict) |
| Tests | pytest |
| Git hooks | pre-commit |
| CI | GitHub Actions (`.github/workflows/ci.yml`) |
| Database | SQLite (Postgres-ready) + SQLAlchemy 2.1 + Alembic |
| HTTP API | FastAPI + Pydantic 2, served by uvicorn |
| Flight lookup (Phase 7) | SerpApi Google Flights (free tier 250 searches/mo) |

## Setup
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # install uv (once)
uv python install 3.13 --default                  # optional: make 3.13 your default `python3`
cd backend
uv sync                      # creates .venv with Python 3.13 + deps
uv run pre-commit install    # enable git hooks (once)
uv run alembic upgrade head  # create/upgrade the local database (backend/data/controltower.db)
cp ../.env.example ../.env   # only needed for Phase 7 flight lookup (never commit .env)
```

## Run the API (from `backend/`)
```bash
uv run alembic upgrade head                            # once, and after pulling new migrations
uv run uvicorn controltower.api.app:app --reload       # then open http://localhost:8000/docs
```
On `/docs` you can try every endpoint in the browser ("Try it out"). A good first path:
1. `POST /trips` with a title and home time zone.
2. `POST /places` to add an airport or hotel.
3. `POST /trips/{trip_id}/items` with a `kind` (flight, stay, transport, activity, note).
4. `GET /trips/{trip_id}` to see the computed dates and phase.

Times accept any offset (e.g. `2027-04-05T11:05:00-07:00`) and come back in UTC.

## Commands (from `backend/`)
```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest   # all checks
uv run ruff check --fix . && uv run ruff format .                                          # auto-fix
uv run alembic upgrade head                                     # apply migrations
uv run alembic revision --autogenerate -m "add X"               # after changing a model; review the file
```

## Project layout
```
backend/            Python package (src/controltower: models/, api/, trips.py, db.py, config.py), migrations/ (Alembic), tests/
docs/               ARCHITECTURE.md (data model), HISTORY_P<phase>.md (context log per phase), python_research.md (tooling notes)
.github/workflows/  CI
.claude/            Claude Code settings + /finish-feature skill
.gitignore          secrets (.env), venvs, caches, OS/editor files
```

Earlier scopes (live flight tracking, fare comparison) were removed on 2026-10-21. Their research and code are recoverable from commit `2580a78`.
