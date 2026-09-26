"""MongoDB query performance optimization application entry point."""

from __future__ import annotations

from pymongo import MongoClient

from config.settings import (
    MONGODB_DATABASE,
    MONGODB_URI,
    MONGODB_SERVER_SELECTION_TIMEOUT_MS,
)


def main() -> None:
    """Connect to MongoDB and verify database availability."""
    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=MONGODB_SERVER_SELECTION_TIMEOUT_MS,
    )

    try:
        client.admin.command("ping")
        database = client[MONGODB_DATABASE]

        print(f"Connected to MongoDB database: {database.name}")
    finally:
        client.close()


if __name__ == "__main__":
    main()

"""MongoDB query performance optimization application entry point."""

from __future__ import annotations

from pymongo import MongoClient

from config.settings import (
    MONGODB_DATABASE,
    MONGODB_URI,
    MONGODB_SERVER_SELECTION_TIMEOUT_MS,
)


def main() -> None:
    """Connect to MongoDB and verify database availability."""
    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=MONGODB_SERVER_SELECTION_TIMEOUT_MS,
    )

    try:
        client.admin.command("ping")
        database = client[MONGODB_DATABASE]

        print(f"Connected to MongoDB database: {database.name}")
    finally:
        client.close()


if __name__ == "__main__":
    main()