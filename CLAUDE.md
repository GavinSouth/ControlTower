# Project: ControlTower

## Purpose
This repo / app contains the first iteration of a system that:
1. tracks flights between locations and returns live data tracking for end users. 

(Scope will increase in time)

## Environment
Backend:
- Python 3.13, managed by **uv** (deps + interpreter; lockfile `backend/uv.lock`)
- **ruff** (lint + format), **mypy** (strict, `src/`), **pytest**, **pre-commit**
- Data source: **OpenSky Network** REST API (credentials in `.env`, see `.env.example`)

Frontend:
- Web first (Phase 3), iOS later (SwiftUI or wrapped web app). Python backend exposes an HTTP API that both consume.

## Layout
- `backend/` — Python package (`src/controltower/`), tests (`tests/`), `pyproject.toml` (tool config)
- `docs/` — `HISTORY_P<phase>.md` per phase
- `.github/workflows/ci.yml` — CI: lint, format, types, tests on push/PR
- `.claude/` — project settings (permission allowlist) and skills (`/finish-feature`)
- `web/`, `ios/` — future frontends

## Commands
Run from `backend/`:
- Setup: `uv sync`
- All checks: `uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest`
- Auto-fix: `uv run ruff check --fix . && uv run ruff format .`
- Hooks: `uv run pre-commit install` (once), `uv run pre-commit run --all-files`
- End of feature: `/finish-feature`

## Rules
- Never paste credentials into CLAUDE.md or elsewhere.
- After each prompt take time to rewrite/update the project README.md and update new features, context, or information about the codebase. Each time there's a change. 

## Workflow
- The plan lives in ROADMAP.md; recent history in docs/HISTORY_x.md. Read both at session start.
- I'll add updates to ROADMAP.md myself but if I prompt you for a feature or task, add it to the appropriate phase and describe it. Tasks and features are sequential so jump to the next unchecked feature or task if you're asked to resume work.
- Work one feature (e.g. F1.1) per session unless told otherwise. Then prompt for new session to start next feature.
- At the end of a feature: run lint + tests, tick the box in ROADMAP.md,
append a dated entry to the correct docs/HISTORY_x.md (what changed, decisions, next step), then commit - I'll push.
- HISTORY_x.md files will be named based off the phase of work. Write your updates (what changed, decisions, next step) to the appropriate place.
- After sessions end and feature development, inform me of the decisions and tooling very concisely and provide a path to the file where work was done. Then, prepare and anticipate to expound on code changes. I want to learn best practices and deepen my understanding.