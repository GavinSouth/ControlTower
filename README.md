# ControlTower

A trip tracking app. ControlTower keeps your past and upcoming trips organized and broken down day by day: each **trip** holds **days**, and each day holds **items** such as flights, stays, activities, transport, and notes. When you need a flight, it can look one up (via SerpApi / Google Flights) and attach it to the trip. Later, an agent will keep a running **trip log** ("minutes") of where you are and what you're doing.

**Status:** Phase 1. Tooling is set up. Next: design the trip data model and database (F1.2). See [ROADMAP.md](ROADMAP.md) and [docs/](docs/).

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
The final model is decided in F1.2 (`docs/ARCHITECTURE.md`).

## Architecture (planned)
- **Backend** (`backend/`): Python 3.13 HTTP API over a database of trips, days, and items. A small SerpApi adapter handles on-demand, cached flight lookups.
- **Agentic trip log** (Phase 4): turns signals (check-ins, location, bookings) into a daily log.
- **Web frontend** (`web/`, Phase 3): trip list and day-by-day timeline.
- **iOS** (Phase 5): SwiftUI app or wrapped web app on the same API.

## Tech stack
| Concern | Tool |
|---|---|
| Python + dependencies | [uv](https://docs.astral.sh/uv/) (`backend/uv.lock`) |
| Lint + format | ruff |
| Type checking | mypy (strict) |
| Tests | pytest |
| Git hooks | pre-commit |
| CI | GitHub Actions (`.github/workflows/ci.yml`) |
| Database | TBD in F1.2 (proposal: SQLite → Postgres, SQLAlchemy 2.0, Alembic) |
| Flight lookup | SerpApi Google Flights (free tier 250 searches/mo) |

## Setup
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # install uv (once)
uv python install 3.13 --default                  # optional: make 3.13 your default `python3`
cd backend
uv sync                      # creates .venv with Python 3.13 + deps
uv run pre-commit install    # enable git hooks (once)
cp ../.env.example ../.env   # then add SERPAPI_API_KEY (never commit .env)
```

## Commands (from `backend/`)
```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest   # all checks
uv run ruff check --fix . && uv run ruff format .                                          # auto-fix
```

## Project layout
```
backend/            Python package (src/controltower) + tests
docs/               HISTORY_P<phase>.md (context log per phase), python_research.md (tooling notes)
.github/workflows/  CI
.claude/            Claude Code settings + /finish-feature skill
.gitignore          secrets (.env), venvs, caches, OS/editor files
```

Earlier scopes (live flight tracking, fare comparison) were removed on 2026-10-21. Their research and code are recoverable from commit `2580a78`.
