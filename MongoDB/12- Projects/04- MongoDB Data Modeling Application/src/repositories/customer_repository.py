"""Repository for MongoDB customer persistence operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from bson import ObjectId
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError

from database.connection import get_database
from models.customer import build_customer, update_customer_fields


def get_customer_collection() -> Collection:
    """Return the MongoDB collection used for customers."""
    return get_database()["customers"]


def create_customer(
    *,
    name: str,
    email: str,
    is_active: bool = True,
    phone: str | None = None,
) -> dict[str, Any]:
    """Create and persist a customer document.

    Raises:
        ValueError: If the model data is invalid.
        DuplicateKeyError: If the email already exists.
        PyMongoError: If MongoDB rejects the operation.
    """
    document = build_customer(
        name=name,
        email=email,
        is_active=is_active,
        phone=phone,
    )

    get_customer_collection().insert_one(document)
    return document


def get_customer_by_id(customer_id: ObjectId) -> dict[str, Any] | None:
    """Return a customer by its MongoDB ObjectId."""
    return get_customer_collection().find_one({"_id": customer_id})


def get_customer_by_email(email: str) -> dict[str, Any] | None:
    """Return a customer by normalized email address."""
    normalized_email = email.strip().lower()
    return get_customer_collection().find_one({"email": normalized_email})


def list_customers(
    *,
    skip: int = 0,
    limit: int = 50,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    """Return customers using bounded offset pagination."""
    if skip < 0:
        raise ValueError("skip cannot be negative.")

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    filters: dict[str, Any] = {}

    if is_active is not None:
        filters["is_active"] = is_active

    cursor = (
        get_customer_collection()
        .find(filters)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    return list(cursor)


def update_customer(
    customer_id: ObjectId,
    *,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    is_active: bool | None = None,
) -> dict[str, Any] | None:
    """Update a customer and return the updated document."""
    updates = update_customer_fields(
        name=name,
        email=email,
        phone=phone,
        is_active=is_active,
    )

    result = get_customer_collection().find_one_and_update(
        {"_id": customer_id},
        {"$set": updates},
        return_document=True,
    )

    return result


def delete_customer(customer_id: ObjectId) -> bool:
    """Delete a customer and return whether a document was removed."""
    result = get_customer_collection().delete_one({"_id": customer_id})
    return result.deleted_count == 1


def customer_exists(
    *,
    customer_id: ObjectId | None = None,
    email: str | None = None,
) -> bool:
    """Check whether a customer exists using an indexed lookup."""
    if customer_id is None and email is None:
        raise ValueError("customer_id or email must be provided.")

    filters: dict[str, Any] = {}

    if customer_id is not None:
        filters["_id"] = customer_id
    else:
        filters["email"] = email.strip().lower()

    return (
        get_customer_collection()
        .find_one(filters, projection={"_id": 1})
        is not None
    )


def update_customer_from_mapping(
    customer_id: ObjectId,
    fields: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Update allowed customer fields from a mapping.

    This helper intentionally whitelists fields through the model update
    function rather than passing arbitrary client-provided keys to MongoDB.
    """
    updates = update_customer_fields(
        name=fields.get("name"),
        email=fields.get("email"),
        phone=fields.get("phone"),
        is_active=fields.get("is_active"),
    )

    return get_customer_collection().find_one_and_update(
        {"_id": customer_id},
        {"$set": updates},
        return_document=True,
    )

"""Repository for MongoDB customer persistence operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from bson import ObjectId
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError

from database.connection import get_database
from models.customer import build_customer, update_customer_fields


def get_customer_collection() -> Collection:
    """Return the MongoDB collection used for customers."""
    return get_database()["customers"]


def create_customer(
    *,
    name: str,
    email: str,
    is_active: bool = True,
    phone: str | None = None,
) -> dict[str, Any]:
    """Create and persist a customer document.

    Raises:
        ValueError: If the model data is invalid.
        DuplicateKeyError: If the email already exists.
        PyMongoError: If MongoDB rejects the operation.
    """
    document = build_customer(
        name=name,
        email=email,
        is_active=is_active,
        phone=phone,
    )

    get_customer_collection().insert_one(document)
    return document


def get_customer_by_id(customer_id: ObjectId) -> dict[str, Any] | None:
    """Return a customer by its MongoDB ObjectId."""
    return get_customer_collection().find_one({"_id": customer_id})


def get_customer_by_email(email: str) -> dict[str, Any] | None:
    """Return a customer by normalized email address."""
    normalized_email = email.strip().lower()
    return get_customer_collection().find_one({"email": normalized_email})


def list_customers(
    *,
    skip: int = 0,
    limit: int = 50,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    """Return customers using bounded offset pagination."""
    if skip < 0:
        raise ValueError("skip cannot be negative.")

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    filters: dict[str, Any] = {}

    if is_active is not None:
        filters["is_active"] = is_active

    cursor = (
        get_customer_collection()
        .find(filters)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    return list(cursor)


def update_customer(
    customer_id: ObjectId,
    *,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    is_active: bool | None = None,
) -> dict[str, Any] | None:
    """Update a customer and return the updated document."""
    updates = update_customer_fields(
        name=name,
        email=email,
        phone=phone,
        is_active=is_active,
    )

    result = get_customer_collection().find_one_and_update(
        {"_id": customer_id},
        {"$set": updates},
        return_document=True,
    )

    return result


def delete_customer(customer_id: ObjectId) -> bool:
    """Delete a customer and return whether a document was removed."""
    result = get_customer_collection().delete_one({"_id": customer_id})
    return result.deleted_count == 1


def customer_exists(
    *,
    customer_id: ObjectId | None = None,
    email: str | None = None,
) -> bool:
    """Check whether a customer exists using an indexed lookup."""
    if customer_id is None and email is None:
        raise ValueError("customer_id or email must be provided.")

    filters: dict[str, Any] = {}

    if customer_id is not None:
        filters["_id"] = customer_id
    else:
        filters["email"] = email.strip().lower()

    return (
        get_customer_collection()
        .find_one(filters, projection={"_id": 1})
        is not None
    )


def update_customer_from_mapping(
    customer_id: ObjectId,
    fields: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Update allowed customer fields from a mapping.

    This helper intentionally whitelists fields through the model update
    function rather than passing arbitrary client-provided keys to MongoDB.
    """
    updates = update_customer_fields(
        name=fields.get("name"),
        email=fields.get("email"),
        phone=fields.get("phone"),
        is_active=fields.get("is_active"),
    )

    return get_customer_collection().find_one_and_update(
        {"_id": customer_id},
        {"$set": updates},
        return_document=True,
    )