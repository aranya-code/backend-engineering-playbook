"""Tests for customer-product-order relationship modeling."""

from __future__ import annotations

from decimal import Decimal

from bson import ObjectId

from models.customer import build_customer
from models.order import build_order
from models.product import build_product


def test_customer_order_relationship_uses_customer_reference() -> None:
    """Represent an order-to-customer relationship with an ObjectId reference."""
    customer = build_customer(
        name="Alice Johnson",
        email="alice@example.com",
    )

    order = build_order(
        customer_id=customer["_id"],
        items=[
            {
                "product_id": ObjectId(),
                "name": "Mechanical Keyboard",
                "quantity": 1,
                "unit_price": Decimal("129.99"),
            },
        ],
    )

    assert order["customer_id"] == customer["_id"]
    assert order["customer_id"] != customer["email"]


def test_order_product_relationship_references_product_and_embeds_snapshot() -> None:
    """Reference the product while embedding immutable order-time product data."""
    product = build_product(
        name="Mechanical Keyboard",
        sku="KB-MECH-001",
        price=Decimal("129.99"),
        category="electronics",
        stock_quantity=50,
    )

    order = build_order(
        customer_id=ObjectId(),
        items=[
            {
                "product_id": product["_id"],
                "name": product["name"],
                "quantity": 2,
                "unit_price": product["price"],
            },
        ],
    )

    item = order["items"][0]

    assert item["product_id"] == product["_id"]
    assert item["name"] == product["name"]
    assert item["unit_price"] == product["price"]
    assert item["line_total"] == Decimal("259.98")


def test_order_preserves_product_snapshot_when_product_changes() -> None:
    """Verify that an order contains historical product values independently."""
    product = build_product(
        name="Wireless Mouse",
        sku="MS-WIRELESS-001",
        price=Decimal("49.99"),
        category="electronics",
        stock_quantity=100,
    )

    order = build_order(
        customer_id=ObjectId(),
        items=[
            {
                "product_id": product["_id"],
                "name": product["name"],
                "quantity": 1,
                "unit_price": product["price"],
            },
        ],
    )

    product["name"] = "Wireless Mouse Pro"
    product["price"] = Decimal("69.99")

    item = order["items"][0]

    assert item["product_id"] == product["_id"]
    assert item["name"] == "Wireless Mouse"
    assert item["unit_price"] == Decimal("49.99")


def test_customer_can_have_multiple_orders() -> None:
    """Represent a one-to-many customer-to-orders relationship."""
    customer_id = ObjectId()
    product_id = ObjectId()

    first_order = build_order(
        customer_id=customer_id,
        items=[
            {
                "product_id": product_id,
                "name": "Keyboard",
                "quantity": 1,
                "unit_price": Decimal("100.00"),
            },
        ],
    )

    second_order = build_order(
        customer_id=customer_id,
        items=[
            {
                "product_id": product_id,
                "name": "Keyboard",
                "quantity": 2,
                "unit_price": Decimal("100.00"),
            },
        ],
    )

    assert first_order["customer_id"] == customer_id
    assert second_order["customer_id"] == customer_id
    assert first_order["_id"] != second_order["_id"]


def test_order_can_contain_multiple_products() -> None:
    """Represent an order-to-products relationship through embedded items."""
    customer_id = ObjectId()
    keyboard_id = ObjectId()
    mouse_id = ObjectId()

    order = build_order(
        customer_id=customer_id,
        items=[
            {
                "product_id": keyboard_id,
                "name": "Keyboard",
                "quantity": 1,
                "unit_price": Decimal("100.00"),
            },
            {
                "product_id": mouse_id,
                "name": "Mouse",
                "quantity": 2,
                "unit_price": Decimal("25.00"),
            },
        ],
    )

    product_ids = {
        item["product_id"]
        for item in order["items"]
    }

    assert product_ids == {keyboard_id, mouse_id}
    assert order["subtotal"] == Decimal("150.00")


