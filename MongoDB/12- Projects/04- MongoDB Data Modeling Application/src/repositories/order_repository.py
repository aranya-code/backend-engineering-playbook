"""Repository for MongoDB order persistence operations."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from database.connection import get_database
from models.order import build_order, update_order_status


def get_order_collection() -> Collection:
    """Return the MongoDB collection used for orders."""
    return get_database()["orders"]


def create_order(
    *,
    customer_id: ObjectId,
    items: list[dict[str, Any]],
    currency: str = "USD",
) -> dict[str, Any]:
    """Create and persist an order document."""
    document = build_order(
        customer_id=customer_id,
        items=items,
        currency=currency,
    )

    get_order_collection().insert_one(document)
    return document


def get_order_by_id(order_id: ObjectId) -> dict[str, Any] | None:
    """Return an order by its MongoDB ObjectId."""
    return get_order_collection().find_one({"_id": order_id})


def list_orders_for_customer(
    customer_id: ObjectId,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return a customer's orders ordered from newest to oldest."""
    if skip < 0:
        raise ValueError("skip cannot be negative.")

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    cursor = (
        get_order_collection()
        .find({"customer_id": customer_id})
        .sort("created_at", DESCENDING)
        .skip(skip)
        .limit(limit)
    )

    return list(cursor)


def list_orders_by_status(
    status: str,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return orders filtered by status."""
    if skip < 0:
        raise ValueError("skip cannot be negative.")

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    cursor = (
        get_order_collection()
        .find({"status": status.strip().lower()})
        .sort("created_at", DESCENDING)
        .skip(skip)
        .limit(limit)
    )

    return list(cursor)


def update_order_status_by_id(
    order_id: ObjectId,
    status: str,
) -> dict[str, Any] | None:
    """Update an order status and return the updated document."""
    update = update_order_status(status)

    return get_order_collection().find_one_and_update(
        {"_id": order_id},
        update,
        return_document=ReturnDocument.AFTER,
    )


def cancel_order(order_id: ObjectId) -> dict[str, Any] | None:
    """Cancel an order and return the updated document."""
    return update_order_status_by_id(order_id, "cancelled")


def delete_order(order_id: ObjectId) -> bool:
    """Delete an order and return whether a document was removed."""
    result = get_order_collection().delete_one({"_id": order_id})
    return result.deleted_count == 1


def order_exists(order_id: ObjectId) -> bool:
    """Check whether an order exists using an indexed identifier lookup."""
    return (
        get_order_collection()
        .find_one(
            {"_id": order_id},
            projection={"_id": 1},
        )
        is not None
    )


def ensure_order_indexes() -> None:
    """Create indexes required by the repository access patterns."""
    collection = get_order_collection()

    collection.create_index(
        [("customer_id", ASCENDING), ("created_at", DESCENDING)],
        name="idx_customer_created_at",
    )

    collection.create_index(
        [("status", ASCENDING), ("created_at", DESCENDING)],
        name="idx_status_created_at",
    )

"""Repository for MongoDB order persistence operations."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from database.connection import get_database
from models.order import build_order, update_order_status


def get_order_collection() -> Collection:
    """Return the MongoDB collection used for orders."""
    return get_database()["orders"]


def create_order(
    *,
    customer_id: ObjectId,
    items: list[dict[str, Any]],
    currency: str = "USD",
) -> dict[str, Any]:
    """Create and persist an order document."""
    document = build_order(
        customer_id=customer_id,
        items=items,
        currency=currency,
    )

    get_order_collection().insert_one(document)
    return document


def get_order_by_id(order_id: ObjectId) -> dict[str, Any] | None:
    """Return an order by its MongoDB ObjectId."""
    return get_order_collection().find_one({"_id": order_id})


def list_orders_for_customer(
    customer_id: ObjectId,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return a customer's orders ordered from newest to oldest."""
    if skip < 0:
        raise ValueError("skip cannot be negative.")

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    cursor = (
        get_order_collection()
        .find({"customer_id": customer_id})
        .sort("created_at", DESCENDING)
        .skip(skip)
        .limit(limit)
    )

    return list(cursor)


def list_orders_by_status(
    status: str,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return orders filtered by status."""
    if skip < 0:
        raise ValueError("skip cannot be negative.")

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    cursor = (
        get_order_collection()
        .find({"status": status.strip().lower()})
        .sort("created_at", DESCENDING)
        .skip(skip)
        .limit(limit)
    )

    return list(cursor)


def update_order_status_by_id(
    order_id: ObjectId,
    status: str,
) -> dict[str, Any] | None:
    """Update an order status and return the updated document."""
    update = update_order_status(status)

    return get_order_collection().find_one_and_update(
        {"_id": order_id},
        update,
        return_document=ReturnDocument.AFTER,
    )


def cancel_order(order_id: ObjectId) -> dict[str, Any] | None:
    """Cancel an order and return the updated document."""
    return update_order_status_by_id(order_id, "cancelled")


def delete_order(order_id: ObjectId) -> bool:
    """Delete an order and return whether a document was removed."""
    result = get_order_collection().delete_one({"_id": order_id})
    return result.deleted_count == 1


def order_exists(order_id: ObjectId) -> bool:
    """Check whether an order exists using an indexed identifier lookup."""
    return (
        get_order_collection()
        .find_one(
            {"_id": order_id},
            projection={"_id": 1},
        )
        is not None
    )


def ensure_order_indexes() -> None:
    """Create indexes required by the repository access patterns."""
    collection = get_order_collection()

    collection.create_index(
        [("customer_id", ASCENDING), ("created_at", DESCENDING)],
        name="idx_customer_created_at",
    )

    collection.create_index(
        [("status", ASCENDING), ("created_at", DESCENDING)],
        name="idx_status_created_at",
    )