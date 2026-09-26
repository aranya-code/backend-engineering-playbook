"""Repository for MongoDB product persistence operations."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.collection import Collection

from database.connection import get_database
from models.product import build_product, update_product_fields


def get_product_collection() -> Collection:
    """Return the MongoDB collection used for products."""
    return get_database()["products"]


def create_product(
    *,
    name: str,
    sku: str,
    price: Decimal | str | float,
    category: str,
    stock_quantity: int = 0,
    description: str | None = None,
    is_active: bool = True,
) -> dict[str, Any]:
    """Create and persist a product document."""
    document = build_product(
        name=name,
        sku=sku,
        price=price,
        category=category,
        stock_quantity=stock_quantity,
        description=description,
        is_active=is_active,
    )

    get_product_collection().insert_one(document)
    return document


def get_product_by_id(product_id: ObjectId) -> dict[str, Any] | None:
    """Return a product by its MongoDB ObjectId."""
    return get_product_collection().find_one({"_id": product_id})


def get_product_by_sku(sku: str) -> dict[str, Any] | None:
    """Return a product by its normalized SKU."""
    return get_product_collection().find_one(
        {"sku": sku.strip().upper()},
    )


def list_products(
    *,
    skip: int = 0,
    limit: int = 50,
    category: str | None = None,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    """Return products using bounded offset pagination."""
    if skip < 0:
        raise ValueError("skip cannot be negative.")

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    filters: dict[str, Any] = {}

    if category is not None:
        filters["category"] = category.strip()

    if is_active is not None:
        filters["is_active"] = is_active

    cursor = (
        get_product_collection()
        .find(filters)
        .sort("created_at", DESCENDING)
        .skip(skip)
        .limit(limit)
    )

    return list(cursor)


def search_products(
    search_term: str,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Search active products by name using a case-insensitive regex."""
    normalized_term = search_term.strip()

    if not normalized_term:
        raise ValueError("search_term cannot be empty.")

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    return list(
        get_product_collection()
        .find(
            {
                "name": {
                    "$regex": normalized_term,
                    "$options": "i",
                },
                "is_active": True,
            },
            projection={
                "_id": 1,
                "name": 1,
                "sku": 1,
                "price": 1,
                "category": 1,
                "stock_quantity": 1,
            },
        )
        .sort("name", ASCENDING)
        .limit(limit)
    )


def update_product(
    product_id: ObjectId,
    *,
    name: str | None = None,
    price: Decimal | str | float | None = None,
    category: str | None = None,
    stock_quantity: int | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> dict[str, Any] | None:
    """Update a product and return the updated document."""
    updates = update_product_fields(
        name=name,
        price=price,
        category=category,
        stock_quantity=stock_quantity,
        description=description,
        is_active=is_active,
    )

    return get_product_collection().find_one_and_update(
        {"_id": product_id},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )


def adjust_stock(
    product_id: ObjectId,
    quantity_delta: int,
) -> dict[str, Any] | None:
    """Atomically adjust product stock and return the updated document.

    A negative delta decrements stock and a positive delta increments it.
    The filter prevents stock from becoming negative.
    """
    if quantity_delta == 0:
        raise ValueError("quantity_delta cannot be zero.")

    collection = get_product_collection()

    filter_query: dict[str, Any] = {"_id": product_id}

    if quantity_delta < 0:
        filter_query["stock_quantity"] = {
            "$gte": abs(quantity_delta),
        }

    return collection.find_one_and_update(
        filter_query,
        {
            "$inc": {
                "stock_quantity": quantity_delta,
            },
            "$set": {
                "updated_at": __import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc,
                ),
            },
        },
        return_document=ReturnDocument.AFTER,
    )


def delete_product(product_id: ObjectId) -> bool:
    """Delete a product and return whether a document was removed."""
    result = get_product_collection().delete_one({"_id": product_id})
    return result.deleted_count == 1


def product_exists(
    *,
    product_id: ObjectId | None = None,
    sku: str | None = None,
) -> bool:
    """Check whether a product exists using an indexed lookup."""
    if product_id is None and sku is None:
        raise ValueError("product_id or sku must be provided.")

    filters: dict[str, Any]

    if product_id is not None:
        filters = {"_id": product_id}
    else:
        filters = {"sku": sku.strip().upper()}

    return (
        get_product_collection().find_one(
            filters,
            projection={"_id": 1},
        )
        is not None
    )


def ensure_product_indexes() -> None:
    """Create indexes required by common product access patterns."""
    collection = get_product_collection()

    collection.create_index(
        [("sku", ASCENDING)],
        unique=True,
        name="uq_sku",
    )

    collection.create_index(
        [("category", ASCENDING), ("created_at", DESCENDING)],
        name="idx_category_created_at",
    )

    collection.create_index(
        [("is_active", ASCENDING), ("created_at", DESCENDING)],
        name="idx_active_created_at",
    )

