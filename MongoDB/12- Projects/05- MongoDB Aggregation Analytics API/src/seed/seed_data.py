"""Seed realistic analytics data for the MongoDB aggregation API."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from bson import Decimal128, ObjectId
from pymongo import ASCENDING

from database.connection import get_database


def _decimal(value: str) -> Decimal128:
    """Convert a decimal string to BSON Decimal128."""
    return Decimal128(Decimal(value))


def _utc(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
) -> datetime:
    """Create a timezone-aware UTC datetime."""
    return datetime(
        year,
        month,
        day,
        hour,
        minute,
        tzinfo=timezone.utc,
    )


def build_customers() -> list[dict[str, Any]]:
    """Build deterministic customer seed documents."""
    return [
        {
            "_id": ObjectId("65a000000000000000000001"),
            "name": "Aarav Sharma",
            "email": "aarav.sharma@example.com",
            "phone": "+919800000001",
            "is_active": True,
            "created_at": _utc(2025, 1, 5),
            "updated_at": _utc(2025, 1, 5),
        },
        {
            "_id": ObjectId("65a000000000000000000002"),
            "name": "Maya Sen",
            "email": "maya.sen@example.com",
            "phone": "+919800000002",
            "is_active": True,
            "created_at": _utc(2025, 1, 12),
            "updated_at": _utc(2025, 1, 12),
        },
        {
            "_id": ObjectId("65a000000000000000000003"),
            "name": "Rohan Das",
            "email": "rohan.das@example.com",
            "phone": "+919800000003",
            "is_active": True,
            "created_at": _utc(2025, 2, 3),
            "updated_at": _utc(2025, 2, 3),
        },
        {
            "_id": ObjectId("65a000000000000000000004"),
            "name": "Ishita Roy",
            "email": "ishita.roy@example.com",
            "phone": "+919800000004",
            "is_active": True,
            "created_at": _utc(2025, 2, 18),
            "updated_at": _utc(2025, 2, 18),
        },
        {
            "_id": ObjectId("65a000000000000000000005"),
            "name": "Kabir Mehta",
            "email": "kabir.mehta@example.com",
            "phone": "+919800000005",
            "is_active": True,
            "created_at": _utc(2025, 3, 10),
            "updated_at": _utc(2025, 3, 10),
        },
    ]


def build_products() -> list[dict[str, Any]]:
    """Build deterministic product seed documents."""
    return [
        {
            "_id": ObjectId("65b000000000000000000001"),
            "name": "Mechanical Keyboard",
            "sku": "KB-MECH-001",
            "price": _decimal("89.99"),
            "category": "Electronics",
            "stock_quantity": 120,
            "description": "Mechanical keyboard for professional workstations.",
            "is_active": True,
            "created_at": _utc(2025, 1, 1),
            "updated_at": _utc(2025, 1, 1),
        },
        {
            "_id": ObjectId("65b000000000000000000002"),
            "name": "Wireless Mouse",
            "sku": "MOUSE-WL-001",
            "price": _decimal("39.99"),
            "category": "Electronics",
            "stock_quantity": 250,
            "description": "Ergonomic wireless mouse with programmable buttons.",
            "is_active": True,
            "created_at": _utc(2025, 1, 2),
            "updated_at": _utc(2025, 1, 2),
        },
        {
            "_id": ObjectId("65b000000000000000000003"),
            "name": "USB-C Dock",
            "sku": "DOCK-USBC-001",
            "price": _decimal("129.99"),
            "category": "Electronics",
            "stock_quantity": 80,
            "description": "Multi-port USB-C docking station.",
            "is_active": True,
            "created_at": _utc(2025, 1, 3),
            "updated_at": _utc(2025, 1, 3),
        },
        {
            "_id": ObjectId("65b000000000000000000004"),
            "name": "Laptop Stand",
            "sku": "STAND-LAP-001",
            "price": _decimal("59.99"),
            "category": "Office",
            "stock_quantity": 150,
            "description": "Adjustable aluminum laptop stand.",
            "is_active": True,
            "created_at": _utc(2025, 1, 4),
            "updated_at": _utc(2025, 1, 4),
        },
        {
            "_id": ObjectId("65b000000000000000000005"),
            "name": "Desk Lamp",
            "sku": "LAMP-DESK-001",
            "price": _decimal("44.99"),
            "category": "Office",
            "stock_quantity": 200,
            "description": "LED desk lamp with adjustable brightness.",
            "is_active": True,
            "created_at": _utc(2025, 1, 5),
            "updated_at": _utc(2025, 1, 5),
        },
        {
            "_id": ObjectId("65b000000000000000000006"),
            "name": "Notebook",
            "sku": "NOTE-A5-001",
            "price": _decimal("12.99"),
            "category": "Stationery",
            "stock_quantity": 500,
            "description": "A5 hardcover notebook for daily planning.",
            "is_active": True,
            "created_at": _utc(2025, 1, 6),
            "updated_at": _utc(2025, 1, 6),
        },
    ]


def build_orders() -> list[dict[str, Any]]:
    """Build deterministic orders covering multiple analytics periods."""
    product_ids = {
        "keyboard": ObjectId("65b000000000000000000001"),
        "mouse": ObjectId("65b000000000000000000002"),
        "dock": ObjectId("65b000000000000000000003"),
        "stand": ObjectId("65b000000000000000000004"),
        "lamp": ObjectId("65b000000000000000000005"),
        "notebook": ObjectId("65b000000000000000000006"),
    }

    products = {
        "keyboard": ("Mechanical Keyboard", "Electronics", Decimal("89.99")),
        "mouse": ("Wireless Mouse", "Electronics", Decimal("39.99")),
        "dock": ("USB-C Dock", "Electronics", Decimal("129.99")),
        "stand": ("Laptop Stand", "Office", Decimal("59.99")),
        "lamp": ("Desk Lamp", "Office", Decimal("44.99")),
        "notebook": ("Notebook", "Stationery", Decimal("12.99")),
    }

    def item(name: str, quantity: int) -> dict[str, Any]:
        """Build an embedded order item."""
        product_name, category, unit_price = products[name]

        return {
            "product_id": product_ids[name],
            "name": product_name,
            "category": category,
            "quantity": quantity,
            "unit_price": _decimal(str(unit_price)),
            "line_total": _decimal(str(unit_price * quantity)),
        }

    def order(
        order_id: str,
        customer_id: str,
        created_at: datetime,
        status: str,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build an order document from embedded items."""
        subtotal = sum(
            (
                item["line_total"].to_decimal()
                for item in items
            ),
            Decimal("0"),
        )

        return {
            "_id": ObjectId(order_id),
            "customer_id": ObjectId(customer_id),
            "items": items,
            "currency": "USD",
            "subtotal": _decimal(str(subtotal)),
            "status": status,
            "created_at": created_at,
            "updated_at": created_at,
        }

    return [
        order(
            "65c000000000000000000001",
            "65a000000000000000000001",
            _utc(2025, 1, 10, 10),
            "delivered",
            [item("keyboard", 1), item("mouse", 2)],
        ),
        order(
            "65c000000000000000000002",
            "65a000000000000000000002",
            _utc(2025, 1, 18, 14),
            "delivered",
            [item("dock", 1), item("stand", 1)],
        ),
        order(
            "65c000000000000000000003",
            "65a000000000000000000003",
            _utc(2025, 2, 5, 9),
            "shipped",
            [item("keyboard", 2), item("notebook", 3)],
        ),
        order(
            "65c000000000000000000004",
            "65a000000000000000000004",
            _utc(2025, 2, 16, 16),
            "delivered",
            [item("dock", 2), item("mouse", 1)],
        ),
        order(
            "65c000000000000000000005",
            "65a000000000000000000005",
            _utc(2025, 3, 2, 11),
            "processing",
            [item("stand", 2), item("lamp", 1)],
        ),
        order(
            "65c000000000000000000006",
            "65a000000000000000000001",
            _utc(2025, 3, 15, 13),
            "confirmed",
            [item("keyboard", 1), item("dock", 1)],
        ),
        order(
            "65c000000000000000000007",
            "65a000000000000000000002",
            _utc(2025, 4, 7, 15),
            "delivered",
            [item("mouse", 3), item("notebook", 5)],
        ),
        order(
            "65c000000000000000000008",
            "65a000000000000000000003",
            _utc(2025, 4, 21, 10),
            "delivered",
            [item("dock", 1), item("lamp", 2)],
        ),
        order(
            "65c000000000000000000009",
            "65a000000000000000000004",
            _utc(2025, 5, 9, 12),
            "cancelled",
            [item("keyboard", 1), item("stand", 1)],
        ),
        order(
            "65c00000000000000000000a",
            "65a000000000000000000005",
            _utc(2025, 5, 19, 17),
            "delivered",
            [item("keyboard", 2), item("dock", 1), item("mouse", 1)],
        ),
        order(
            "65c00000000000000000000b",
            "65a000000000000000000001",
            _utc(2025, 6, 3, 8),
            "delivered",
            [item("stand", 1), item("lamp", 2), item("notebook", 4)],
        ),
        order(
            "65c00000000000000000000c",
            "65a000000000000000000002",
            _utc(2025, 6, 22, 18),
            "returned",
            [item("dock", 1), item("mouse", 1)],
        ),
    ]


