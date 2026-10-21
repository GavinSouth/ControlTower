# ControlTower

An app for comparing flight prices: pick two airports and your dates, and see a list of flights with current fares. Live flight tracking is planned for later.

**Status:** Phase 1. Tooling is set up. In progress: F1.2, hands-on testing of two flight-price APIs (SerpApi Google Flights and Duffel) before any backend is built. Earlier live-tracking work (OpenSky research, tracking design) is parked under Phase 4. See [ROADMAP.md](ROADMAP.md) and [docs/](docs/).

**Research (fares, in progress):** [Fare API Testing/](Fare%20API%20Testing/README.md): scripts comparing SerpApi (Google Flights) and Duffel on search results, airport lookup, price freshness, cost, and terms.

**Research (tracking, parked):** [OpenSky API Testing/](OpenSky%20API%20Testing/README.md) — live experiments on the OpenSky API (coverage, refresh rate, credit costs, gaps). Verdict: viable for an MVP with a free account, backend-side caching, and a separate callsign->route lookup.

## Architecture (planned)
- **Backend** (`backend/`): Python 3.13. Calls a flight-fare API (chosen in F1.2) and serves search results over an HTTP API.
- **Web frontend** (`web/`, Phase 3): airport search, date picker, list of priced flights.
- **iOS** (later): SwiftUI app or wrapped web app on the same API.

The parked live-tracking design is in [docs/TRACKING_ARCHITECTURE.md](docs/TRACKING_ARCHITECTURE.md).

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
cp ../.env.example ../.env   # then add API credentials (never commit .env)
```

## Commands (from `backend/`)
```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest   # all checks
uv run ruff check --fix . && uv run ruff format .                                          # auto-fix
```

## Project layout
```
backend/            Python package (src/controltower) + tests
docs/               HISTORY_P<phase>.md (context log per phase), TRACKING_ARCHITECTURE.md (parked)
.github/workflows/  CI
.claude/            Claude Code settings + /finish-feature skill
.gitignore          secrets (.env), venvs, caches, OS/editor files
Fare API Testing/     F1.2 research sandbox: fare API scripts, raw JSON + CSV data, findings
OpenSky API Testing/  parked tracking research: scripts, notes, raw JSON + CSV data
```
