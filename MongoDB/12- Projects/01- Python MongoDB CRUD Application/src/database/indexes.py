"""MongoDB index definitions and initialization helpers."""

from __future__ import annotations

from pymongo import ASCENDING, IndexModel
from pymongo.collection import Collection


def create_indexes(collection: Collection) -> list[str]:
    """Create indexes required by the CRUD application's user collection.

    Index creation is idempotent: MongoDB reuses existing equivalent indexes
    instead of creating duplicates.
    """
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

    This helper is intended for local development and controlled deployments.
    In larger production systems, index creation is usually handled through a
    dedicated deployment or migration workflow rather than during application
    startup.
    """
    create_indexes(collection)

"""MongoDB index definitions and initialization helpers."""

from __future__ import annotations

from pymongo import ASCENDING, IndexModel
from pymongo.collection import Collection


def create_indexes(collection: Collection) -> list[str]:
    """Create indexes required by the CRUD application's user collection.

    Index creation is idempotent: MongoDB reuses existing equivalent indexes
    instead of creating duplicates.
    """
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

    This helper is intended for local development and controlled deployments.
    In larger production systems, index creation is usually handled through a
    dedicated deployment or migration workflow rather than during application
    startup.
    """
    create_indexes(collection)