"""Runtime settings, read from the environment."""

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = BACKEND_DIR / "data" / "controltower.db"


def database_url() -> str:
    """`DATABASE_URL` if set (e.g. a Postgres URL later), else the local SQLite file."""
    return os.environ.get("DATABASE_URL") or f"sqlite:///{DEFAULT_DB_PATH}"
