# History — Phase 1 (context log)

Chronological log of every prompt/work item: what was asked, what was done, decisions, and what's next.
ROADMAP.md tracks feature completion; this file is the context a new session needs to pick up where we left off.

---

## 2026-10-20 — Session 1

### Plan-mode walkthrough → F1.1 planned
- Asked: first project with Claude; explain plan mode.
- Done: read CLAUDE/ROADMAP/HISTORY/README (repo was empty scaffolding). Asked 4 setup questions; wrote plan to `~/.claude/plans/okay-this-is-my-zesty-wilkes.md`; approved.
- Decisions (user): **OpenSky Network** as data source; **web-first, iOS later** (Python HTTP API serves both); **uv + ruff + pytest + mypy**; Claude helpers = permissions allowlist, `/finish-feature` skill, GitHub Actions CI.

### F1.1 — Tooling setup (commit `73afe81`)
- Done: installed uv 0.13.4 to `~/.local/bin` (machine had only system Python 3.9, no Homebrew). Scaffolded `backend/` (Python 3.13.16, `src/controltower`, `tests/test_smoke.py`). Configured ruff (line 100; rules E,W,F,I,B,UP,SIM,N), mypy strict on `src/`, pytest in `backend/pyproject.toml`. Added `.pre-commit-config.yaml`, `.github/workflows/ci.yml`, `.claude/settings.json`, `.claude/skills/finish-feature/SKILL.md`, `.env.example`. Filled CLAUDE.md Environment/Layout/Commands.
- Decisions: backend lives in `backend/` so `web/` and `ios/` can be siblings. Pre-commit hooks call `uv run` so local, hook, and CI tool versions all come from `uv.lock`. `.claude/settings.json` denies Claude reading `.env`. Smoke test uses a typed `pytest.CaptureFixture[str]` rather than a `type: ignore`.
- Verified: ruff, format, mypy, pytest (2 passed), pre-commit all green. CI not yet run (needs a push).

