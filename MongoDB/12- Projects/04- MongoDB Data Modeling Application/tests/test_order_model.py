"""Tests for MongoDB order data models."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from bson import ObjectId

from models.order import (
    ORDER_STATUSES,
    build_order,
    update_order_status,
)


def test_build_order_creates_valid_document() -> None:
    """Build an order with references, embedded item snapshots, and totals."""
    customer_id = ObjectId()
    product_id = ObjectId()

    document = build_order(
        customer_id=customer_id,
        items=[
            {
                "product_id": product_id,
                "name": "Mechanical Keyboard",
                "quantity": 2,
                "unit_price": "129.99",
            },
            {
                "product_id": ObjectId(),
                "name": "Wireless Mouse",
                "quantity": 1,
                "unit_price": "49.99",
            },
        ],
    )

    assert isinstance(document["_id"], ObjectId)
    assert document["customer_id"] == customer_id
    assert document["currency"] == "USD"
    assert document["status"] == "pending"
    assert document["subtotal"] == Decimal("309.97")
    assert len(document["items"]) == 2
    assert document["items"][0]["product_id"] == product_id
    assert document["items"][0]["name"] == "Mechanical Keyboard"
    assert document["items"][0]["quantity"] == 2
    assert document["items"][0]["unit_price"] == Decimal("129.99")
    assert document["items"][0]["line_total"] == Decimal("259.98")
    assert isinstance(document["created_at"], datetime)
    assert isinstance(document["updated_at"], datetime)
    assert document["created_at"].tzinfo == timezone.utc
    assert document["updated_at"].tzinfo == timezone.utc


def test_build_order_requires_at_least_one_item() -> None:
    """Reject orders that contain no line items."""
    with pytest.raises(
        ValueError,
        match="An order must contain at least one item",
    ):
        build_order(
            customer_id=ObjectId(),
            items=[],
        )


def test_build_order_rejects_non_positive_quantity() -> None:
    """Reject zero or negative item quantities."""
    with pytest.raises(
        ValueError,
        match="Item quantity must be greater than zero",
    ):
        build_order(
            customer_id=ObjectId(),
            items=[
                {
                    "product_id": ObjectId(),
                    "name": "Mechanical Keyboard",
                    "quantity": 0,
                    "unit_price": "129.99",
                },
            ],
        )


def test_build_order_rejects_negative_unit_price() -> None:
    """Reject negative prices before persistence."""
    with pytest.raises(
        ValueError,
        match="Item unit price cannot be negative",
    ):
        build_order(
            customer_id=ObjectId(),
            items=[
                {
                    "product_id": ObjectId(),
                    "name": "Mechanical Keyboard",
                    "quantity": 1,
                    "unit_price": "-1.00",
                },
            ],
        )


def test_build_order_calculates_line_totals_and_subtotal() -> None:
    """Calculate monetary totals using Decimal arithmetic."""
    document = build_order(
        customer_id=ObjectId(),
        items=[
            {
                "product_id": ObjectId(),
                "name": "Product A",
                "quantity": 3,
                "unit_price": Decimal("10.25"),
            },
            {
                "product_id": ObjectId(),
                "name": "Product B",
                "quantity": 2,
                "unit_price": Decimal("5.50"),
            },
        ],
    )

    assert document["items"][0]["line_total"] == Decimal("30.75")
    assert document["items"][1]["line_total"] == Decimal("11.00")
    assert document["subtotal"] == Decimal("41.75")


def test_build_order_normalizes_currency() -> None:
    """Normalize currency codes to uppercase."""
    document = build_order(
        customer_id=ObjectId(),
        items=[
            {
                "product_id": ObjectId(),
                "name": "Mechanical Keyboard",
                "quantity": 1,
                "unit_price": "129.99",
            },
        ],
        currency="eur",
    )

    assert document["currency"] == "EUR"


def test_build_order_embeds_product_snapshot_data() -> None:
    """Preserve product details required for historical order reads."""
    document = build_order(
        customer_id=ObjectId(),
        items=[
            {
                "product_id": ObjectId(),
                "name": "Mechanical Keyboard",
                "quantity": 1,
                "unit_price": "129.99",
            },
        ],
    )

    item = document["items"][0]

    assert set(item) == {
        "product_id",
        "name",
        "quantity",
        "unit_price",
        "line_total",
    }


def test_build_order_sets_pending_status() -> None:
    """Initialize every new order in the pending state."""
    document = build_order(
        customer_id=ObjectId(),
        items=[
            {
                "product_id": ObjectId(),
                "name": "Mechanical Keyboard",
                "quantity": 1,
                "unit_price": "129.99",
            },
        ],
    )

    assert document["status"] == "pending"


def test_build_order_uses_utc_timestamps() -> None:
    """Initialize order lifecycle timestamps with UTC-aware datetimes."""
    before = datetime.now(timezone.utc)

    document = build_order(
        customer_id=ObjectId(),
        items=[
            {
                "product_id": ObjectId(),
                "name": "Mechanical Keyboard",
                "quantity": 1,
                "unit_price": "129.99",
            },
        ],
    )

    after = datetime.now(timezone.utc)

    assert before <= document["created_at"] <= after
    assert before <= document["updated_at"] <= after


@pytest.mark.parametrize("status", sorted(ORDER_STATUSES))
def test_update_order_status_accepts_supported_statuses(
    status: str,
) -> None:
    """Build valid status updates for every supported order state."""
    update = update_order_status(status)

    assert update["$set"]["status"] == status
    assert isinstance(update["$set"]["updated_at"], datetime)
    assert update["$set"]["updated_at"].tzinfo == timezone.utc


def test_update_order_status_normalizes_status() -> None:
    """Normalize status input before constructing the update."""
    update = update_order_status("  SHIPPED  ")

    assert update["$set"]["status"] == "shipped"


def test_update_order_status_rejects_unsupported_status() -> None:
    """Reject status values outside the application's state machine."""
    with pytest.raises(
        ValueError,
        match="Unsupported order status",
    ):
        update_order_status("returned")


