"""Service layer for order business operations."""

from __future__ import annotations

from typing import Any

from bson import ObjectId

from repositories.order_repository import (
    cancel_order,
    create_order,
    delete_order,
    get_order_by_id,
    list_orders_by_status,
    list_orders_for_customer,
    update_order_status_by_id,
)


def create_order_service(
    *,
    customer_id: ObjectId,
    items: list[dict[str, Any]],
    currency: str = "USD",
) -> dict[str, Any]:
    """Create an order after validating service-level business rules."""
    if not isinstance(customer_id, ObjectId):
        raise ValueError("customer_id must be a valid ObjectId.")

    if not items:
        raise ValueError("An order must contain at least one item.")

    normalized_currency = currency.strip().upper()

    if len(normalized_currency) != 3:
        raise ValueError("currency must be a three-letter ISO currency code.")

    normalized_items: list[dict[str, Any]] = []

    for item in items:
        if "product_id" not in item:
            raise ValueError("Each order item must contain product_id.")

        if "name" not in item:
            raise ValueError("Each order item must contain name.")

        if "quantity" not in item:
            raise ValueError("Each order item must contain quantity.")

        if "unit_price" not in item:
            raise ValueError("Each order item must contain unit_price.")

        normalized_items.append(
            {
                "product_id": item["product_id"],
                "name": str(item["name"]).strip(),
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
            }
        )

    return create_order(
        customer_id=customer_id,
        items=normalized_items,
        currency=normalized_currency,
    )


def get_order_service(
    order_id: ObjectId,
) -> dict[str, Any] | None:
    """Return an order by identifier."""
    if not isinstance(order_id, ObjectId):
        raise ValueError("order_id must be a valid ObjectId.")

    return get_order_by_id(order_id)


def list_customer_orders_service(
    customer_id: ObjectId,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return orders belonging to a customer."""
    if not isinstance(customer_id, ObjectId):
        raise ValueError("customer_id must be a valid ObjectId.")

    if skip < 0:
        raise ValueError("skip cannot be negative.")

    if limit <= 0 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    return list_orders_for_customer(
        customer_id,
        skip=skip,
        limit=limit,
    )


def list_orders_by_status_service(
    status: str,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return orders filtered by normalized status."""
    normalized_status = status.strip().lower()

    if not normalized_status:
        raise ValueError("status cannot be empty.")

    if skip < 0:
        raise ValueError("skip cannot be negative.")

    if limit <= 0 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    return list_orders_by_status(
        normalized_status,
        skip=skip,
        limit=limit,
    )


def update_order_status_service(
    order_id: ObjectId,
    status: str,
) -> dict[str, Any] | None:
    """Update an order status after validating the order identifier."""
    if not isinstance(order_id, ObjectId):
        raise ValueError("order_id must be a valid ObjectId.")

    normalized_status = status.strip().lower()

    if not normalized_status:
        raise ValueError("status cannot be empty.")

    return update_order_status_by_id(
        order_id,
        normalized_status,
    )


def cancel_order_service(
    order_id: ObjectId,
) -> dict[str, Any] | None:
    """Cancel an order by identifier."""
    if not isinstance(order_id, ObjectId):
        raise ValueError("order_id must be a valid ObjectId.")

    return cancel_order(order_id)


def delete_order_service(order_id: ObjectId) -> bool:
    """Delete an order by identifier."""
    if not isinstance(order_id, ObjectId):
        raise ValueError("order_id must be a valid ObjectId.")

    return delete_order(order_id)

"""Service layer for order business operations."""

from __future__ import annotations

from typing import Any

from bson import ObjectId

from repositories.order_repository import (
    cancel_order,
    create_order,
    delete_order,
    get_order_by_id,
    list_orders_by_status,
    list_orders_for_customer,
    update_order_status_by_id,
)


def create_order_service(
    *,
    customer_id: ObjectId,
    items: list[dict[str, Any]],
    currency: str = "USD",
) -> dict[str, Any]:
    """Create an order after validating service-level business rules."""
    if not isinstance(customer_id, ObjectId):
        raise ValueError("customer_id must be a valid ObjectId.")

    if not items:
        raise ValueError("An order must contain at least one item.")

    normalized_currency = currency.strip().upper()

    if len(normalized_currency) != 3:
        raise ValueError("currency must be a three-letter ISO currency code.")

    normalized_items: list[dict[str, Any]] = []

    for item in items:
        if "product_id" not in item:
            raise ValueError("Each order item must contain product_id.")

        if "name" not in item:
            raise ValueError("Each order item must contain name.")

        if "quantity" not in item:
            raise ValueError("Each order item must contain quantity.")

        if "unit_price" not in item:
            raise ValueError("Each order item must contain unit_price.")

        normalized_items.append(
            {
                "product_id": item["product_id"],
                "name": str(item["name"]).strip(),
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
            }
        )

    return create_order(
        customer_id=customer_id,
        items=normalized_items,
        currency=normalized_currency,
    )


def get_order_service(
    order_id: ObjectId,
) -> dict[str, Any] | None:
    """Return an order by identifier."""
    if not isinstance(order_id, ObjectId):
        raise ValueError("order_id must be a valid ObjectId.")

    return get_order_by_id(order_id)


def list_customer_orders_service(
    customer_id: ObjectId,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return orders belonging to a customer."""
    if not isinstance(customer_id, ObjectId):
        raise ValueError("customer_id must be a valid ObjectId.")

    if skip < 0:
        raise ValueError("skip cannot be negative.")

    if limit <= 0 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    return list_orders_for_customer(
        customer_id,
        skip=skip,
        limit=limit,
    )


def list_orders_by_status_service(
    status: str,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return orders filtered by normalized status."""
    normalized_status = status.strip().lower()

    if not normalized_status:
        raise ValueError("status cannot be empty.")

    if skip < 0:
        raise ValueError("skip cannot be negative.")

    if limit <= 0 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    return list_orders_by_status(
        normalized_status,
        skip=skip,
        limit=limit,
    )


def update_order_status_service(
    order_id: ObjectId,
    status: str,
) -> dict[str, Any] | None:
    """Update an order status after validating the order identifier."""
    if not isinstance(order_id, ObjectId):
        raise ValueError("order_id must be a valid ObjectId.")

    normalized_status = status.strip().lower()

    if not normalized_status:
        raise ValueError("status cannot be empty.")

    return update_order_status_by_id(
        order_id,
        normalized_status,
    )


def cancel_order_service(
    order_id: ObjectId,
) -> dict[str, Any] | None:
    """Cancel an order by identifier."""
    if not isinstance(order_id, ObjectId):
        raise ValueError("order_id must be a valid ObjectId.")

    return cancel_order(order_id)


def delete_order_service(order_id: ObjectId) -> bool:
    """Delete an order by identifier."""
    if not isinstance(order_id, ObjectId):
        raise ValueError("order_id must be a valid ObjectId.")

    return delete_order(order_id)