### Q&A + `.gitignore` + default Python (commit `b4923a2`)
- Asked: what is CI; install Python 3.13 system-wide; explain uv/ruff/lint/mypy/pytest/.toml; does `.gitignore` need to be at root. User changed the CLAUDE.md rule so **Claude now manages `.gitignore`**.
- Done: `uv python install 3.13 --default` → `python`/`python3`/`python3.13` in `~/.local/bin` point to 3.13.16 (user-wide; Apple's `/usr/bin/python3` 3.9 untouched — true machine-wide needs the python.org installer + admin). Project venv already used the same interpreter, so no path change. Created root `.gitignore` (secrets, venvs, caches, `.claude/settings.local.json`, OS/editor files).
- Notes: one root `.gitignore` covers the repo; nested ones only add folder-specific rules. User saved the terms explanation in `docs/python_research.md`.

### HISTORY naming check
- User renamed history references in CLAUDE.md to `HISTORY_x.md` / `HISTORY_Px.md`. Confirmed consistent with actual file `docs/HISTORY_P1.md`. No change needed.

### OpenSky API experiments (anonymous, no account)
- Asked: before committing to anything, find out what OpenSky gives us, how often, and whether it meets project needs.
- Findings:
  - `/states/all` works anonymously. Global snapshot: 6,103 aircraft (5,431 airborne) at 05:46 UTC (quiet hour), ~790 KB, ~1.3 s. 97.5% have callsign, 99% have position; median data age 0 s, p90 59 s.
  - Refresh: ~10 s anonymous (5 s polls returned duplicates; 10 s polls did not). 5 s with account.
  - Credits: bbox ≤25 sq° = 1, global = 4. Anonymous 400/day, free account 4,000/day, feeder 8,000/day.
  - `/flights/*` = 403 anonymously; need account and are batched **nightly** (yesterday or older). `/tracks/all?time=0` (live path) works anonymously.
  - No live origin/destination, schedules, or ETAs. adsbdb.com (free) resolved 7/10 callsigns to routes; misses were private `N…` aircraft.
  - Licence (unverified): OpenSky aimed at non-commercial/research use — check before public launch.
- Verdict: **viable for MVP** if we (1) create a free account, (2) poll once in the backend and fan out to users, (3) add a callsign→route source, (4) keep the provider behind an interface for a future paid swap (e.g. FlightAware).

### Research folder (commit `05fe146`) → F1.2 complete
- Asked: save the scripts, results, notes, and data as CSV into a browsable folder.
- Done: `OpenSky API Testing/` with `README.md` (full findings), `scripts/` (stdlib-only `opensky.py` helper + `01_snapshot` … `05_route_lookup`, `convert_raw_to_csv`), `data/raw/*.json` and `data/*.csv`. All scripts re-run successfully; linted with ruff. ~12 of 400 anonymous credits used.
- Decision: research lives outside `backend/` (sandbox, not production code; not covered by pre-commit/CI).

### Workflow change
- User changed CLAUDE.md Workflow: **HISTORY = context log** updated on every prompt/work item; **ROADMAP = feature completion log**. Confirmed with user: still commit at end of each feature (user pushes); OpenSky research inserted as F1.2 (done), architecture renumbered to F1.3.
- Done: rewrote this file as a session log; updated ROADMAP; fixed dangling end-of-feature line in CLAUDE.md; updated `/finish-feature` skill to match.

### How to start a new session
- Asked: best practice for starting a new session.
- Answered: commit, push, then `/clear` or exit and run `claude`. Begin in plan mode with "Resume work" or "Start F1.3". CLAUDE.md loads automatically and points to ROADMAP + HISTORY. Use `--continue`/`--resume` only to pick up an interrupted conversation, not to start a new feature.

### Session 2 — `--continue` → F1.3 started
- Asked: `--continue` (resume). Took the next unchecked feature, F1.3. No `.env` yet, so design proceeded without authenticated OpenSky tests; flagged as carried over.

### F1.3 — Architecture & API design complete
- Done: `docs/ARCHITECTURE.md` (diagram, decisions D1–D10, polling budget table, HTTP contract, code map, open questions). Typed stubs in `backend/src/controltower/`: `models.py`, `config.py`, `polling.py`, `store.py`, `providers/{base,opensky,adsbdb}.py`, `api/{app,schemas}.py`. Added deps `fastapi`, `httpx`, `pydantic-settings`; enabled the `pydantic.mypy` plugin. `tests/test_design.py` (13 tests) pins the contract with a fake store and covers the credit tiers and poll-interval math. Extended `.env.example` with tuning knobs. 15 tests pass; ruff + mypy strict clean.
- Decisions: Protocol interfaces for providers/store (swappable, easy fakes). Frozen dataclass domain models kept separate from Pydantic API schemas. SI units in field names. `icao24` as key. Single process + in-memory store. Clients poll and dead-reckon (no WebSocket yet). Tracks built from our own polls. Route cache 24 h including misses. Stubs return HTTP 501. Default poll: **global every 96 s** (4000 credits, 10% reserve, 4 credits/poll), because any box over 400 sq° costs the same as global. Demand-driven pause after 10 min idle.
- Real logic already in place: `credit_cost()`, `poll_interval_s()`, `BoundingBox` validation, bbox query parsing, domain→schema converters. Everything else raises `NotImplementedError("Phase 2")`.
- Notes: corrected my own test arithmetic (box interval is 24 s with the reserve, not 22 s). Starlette warns that `TestClient` on `httpx` is deprecated in favour of `httpx2`; left as is.

### Scope reset: fare search first, tracking parked
- Asked: slow down. The first product is **flight fares**: the user picks two airports and dates and gets a list of flights with current prices. Tracking comes later. Research a fare API (as we did with OpenSky) before any development.
- Done: rewrote ROADMAP. New **F1.2 = fare data source research** (unchecked). The OpenSky research and tracking design moved to **Phase 4 — Live Flight Tracking [PARKED]** as F4.1 (was F1.2) and F4.2 (was F1.3). Earlier entries in this log keep the old numbers. Marked `docs/ARCHITECTURE.md` as parked; reframed README. No code removed: the tracking stubs and `fastapi`/`httpx`/`pydantic-settings` deps stay in `backend/` (commit `3459315`).
- Lesson: on `--continue` I moved straight into a whole feature without checking in. From now on, confirm scope before starting a feature.

### Clean backend + CLAUDE.md purpose
- Asked: (1) remove the parked tracking code so the backend starts clean; (2) update CLAUDE.md Purpose.
- Done: deleted `models.py`, `config.py`, `polling.py`, `store.py`, `providers/`, `api/`, `tests/test_design.py`. Removed the `fastapi`, `httpx`, `pydantic-settings` deps and the `pydantic.mypy` plugin. Backend is back to the F1.1 skeleton. All of it can be recovered from commit `3459315`. Renamed `docs/ARCHITECTURE.md` → `docs/TRACKING_ARCHITECTURE.md` (parked; frees the name for the fare design). CLAUDE.md Purpose is now fare search (tracking later); its Environment data source is "fare API, TBD in F1.2". `.env.example`: OpenSky lines commented out as parked, placeholder for fare API keys. README/ROADMAP updated to match.

### Branching: work on `main`
- Decision (user): day-to-day work happens on **`main`**. `development` is reserved for large, risky feature experiments once the app is live. PR #2 merged `development` into `main`; commit `fb3893d` (scope reset) is on `main`.

### Next
- **F1.2 Fare data source research** (new session): first bring the user a shortlist of flight-price APIs with trade-offs; pick one or two together; then write test scripts. Research only, no backend code.
- User to push to GitHub and confirm the CI run is green.
