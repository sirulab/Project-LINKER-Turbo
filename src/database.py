"""
Shared module: database connection and session management.

Uses SQLModel (SQLAlchemy under the hood) with a SQLite engine.
The session dependency `get_session` is injected into routers via FastAPI's DI system.
Switching to PostgreSQL later only requires changing DATABASE_URL in .env.
"""

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./linker.db")

# `check_same_thread=False` is required for SQLite when used with FastAPI's
# async request handling across multiple threads.
connect_args: dict = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)


def create_db_and_tables() -> None:
    """Create all tables defined in SQLModel metadata. Called once on startup."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session per request.

    Usage in a router:
        from fastapi import Depends
        from src.database import get_session

        @router.get("/items")
        def list_items(session: Session = Depends(get_session)):
            ...
    """
    with Session(engine) as session:
        yield session
