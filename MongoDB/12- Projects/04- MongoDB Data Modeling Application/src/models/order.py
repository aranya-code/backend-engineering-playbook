"""Order data model definitions."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from bson import ObjectId


ORDER_STATUSES = frozenset(
    {
        "pending",
        "confirmed",
        "processing",
        "shipped",
        "delivered",
        "cancelled",
    }
)


def build_order(
    *,
    customer_id: ObjectId,
    items: list[dict[str, Any]],
    currency: str = "USD",
) -> dict[str, Any]:
    """Build an order document optimized for order-centric reads.

    Order items are embedded because they represent an immutable snapshot of
    the purchased products at checkout time. The customer is referenced by
    ObjectId to avoid duplicating the full customer document.
    """
    if not items:
        raise ValueError("An order must contain at least one item.")

    normalized_items: list[dict[str, Any]] = []
    total = Decimal("0")

    for item in items:
        quantity = int(item["quantity"])
        unit_price = Decimal(str(item["unit_price"]))

        if quantity <= 0:
            raise ValueError("Item quantity must be greater than zero.")

        if unit_price < 0:
            raise ValueError("Item unit price cannot be negative.")

        line_total = unit_price * quantity

        normalized_items.append(
            {
                "product_id": item["product_id"],
                "name": str(item["name"]).strip(),
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )

        total += line_total

    now = datetime.now(timezone.utc)

    return {
        "_id": ObjectId(),
        "customer_id": customer_id,
        "items": normalized_items,
        "currency": currency.upper(),
        "subtotal": total,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
    }


def update_order_status(status: str) -> dict[str, Any]:
    """Build the update document for an order status transition."""
    normalized_status = status.strip().lower()

    if normalized_status not in ORDER_STATUSES:
        raise ValueError(f"Unsupported order status: {status!r}")

    return {
        "$set": {
            "status": normalized_status,
            "updated_at": datetime.now(timezone.utc),
        }
    }

"""Order data model definitions."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from bson import ObjectId


ORDER_STATUSES = frozenset(
    {
        "pending",
        "confirmed",
        "processing",
        "shipped",
        "delivered",
        "cancelled",
    }
)


def build_order(
    *,
    customer_id: ObjectId,
    items: list[dict[str, Any]],
    currency: str = "USD",
) -> dict[str, Any]:
    """Build an order document optimized for order-centric reads.

    Order items are embedded because they represent an immutable snapshot of
    the purchased products at checkout time. The customer is referenced by
    ObjectId to avoid duplicating the full customer document.
    """
    if not items:
        raise ValueError("An order must contain at least one item.")

    normalized_items: list[dict[str, Any]] = []
    total = Decimal("0")

    for item in items:
        quantity = int(item["quantity"])
        unit_price = Decimal(str(item["unit_price"]))

        if quantity <= 0:
            raise ValueError("Item quantity must be greater than zero.")

        if unit_price < 0:
            raise ValueError("Item unit price cannot be negative.")

        line_total = unit_price * quantity

        normalized_items.append(
            {
                "product_id": item["product_id"],
                "name": str(item["name"]).strip(),
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )

        total += line_total

    now = datetime.now(timezone.utc)

    return {
        "_id": ObjectId(),
        "customer_id": customer_id,
        "items": normalized_items,
        "currency": currency.upper(),
        "subtotal": total,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
    }


def update_order_status(status: str) -> dict[str, Any]:
    """Build the update document for an order status transition."""
    normalized_status = status.strip().lower()

    if normalized_status not in ORDER_STATUSES:
        raise ValueError(f"Unsupported order status: {status!r}")

    return {
        "$set": {
            "status": normalized_status,
            "updated_at": datetime.now(timezone.utc),
        }
    }