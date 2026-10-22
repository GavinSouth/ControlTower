"""Shared fixtures: a fresh SQLite file database per test."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from controltower.db import make_engine, make_session_factory
from controltower.models import Base


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    # A real file (not :memory:) so every connection sees the same database.
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    return make_session_factory(engine)


@pytest.fixture
def session(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    with session_factory() as session:
        yield session
