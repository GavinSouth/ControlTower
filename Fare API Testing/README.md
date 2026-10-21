# Fare API Testing (F1.2)

Research sandbox for choosing the flight-price data source behind ControlTower's core feature: pick two airports and dates, get a list of flights with current prices.
This is not production code: it's stdlib-only Python, kept outside `backend/`, and not covered by CI. The backend will be designed around the provider this research picks.

**Status:** scripts are built and tested offline; live runs are waiting on API keys. Findings below are still **TBD**.

## Candidates
| Provider | What it is | Why tested |
|---|---|---|
| **SerpApi, Google Flights engine** | Paid API that scrapes Google Flights results | Live consumer prices, broad airline coverage, airport autocomplete. ~250 free searches/mo |
| **Duffel** | Official airline-content + booking API (NDC/GDS) | Licensed data with a real booking path. Free to search; paid per booked order |

Ruled out at shortlist (Oct 2026): Amadeus Self-Service (shut down 17 Jul 2026), Kiwi Tequila (invite-only partners), Skyscanner (commercial approval only). Travelpayouts (cached prices, affiliate-only) and FlightAPI.io (20 free calls) are fallbacks.

## Setup
1. **SerpApi:** sign up at <https://serpapi.com> → *Your API key*.
2. **Duffel:** sign up at <https://app.duffel.com> → *Developers → Access tokens* → create a **test** token (`duffel_test_…`). Note whether the dashboard lets you request live mode, and on what conditions.
3. Repo root: `cp .env.example .env`, then fill in `SERPAPI_API_KEY` and `DUFFEL_ACCESS_TOKEN`.

The scripts load `.env` themselves. Keys are scrubbed from everything written to `data/`.

## Run (from `Fare API Testing/scripts/`)
```bash
uv run --no-project python 01_airport_lookup.py   # airport search box: "london", "san fran", ...
uv run --no-project python 02_search_oneway.py    # 3 routes x 2 dates, one-way
uv run --no-project python 03_search_return.py    # same, round trip (+ SerpApi return-leg call)
uv run --no-project python 04_freshness.py        # repeat one search 3x, 10 min apart, diff prices
uv run --no-project python 05_compare.py          # offline: overlap + price gap between providers
```
Add `serpapi` or `duffel` to run a single provider. Raw responses are cached in `data/raw/`, so re-running costs no searches; `04` always fetches fresh.
SerpApi budget: about 22 searches in total (4 + 6 + 9 + 3).

Routes: JFK→LAX (domestic trunk), LHR→JFK (transatlantic), SFO→SEA (short-haul). Dates: today +14 and +60 days; returns 7 days later.

## Files
- `scripts/common.py`: `.env` loader, HTTP, raw/CSV I/O, and the shared `FARE_FIELDS` schema (one row per itinerary, the same for both providers).
- `scripts/serpapi_client.py`, `scripts/duffel_client.py`: request + normalize for each provider.
- `scripts/fares.py`: runs one search with raw caching and builds a summary row.
- `data/raw/*.json`: raw responses. `data/*.csv`: `airport_lookup`, `fares_oneway`, `fares_return`, `serpapi_return_legs`, `summary_*`, `freshness`, `compare_oneway`.

## Findings (TBD after live runs)
### 1. Search: what comes back?
### 2. Airport lookup
### 3. Freshness and drift
### 4. Access and cost
### 5. Terms: public display, booking links
### Comparison
### Verdict
