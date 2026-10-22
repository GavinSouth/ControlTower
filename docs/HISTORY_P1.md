# History — Phase 1 (context log)

Chronological log of every prompt/work item: what was asked, what was done, decisions, and what's next.
ROADMAP.md tracks feature completion; this file is the context a new session needs to pick up where we left off.
The detailed log of the earlier scopes was condensed on 2026-10-21; the full version is in git history (commit `2580a78`).

---

## Carried over from earlier scopes (2026-10-20 → 21)

### Tooling & workflow (still current)
- **F1.1 done** (commits `73afe81`, `b4923a2`): uv 0.13.4 in `~/.local/bin`; Python 3.13.16 is the user-wide default (`uv python install 3.13 --default`; Apple's 3.9 untouched). `backend/` package with ruff (line 100; E,W,F,I,B,UP,SIM,N), mypy strict on `src/`, pytest, pre-commit hooks via `uv run`, GitHub Actions CI, `.claude/settings.json` allowlist (denies reading `.env`), `/finish-feature` skill. Claude manages the root `.gitignore`.
- **Workflow:** HISTORY = context log, updated on every prompt; ROADMAP = feature completion log. Commit at the end of each feature; the user pushes. Work on `main` (`development` only for risky experiments after launch). New feature = new session, starting in plan mode.
- **Lesson:** confirm scope before starting a feature, take small steps, and test data sources before building around them.

### Superseded scopes (removed)
1. **Live flight tracking** (OpenSky Network): researched and designed, then parked. Verdict: viable with a free account and backend polling.
2. **Fare comparison** (pick two airports and dates → priced flight list). Shortlist: Amadeus Self-Service shut down (Jul 2026), Kiwi invite-only, Skyscanner commercial-only. Built a SerpApi + Duffel test harness; never run live (no keys).
- All research folders, scripts, and the tracking design were removed in the scope reset below. Recover them from commit `2580a78`.

### SerpApi facts (from docs, unverified live; input for F6.1)
- Billing: 1 search = 1 successful request, whatever the result count. Cached (identical params, 1 h), errored, and failed requests are free. Free 250/mo (50/h); $25 → 1k, $75 → 5k, $150 → 15k (+ U.S. Legal Shield).
- One-way request (`engine=google_flights`, `departure_id`, `arrival_id`, `outbound_date`, `type=2`) returns `best_flights[]` + `other_flights[]` (whole itineraries: one `price`, `total_duration`, `layovers`, segments with airport/local time/airline/flight number/aircraft/class/legroom/free-text `extensions`), plus `price_insights`. No pagination. No booking URL or structured baggage (booking needs another `booking_token` call). A round trip costs 2+ calls (`departure_token`).
- Filters (`stops`, `max_price`, `bags`, `outbound_times`, `include_airlines`, `max_duration`, `sort_by`…) are applied by Google, and each new combination is billable. So fetch broad, cache, and filter locally.
- Off-record discussion: no official Google Flights API exists (QPX ended 2018). Direct scraping (e.g. `fast-flights`) breaches Google's ToS; SerpApi is the maintained route.

---

## 2026-10-21 — Scope reset: ControlTower becomes a trip tracker

- Asked: gut the project and change scope. New product:
  - A **trip tracking app and system** with backend databases recording past and future trips.
  - Trips broken into **nodes/subsections**: flights, stays, and a day-by-day breakdown.
  - **Flight search via SerpApi**, but much less often (on demand, not the core loop).
  - Later, **agentic tracking** of where a person is and what they're doing, kept as a log, "like taking minutes".
- Done:
  - Removed `OpenSky API Testing/`, `Fare API Testing/`, and `docs/TRACKING_ARCHITECTURE.md` (`git rm`; recoverable from `2580a78`). Two empty folders remain on disk with only ignored `__pycache__/`; the user can delete them.
  - Rewrote ROADMAP: Phase 1 = F1.2 trip domain model & data design, F1.3 SerpApi lookup spike, F1.4 agentic log research. Phase 2 = backend core (DB, trip API, timeline, flight attach). Phase 3 = web. Phase 4 = agentic trip log. Phase 5 = iOS.
  - Updated CLAUDE.md (Purpose, Environment, Layout), README, `.env.example` (SerpApi only), and the backend package/pyproject descriptions.
  - Condensed this log.
- Decisions (mine, open to change in F1.2):
  - Model is a tree: Trip → Day → Item, with typed items (Flight, Stay, Activity, Transport, Note) plus LogEntry for the minutes.
  - Multi-day items (stays, overnight flights) belong to the trip with start/end times and appear on each day they span, rather than being duplicated per day.
  - Store times in UTC plus the local zone.
  - Database proposal: SQLite to start, Postgres-ready, SQLAlchemy 2.0 + Alembic.
  - The data model comes before any SerpApi or agent work, because both attach to it.

### Flight data deprioritized
- Asked: push flight data much further down the priority list.
- Done: moved the SerpApi spike and flight search/attach into a new last phase, **Phase 6 — Flight Lookup [LOW PRIORITY]** (F6.1 spike, F6.2 adapter; renumbered Phase 7 / F7.x below). Removed them from Phase 1/2. Agentic log research is now **F1.3** (was F1.4). Updated CLAUDE.md Purpose/Environment and README.
- Decision: Flight stays an item type in the data model (entered manually, like a stay or activity). Only *automatic lookup* moved down.

### F1.2 — Trip domain model & data design
- Asked: start F1.2. Confirmed scope first (4 questions).
- User decisions: **single user now, scale up later** (accounts, then shared trips, at separate points); **plan + actual** fields on items; **SQLite + SQLAlchemy 2.0 + Alembic**; **days derived** from item times, not stored.
- Done: `docs/ARCHITECTURE.md` with decisions D1–D10, a Mermaid ER diagram, entity field lists, the timeline rule, DB conventions for F2.1, an API resource draft, a scale-up table, and open questions. ROADMAP: new **Phase 6 — Accounts & Sharing** (F6.1 accounts, F6.2 shared trips); flight lookup renumbered to **Phase 7** (F7.1, F7.2). Updated README and CLAUDE.md.
- Design decisions (mine):
  - Item = common table + per-kind detail tables (SQLAlchemy joined-table inheritance). Kinds: flight, stay, transport, activity, note.
  - Every item has `start_tz` + `end_tz` (IANA), and times are stored UTC.
  - Day placement: an item appears on each local date from its start day (in `start_tz`) to its end day (in `end_tz`), with roles starts/continues/ends/single. Effective time = actual else planned.
  - `trip_day` rows only for per-day extras.
  - Reusable `place` rows with their own tz.
  - `log_entry` is separate from items (source + kind + raw JSON); agents propose actuals, never overwrite.
  - UUID keys, string enums, Decimal money, a UTC-enforcing column type, SQLite `foreign_keys` pragma.
  - Past/current/upcoming is computed, never stored.
  - Proposed FastAPI + Pydantic for the API (decide in F2.2).
- Status: user reviewed and ran `/finish-feature`.

### F1.2 — Trip domain model & data design complete
- Done: `docs/ARCHITECTURE.md` (new). ROADMAP ticked F1.2 and added Phase 6 Accounts & Sharing; flight lookup moved to Phase 7. README and CLAUDE.md updated. Checks green (ruff, format, mypy, pytest 2 passed). No backend code: models are built in F2.1.
- Decisions: Trip → Item tree with derived days; plan + actual times; UTC + per-end IANA zone; joined-table item kinds; shared places; separate log entries; SQLite + SQLAlchemy 2.0 + Alembic; UUID keys; single user with an `owner_id` so accounts and sharing can be added later.
- Next: **F1.3 Agentic trip log research** (new session, plan mode). Open questions: which signals are realistic on web vs iOS (location needs the phone app); manual check-ins as the MVP signal; which LLM and where it runs; privacy of location history.

### Roadmap reorder: web app first
- Asked: when can a functioning local web app be reviewed? Answered: real UI at F3.1; the interactive FastAPI docs page (`localhost:8000/docs`) from F2.2 onwards. Suggested moving the agentic research out of the way.
- Decision (user): move **F1.3 agentic trip log research → F4.1** (Phase 4, after the web frontend). Added F4.2 (build the log, TBD). Phase 1 is now **[DONE]**; Phase 2 marked **[NEXT]**. The path to a reviewable app is F2.1 → F2.2 (API page) → F2.3 → F3.1 (web app).

### Next
- **F2.1 Database, models, migrations** (new session, plan mode). Implement `docs/ARCHITECTURE.md`: SQLAlchemy 2.0 models, the `UTCDateTime` type, Alembic setup, a seed "me" user, and tests. Phase 2 work gets logged in a new `docs/HISTORY_P2.md`.
- Phase 1 closed. Continued in `docs/HISTORY_P2.md`.
