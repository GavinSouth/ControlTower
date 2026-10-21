# ControlTower

An app that tracks flights between locations and returns live tracking data to end users.

**Status:** Phase 1 — project setup. Tooling is in place; flight logic begins in Phase 2. See [ROADMAP.md](ROADMAP.md) and [docs/](docs/).

## Architecture (planned)
- **Backend** (`backend/`): Python 3.13. Pulls live aircraft state from the [OpenSky Network](https://opensky-network.org) API and serves it over an HTTP API.
- **Web frontend** (`web/`, Phase 3): browser UI consuming the backend API.
- **iOS** (later): SwiftUI app or wrapped web app on the same API.

## Tech stack
| Concern | Tool |
|---|---|
| Python + dependencies | [uv](https://docs.astral.sh/uv/) (`backend/uv.lock`) |
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
backend/            Python package (src/controltower) + tests
docs/               HISTORY_P<phase>.md — dated log per phase
.github/workflows/  CI
.claude/            Claude Code settings + /finish-feature skill
.gitignore          secrets (.env), venvs, caches, OS/editor files
```