"""Repository for MongoDB product persistence operations."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.collection import Collection

from database.connection import get_database
from models.product import build_product, update_product_fields


def get_product_collection() -> Collection:
    """Return the MongoDB collection used for products."""
    return get_database()["products"]


def create_product(
    *,
    name: str,
    sku: str,
    price: Decimal | str | float,
    category: str,
    stock_quantity: int = 0,
    description: str | None = None,
    is_active: bool = True,
) -> dict[str, Any]:
    """Create and persist a product document."""
    document = build_product(
        name=name,
        sku=sku,
        price=price,
        category=category,
        stock_quantity=stock_quantity,
        description=description,
        is_active=is_active,
    )

    get_product_collection().insert_one(document)
    return document


def get_product_by_id(product_id: ObjectId) -> dict[str, Any] | None:
    """Return a product by its MongoDB ObjectId."""
    return get_product_collection().find_one({"_id": product_id})


def get_product_by_sku(sku: str) -> dict[str, Any] | None:
    """Return a product by its normalized SKU."""
    return get_product_collection().find_one(
        {"sku": sku.strip().upper()},
    )


def list_products(
    *,
    skip: int = 0,
    limit: int = 50,
    category: str | None = None,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    """Return products using bounded offset pagination."""
    if skip < 0:
        raise ValueError("skip cannot be negative.")

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    filters: dict[str, Any] = {}

    if category is not None:
        filters["category"] = category.strip()

    if is_active is not None:
        filters["is_active"] = is_active

    cursor = (
        get_product_collection()
        .find(filters)
        .sort("created_at", DESCENDING)
        .skip(skip)
        .limit(limit)
    )

    return list(cursor)


def search_products(
    search_term: str,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Search active products by name using a case-insensitive regex."""
    normalized_term = search_term.strip()

    if not normalized_term:
        raise ValueError("search_term cannot be empty.")

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    return list(
        get_product_collection()
        .find(
            {
                "name": {
                    "$regex": normalized_term,
                    "$options": "i",
                },
                "is_active": True,
            },
            projection={
                "_id": 1,
                "name": 1,
                "sku": 1,
                "price": 1,
                "category": 1,
                "stock_quantity": 1,
            },
        )
        .sort("name", ASCENDING)
        .limit(limit)
    )


def update_product(
    product_id: ObjectId,
    *,
    name: str | None = None,
    price: Decimal | str | float | None = None,
    category: str | None = None,
    stock_quantity: int | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> dict[str, Any] | None:
    """Update a product and return the updated document."""
    updates = update_product_fields(
        name=name,
        price=price,
        category=category,
        stock_quantity=stock_quantity,
        description=description,
        is_active=is_active,
    )

    return get_product_collection().find_one_and_update(
        {"_id": product_id},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )


def adjust_stock(
    product_id: ObjectId,
    quantity_delta: int,
) -> dict[str, Any] | None:
    """Atomically adjust product stock and return the updated document.

    A negative delta decrements stock and a positive delta increments it.
    The filter prevents stock from becoming negative.
    """
    if quantity_delta == 0:
        raise ValueError("quantity_delta cannot be zero.")

    collection = get_product_collection()

    filter_query: dict[str, Any] = {"_id": product_id}

    if quantity_delta < 0:
        filter_query["stock_quantity"] = {
            "$gte": abs(quantity_delta),
        }

    return collection.find_one_and_update(
        filter_query,
        {
            "$inc": {
                "stock_quantity": quantity_delta,
            },
            "$set": {
                "updated_at": __import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc,
                ),
            },
        },
        return_document=ReturnDocument.AFTER,
    )


def delete_product(product_id: ObjectId) -> bool:
    """Delete a product and return whether a document was removed."""
    result = get_product_collection().delete_one({"_id": product_id})
    return result.deleted_count == 1


def product_exists(
    *,
    product_id: ObjectId | None = None,
    sku: str | None = None,
) -> bool:
    """Check whether a product exists using an indexed lookup."""
    if product_id is None and sku is None:
        raise ValueError("product_id or sku must be provided.")

    filters: dict[str, Any]

    if product_id is not None:
        filters = {"_id": product_id}
    else:
        filters = {"sku": sku.strip().upper()}

    return (
        get_product_collection().find_one(
            filters,
            projection={"_id": 1},
        )
        is not None
    )


def ensure_product_indexes() -> None:
    """Create indexes required by common product access patterns."""
    collection = get_product_collection()

    collection.create_index(
        [("sku", ASCENDING)],
        unique=True,
        name="uq_sku",
    )

    collection.create_index(
        [("category", ASCENDING), ("created_at", DESCENDING)],
        name="idx_category_created_at",
    )

    collection.create_index(
        [("is_active", ASCENDING), ("created_at", DESCENDING)],
        name="idx_active_created_at",
    )