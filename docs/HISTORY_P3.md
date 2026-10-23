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

### Running the app for review
- Asked: where is the link to the app? Answered: there's no hosted URL; it's local at http://localhost:5173 and only works while both servers run.
- Done: migrated the real local DB and seeded "Japan (demo)" into it (deletable from the UI). Started uvicorn on :8000 and Vite on :5173 as background tasks; health check and `/api/trips` verified through the proxy.

### Feature requests for F3.2
- Asked: jot down features before restarting the session.
  1. **Trip location**: more user-entered fields on a new trip, starting with a location at any level of detail ("Shinjuku, Japan" or "Japan"). Added to ROADMAP F3.2 with the implementation outline (DB column + migration, API, regenerated types, TripForm, shown on cards and header). Open question: free text vs also a country code.

### F3.2 — Trip details & polish complete
- Asked: resume. Confirmed scope first: all four parts (trip location, day extras editing, log entry editing, places page); no other review feedback.
- On location storage the user answered with a direction rather than a choice: *"I just want the whole project to have an agentic process… it'll look at the location and time of year and do some recommendation processes."* So:
  - Location is **free text** (an LLM reads "Shinjuku, Japan" as-is; geocoding is a later research question).
  - Added **F4.3 Recommendations agent** to ROADMAP. Phase 4 was renamed *Agentic Trip Log & Recommendations*, with a line on the app-wide agentic goal.
- Done:
  - **Backend:**
    - `Trip.location` (String 200, nullable) + migration `19b2f4c23aa1_trip_location.py`.
    - `location` on TripCreate/Patch/Read.
    - New `LogEntryPatch` + `PATCH /log/{id}`. The item check is shared with create (`require_trip_item`), so an entry can only point at an item on its own trip.
    - The demo trip has a location.
    - 2 new tests (location; log patch incl. 404/422 cases) → **51 passed**.
  - **Web:**
    - **Types and hooks:** new aliases (`DayWrite`, `LogEntryCreate/Patch`, `PlacePatch`, `LogKind`) and hooks (`useSaveDay`, `useCreate/Update/DeleteLogEntry`, `useUpdate/DeletePlace`). Place changes invalidate places and trips.
    - **Trip location:** a TripForm field, shown as 📍 on trip cards and the trip header.
    - **DayCard:** "Edit day" button, summary shown, clickable log entries, "+ Log entry" → `DayForm` / `LogForm` dialogs in `TripPage`.
    - **Pure, tested form logic:** `lib/logForm.ts` and `lib/placeForm.ts`.
    - **Places page:** `PlacesPage` (`/places`, search, add, edit, delete) + `PlaceForm`. Header nav (Trips / Places).
    - Tests: **28 passed** (+9).
  - **Docs:** ARCHITECTURE (TRIP.location, PATCH /log, web notes), README, web/README.
- Decisions:
  - **Free-text location** (see above). A country code can be added later as a nullable column without reshaping.
  - **Log form time default:** now if the day is today in the trip's zone (logging live), else 12:00.
  - **Log "About" picker** lists every trip item once (a multi-day stay appears on several days, so items are deduped by id).
  - **The UI sends `source: 'manual'` explicitly:** generated create types mark defaulted fields as required, and it documents intent (agents will use other sources).
  - **Day extras use the existing PUT** (replace all; blanks clear). An all-blank save leaves an empty row, which is harmless.
- Verified:
  - Backend ruff/mypy/pytest clean.
  - Web oxlint/tsc/Vitest clean; build 399 kB JS / 123 kB gzip.
  - Scratch DB: migration up → down → up, then demo seed, `PATCH /log`, and `PUT /days`, all reflected in the timeline.
  - Ran `alembic upgrade head` on the real local DB (adds the nullable column; data untouched).
  - Not verified in a real browser (no automation here).

### Next
- **User review of F3.2 in the browser.** The existing "Japan (demo)" was seeded before location existed, so add one via Edit trip.
- Phase 4: **F4.1** agentic trip log research. **F4.3** recommendations research can be paired with it, since both need the LLM/agent choice.

