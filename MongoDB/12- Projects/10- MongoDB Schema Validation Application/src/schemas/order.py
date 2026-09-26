"""Product schema definitions for MongoDB validation."""

from __future__ import annotations

from typing import Any


PRODUCT_SCHEMA: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "product_id",
            "name",
            "sku",
            "price",
            "currency",
            "category",
            "status",
        ],
        "properties": {
            "product_id": {
                "bsonType": "string",
                "minLength": 1,
                "description": "must be a non-empty product identifier",
            },
            "name": {
                "bsonType": "string",
                "minLength": 1,
                "description": "must be a non-empty product name",
            },
            "sku": {
                "bsonType": "string",
                "minLength": 1,
                "description": "must be a non-empty stock keeping unit",
            },
            "price": {
                "bsonType": ["double", "decimal", "int", "long"],
                "minimum": 0,
                "description": "must be a non-negative numeric price",
            },
            "currency": {
                "bsonType": "string",
                "enum": ["INR", "USD", "EUR", "GBP"],
                "description": "must be a supported currency code",
            },
            "category": {
                "bsonType": "string",
                "minLength": 1,
                "description": "must be a non-empty product category",
            },
            "status": {
                "bsonType": "string",
                "enum": ["active", "inactive", "discontinued"],
                "description": "must be a supported product status",
            },
            "description": {
                "bsonType": "string",
                "maxLength": 5000,
                "description": "must be a string when provided",
            },
            "stock_quantity": {
                "bsonType": "int",
                "minimum": 0,
                "description": "must be a non-negative integer",
            },
            "tags": {
                "bsonType": "array",
                "items": {"bsonType": "string"},
                "description": "must contain only string tags",
            },
            "dimensions": {
                "bsonType": "object",
                "properties": {
                    "length": {
                        "bsonType": ["double", "decimal", "int", "long"],
                        "minimum": 0,
                    },
                    "width": {
                        "bsonType": ["double", "decimal", "int", "long"],
                        "minimum": 0,
                    },
                    "height": {
                        "bsonType": ["double", "decimal", "int", "long"],
                        "minimum": 0,
                    },
                },
                "additionalProperties": True,
            },
        },
        "additionalProperties": True,
    }
}


def get_product_schema() -> dict[str, Any]:
    """Return a copy of the MongoDB product document validator."""
    return PRODUCT_SCHEMA.copy()

"""Product schema definitions for MongoDB validation."""

from __future__ import annotations

from typing import Any


PRODUCT_SCHEMA: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "product_id",
            "name",
            "sku",
            "price",
            "currency",
            "category",
            "status",
        ],
        "properties": {
            "product_id": {
                "bsonType": "string",
                "minLength": 1,
                "description": "must be a non-empty product identifier",
            },
            "name": {
                "bsonType": "string",
                "minLength": 1,
                "description": "must be a non-empty product name",
            },
            "sku": {
                "bsonType": "string",
                "minLength": 1,
                "description": "must be a non-empty stock keeping unit",
            },
            "price": {
                "bsonType": ["double", "decimal", "int", "long"],
                "minimum": 0,
                "description": "must be a non-negative numeric price",
            },
            "currency": {
                "bsonType": "string",
                "enum": ["INR", "USD", "EUR", "GBP"],
                "description": "must be a supported currency code",
            },
            "category": {
                "bsonType": "string",
                "minLength": 1,
                "description": "must be a non-empty product category",
            },
            "status": {
                "bsonType": "string",
                "enum": ["active", "inactive", "discontinued"],
                "description": "must be a supported product status",
            },
            "description": {
                "bsonType": "string",
                "maxLength": 5000,
                "description": "must be a string when provided",
            },
            "stock_quantity": {
                "bsonType": "int",
                "minimum": 0,
                "description": "must be a non-negative integer",
            },
            "tags": {
                "bsonType": "array",
                "items": {"bsonType": "string"},
                "description": "must contain only string tags",
            },
            "dimensions": {
                "bsonType": "object",
                "properties": {
                    "length": {
                        "bsonType": ["double", "decimal", "int", "long"],
                        "minimum": 0,
                    },
                    "width": {
                        "bsonType": ["double", "decimal", "int", "long"],
                        "minimum": 0,
                    },
                    "height": {
                        "bsonType": ["double", "decimal", "int", "long"],
                        "minimum": 0,
                    },
                },
                "additionalProperties": True,
            },
        },
        "additionalProperties": True,
    }
}


def get_product_schema() -> dict[str, Any]:
    """Return a copy of the MongoDB product document validator."""
    return PRODUCT_SCHEMA.copy()