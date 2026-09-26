"""Application entry point for the MongoDB CRUD project."""

from __future__ import annotations

import os

from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError


def get_mongodb_client() -> MongoClient:
    """Create a MongoDB client using environment-based configuration."""
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    timeout_ms = int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000"))

    return MongoClient(
        uri,
        serverSelectionTimeoutMS=timeout_ms,
        connectTimeoutMS=timeout_ms,
    )


def main() -> None:
    """Run a small CRUD workflow against MongoDB."""
    client = get_mongodb_client()

    try:
        client.admin.command("ping")

        database = client["crud_app"]
        collection = database["users"]

        result = collection.insert_one(
            {
                "name": "Alice",
                "email": "alice@example.com",
                "active": True,
            }
        )

        print(f"Inserted document: {result.inserted_id}")

        document = collection.find_one({"_id": result.inserted_id})
        print(f"Found document: {document}")

        collection.update_one(
            {"_id": result.inserted_id},
            {"$set": {"active": False}},
        )

        updated_document = collection.find_one({"_id": result.inserted_id})
        print(f"Updated document: {updated_document}")

        collection.delete_one({"_id": result.inserted_id})
        print("Document deleted.")

    except ServerSelectionTimeoutError as exc:
        print(f"Unable to connect to MongoDB: {exc}")
        raise SystemExit(1) from exc
    except PyMongoError as exc:
        print(f"MongoDB operation failed: {exc}")
        raise SystemExit(1) from exc
    finally:
        client.close()


if __name__ == "__main__":
    main()

"""Application entry point for the MongoDB CRUD project."""

from __future__ import annotations

import os

from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError


def get_mongodb_client() -> MongoClient:
    """Create a MongoDB client using environment-based configuration."""
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    timeout_ms = int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000"))

    return MongoClient(
        uri,
        serverSelectionTimeoutMS=timeout_ms,
        connectTimeoutMS=timeout_ms,
    )


def main() -> None:
    """Run a small CRUD workflow against MongoDB."""
    client = get_mongodb_client()

    try:
        client.admin.command("ping")

        database = client["crud_app"]
        collection = database["users"]

        result = collection.insert_one(
            {
                "name": "Alice",
                "email": "alice@example.com",
                "active": True,
            }
        )

        print(f"Inserted document: {result.inserted_id}")

        document = collection.find_one({"_id": result.inserted_id})
        print(f"Found document: {document}")

        collection.update_one(
            {"_id": result.inserted_id},
            {"$set": {"active": False}},
        )

        updated_document = collection.find_one({"_id": result.inserted_id})
        print(f"Updated document: {updated_document}")

        collection.delete_one({"_id": result.inserted_id})
        print("Document deleted.")

    except ServerSelectionTimeoutError as exc:
        print(f"Unable to connect to MongoDB: {exc}")
        raise SystemExit(1) from exc
    except PyMongoError as exc:
        print(f"MongoDB operation failed: {exc}")
        raise SystemExit(1) from exc
    finally:
        client.close()


if __name__ == "__main__":
    main()