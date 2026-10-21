# ControlTower

An app that tracks flights between locations and returns live tracking data to end users.

**Status:** Phase 1 complete — tooling, data-source research, and architecture/API design are done. The backend has typed stubs; endpoints return 501 until Phase 2 implements them. See [ROADMAP.md](ROADMAP.md) and [docs/](docs/).

**Research:** [OpenSky API Testing/](OpenSky%20API%20Testing/README.md) — live experiments on the OpenSky API (coverage, refresh rate, credit costs, gaps). Verdict: viable for an MVP with a free account, backend-side caching, and a separate callsign->route lookup.

## Architecture
Full design: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- **Backend** (`backend/`): Python 3.13 + FastAPI. A single background poller pulls live aircraft state from [OpenSky](https://opensky-network.org), paced to stay within the daily credit budget (default: global every ~96 s). It also looks up origin -> destination from adsbdb, caches everything in memory, and serves it read-only over `/api/v1`. User requests never hit OpenSky.
- **Providers** sit behind `Protocol` interfaces (`providers/base.py`), so OpenSky can be swapped for a paid API without touching the rest.
- **Web frontend** (`web/`, Phase 3) and **iOS** (later) consume the same HTTP API.

### API (v1)
| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness + age of the cached snapshot |
| `GET /api/v1/flights?bbox=&include_ground=&origin=&destination=` | Live aircraft in a viewport, optionally between two airports |
| `GET /api/v1/flights/{icao24}` | One aircraft's details + route |
| `GET /api/v1/flights/{icao24}/track` | Path so far |

## Tech stack
| Concern | Tool |
|---|---|
| Python + dependencies | [uv](https://docs.astral.sh/uv/) (`backend/uv.lock`) |
| HTTP API | FastAPI (+ Pydantic schemas) |
| HTTP client | httpx (async) |
| Config | pydantic-settings (reads `.env`) |
| Lint + format | ruff |
| Type checking | mypy (strict) |
| Tests | pytest |
| Git hooks | pre-commit |
| CI | GitHub Actions (`.github/workflows/ci.yml`) |

## Setup
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # install uv (once)
uv python install 3.13 --default                  # optional: make 3.13 your default `python3`
cd backend
uv sync                      # creates .venv with Python 3.13 + deps
uv run pre-commit install    # enable git hooks (once)
cp ../.env.example ../.env   # then add OpenSky credentials (never commit .env)
```

## Commands (from `backend/`)
```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest   # all checks
uv run ruff check --fix . && uv run ruff format .                                          # auto-fix
```

## Project layout
```
backend/            Python package + tests
  src/controltower/
    models.py         domain dataclasses (aircraft state, position, airport, route, track)
    providers/        OpenSky + adsbdb adapters behind Protocol interfaces
    polling.py        credit-budget poll interval + poller loop
    store.py          in-memory cache the API reads from
    config.py         settings from env/.env
    api/              FastAPI app factory + response schemas
docs/               ARCHITECTURE.md (design) + HISTORY_P<phase>.md (context log per phase)
.github/workflows/  CI
.claude/            Claude Code settings + /finish-feature skill
.gitignore          secrets (.env), venvs, caches, OS/editor files
OpenSky API Testing/  research sandbox: scripts, notes, raw JSON + CSV data
```
