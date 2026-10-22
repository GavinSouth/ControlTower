# ControlTower web

React 19 + TypeScript + Vite + Tailwind. Talks to the FastAPI backend through Vite's `/api` proxy.
See the [project README](../README.md) for setup and running both servers.

```bash
npm install
npm run dev        # http://localhost:5173 (needs the API on :8000)
npm run lint && npm run typecheck && npm test && npm run build
npm run gen:api    # after a backend API change: refresh openapi.json + src/api/schema.d.ts
```

- `src/api/`: typed client (`openapi-fetch`), generated `schema.d.ts`, type aliases, TanStack Query hooks.
- `src/lib/`: pure logic with unit tests: time zones (`time.ts`), item form ↔ API bodies (`itemForm.ts`), timeline labels (`listing.ts`).
- `src/components/`: `DayCard`, `ItemForm`, `TripForm`, `PlacePicker`, shared `ui`.
- `src/pages/`: `TripsPage` (`/`), `TripPage` (`/trips/:tripId`).