### Past trip record: idea → F3.3 / F3.4
- Asked: experiment with what a past-trip record looks like. It should read as a fond historical record, with enough data to query, surface, and use for future recommendations. Update ROADMAP as needed.
- Started both dev servers for the F3.2 review (uvicorn :8000, Vite :5173).
- Done: ROADMAP gets **F3.3** (design spike: mockup + data/query design) and **F3.4** (build), placed before Phase 4 because F4.3 recommendations need this data. F4.3 now cites past-trip signals. Phase 3 is back to IN PROGRESS.
- Proposed in chat:
  - **Model:** trip reflection (rating, highlight, would-return, tags, companions) and item feedback (rating, favourite, review). Derived stats stay computed.
  - **Past-trip "memory" view:** an ASCII mock.
  - **Open questions** for the user before the spike.
- Next: the user answers the open questions → F3.3 spike.

### F3.3 — Past trip record: design spike complete (2026-10-21)
- Asked: `--resume`. The open questions from last session weren't in this log, so they were asked again. Answers:
  - Mockup as a **static HTML page**.
  - "Past" is **automatic after the end date**.
  - Items rated **👍/👎 + ♥ favourite**.
  - Tags and companions as **free-text lists**.
- Done (design only, no code):
  - `docs/mockups/past-trip.html`: self-contained mockup of a fictional "Lisbon & Sintra, May 2025" trip:
    - cover, derived-stats strip, reflection, favourite moments, days as journal (summary, log, items with inline 👍/👎/♥, a skipped item);
    - a "what this feeds" table;
    - a toggle between "just ended" (reflect banner) and "reflected".
    - Grey labels name the field behind each value.
  - `docs/ARCHITECTURE.md` → new section *Past trip record*:
    - decisions P1–P7;
    - `trip_reflection` + `item_feedback` tables;
    - the derived stats rules;
    - the queries it must answer;
    - the F3.4 API (`/reflection`, `/feedback`, `/stats`, `/favourites`) and web plan.
- Decisions:
  - **Reflection and feedback are separate tables keyed (trip/item, user)**, not trip/item columns. Opinions are per person, so Phase 6 shared trips need no reshaping.
  - **Trip rating stays 1–5** while items use thumbs. Trips are rated once, so the finer scale is worth it (and the ROADMAP query "trips I rated 5" uses it). **Confirmed by the user** after the spike.
  - **`skipped` status counts as a negative signal** with no user input.
  - **Tags are a JSON list** (lower-cased), filtered in Python at this scale. A `trip_tag` table is the upgrade path.
  - **Stats are computed** by a pure `trip_stats()`, never stored:
    - cities and countries come from stays and activities only, so the home airport doesn't count;
    - spend is per currency;
    - season comes from the middle date, with a southern-hemisphere flip.
  - **F4.3 gets a backend-built "taste profile"**; the agent never queries the DB directly.
- Verified: backend ruff/mypy/pytest clean (51 passed). The mockup is static and wasn't rendered in a browser here.
- Next: **user reviews the mockup + ARCHITECTURE section**. Then **F3.4** builds it.

### Question: using Claude Design
- Asked: can Claude Design be used in this project?
- Answered: yes. It lives in Claude as two Artifact types: **Design** (a canvas of artboards for screens and mockups) and **Design System** (tokens, components with live previews, guidelines). Standalone claude.ai/design closes 2026-12-14.
- Proposed:
  1. A Design System built from `web/` (stone/teal Tailwind, the existing components). Later web and iOS (Phase 5) work builds on it.
  2. Do the F3.4 past-trip view on a Design canvas (desktop + phone, both states, the reflect dialog) instead of hand-written HTML mockups.
- Nothing created yet; waiting for the user's go-ahead.

