"""
Shared module: database connection and session management.

Uses SQLModel (SQLAlchemy under the hood).
The session dependency `get_session` is injected into routers via FastAPI's DI system.

Database strategy:
  - SQLite  (local dev) : tables are created automatically via create_db_and_tables().
  - PostgreSQL (production): tables are managed exclusively by Alembic migrations.
    The entrypoint script runs `alembic upgrade head` before the server starts.

Switching environments only requires changing DATABASE_URL in .env.
"""

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./linker.db")

_is_sqlite = DATABASE_URL.startswith("sqlite")

# SQLite requires check_same_thread=False for FastAPI's threaded request handling.
connect_args: dict = {"check_same_thread": False} if _is_sqlite else {}

# pool_pre_ping tests connections before use — essential for long-lived PG connections.
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=not _is_sqlite,   # NullPool is used for SQLite; pre_ping is PG-only
)


def create_db_and_tables() -> None:
    """Auto-create tables for SQLite dev only.

    For PostgreSQL, this is a no-op: Alembic migrations (alembic upgrade head)
    run via scripts/entrypoint.sh before the server starts.
    """
    if _is_sqlite:
        SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a scoped database session per request."""
    with Session(engine) as session:
        yield session
