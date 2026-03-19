"""Alembic migration environment — Project LINKER Turbo.

Key decisions:
  - DATABASE_URL is read from the environment (via .env or shell), so this file
    works unchanged in both local and CI/CD contexts.
  - All SQLModel table models are imported below so that SQLModel.metadata
    contains the full schema before autogenerate runs.
  - render_as_batch=True enables SQLite-compatible ALTER TABLE support
    (Alembic recreates the table behind the scenes for SQLite).
"""

import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

load_dotenv()

# ── Import every model so SQLModel.metadata is fully populated ────────────────
import src.models  # noqa: F401  (registers Company, Project, Quote, Task, Employee, Timesheet)

# ── Alembic Config object ─────────────────────────────────────────────────────
config = context.config

# Inject DATABASE_URL from environment (overrides placeholder in alembic.ini)
database_url = os.environ.get("DATABASE_URL", "sqlite:///./linker.db")
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


# ── Offline mode (generate SQL script without connecting) ─────────────────────
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (connect and apply migrations) ────────────────────────────────
def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
