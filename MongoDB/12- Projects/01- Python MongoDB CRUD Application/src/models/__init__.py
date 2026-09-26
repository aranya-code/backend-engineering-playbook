"""Index definitions for the MongoDB CRUD application."""

from __future__ import annotations

from pymongo import ASCENDING, IndexModel
from pymongo.collection import Collection


def get_index_models() -> list[IndexModel]:
    """Return the application's MongoDB index definitions."""
    return [
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


def create_indexes(collection: Collection) -> list[str]:
    """Create all application indexes and return their names."""
    return collection.create_indexes(get_index_models())


def ensure_indexes(collection: Collection) -> None:
    """Ensure required indexes exist.

    Index creation is idempotent for unchanged index definitions. In a larger
    production deployment, index lifecycle management should normally be
    handled separately from application startup.
    """
    create_indexes(collection)

"""Index definitions for the MongoDB CRUD application."""

from __future__ import annotations

from pymongo import ASCENDING, IndexModel
from pymongo.collection import Collection


def get_index_models() -> list[IndexModel]:
    """Return the application's MongoDB index definitions."""
    return [
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


def create_indexes(collection: Collection) -> list[str]:
    """Create all application indexes and return their names."""
    return collection.create_indexes(get_index_models())


def ensure_indexes(collection: Collection) -> None:
    """Ensure required indexes exist.

    Index creation is idempotent for unchanged index definitions. In a larger
    production deployment, index lifecycle management should normally be
    handled separately from application startup.
    """
    create_indexes(collection)