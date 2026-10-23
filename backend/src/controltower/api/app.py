"""FastAPI application.

Run locally (after `uv run alembic upgrade head`):
    uv run uvicorn controltower.api.app:app --reload
then open http://localhost:8000/docs for the interactive API page.
"""

from fastapi import FastAPI
from sqlalchemy.orm import Session, sessionmaker

from controltower import __version__
from controltower.api.routes import (
    days,
    items,
    log,
    photos,
    places,
    reflection,
    timeline,
    trips,
)
from controltower.config import photos_dir
from controltower.db import make_engine, make_session_factory
from controltower.photos import PhotoStore


def create_app(
    session_factory: sessionmaker[Session] | None = None, photo_store: PhotoStore | None = None
) -> FastAPI:
    """Build the app. Tests pass their own session factory and photo store (temp folders)."""
    app = FastAPI(
        title="ControlTower API",
        version=__version__,
        description=(
            "Trips broken down day by day: trips, items, places, day extras, trip log, "
            "the past trip record (reflection, item feedback, stats, favourites), and cover photos."
        ),
    )
    app.state.session_factory = session_factory or make_session_factory(make_engine())
    app.state.photo_store = photo_store or PhotoStore(photos_dir())
    for module in (trips, timeline, items, places, days, log, reflection, photos):
        app.include_router(module.router)

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
