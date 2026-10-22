# History — Phase 3 (context log)

Chronological log of every prompt/work item: what was asked, what was done, decisions, and what's next.
ROADMAP.md tracks feature completion; this file is the context a new session needs to pick up where we left off.
Earlier phases: `HISTORY_P1.md` (tooling, scope, design), `HISTORY_P2.md` (database, API, timeline).

---

## 2026-10-21

### F3.1 — Web frontend complete
- Asked: start F3.1. Confirmed scope first. User chose **React + TypeScript + Vite**, **Tailwind**, and **trips + timeline + item forms** (log entries and day extras read-only).
- Tooling:
  - No Node or Homebrew on the machine. Installed **Node 24.22.1 LTS** from nodejs.org (SHA-256 verified) to `~/.local/share/node`, with `node`/`npm`/`npx`/`corepack` symlinked into `~/.local/bin`. No shell rc changes, no admin. npm is 11.19.1.
  - `npm create vite` (react-ts) gave Vite 8, React 19.3, TypeScript 6, and oxlint (replaces ESLint in the template).
  - Added react-router 8, @tanstack/react-query 5, openapi-fetch, @date-fns/tz. Dev: tailwindcss 4 + @tailwindcss/vite, openapi-typescript 7, vitest 5, jsdom, Testing Library.
  - `openapi-typescript` 7 declares a peer of TypeScript ^5. Fixed with npm `overrides` (`"$typescript"`) rather than `--force`; generation verified under TS 6.
  - npm 11 blocks install scripts by default: only `fsevents` was blocked, so it's explicitly denied in `allowScripts` (unused by Vite 8).
- Done:
  - **Config:** `web/` config (Vite proxy `/api` → :8000, Vitest jsdom, strict TS, `.nvmrc` 24).
  - **API layer:** `src/api/` (typed client, generated `schema.d.ts`, type aliases, query/mutation hooks).
  - **Logic:** `src/lib/` (`time.ts`, `itemForm.ts`, `listing.ts`).
  - **UI:** `src/components/` (`ui`, `DayCard`, `ItemForm`, `TripForm`, `PlacePicker`), `src/pages/` (`TripsPage`, `TripPage`), `App.tsx`, `main.tsx`.
  - **Backend:** `controltower/api/openapi.py` (schema export), `controltower/demo.py` (demo trip), `tests/test_openapi.py` (fails if `web/openapi.json` is stale), `tests/test_demo.py`.
  - **CI and hooks:** `web` CI job (npm ci, lint, typecheck, test, build); pre-commit hook for web lint + typecheck.
  - **Docs:** README *Run the app*, CLAUDE.md, ARCHITECTURE *Web app*, `web/README.md`. ROADMAP: F3.1 ticked, F3.2 placeholder added.
- Decisions:
  - **Dev proxy instead of CORS**: one origin for the browser.
  - **Generated types + schema drift test**: an API change that isn't regenerated fails the backend tests.
  - **TanStack Query** for server state; mutations invalidate `['trips']` (list + trip + timeline).
  - **Time zones in forms:** wall-clock time + IANA zone → UTC via `@date-fns/tz` (DST-gap times move forward), with zone validation that gives a readable error. Display uses `Intl` in the item's own zone, naming the zone only when it isn't the trip's.
  - **Item form logic is pure and unit-tested.** Create omits blanks (server defaults apply); PATCH sends all fields (blanks clear). One `DETAIL_FIELDS` table drives the per-kind fields.
  - Choosing a place sets the matching zone (from → start, to → end).
  - Native `<dialog>` for modals (no UI library). Tailwind with stone/teal styling.
  - The demo trip is opt-in and safe to re-run; it's for reviewing the UI.
- Bugs and fixes while building:
  1. Generated read types make kind fields optional (`| undefined`); `tsc` caught the mismatch.
  2. Testing Library didn't clean up between tests (no Vitest globals); added `afterEach(cleanup)`.
  3. `openapi-fetch` captured `fetch` at import, so test stubs were ignored; the client now resolves `globalThis.fetch` per request.
  4. Node's fetch can't take a relative `/api` URL; the base URL is now `window.location.origin + '/api'`.
  5. The router was created at module load and kept state between tests; it's now created per `App` mount.
  6. oxlint fast-refresh warnings; moved helpers to `lib/listing.ts` and the shell into `App.tsx`.
- Verified:
  - Web: oxlint clean, `tsc` clean, Vitest **19 passed** (time 7, itemForm 6, DayCard 3, App 3), production build 387 kB JS / 120 kB gzip.
  - Backend: **49 passed**, ruff + mypy clean.
  - Full stack on a scratch DB (your real DB untouched): migrate → demo seed → uvicorn :8000 + Vite :5173 → `/api/trips` and the timeline through the proxy (5 days with correct roles, log entry on Day 2, the idea unscheduled), and the SPA deep link returned 200.
  - Not verified: an actual browser render (no browser automation here). That's the user's review.

### Next
- **User review of the running app** → feedback becomes **F3.2** (also planned: editing for day extras and log entries, a places page).
- Then Phase 4 (F4.1 agentic trip log research).
