"""Alembic environment: runs migrations against controltower's models and engine."""

from logging.config import fileConfig

from alembic import context

import controltower.models  # noqa: F401  (registers every table on Base.metadata)
from controltower.config import database_url
from controltower.db import make_engine
from controltower.models import Base

config = context.config
if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Tests can pass a URL with `config.set_main_option("sqlalchemy.url", ...)`.
url = config.get_main_option("sqlalchemy.url") or database_url()


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of running it (`alembic upgrade head --sql`)."""
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = make_engine(url)  # same engine setup as the app (SQLite foreign keys on)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite can't ALTER most things in place; batch mode rebuilds the table instead.
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