### Claude Design rule + first design artifacts
- Asked: should Claude Design be used throughout frontend work? Proposed a rule; the user added it to CLAUDE.md (*Design (Claude Design)*) and said to start the canvas work and follow it from now on.
- Done:
  - **Design system:** [ControlTower](https://claude.ai/artifact/U3TJjZ1ABvNMs8xPzNczwL) (private). Built from `web/src` at `bc3c6b6`:
    - exact Tailwind 4 oklch values for the 22 colours in use;
    - 9 text styles, spacing, radii, shadows, layout sizes;
    - the favicon mark;
    - a brand-book README (copy voice, foundations, iconography);
    - 9 components with guidelines and static previews (`bundle.css` recreates the Tailwind classes).
  - **F3.4 canvas:** [Past Trip Record (F3.4)](https://claude.ai/artifact/TrsVJXeop1z8QH6Bh887wn) (private), with the design system installed. Five artboards: trip list, just ended (Montréal demo), reflect dialog, reflected record (interactive 👍/👎/♥; ♥ fills "Favourite moments" live; a sans/serif `voice` tweak), phone.
  - `docs/ARCHITECTURE.md`: new *Design system* section and *Past trip record → Design* (links + proposed decisions). The F3.3 HTML mockup is marked superseded.
  - `/finish-feature` gained a design-system check (step 5). The ROADMAP F3.4 line and the README point to the canvas.
- Decisions (proposed, in ARCHITECTURE):
  - Record/Plan toggle; a solid teal cover.
  - Stars and ♥ in `teal-700`, and a neutral (not red) 👎, to keep one accent and leave red for errors.
  - SVG icons for the feedback buttons only; kind icons stay emoji.
  - Skipped items get no buttons.
  - Serif voice left as a tweak to decide.
- Gaps: previews are static (no React bundle); no dark theme (the app has none); `stone-400` hint text is 2.5:1, kept exact from the source. Not rendered or checked here, as the canvas type asks.
- Next: the user reviews the canvas (comments can go on the artboards), picks sans or serif, then F3.4 builds.

### Session pinned (2026-10-21, evening)
- State: F3.3 done; F3.4 not started. Working tree clean on `main`; nothing pushed.
- **Morning review (user):**
  - The design canvas: https://claude.ai/artifact/TrsVJXeop1z8QH6Bh887wn. Open it and press Play on artboard 4 to try 👍/👎/♥.
  - The design system: https://claude.ai/artifact/U3TJjZ1ABvNMs8xPzNczwL.
  - Leave comments on the artboards.
- **Open decisions for F3.4:**
  1. Sans or serif journal voice (the `voice` tweak).
  2. Keep teal stars/♥ and a neutral 👎?
  3. Keep the Record/Plan toggle and the solid teal cover?
  4. Skipped items get no buttons: OK?
- **Next session:** read the canvas comments → settle the decisions above → update the canvas or design system if needed → start the F3.4 build (backend tables + migration first).

- Asked: start the app for a look. Ran `alembic upgrade head` (already current), then started uvicorn :8000 + Vite :5173 in the background; `/api/health` ok and "Japan (demo)" listed through the proxy.
- Asked: is the past-trip work done? It is not in the app. Answered: no. F3.3 was design only; the build is F3.4, not started (waiting on the canvas review).

### F3.4 — Past trip record: build started (2026-10-22)
- Asked: `--resume`. The canvas and design system had no comments, so the four open decisions were asked directly. Answers:
  1. Journal voice: **serif** (day summaries, log, highlight quote). New `font-serif` token.
  2. Feedback colours: **red ♥ and red 👎** (user overrode the teal ♥ / neutral 👎 proposal). 👍 stays teal; stars stay teal.
  3. Record/Plan toggle + solid teal cover: **kept**.
  4. Skipped items: **no feedback buttons**.
- Recorded in `docs/ARCHITECTURE.md` → *Past trip record → Design*. The canvas and design system still show the old choices; both get updated during F3.4, before `/finish-feature`.
- Built (backend):
  - `trip_reflection` + `item_feedback` tables (`models/reflection.py`), keyed (trip/item, user), with cascade deletes and a 1–5 check. Migration `7214a9969f07`.
  - Pure `trip_stats()` in `stats.py`: nights, cities and countries (stays/activities + day cities only), flights, spend per currency, season (middle date, southern flip), and feedback counts incl. `pending`.
  - `api/routes/reflection.py`: reflection GET/PUT/DELETE, item feedback PUT/DELETE (an empty PUT deletes the row and returns null), `GET /trips/{id}/stats`, `GET /favourites?country=&kind=&category=`.
  - The timeline's items carry my `feedback`. Trip reads carry `reflection: {rating, highlight} | null`.
  - Demo: "Lisbon (demo)", May 2025, past, 4 of 8 rateable items rated (2 ♥, 1 👎), a skipped museum, EUR + USD costs, **no reflection**, so it opens on the prompt.
- Built (web):
  - A past trip opens in **Record** view, with a Record/Plan toggle (`TripPage`). `TripRecord.tsx` follows the canvas: reflect banner → teal cover → stats strip → reflection panel → favourite moments → days as a journal.
  - `FeedbackButtons` (👍 teal, 👎/♥ red), `Stars`/`StarInput`, `ReflectForm` (rating, highlight, would return, tag/companion chips, notes), and `ListInput` (chips). The app's first SVG icons are in `icons.tsx`.
  - Pure rules in `lib/record.ts`: each item once on its first day; favourites; "x of y rated"; stats text.
  - Trip cards: an unreflected past trip gets a teal border + "How was it? Reflect on this trip →"; a reflected one shows stars and the highlight.
- Decision changed during the build: `reflected: bool` became `reflection: {rating, highlight} | null`. The trip card needs both, and a bool would mean one request per card (N+1).
- Design artifacts updated:
  - Design system v6: `font-serif` + Journal text styles, `red-300`/`red-600`, new FeedbackButtons and RatingStars components, past TripCard states, README colour/type/icon rules.
  - Canvas v10: serif is now the default voice; 👎/♥ are red.
- Verified:
  - backend ruff/format/mypy clean, 63 tests;
  - web lint/typecheck/build clean, 34 tests;
  - real DB migrated and seeded; `/stats` and `/favourites` checked against the Lisbon demo.
- Not verified: no visual check in a browser (the Chrome tools weren't available this session).

### F3.4 — Past trip record: build complete (2026-10-22)
- Done: see the build entry above.
  - Backend: `models/reflection.py`, `stats.py`, `api/routes/reflection.py`, migration `7214a9969f07`, `demo.py` (Lisbon).
  - Web: `components/TripRecord.tsx`, `ReflectForm.tsx`, `FeedbackButtons.tsx`, `Stars.tsx`, `ListInput.tsx`, `icons.tsx`, `lib/record.ts`, `pages/TripPage.tsx`, `pages/TripsPage.tsx`.
  - Tests: `test_stats.py`, `test_api_past_trips.py`, `test_demo.py`, `record.test.ts`, `App.test.tsx`.
- Decisions:
  - Serif journal voice; red 👎/♥ (user).
  - `reflection` brief on trip reads instead of `reflected: bool`.
  - Each item appears once in the journal, on its first day.
  - Feedback is saved per click, with no form.
  - The `pending` count and the web's `isRateable` share one rule: flight/stay/transport/activity, not idea/skipped/cancelled.
- Design system: updated (v6), canvas updated (v10); see above.
- Next: Phase 3 is done. **F4.1 agentic trip log research** in a new session. Before that, the user should review the past-trip view in the browser (`uv run python -m controltower.demo`, then open "Lisbon (demo)").

### F3.5 — Trip cover photo: proposed (2026-10-22)
- Asked: let users upload a main photo for the green cover block (as a placeholder and visual sugar across the app). Does it make sense?
- Answered: yes. Added **F3.5** to ROADMAP (Phase 3 back to IN PROGRESS). Proposed:
  - files on disk + a `photo` table;
  - resized copies with EXIF GPS stripped;
  - a scrim under the cover text;
  - a canvas pass first.
- Open questions put to the user: where the photo shows, storage, upload entry point, design step.
- Answers:
  - The photo shows on all four placements: past-trip cover, trip cards, Plan view banner, phone.
  - Storage: disk + `photo` table.
  - Upload: on the cover and in Edit trip.
  - Design: **build directly**, skipping the canvas.
- Recorded in the ROADMAP F3.5 entry. Next: build F3.5 (new session per the one-feature-per-session rule, unless the user says to continue here).

### F3.5 — Trip cover photo: backend (step 1) (2026-10-22)
- Asked: `resume`, then "go ahead with step 1" after the build plan (backend → web → wrap-up) was proposed.
- Built:
  - Deps: `pillow`, `pillow-heif` (HEIC), `python-multipart` (FastAPI file uploads).
  - `models/photo.py`: a `photo` table; `trip.cover_photo_id` (SET NULL). The link is one-way (trip → photo), so the foreign keys aren't circular. Migration `898ac4e06ea5`, applied to the local DB.
  - `photos.py`: pure `process()` applies EXIF rotation, then writes WebP `sm`/`md`/`lg` (400/1200/2400px longest edge, no upscaling) with no EXIF (GPS dropped) and the ICC profile kept. JPEG/PNG/WebP/HEIC only, 20 MB cap. `PhotoStore` keeps the files at `data/photos/<id>/<size>.webp`, with `PHOTOS_DIR` as an override.
  - `api/routes/photos.py`: `PUT/DELETE /trips/{id}/cover` (both return the trip), `GET /photos/{id}/{size}` (immutable cache). Trip reads gain `cover: {id, width, height} | null`. Deleting a trip removes its cover files.
  - Tests: `test_photos.py` (sizes, rotation, EXIF/GPS stripped, formats, rejects) and `test_api_photos.py` (upload, replace, remove, trip delete, 422, 404). The `client` fixture now uses a temp photo folder.
  - Web: `npm run gen:api`; `cover: null` added to the `App.test.tsx` fixture. No UI yet.
- Decisions:
  - Every upload is a new photo id, so URLs can be cached forever.
  - Files are written before the commit and old files deleted after it, so a failure never leaves a trip pointing at missing files.
  - DELETE cover returns the trip (200), not a 204, so the web can update in one round trip.
  - Kept as a sync route so the resize runs in a worker thread.
- Verified: backend ruff/format/mypy clean, 81 tests; web lint/typecheck/build clean, 34 tests.
- Next: step 2, the web UI (cover with scrim, card strip, Plan banner, upload controls, phone width).
- Asked: the app showed "failed to load page / connection refused". Cause: neither dev server was running (last session's had stopped). Started uvicorn :8000 + Vite :5173 in the background. `/health` ok; `/api/trips` through the proxy lists both demo trips with the new `cover: null`.

### F3.5 — Trip cover photo: web UI (step 2) (2026-10-22)
- Asked: what changed at a high level (answer: step 1 was backend only, nothing visible yet), then "go ahead with step 2".
- Built:
  - `lib/photo.ts`: `photoUrl`, `photoSrcSet` (each copy at its real width; duplicates dropped for small photos), and `uploadProblem` (type + 20 MB, HEIC by extension).
  - `api/hooks.ts`: `useSetCover` (multipart: the generated type says `file: string`, so a `bodySerializer` builds the FormData) and `useRemoveCover`.
  - `components/CoverPhoto.tsx`: `CoverImage` (img + optional scrim) and `CoverPhotoControls` (`overlay` on covers, `form` in Edit trip).
  - Placements:
    - past-trip cover: taller, text at the bottom over the scrim, teal fallback;
    - Plan view: a banner with title and location, only when there is a photo;
    - trip cards: a lazy `h-28` strip, greyed when cancelled;
    - Edit trip: a "Cover photo" field with a thumbnail.
- Tests: `lib/photo.test.ts`; `App.test.tsx` covers the card strip with its srcset, and an upload from the cover (refused at >20 MB; otherwise a multipart PUT). The fake API now reads multipart bodies as text.
  - Gotcha: in Vitest, `fetch`/`FormData` are Node's (undici) but `File` is jsdom's, and undici rejects it. The test builds its File through a Node FormData round trip.
- Verified:
  - web lint/typecheck/build clean, 42 tests;
  - a synthetic gradient image (no real photo) uploaded to "Lisbon (demo)" through the running API; `/api/photos/<id>/sm|lg` serves WebP through the Vite proxy.
- Not verified: no screenshot or phone-width check. There's no browser automation on this machine (no Chrome or Playwright), so the user does the visual review.
- Next: user review in the browser → step 3 (demo covers in the seeder, design system update, `/finish-feature`).
