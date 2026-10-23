"""Runtime settings, read from the environment."""

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = BACKEND_DIR / "data" / "controltower.db"
DEFAULT_PHOTOS_DIR = BACKEND_DIR / "data" / "photos"


def database_url() -> str:
    """`DATABASE_URL` if set (e.g. a Postgres URL later), else the local SQLite file."""
    return os.environ.get("DATABASE_URL") or f"sqlite:///{DEFAULT_DB_PATH}"


def photos_dir() -> Path:
    """`PHOTOS_DIR` if set, else `backend/data/photos/` (git-ignored with the database)."""
    return Path(os.environ.get("PHOTOS_DIR") or DEFAULT_PHOTOS_DIR)
