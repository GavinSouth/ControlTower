"""Engine and session setup, plus the single-user ("me") seed."""

from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from controltower.config import database_url
from controltower.models import User

OWNER_NAME = "Me"


def _enable_sqlite_foreign_keys(dbapi_connection: Any, _record: Any) -> None:
    # SQLite ignores FOREIGN KEY / ON DELETE CASCADE unless enabled on every connection.
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def make_engine(url: str | None = None) -> Engine:
    url = url or database_url()
    parsed = make_url(url)
    if parsed.get_backend_name() == "sqlite" and parsed.database not in (None, "", ":memory:"):
        Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url)
    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    # expire_on_commit=False: objects stay readable after commit (handy for API responses).
    return sessionmaker(engine, expire_on_commit=False)


def get_or_create_owner(session: Session) -> User:
    """The one user until accounts exist (ARCHITECTURE.md D1). Idempotent."""
    owner = session.scalars(select(User).order_by(User.created_at).limit(1)).first()
    if owner is None:
        owner = User(name=OWNER_NAME)
        session.add(owner)
        session.flush()
    return owner
