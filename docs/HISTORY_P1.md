# History — Phase 1

## 2026-10-20 — F1.1
- Done: installed uv; scaffolded `backend/` Python 3.13 package (`src/controltower`, `tests/test_smoke.py`); configured ruff, mypy (strict), pytest in `pyproject.toml`; `.pre-commit-config.yaml`; `.github/workflows/ci.yml`; `.claude/settings.json` allowlist (+ deny reading `.env`); `/finish-feature` skill; `.env.example`; filled CLAUDE.md Environment/Layout/Commands.
- Decision: OpenSky Network as data source (free, live ADS-B; limited schedule data). Web-first frontend, iOS later. uv over pip for reproducible locked deps. Pre-commit hooks call `uv run` so hook/CI/local tool versions all come from `uv.lock`. Backend lives in `backend/` to leave room for `web/` and `ios/` siblings.
- Next: F1.2 architecture & API design. Open questions: polling cadence vs OpenSky rate limits; where airport/route data comes from (OpenSky lacks schedules).
