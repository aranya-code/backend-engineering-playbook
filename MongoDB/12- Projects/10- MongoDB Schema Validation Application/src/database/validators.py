"""MongoDB schema validation definitions and helpers."""

from __future__ import annotations

from typing import Any

from pymongo.database import Database
from pymongo.errors import CollectionInvalid

from config.settings import (
    MONGODB_COLLECTION,
    MONGODB_VALIDATION_ACTION,
    MONGODB_VALIDATION_LEVEL,
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
                "minLength": 1,
                "description": "must be a non-empty string",
            },
            "email": {
                "bsonType": "string",
                "minLength": 3,
                "description": "must be a valid application-level email string",
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
                "description": "must be an array containing only strings",
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
                        "minLength": 1,
                    },
                    "country": {
                        "bsonType": "string",
                        "minLength": 1,
                    },
                },
                "additionalProperties": True,
            },
        },
        "additionalProperties": True,
    }
}


def create_validated_collection(database: Database) -> Any:
    """Create or configure the application collection with schema validation.

    MongoDB enforces the validator at the database boundary, protecting the
    collection from invalid writes regardless of whether they originate from
    this application, another service, or a MongoDB client.
    """
    try:
        return database.create_collection(
            MONGODB_COLLECTION,
            validator=USER_SCHEMA,
            validationLevel=MONGODB_VALIDATION_LEVEL,
            validationAction=MONGODB_VALIDATION_ACTION,
        )
    except CollectionInvalid:
        database.command(
            "collMod",
            MONGODB_COLLECTION,
            validator=USER_SCHEMA,
            validationLevel=MONGODB_VALIDATION_LEVEL,
            validationAction=MONGODB_VALIDATION_ACTION,
        )

        return database[MONGODB_COLLECTION]


def get_validator() -> dict[str, Any]:
    """Return a defensive copy of the configured MongoDB validator."""
    return {
        **USER_SCHEMA,
        "$jsonSchema": {
            **USER_SCHEMA["$jsonSchema"],
            "required": list(USER_SCHEMA["$jsonSchema"]["required"]),
            "properties": {
                name: dict(properties)
                for name, properties
                in USER_SCHEMA["$jsonSchema"]["properties"].items()
            },
        },
    }

"""MongoDB schema validation definitions and helpers."""

from __future__ import annotations

from typing import Any

from pymongo.database import Database
from pymongo.errors import CollectionInvalid

from config.settings import (
    MONGODB_COLLECTION,
    MONGODB_VALIDATION_ACTION,
    MONGODB_VALIDATION_LEVEL,
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
                "minLength": 1,
                "description": "must be a non-empty string",
            },
            "email": {
                "bsonType": "string",
                "minLength": 3,
                "description": "must be a valid application-level email string",
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
                "description": "must be an array containing only strings",
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
                        "minLength": 1,
                    },
                    "country": {
                        "bsonType": "string",
                        "minLength": 1,
                    },
                },
                "additionalProperties": True,
            },
        },
        "additionalProperties": True,
    }
}


def create_validated_collection(database: Database) -> Any:
    """Create or configure the application collection with schema validation.

    MongoDB enforces the validator at the database boundary, protecting the
    collection from invalid writes regardless of whether they originate from
    this application, another service, or a MongoDB client.
    """
    try:
        return database.create_collection(
            MONGODB_COLLECTION,
            validator=USER_SCHEMA,
            validationLevel=MONGODB_VALIDATION_LEVEL,
            validationAction=MONGODB_VALIDATION_ACTION,
        )
    except CollectionInvalid:
        database.command(
            "collMod",
            MONGODB_COLLECTION,
            validator=USER_SCHEMA,
            validationLevel=MONGODB_VALIDATION_LEVEL,
            validationAction=MONGODB_VALIDATION_ACTION,
        )

        return database[MONGODB_COLLECTION]


def get_validator() -> dict[str, Any]:
    """Return a defensive copy of the configured MongoDB validator."""
    return {
        **USER_SCHEMA,
        "$jsonSchema": {
            **USER_SCHEMA["$jsonSchema"],
            "required": list(USER_SCHEMA["$jsonSchema"]["required"]),
            "properties": {
                name: dict(properties)
                for name, properties
                in USER_SCHEMA["$jsonSchema"]["properties"].items()
            },
        },
    }