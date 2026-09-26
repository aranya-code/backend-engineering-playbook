"""MongoDB index definitions for the FastAPI application."""

from __future__ import annotations

from pymongo import ASCENDING, IndexModel
from pymongo.collection import Collection


def create_indexes(collection: Collection) -> list[str]:
    """Create indexes required by the application's user collection."""
    indexes = [
        IndexModel(
            [("email", ASCENDING)],
            name="idx_users_email_unique",
            unique=True,
        ),
        IndexModel(
            [("active", ASCENDING), ("email", ASCENDING)],
            name="idx_users_active_email",
        ),
    ]

    return collection.create_indexes(indexes)


def ensure_indexes(collection: Collection) -> None:
    """Ensure application indexes exist.

    For production deployments, prefer managing index creation through a
    controlled deployment or migration workflow rather than on every startup.
    """
    create_indexes(collection)

"""MongoDB index definitions for the FastAPI application."""

from __future__ import annotations

from pymongo import ASCENDING, IndexModel
from pymongo.collection import Collection


def create_indexes(collection: Collection) -> list[str]:
    """Create indexes required by the application's user collection."""
    indexes = [
        IndexModel(
            [("email", ASCENDING)],
            name="idx_users_email_unique",
            unique=True,
        ),
        IndexModel(
            [("active", ASCENDING), ("email", ASCENDING)],
            name="idx_users_active_email",
        ),
    ]

    return collection.create_indexes(indexes)


def ensure_indexes(collection: Collection) -> None:
    """Ensure application indexes exist.

    For production deployments, prefer managing index creation through a
    controlled deployment or migration workflow rather than on every startup.
    """
    create_indexes(collection)