def test_multiple_orders_can_reference_same_product() -> None:
    """Allow the same product to be referenced by independent orders."""
    customer_one_id = ObjectId()
    customer_two_id = ObjectId()
    product_id = ObjectId()

    first_order = build_order(
        customer_id=customer_one_id,
        items=[
            {
                "product_id": product_id,
                "name": "USB-C Dock",
                "quantity": 1,
                "unit_price": Decimal("89.99"),
            },
        ],
    )

    second_order = build_order(
        customer_id=customer_two_id,
        items=[
            {
                "product_id": product_id,
                "name": "USB-C Dock",
                "quantity": 2,
                "unit_price": Decimal("89.99"),
            },
        ],
    )

    assert first_order["items"][0]["product_id"] == product_id
    assert second_order["items"][0]["product_id"] == product_id
    assert first_order["_id"] != second_order["_id"]


def test_customer_identity_is_not_embedded_in_order() -> None:
    """Keep customer identity referenced rather than duplicating the document."""
    customer = build_customer(
        name="Alice Johnson",
        email="alice@example.com",
        phone="+1-555-0101",
    )

    order = build_order(
        customer_id=customer["_id"],
        items=[
            {
                "product_id": ObjectId(),
                "name": "Keyboard",
                "quantity": 1,
                "unit_price": Decimal("100.00"),
            },
        ],
    )

    assert order["customer_id"] == customer["_id"]
    assert "customer" not in order
    assert "email" not in order
    assert "phone" not in order


def test_order_item_is_embedded_for_order_centric_reads() -> None:
    """Keep line-item data embedded to support efficient order reads."""
    product_id = ObjectId()

    order = build_order(
        customer_id=ObjectId(),
        items=[
            {
                "product_id": product_id,
                "name": "Mechanical Keyboard",
                "quantity": 1,
                "unit_price": Decimal("129.99"),
            },
        ],
    )

    assert len(order["items"]) == 1
    assert order["items"][0]["product_id"] == product_id
    assert "quantity" in order["items"][0]
    assert "unit_price" in order["items"][0]
    assert "line_total" in order["items"][0]


def test_relationship_identifiers_are_object_ids() -> None:
    """Use BSON ObjectId values for document relationships."""
    customer_id = ObjectId()
    product_id = ObjectId()

    order = build_order(
        customer_id=customer_id,
        items=[
            {
                "product_id": product_id,
                "name": "Keyboard",
                "quantity": 1,
                "unit_price": Decimal("100.00"),
            },
        ],
    )

    assert isinstance(order["customer_id"], ObjectId)
    assert isinstance(order["items"][0]["product_id"], ObjectId)

"""Tests for customer-product-order relationship modeling."""

from __future__ import annotations

from decimal import Decimal

from bson import ObjectId

from models.customer import build_customer
from models.order import build_order
from models.product import build_product


def test_customer_order_relationship_uses_customer_reference() -> None:
    """Represent an order-to-customer relationship with an ObjectId reference."""
    customer = build_customer(
        name="Alice Johnson",
        email="alice@example.com",
    )

    order = build_order(
        customer_id=customer["_id"],
        items=[
            {
                "product_id": ObjectId(),
                "name": "Mechanical Keyboard",
                "quantity": 1,
                "unit_price": Decimal("129.99"),
            },
        ],
    )

    assert order["customer_id"] == customer["_id"]
    assert order["customer_id"] != customer["email"]


def test_order_product_relationship_references_product_and_embeds_snapshot() -> None:
    """Reference the product while embedding immutable order-time product data."""
    product = build_product(
        name="Mechanical Keyboard",
        sku="KB-MECH-001",
        price=Decimal("129.99"),
        category="electronics",
        stock_quantity=50,
    )

    order = build_order(
        customer_id=ObjectId(),
        items=[
            {
                "product_id": product["_id"],
                "name": product["name"],
                "quantity": 2,
                "unit_price": product["price"],
            },
        ],
    )

    item = order["items"][0]

    assert item["product_id"] == product["_id"]
    assert item["name"] == product["name"]
    assert item["unit_price"] == product["price"]
    assert item["line_total"] == Decimal("259.98")


def test_order_preserves_product_snapshot_when_product_changes() -> None:
    """Verify that an order contains historical product values independently."""
    product = build_product(
        name="Wireless Mouse",
        sku="MS-WIRELESS-001",
        price=Decimal("49.99"),
        category="electronics",
        stock_quantity=100,
    )

    order = build_order(
        customer_id=ObjectId(),
        items=[
            {
                "product_id": product["_id"],
                "name": product["name"],
                "quantity": 1,
                "unit_price": product["price"],
            },
        ],
    )

    product["name"] = "Wireless Mouse Pro"
    product["price"] = Decimal("69.99")

    item = order["items"][0]

    assert item["product_id"] == product["_id"]
    assert item["name"] == "Wireless Mouse"
    assert item["unit_price"] == Decimal("49.99")