def test_update_order_status_returns_mongo_set_update() -> None:
    """Return an update document suitable for find_one_and_update."""
    update = update_order_status("confirmed")

    assert set(update) == {"$set"}
    assert set(update["$set"]) == {"status", "updated_at"}

"""Tests for MongoDB order data models."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from bson import ObjectId

from models.order import (
    ORDER_STATUSES,
    build_order,
    update_order_status,
)


def test_build_order_creates_valid_document() -> None:
    """Build an order with references, embedded item snapshots, and totals."""
    customer_id = ObjectId()
    product_id = ObjectId()

    document = build_order(
        customer_id=customer_id,
        items=[
            {
                "product_id": product_id,
                "name": "Mechanical Keyboard",
                "quantity": 2,
                "unit_price": "129.99",
            },
            {
                "product_id": ObjectId(),
                "name": "Wireless Mouse",
                "quantity": 1,
                "unit_price": "49.99",
            },
        ],
    )

    assert isinstance(document["_id"], ObjectId)
    assert document["customer_id"] == customer_id
    assert document["currency"] == "USD"
    assert document["status"] == "pending"
    assert document["subtotal"] == Decimal("309.97")
    assert len(document["items"]) == 2
    assert document["items"][0]["product_id"] == product_id
    assert document["items"][0]["name"] == "Mechanical Keyboard"
    assert document["items"][0]["quantity"] == 2
    assert document["items"][0]["unit_price"] == Decimal("129.99")
    assert document["items"][0]["line_total"] == Decimal("259.98")
    assert isinstance(document["created_at"], datetime)
    assert isinstance(document["updated_at"], datetime)
    assert document["created_at"].tzinfo == timezone.utc
    assert document["updated_at"].tzinfo == timezone.utc


def test_build_order_requires_at_least_one_item() -> None:
    """Reject orders that contain no line items."""
    with pytest.raises(
        ValueError,
        match="An order must contain at least one item",
    ):
        build_order(
            customer_id=ObjectId(),
            items=[],
        )


def test_build_order_rejects_non_positive_quantity() -> None:
    """Reject zero or negative item quantities."""
    with pytest.raises(
        ValueError,
        match="Item quantity must be greater than zero",
    ):
        build_order(
            customer_id=ObjectId(),
            items=[
                {
                    "product_id": ObjectId(),
                    "name": "Mechanical Keyboard",
                    "quantity": 0,
                    "unit_price": "129.99",
                },
            ],
        )


def test_build_order_rejects_negative_unit_price() -> None:
    """Reject negative prices before persistence."""
    with pytest.raises(
        ValueError,
        match="Item unit price cannot be negative",
    ):
        build_order(
            customer_id=ObjectId(),
            items=[
                {
                    "product_id": ObjectId(),
                    "name": "Mechanical Keyboard",
                    "quantity": 1,
                    "unit_price": "-1.00",
                },
            ],
        )


def test_build_order_calculates_line_totals_and_subtotal() -> None:
    """Calculate monetary totals using Decimal arithmetic."""
    document = build_order(
        customer_id=ObjectId(),
        items=[
            {
                "product_id": ObjectId(),
                "name": "Product A",
                "quantity": 3,
                "unit_price": Decimal("10.25"),
            },
            {
                "product_id": ObjectId(),
                "name": "Product B",
                "quantity": 2,
                "unit_price": Decimal("5.50"),
            },
        ],
    )

    assert document["items"][0]["line_total"] == Decimal("30.75")
    assert document["items"][1]["line_total"] == Decimal("11.00")
    assert document["subtotal"] == Decimal("41.75")


def test_build_order_normalizes_currency() -> None:
    """Normalize currency codes to uppercase."""
    document = build_order(
        customer_id=ObjectId(),
        items=[
            {
                "product_id": ObjectId(),
                "name": "Mechanical Keyboard",
                "quantity": 1,
                "unit_price": "129.99",
            },
        ],
        currency="eur",
    )

    assert document["currency"] == "EUR"


def test_build_order_embeds_product_snapshot_data() -> None:
    """Preserve product details required for historical order reads."""
    document = build_order(
        customer_id=ObjectId(),
        items=[
            {
                "product_id": ObjectId(),
                "name": "Mechanical Keyboard",
                "quantity": 1,
                "unit_price": "129.99",
            },
        ],
    )

    item = document["items"][0]

    assert set(item) == {
        "product_id",
        "name",
        "quantity",
        "unit_price",
        "line_total",
    }


def test_build_order_sets_pending_status() -> None:
    """Initialize every new order in the pending state."""
    document = build_order(
        customer_id=ObjectId(),
        items=[
            {
                "product_id": ObjectId(),
                "name": "Mechanical Keyboard",
                "quantity": 1,
                "unit_price": "129.99",
            },
        ],
    )

    assert document["status"] == "pending"


def test_build_order_uses_utc_timestamps() -> None:
    """Initialize order lifecycle timestamps with UTC-aware datetimes."""
    before = datetime.now(timezone.utc)

    document = build_order(
        customer_id=ObjectId(),
        items=[
            {
                "product_id": ObjectId(),
                "name": "Mechanical Keyboard",
                "quantity": 1,
                "unit_price": "129.99",
            },
        ],
    )

    after = datetime.now(timezone.utc)

    assert before <= document["created_at"] <= after
    assert before <= document["updated_at"] <= after


@pytest.mark.parametrize("status", sorted(ORDER_STATUSES))
def test_update_order_status_accepts_supported_statuses(
    status: str,
) -> None:
    """Build valid status updates for every supported order state."""
    update = update_order_status(status)

    assert update["$set"]["status"] == status
    assert isinstance(update["$set"]["updated_at"], datetime)
    assert update["$set"]["updated_at"].tzinfo == timezone.utc


def test_update_order_status_normalizes_status() -> None:
    """Normalize status input before constructing the update."""
    update = update_order_status("  SHIPPED  ")

    assert update["$set"]["status"] == "shipped"


def test_update_order_status_rejects_unsupported_status() -> None:
    """Reject status values outside the application's state machine."""
    with pytest.raises(
        ValueError,
        match="Unsupported order status",
    ):
        update_order_status("returned")


def test_update_order_status_returns_mongo_set_update() -> None:
    """Return an update document suitable for find_one_and_update."""
    update = update_order_status("confirmed")

    assert set(update) == {"$set"}
    assert set(update["$set"]) == {"status", "updated_at"}