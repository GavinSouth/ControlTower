# Roadmap

## Phase 1 — Project Structure & Scope  [IN PROGRESS]
- [x] F1.1 Identify and set up the tools, skills, and processes necessary for the project.
  uv + Python 3.13 package in `backend/`, ruff/mypy/pytest, pre-commit, GitHub Actions CI, Claude allowlist + `/finish-feature` skill.
  Follow-ups: Claude-managed root `.gitignore`; Python 3.13 set as user-wide default via uv.
- [x] F1.2 Data source research — test the OpenSky API (coverage, refresh rate, credit costs, endpoint access) and judge fit for the project.
  Verdict: viable for MVP with a free account, backend-side polling/caching, and a callsign→route source (adsbdb). Findings, scripts, and CSV data in `OpenSky API Testing/`.
- [ ] F1.3 Architecture & API design — define the flight-data provider interface (OpenSky first, swappable), core data models (flight, position, airport, route), polling/caching strategy within credit limits, and the FastAPI endpoint contract the web/iOS frontends will consume. Output: design doc + typed stubs.
  Prereq: free OpenSky account + API client credentials in `.env`.

## Phase 2 — Initialize & Test Backend  [NOT STARTED]
- [ ] F2.1 TBD

## Phase 3 — Web Frontend Development  [NOT STARTED]
- [ ] F3.1 TBD