def test_customer_can_have_multiple_orders() -> None:
    """Represent a one-to-many customer-to-orders relationship."""
    customer_id = ObjectId()
    product_id = ObjectId()

    first_order = build_order(
        customer_id=customer_id,
        items=[
            {
                "product_id": product_id,
                "name": "Keyboard",
                "quantity": 1,
                "unit_price": Decimal("100.00"),
            },
        ],
    )

    second_order = build_order(
        customer_id=customer_id,
        items=[
            {
                "product_id": product_id,
                "name": "Keyboard",
                "quantity": 2,
                "unit_price": Decimal("100.00"),
            },
        ],
    )

    assert first_order["customer_id"] == customer_id
    assert second_order["customer_id"] == customer_id
    assert first_order["_id"] != second_order["_id"]


def test_order_can_contain_multiple_products() -> None:
    """Represent an order-to-products relationship through embedded items."""
    customer_id = ObjectId()
    keyboard_id = ObjectId()
    mouse_id = ObjectId()

    order = build_order(
        customer_id=customer_id,
        items=[
            {
                "product_id": keyboard_id,
                "name": "Keyboard",
                "quantity": 1,
                "unit_price": Decimal("100.00"),
            },
            {
                "product_id": mouse_id,
                "name": "Mouse",
                "quantity": 2,
                "unit_price": Decimal("25.00"),
            },
        ],
    )

    product_ids = {
        item["product_id"]
        for item in order["items"]
    }

    assert product_ids == {keyboard_id, mouse_id}
    assert order["subtotal"] == Decimal("150.00")


def test_multiple_orders_can_reference_same_product() -> None:
    """Allow the same product to be referenced by independent orders."""
    customer_one_id = ObjectId()
    customer_two_id = ObjectId()
    product_id = ObjectId()

    first_order = build_order(
        customer_id=customer_one_id,
        items=[
            {
                "product_id": product_id,
                "name": "USB-C Dock",
                "quantity": 1,
                "unit_price": Decimal("89.99"),
            },
        ],
    )

    second_order = build_order(
        customer_id=customer_two_id,
        items=[
            {
                "product_id": product_id,
                "name": "USB-C Dock",
                "quantity": 2,
                "unit_price": Decimal("89.99"),
            },
        ],
    )

    assert first_order["items"][0]["product_id"] == product_id
    assert second_order["items"][0]["product_id"] == product_id
    assert first_order["_id"] != second_order["_id"]


def test_customer_identity_is_not_embedded_in_order() -> None:
    """Keep customer identity referenced rather than duplicating the document."""
    customer = build_customer(
        name="Alice Johnson",
        email="alice@example.com",
        phone="+1-555-0101",
    )

    order = build_order(
        customer_id=customer["_id"],
        items=[
            {
                "product_id": ObjectId(),
                "name": "Keyboard",
                "quantity": 1,
                "unit_price": Decimal("100.00"),
            },
        ],
    )

    assert order["customer_id"] == customer["_id"]
    assert "customer" not in order
    assert "email" not in order
    assert "phone" not in order


def test_order_item_is_embedded_for_order_centric_reads() -> None:
    """Keep line-item data embedded to support efficient order reads."""
    product_id = ObjectId()

    order = build_order(
        customer_id=ObjectId(),
        items=[
            {
                "product_id": product_id,
                "name": "Mechanical Keyboard",
                "quantity": 1,
                "unit_price": Decimal("129.99"),
            },
        ],
    )

    assert len(order["items"]) == 1
    assert order["items"][0]["product_id"] == product_id
    assert "quantity" in order["items"][0]
    assert "unit_price" in order["items"][0]
    assert "line_total" in order["items"][0]


def test_relationship_identifiers_are_object_ids() -> None:
    """Use BSON ObjectId values for document relationships."""
    customer_id = ObjectId()
    product_id = ObjectId()

    order = build_order(
        customer_id=customer_id,
        items=[
            {
                "product_id": product_id,
                "name": "Keyboard",
                "quantity": 1,
                "unit_price": Decimal("100.00"),
            },
        ],
    )

    assert isinstance(order["customer_id"], ObjectId)
    assert isinstance(order["items"][0]["product_id"], ObjectId)