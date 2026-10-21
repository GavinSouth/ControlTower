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

### Next
- **F1.3 Architecture & API design** (new session).
- Before/early in F1.3: user to create a free OpenSky account and API client (credentials into `.env`, never committed) so we can test 5 s resolution and `/flights/*`.
- User to push to GitHub and confirm the CI run is green.
- Open questions: polling cadence vs credits (single region vs global); adsbdb rate limits/terms; OpenSky licence for a public app; peak-hour snapshot size.
