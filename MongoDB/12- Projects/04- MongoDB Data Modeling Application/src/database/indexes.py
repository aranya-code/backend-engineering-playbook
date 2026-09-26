"""MongoDB index management utilities."""

from __future__ import annotations

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection

from database.connection import get_database


def create_indexes(collection: Collection) -> None:
    """Create indexes required by the collection's access patterns."""
    collection.create_index(
        [("email", ASCENDING)],
        unique=True,
        name="uq_email",
    )

    collection.create_index(
        [("status", ASCENDING), ("created_at", DESCENDING)],
        name="idx_status_created_at",
    )

    collection.create_index(
        [("customer_id", ASCENDING), ("created_at", DESCENDING)],
        name="idx_customer_created_at",
    )


def initialize_indexes() -> None:
    """Create indexes for the application's primary collections."""
    database = get_database()
    create_indexes(database["users"])

"""MongoDB index management utilities."""

from __future__ import annotations

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection

from database.connection import get_database


def create_indexes(collection: Collection) -> None:
    """Create indexes required by the collection's access patterns."""
    collection.create_index(
        [("email", ASCENDING)],
        unique=True,
        name="uq_email",
    )

    collection.create_index(
        [("status", ASCENDING), ("created_at", DESCENDING)],
        name="idx_status_created_at",
    )

    collection.create_index(
        [("customer_id", ASCENDING), ("created_at", DESCENDING)],
        name="idx_customer_created_at",
    )


def initialize_indexes() -> None:
    """Create indexes for the application's primary collections."""
    database = get_database()
    create_indexes(database["users"])