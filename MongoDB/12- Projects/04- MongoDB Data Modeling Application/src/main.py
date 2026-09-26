"""MongoDB data modeling application entry point."""

from __future__ import annotations

import os

from pymongo import MongoClient
from pymongo.errors import PyMongoError


def main() -> None:
    """Run a basic MongoDB connectivity check."""
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("MONGODB_DATABASE", "mongodb_data_modeling")

    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=int(
            os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000")
        ),
    )

    try:
        client.admin.command("ping")
        database = client[database_name]

        print(f"Connected to MongoDB database: {database.name}")
    except PyMongoError as exc:
        raise RuntimeError("Unable to connect to MongoDB.") from exc
    finally:
        client.close()


if __name__ == "__main__":
    main()

"""MongoDB data modeling application entry point."""

from __future__ import annotations

import os

from pymongo import MongoClient
from pymongo.errors import PyMongoError


def main() -> None:
    """Run a basic MongoDB connectivity check."""
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("MONGODB_DATABASE", "mongodb_data_modeling")

    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=int(
            os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000")
        ),
    )

    try:
        client.admin.command("ping")
        database = client[database_name]

        print(f"Connected to MongoDB database: {database.name}")
    except PyMongoError as exc:
        raise RuntimeError("Unable to connect to MongoDB.") from exc
    finally:
        client.close()


if __name__ == "__main__":
    main()