def seed_database() -> None:
    """Replace existing seed collections with deterministic sample data."""
    database = get_database()

    customers = build_customers()
    products = build_products()
    orders = build_orders()

    database["customers"].delete_many({})
    database["products"].delete_many({})
    database["orders"].delete_many({})

    database["customers"].insert_many(customers, ordered=True)
    database["products"].insert_many(products, ordered=True)
    database["orders"].insert_many(orders, ordered=True)

    database["orders"].create_index(
        [("status", ASCENDING), ("created_at", ASCENDING)],
        name="status_created_at",
    )
    database["orders"].create_index(
        [("customer_id", ASCENDING), ("created_at", ASCENDING)],
        name="customer_created_at",
    )
    database["orders"].create_index(
        [("items.product_id", ASCENDING), ("created_at", ASCENDING)],
        name="items_product_created_at",
    )


def main() -> None:
    """Seed the configured MongoDB database."""
    seed_database()
    print("MongoDB analytics seed data inserted successfully.")


if __name__ == "__main__":
    main()

"""Seed realistic analytics data for the MongoDB aggregation API."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from bson import Decimal128, ObjectId
from pymongo import ASCENDING

from database.connection import get_database


def _decimal(value: str) -> Decimal128:
    """Convert a decimal string to BSON Decimal128."""
    return Decimal128(Decimal(value))


def _utc(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
) -> datetime:
    """Create a timezone-aware UTC datetime."""
    return datetime(
        year,
        month,
        day,
        hour,
        minute,
        tzinfo=timezone.utc,
    )


def build_customers() -> list[dict[str, Any]]:
    """Build deterministic customer seed documents."""
    return [
        {
            "_id": ObjectId("65a000000000000000000001"),
            "name": "Aarav Sharma",
            "email": "aarav.sharma@example.com",
            "phone": "+919800000001",
            "is_active": True,
            "created_at": _utc(2025, 1, 5),
            "updated_at": _utc(2025, 1, 5),
        },
        {
            "_id": ObjectId("65a000000000000000000002"),
            "name": "Maya Sen",
            "email": "maya.sen@example.com",
            "phone": "+919800000002",
            "is_active": True,
            "created_at": _utc(2025, 1, 12),
            "updated_at": _utc(2025, 1, 12),
        },
        {
            "_id": ObjectId("65a000000000000000000003"),
            "name": "Rohan Das",
            "email": "rohan.das@example.com",
            "phone": "+919800000003",
            "is_active": True,
            "created_at": _utc(2025, 2, 3),
            "updated_at": _utc(2025, 2, 3),
        },
        {
            "_id": ObjectId("65a000000000000000000004"),
            "name": "Ishita Roy",
            "email": "ishita.roy@example.com",
            "phone": "+919800000004",
            "is_active": True,
            "created_at": _utc(2025, 2, 18),
            "updated_at": _utc(2025, 2, 18),
        },
        {
            "_id": ObjectId("65a000000000000000000005"),
            "name": "Kabir Mehta",
            "email": "kabir.mehta@example.com",
            "phone": "+919800000005",
            "is_active": True,
            "created_at": _utc(2025, 3, 10),
            "updated_at": _utc(2025, 3, 10),
        },
    ]


def build_products() -> list[dict[str, Any]]:
    """Build deterministic product seed documents."""
    return [
        {
            "_id": ObjectId("65b000000000000000000001"),
            "name": "Mechanical Keyboard",
            "sku": "KB-MECH-001",
            "price": _decimal("89.99"),
            "category": "Electronics",
            "stock_quantity": 120,
            "description": "Mechanical keyboard for professional workstations.",
            "is_active": True,
            "created_at": _utc(2025, 1, 1),
            "updated_at": _utc(2025, 1, 1),
        },
        {
            "_id": ObjectId("65b000000000000000000002"),
            "name": "Wireless Mouse",
            "sku": "MOUSE-WL-001",
            "price": _decimal("39.99"),
            "category": "Electronics",
            "stock_quantity": 250,
            "description": "Ergonomic wireless mouse with programmable buttons.",
            "is_active": True,
            "created_at": _utc(2025, 1, 2),
            "updated_at": _utc(2025, 1, 2),
        },
        {
            "_id": ObjectId("65b000000000000000000003"),
            "name": "USB-C Dock",
            "sku": "DOCK-USBC-001",
            "price": _decimal("129.99"),
            "category": "Electronics",
            "stock_quantity": 80,
            "description": "Multi-port USB-C docking station.",
            "is_active": True,
            "created_at": _utc(2025, 1, 3),
            "updated_at": _utc(2025, 1, 3),
        },
        {
            "_id": ObjectId("65b000000000000000000004"),
            "name": "Laptop Stand",
            "sku": "STAND-LAP-001",
            "price": _decimal("59.99"),
            "category": "Office",
            "stock_quantity": 150,
            "description": "Adjustable aluminum laptop stand.",
            "is_active": True,
            "created_at": _utc(2025, 1, 4),
            "updated_at": _utc(2025, 1, 4),
        },
        {
            "_id": ObjectId("65b000000000000000000005"),
            "name": "Desk Lamp",
            "sku": "LAMP-DESK-001",
            "price": _decimal("44.99"),
            "category": "Office",
            "stock_quantity": 200,
            "description": "LED desk lamp with adjustable brightness.",
            "is_active": True,
            "created_at": _utc(2025, 1, 5),
            "updated_at": _utc(2025, 1, 5),
        },
        {
            "_id": ObjectId("65b000000000000000000006"),
            "name": "Notebook",
            "sku": "NOTE-A5-001",
            "price": _decimal("12.99"),
            "category": "Stationery",
            "stock_quantity": 500,
            "description": "A5 hardcover notebook for daily planning.",
            "is_active": True,
            "created_at": _utc(2025, 1, 6),
            "updated_at": _utc(2025, 1, 6),
        },
    ]


def build_orders() -> list[dict[str, Any]]:
    """Build deterministic orders covering multiple analytics periods."""
    product_ids = {
        "keyboard": ObjectId("65b000000000000000000001"),
        "mouse": ObjectId("65b000000000000000000002"),
        "dock": ObjectId("65b000000000000000000003"),
        "stand": ObjectId("65b000000000000000000004"),
        "lamp": ObjectId("65b000000000000000000005"),
        "notebook": ObjectId("65b000000000000000000006"),
    }

    products = {
        "keyboard": ("Mechanical Keyboard", "Electronics", Decimal("89.99")),
        "mouse": ("Wireless Mouse", "Electronics", Decimal("39.99")),
        "dock": ("USB-C Dock", "Electronics", Decimal("129.99")),
        "stand": ("Laptop Stand", "Office", Decimal("59.99")),
        "lamp": ("Desk Lamp", "Office", Decimal("44.99")),
        "notebook": ("Notebook", "Stationery", Decimal("12.99")),
    }

    def item(name: str, quantity: int) -> dict[str, Any]:
        """Build an embedded order item."""
        product_name, category, unit_price = products[name]

        return {
            "product_id": product_ids[name],
            "name": product_name,
            "category": category,
            "quantity": quantity,
            "unit_price": _decimal(str(unit_price)),
            "line_total": _decimal(str(unit_price * quantity)),
        }

    def order(
        order_id: str,
        customer_id: str,
        created_at: datetime,
        status: str,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build an order document from embedded items."""
        subtotal = sum(
            (
                item["line_total"].to_decimal()
                for item in items
            ),
            Decimal("0"),
        )

        return {
            "_id": ObjectId(order_id),
            "customer_id": ObjectId(customer_id),
            "items": items,
            "currency": "USD",
            "subtotal": _decimal(str(subtotal)),
            "status": status,
            "created_at": created_at,
            "updated_at": created_at,
        }

    return [
        order(
            "65c000000000000000000001",
            "65a000000000000000000001",
            _utc(2025, 1, 10, 10),
            "delivered",
            [item("keyboard", 1), item("mouse", 2)],
        ),
        order(
            "65c000000000000000000002",
            "65a000000000000000000002",
            _utc(2025, 1, 18, 14),
            "delivered",
            [item("dock", 1), item("stand", 1)],
        ),
        order(
            "65c000000000000000000003",
            "65a000000000000000000003",
            _utc(2025, 2, 5, 9),
            "shipped",
            [item("keyboard", 2), item("notebook", 3)],
        ),
        order(
            "65c000000000000000000004",
            "65a000000000000000000004",
            _utc(2025, 2, 16, 16),
            "delivered",
            [item("dock", 2), item("mouse", 1)],
        ),
        order(
            "65c000000000000000000005",
            "65a000000000000000000005",
            _utc(2025, 3, 2, 11),
            "processing",
            [item("stand", 2), item("lamp", 1)],
        ),
        order(
            "65c000000000000000000006",
            "65a000000000000000000001",
            _utc(2025, 3, 15, 13),
            "confirmed",
            [item("keyboard", 1), item("dock", 1)],
        ),
        order(
            "65c000000000000000000007",
            "65a000000000000000000002",
            _utc(2025, 4, 7, 15),
            "delivered",
            [item("mouse", 3), item("notebook", 5)],
        ),
        order(
            "65c000000000000000000008",
            "65a000000000000000000003",
            _utc(2025, 4, 21, 10),
            "delivered",
            [item("dock", 1), item("lamp", 2)],
        ),
        order(
            "65c000000000000000000009",
            "65a000000000000000000004",
            _utc(2025, 5, 9, 12),
            "cancelled",
            [item("keyboard", 1), item("stand", 1)],
        ),
        order(
            "65c00000000000000000000a",
            "65a000000000000000000005",
            _utc(2025, 5, 19, 17),
            "delivered",
            [item("keyboard", 2), item("dock", 1), item("mouse", 1)],
        ),
        order(
            "65c00000000000000000000b",
            "65a000000000000000000001",
            _utc(2025, 6, 3, 8),
            "delivered",
            [item("stand", 1), item("lamp", 2), item("notebook", 4)],
        ),
        order(
            "65c00000000000000000000c",
            "65a000000000000000000002",
            _utc(2025, 6, 22, 18),
            "returned",
            [item("dock", 1), item("mouse", 1)],
        ),
    ]


def seed_database() -> None:
    """Replace existing seed collections with deterministic sample data."""
    database = get_database()

    customers = build_customers()
    products = build_products()
    orders = build_orders()

    database["customers"].delete_many({})
    database["products"].delete_many({})
    database["orders"].delete_many({})

    database["customers"].insert_many(customers, ordered=True)
    database["products"].insert_many(products, ordered=True)
    database["orders"].insert_many(orders, ordered=True)

    database["orders"].create_index(
        [("status", ASCENDING), ("created_at", ASCENDING)],
        name="status_created_at",
    )
    database["orders"].create_index(
        [("customer_id", ASCENDING), ("created_at", ASCENDING)],
        name="customer_created_at",
    )
    database["orders"].create_index(
        [("items.product_id", ASCENDING), ("created_at", ASCENDING)],
        name="items_product_created_at",
    )


def main() -> None:
    """Seed the configured MongoDB database."""
    seed_database()
    print("MongoDB analytics seed data inserted successfully.")


if __name__ == "__main__":
    main()