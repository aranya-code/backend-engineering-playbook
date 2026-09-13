"""Database initialization and lifecycle helpers."""

from __future__ import annotations

from sqlalchemy import text

from src.database.connection import dispose_engine, engine


def initialize_database() -> None:
    """Verify that the configured database is reachable."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def shutdown_database() -> None:
    """Release database resources during application shutdown."""
    dispose_engine()

"""Database initialization and lifecycle helpers."""

from __future__ import annotations

from sqlalchemy import text

from src.database.connection import dispose_engine, engine


def initialize_database() -> None:
    """Verify that the configured database is reachable."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def shutdown_database() -> None:
    """Release database resources during application shutdown."""
    dispose_engine()