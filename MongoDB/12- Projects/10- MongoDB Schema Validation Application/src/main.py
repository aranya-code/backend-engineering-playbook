"""MongoDB schema validation application entry point."""

from __future__ import annotations

import os
from typing import Any

from pymongo import MongoClient
from pymongo.errors import (
    CollectionInvalid,
    OperationFailure,
    PyMongoError,
)


MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017",
)

MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "mongodb_schema_validation",
)

MONGODB_COLLECTION = os.getenv(
    "MONGODB_COLLECTION",
    "users",
)


USER_SCHEMA: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "name",
            "email",
            "age",
        ],
        "properties": {
            "name": {
                "bsonType": "string",
                "description": "must be a string",
            },
            "email": {
                "bsonType": "string",
                "description": "must be a string",
            },
            "age": {
                "bsonType": "int",
                "minimum": 18,
                "description": "must be an integer greater than or equal to 18",
            },
            "roles": {
                "bsonType": "array",
                "items": {
                    "bsonType": "string",
                },
                "description": "must be an array of strings",
            },
            "address": {
                "bsonType": "object",
                "required": [
                    "city",
                    "country",
                ],
                "properties": {
                    "city": {
                        "bsonType": "string",
                    },
                    "country": {
                        "bsonType": "string",
                    },
                },
            },
        },
    }
}


def get_client() -> MongoClient:
    """Create a MongoDB client using application configuration."""
    return MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5_000,
        connectTimeoutMS=5_000,
        socketTimeoutMS=30_000,
        retryReads=True,
        retryWrites=True,
    )


def create_validated_collection(
    database: Any,
    collection_name: str,
) -> Any:
    """Create a collection with MongoDB JSON Schema validation.

    MongoDB enforces this schema at the database boundary, protecting the
    collection even when writes originate outside the application.
    """
    try:
        return database.create_collection(
            collection_name,
            validator=USER_SCHEMA,
            validationLevel="strict",
            validationAction="error",
        )
    except CollectionInvalid:
        collection = database[collection_name]

        collection_info = database.command(
            "listCollections",
            filter={"name": collection_name},
        )

        existing = next(
            collection_info["cursor"]["firstBatch"],
            None,
        )

        if existing is None:
            raise

        options = existing.get("options", {})

        if options.get("validator") != USER_SCHEMA:
            database.command(
                "collMod",
                collection_name,
                validator=USER_SCHEMA,
                validationLevel="strict",
                validationAction="error",
            )

        return collection


def insert_valid_document(collection: Any) -> Any:
    """Insert a document that satisfies the configured schema."""
    document = {
        "name": "Alice",
        "email": "alice@example.com",
        "age": 30,
        "roles": [
            "user",
            "admin",
        ],
        "address": {
            "city": "Kolkata",
            "country": "India",
        },
    }

    return collection.insert_one(document)


def insert_invalid_document(collection: Any) -> None:
    """Demonstrate MongoDB rejecting a document that violates the schema."""
    invalid_document = {
        "name": "Bob",
        "email": "bob@example.com",
        "age": 16,
    }

    try:
        collection.insert_one(invalid_document)
    except OperationFailure as exc:
        print(f"Schema validation rejected the document: {exc}")


def main() -> int:
    """Run the MongoDB schema validation example."""
    client = get_client()

    try:
        client.admin.command("ping")

        database = client[MONGODB_DATABASE]
        collection = create_validated_collection(
            database,
            MONGODB_COLLECTION,
        )

        result = insert_valid_document(collection)

        print(f"Inserted valid document: {result.inserted_id}")

        insert_invalid_document(collection)

        return 0

    except PyMongoError as exc:
        print(f"MongoDB operation failed: {exc}")
        return 1

    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())

"""MongoDB schema validation application entry point."""

from __future__ import annotations

import os
from typing import Any

from pymongo import MongoClient
from pymongo.errors import (
    CollectionInvalid,
    OperationFailure,
    PyMongoError,
)


MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017",
)

MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "mongodb_schema_validation",
)

MONGODB_COLLECTION = os.getenv(
    "MONGODB_COLLECTION",
    "users",
)


USER_SCHEMA: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "name",
            "email",
            "age",
        ],
        "properties": {
            "name": {
                "bsonType": "string",
                "description": "must be a string",
            },
            "email": {
                "bsonType": "string",
                "description": "must be a string",
            },
            "age": {
                "bsonType": "int",
                "minimum": 18,
                "description": "must be an integer greater than or equal to 18",
            },
            "roles": {
                "bsonType": "array",
                "items": {
                    "bsonType": "string",
                },
                "description": "must be an array of strings",
            },
            "address": {
                "bsonType": "object",
                "required": [
                    "city",
                    "country",
                ],
                "properties": {
                    "city": {
                        "bsonType": "string",
                    },
                    "country": {
                        "bsonType": "string",
                    },
                },
            },
        },
    }
}


def get_client() -> MongoClient:
    """Create a MongoDB client using application configuration."""
    return MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5_000,
        connectTimeoutMS=5_000,
        socketTimeoutMS=30_000,
        retryReads=True,
        retryWrites=True,
    )


def create_validated_collection(
    database: Any,
    collection_name: str,
) -> Any:
    """Create a collection with MongoDB JSON Schema validation.

    MongoDB enforces this schema at the database boundary, protecting the
    collection even when writes originate outside the application.
    """
    try:
        return database.create_collection(
            collection_name,
            validator=USER_SCHEMA,
            validationLevel="strict",
            validationAction="error",
        )
    except CollectionInvalid:
        collection = database[collection_name]

        collection_info = database.command(
            "listCollections",
            filter={"name": collection_name},
        )

        existing = next(
            collection_info["cursor"]["firstBatch"],
            None,
        )

        if existing is None:
            raise

        options = existing.get("options", {})

        if options.get("validator") != USER_SCHEMA:
            database.command(
                "collMod",
                collection_name,
                validator=USER_SCHEMA,
                validationLevel="strict",
                validationAction="error",
            )

        return collection


def insert_valid_document(collection: Any) -> Any:
    """Insert a document that satisfies the configured schema."""
    document = {
        "name": "Alice",
        "email": "alice@example.com",
        "age": 30,
        "roles": [
            "user",
            "admin",
        ],
        "address": {
            "city": "Kolkata",
            "country": "India",
        },
    }

    return collection.insert_one(document)


def insert_invalid_document(collection: Any) -> None:
    """Demonstrate MongoDB rejecting a document that violates the schema."""
    invalid_document = {
        "name": "Bob",
        "email": "bob@example.com",
        "age": 16,
    }

    try:
        collection.insert_one(invalid_document)
    except OperationFailure as exc:
        print(f"Schema validation rejected the document: {exc}")


def main() -> int:
    """Run the MongoDB schema validation example."""
    client = get_client()

    try:
        client.admin.command("ping")

        database = client[MONGODB_DATABASE]
        collection = create_validated_collection(
            database,
            MONGODB_COLLECTION,
        )

        result = insert_valid_document(collection)

        print(f"Inserted valid document: {result.inserted_id}")

        insert_invalid_document(collection)

        return 0

    except PyMongoError as exc:
        print(f"MongoDB operation failed: {exc}")
        return 1

    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())