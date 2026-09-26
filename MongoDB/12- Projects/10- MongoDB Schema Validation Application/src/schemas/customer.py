"""Customer schema definitions for MongoDB validation."""

from __future__ import annotations

from typing import Any


CUSTOMER_SCHEMA: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "customer_id",
            "name",
            "email",
            "age",
            "status",
        ],
        "properties": {
            "customer_id": {
                "bsonType": "string",
                "minLength": 1,
                "description": "must be a non-empty customer identifier",
            },
            "name": {
                "bsonType": "string",
                "minLength": 1,
                "description": "must be a non-empty customer name",
            },
            "email": {
                "bsonType": "string",
                "minLength": 3,
                "description": "must be an email string validated by the application",
            },
            "age": {
                "bsonType": "int",
                "minimum": 18,
                "description": "must be an integer greater than or equal to 18",
            },
            "status": {
                "bsonType": "string",
                "enum": [
                    "active",
                    "inactive",
                    "suspended",
                ],
                "description": "must be a supported customer status",
            },
            "roles": {
                "bsonType": "array",
                "items": {
                    "bsonType": "string",
                },
                "description": "must contain only string role names",
            },
            "phone": {
                "bsonType": "string",
                "minLength": 7,
                "description": "must be a phone number string",
            },
            "address": {
                "bsonType": "object",
                "required": [
                    "city",
                    "country",
                ],
                "properties": {
                    "street": {
                        "bsonType": "string",
                    },
                    "city": {
                        "bsonType": "string",
                        "minLength": 1,
                    },
                    "state": {
                        "bsonType": "string",
                    },
                    "postal_code": {
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


def get_customer_schema() -> dict[str, Any]:
    """Return the MongoDB JSON Schema validator for customer documents."""
    return CUSTOMER_SCHEMA.copy()

"""Customer schema definitions for MongoDB validation."""

from __future__ import annotations

from typing import Any


CUSTOMER_SCHEMA: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "customer_id",
            "name",
            "email",
            "age",
            "status",
        ],
        "properties": {
            "customer_id": {
                "bsonType": "string",
                "minLength": 1,
                "description": "must be a non-empty customer identifier",
            },
            "name": {
                "bsonType": "string",
                "minLength": 1,
                "description": "must be a non-empty customer name",
            },
            "email": {
                "bsonType": "string",
                "minLength": 3,
                "description": "must be an email string validated by the application",
            },
            "age": {
                "bsonType": "int",
                "minimum": 18,
                "description": "must be an integer greater than or equal to 18",
            },
            "status": {
                "bsonType": "string",
                "enum": [
                    "active",
                    "inactive",
                    "suspended",
                ],
                "description": "must be a supported customer status",
            },
            "roles": {
                "bsonType": "array",
                "items": {
                    "bsonType": "string",
                },
                "description": "must contain only string role names",
            },
            "phone": {
                "bsonType": "string",
                "minLength": 7,
                "description": "must be a phone number string",
            },
            "address": {
                "bsonType": "object",
                "required": [
                    "city",
                    "country",
                ],
                "properties": {
                    "street": {
                        "bsonType": "string",
                    },
                    "city": {
                        "bsonType": "string",
                        "minLength": 1,
                    },
                    "state": {
                        "bsonType": "string",
                    },
                    "postal_code": {
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


def get_customer_schema() -> dict[str, Any]:
    """Return the MongoDB JSON Schema validator for customer documents."""
    return CUSTOMER_SCHEMA.copy()