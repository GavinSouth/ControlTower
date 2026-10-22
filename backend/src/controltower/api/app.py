"""FastAPI application.

Run locally (after `uv run alembic upgrade head`):
    uv run uvicorn controltower.api.app:app --reload
then open http://localhost:8000/docs for the interactive API page.
"""

from fastapi import FastAPI
from sqlalchemy.orm import Session, sessionmaker

from controltower import __version__
from controltower.api.routes import days, items, log, places, timeline, trips
from controltower.db import make_engine, make_session_factory


def create_app(session_factory: sessionmaker[Session] | None = None) -> FastAPI:
    """Build the app. Tests pass their own session factory (a temporary database)."""
    app = FastAPI(
        title="ControlTower API",
        version=__version__,
        description="Trips broken down day by day: trips, items, places, day extras, trip log.",
    )
    app.state.session_factory = session_factory or make_session_factory(make_engine())
    for module in (trips, timeline, items, places, days, log):
        app.include_router(module.router)

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
