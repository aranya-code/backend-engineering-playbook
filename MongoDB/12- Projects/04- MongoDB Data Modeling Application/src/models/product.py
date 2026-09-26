"""Product data model definitions."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from bson import ObjectId


def build_product(
    *,
    name: str,
    sku: str,
    price: Decimal | str | float,
    category: str,
    stock_quantity: int = 0,
    description: str | None = None,
    is_active: bool = True,
) -> dict[str, Any]:
    """Build a MongoDB product document."""
    normalized_name = name.strip()
    normalized_sku = sku.strip().upper()
    normalized_category = category.strip()

    if not normalized_name:
        raise ValueError("Product name cannot be empty.")

    if not normalized_sku:
        raise ValueError("Product SKU cannot be empty.")

    if not normalized_category:
        raise ValueError("Product category cannot be empty.")

    normalized_price = Decimal(str(price))

    if normalized_price < 0:
        raise ValueError("Product price cannot be negative.")

    if stock_quantity < 0:
        raise ValueError("Stock quantity cannot be negative.")

    now = datetime.now(timezone.utc)

    return {
        "_id": ObjectId(),
        "name": normalized_name,
        "sku": normalized_sku,
        "price": normalized_price,
        "category": normalized_category,
        "stock_quantity": stock_quantity,
        "description": description.strip() if description else None,
        "is_active": is_active,
        "created_at": now,
        "updated_at": now,
    }


def update_product_fields(
    *,
    name: str | None = None,
    price: Decimal | str | float | None = None,
    category: str | None = None,
    stock_quantity: int | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> dict[str, Any]:
    """Build the mutable fields for a product update."""
    updates: dict[str, Any] = {}

    if name is not None:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Product name cannot be empty.")
        updates["name"] = normalized_name

    if price is not None:
        normalized_price = Decimal(str(price))
        if normalized_price < 0:
            raise ValueError("Product price cannot be negative.")
        updates["price"] = normalized_price

    if category is not None:
        normalized_category = category.strip()
        if not normalized_category:
            raise ValueError("Product category cannot be empty.")
        updates["category"] = normalized_category

    if stock_quantity is not None:
        if stock_quantity < 0:
            raise ValueError("Stock quantity cannot be negative.")
        updates["stock_quantity"] = stock_quantity

    if description is not None:
        updates["description"] = description.strip()

    if is_active is not None:
        updates["is_active"] = is_active

    updates["updated_at"] = datetime.now(timezone.utc)

    return updates

"""Product data model definitions."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from bson import ObjectId


def build_product(
    *,
    name: str,
    sku: str,
    price: Decimal | str | float,
    category: str,
    stock_quantity: int = 0,
    description: str | None = None,
    is_active: bool = True,
) -> dict[str, Any]:
    """Build a MongoDB product document."""
    normalized_name = name.strip()
    normalized_sku = sku.strip().upper()
    normalized_category = category.strip()

    if not normalized_name:
        raise ValueError("Product name cannot be empty.")

    if not normalized_sku:
        raise ValueError("Product SKU cannot be empty.")

    if not normalized_category:
        raise ValueError("Product category cannot be empty.")

    normalized_price = Decimal(str(price))

    if normalized_price < 0:
        raise ValueError("Product price cannot be negative.")

    if stock_quantity < 0:
        raise ValueError("Stock quantity cannot be negative.")

    now = datetime.now(timezone.utc)

    return {
        "_id": ObjectId(),
        "name": normalized_name,
        "sku": normalized_sku,
        "price": normalized_price,
        "category": normalized_category,
        "stock_quantity": stock_quantity,
        "description": description.strip() if description else None,
        "is_active": is_active,
        "created_at": now,
        "updated_at": now,
    }


def update_product_fields(
    *,
    name: str | None = None,
    price: Decimal | str | float | None = None,
    category: str | None = None,
    stock_quantity: int | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> dict[str, Any]:
    """Build the mutable fields for a product update."""
    updates: dict[str, Any] = {}

    if name is not None:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Product name cannot be empty.")
        updates["name"] = normalized_name

    if price is not None:
        normalized_price = Decimal(str(price))
        if normalized_price < 0:
            raise ValueError("Product price cannot be negative.")
        updates["price"] = normalized_price

    if category is not None:
        normalized_category = category.strip()
        if not normalized_category:
            raise ValueError("Product category cannot be empty.")
        updates["category"] = normalized_category

    if stock_quantity is not None:
        if stock_quantity < 0:
            raise ValueError("Stock quantity cannot be negative.")
        updates["stock_quantity"] = stock_quantity

    if description is not None:
        updates["description"] = description.strip()

    if is_active is not None:
        updates["is_active"] = is_active

    updates["updated_at"] = datetime.now(timezone.utc)

    return updates