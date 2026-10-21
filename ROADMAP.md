# Roadmap

Core product (first): a user picks two airports and travel dates, and the app returns a list of flights with current prices so they can compare fares.
Live flight tracking comes later (see Phase 4, parked).

## Phase 1 — Project Structure & Scope  [IN PROGRESS]
- [x] F1.1 Identify and set up the tools, skills, and processes necessary for the project.
  uv + Python 3.13 package in `backend/`, ruff/mypy/pytest, pre-commit, GitHub Actions CI, Claude allowlist + `/finish-feature` skill.
  Follow-ups: Claude-managed root `.gitignore`; Python 3.13 set as user-wide default via uv.
- [ ] F1.2 Fare data source research. Find candidate flight-price APIs and test the best one or two, as we did with OpenSky. Questions to answer:
  - Search: given origin, destination, and dates (one-way and return), what comes back? Price, currency, airline, flight numbers, departure/arrival times, stops, duration, cabin, baggage.
  - Airport lookup: can it search airports by name or city (for the search box)?
  - Freshness: are prices live or cached, and how much do they drift from airline sites?
  - Access and cost: sign-up, free tier, rate limits, price per search, test vs. production data.
  - Terms: can we show prices in a public app? Booking links or affiliate requirements?
  Output: a research folder with scripts, raw responses, CSV data, and a findings README with a verdict.

## Phase 2 — Initialize & Test Backend  [NOT STARTED]
- [ ] F2.1 TBD (fare search backend, scoped after F1.2)

## Phase 3 — Web Frontend Development  [NOT STARTED]
- [ ] F3.1 TBD (search airports, pick dates, show priced flights)

## Phase 4 — Live Flight Tracking  [PARKED]
Done earlier, before the product focus changed. Kept for later; not being built now.
- [x] F4.1 OpenSky API research (was F1.2). Verdict: viable for tracking with a free account, backend polling/caching, and adsbdb for routes. See `OpenSky API Testing/`.
- [x] F4.2 Tracking architecture & typed stubs (was F1.3). Design kept in `docs/TRACKING_ARCHITECTURE.md`. The stub code was removed for a clean fare-focused backend; it's recoverable from commit `3459315`.
  Open: OpenSky account/credentials not set up; authenticated behaviour unverified.
