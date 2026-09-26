"""Seed representative data for the MongoDB data modeling application."""

from __future__ import annotations

from decimal import Decimal

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError

from database.connection import get_database, ping_database
from models.customer import build_customer
from models.order import build_order
from models.product import build_product


def seed_customers() -> dict[str, ObjectId]:
    """Create representative customers and return their identifiers."""
    collection = get_database()["customers"]

    customers = [
        {
            "name": "Alice Johnson",
            "email": "alice.johnson@example.com",
            "phone": "+1-555-0101",
        },
        {
            "name": "Bob Smith",
            "email": "bob.smith@example.com",
            "phone": "+1-555-0102",
        },
        {
            "name": "Carol Williams",
            "email": "carol.williams@example.com",
            "phone": "+1-555-0103",
        },
    ]

    customer_ids: dict[str, ObjectId] = {}

    for customer in customers:
        existing = collection.find_one(
            {"email": customer["email"]},
            projection={"_id": 1},
        )

        if existing is not None:
            customer_ids[customer["email"]] = existing["_id"]
            continue

        document = build_customer(**customer)

        try:
            collection.insert_one(document)
            customer_ids[customer["email"]] = document["_id"]
        except DuplicateKeyError:
            existing = collection.find_one(
                {"email": customer["email"]},
                projection={"_id": 1},
            )

            if existing is None:
                raise

            customer_ids[customer["email"]] = existing["_id"]

    return customer_ids


def seed_products() -> dict[str, ObjectId]:
    """Create representative products and return their identifiers."""
    collection = get_database()["products"]

    products = [
        {
            "name": "Mechanical Keyboard",
            "sku": "KB-MECH-001",
            "price": Decimal("129.99"),
            "category": "electronics",
            "stock_quantity": 50,
            "description": "Mechanical keyboard with programmable keys.",
        },
        {
            "name": "Wireless Mouse",
            "sku": "MS-WIRELESS-001",
            "price": Decimal("49.99"),
            "category": "electronics",
            "stock_quantity": 100,
            "description": "Ergonomic wireless mouse with adjustable DPI.",
        },
        {
            "name": "USB-C Dock",
            "sku": "DOCK-USBC-001",
            "price": Decimal("89.99"),
            "category": "accessories",
            "stock_quantity": 35,
            "description": "USB-C dock with HDMI, USB, and Ethernet ports.",
        },
    ]

    product_ids: dict[str, ObjectId] = {}

    for product in products:
        existing = collection.find_one(
            {"sku": product["sku"]},
            projection={"_id": 1},
        )

        if existing is not None:
            product_ids[product["sku"]] = existing["_id"]
            continue

        document = build_product(**product)

        try:
            collection.insert_one(document)
            product_ids[product["sku"]] = document["_id"]
        except DuplicateKeyError:
            existing = collection.find_one(
                {"sku": product["sku"]},
                projection={"_id": 1},
            )

            if existing is None:
                raise

            product_ids[product["sku"]] = existing["_id"]

    return product_ids


def seed_orders(
    customer_ids: dict[str, ObjectId],
    product_ids: dict[str, ObjectId],
) -> None:
    """Create representative orders using customer references and snapshots."""
    collection = get_database()["orders"]

    alice_id = customer_ids["alice.johnson@example.com"]
    bob_id = customer_ids["bob.smith@example.com"]

    keyboard_id = product_ids["KB-MECH-001"]
    mouse_id = product_ids["MS-WIRELESS-001"]
    dock_id = product_ids["DOCK-USBC-001"]

    orders = [
        {
            "customer_id": alice_id,
            "items": [
                {
                    "product_id": keyboard_id,
                    "name": "Mechanical Keyboard",
                    "quantity": 1,
                    "unit_price": Decimal("129.99"),
                },
                {
                    "product_id": mouse_id,
                    "name": "Wireless Mouse",
                    "quantity": 2,
                    "unit_price": Decimal("49.99"),
                },
            ],
            "currency": "USD",
        },
        {
            "customer_id": bob_id,
            "items": [
                {
                    "product_id": dock_id,
                    "name": "USB-C Dock",
                    "quantity": 1,
                    "unit_price": Decimal("89.99"),
                },
            ],
            "currency": "USD",
        },
    ]

    for order in orders:
        document = build_order(**order)

        existing = collection.find_one(
            {
                "customer_id": document["customer_id"],
                "items": {
                    "$elemMatch": {
                        "product_id": document["items"][0]["product_id"],
                    },
                },
                "subtotal": document["subtotal"],
            },
            projection={"_id": 1},
        )

        if existing is None:
            collection.insert_one(document)


def ensure_seed_indexes() -> None:
    """Create indexes required by the seeded access patterns."""
    database = get_database()

    database["customers"].create_index(
        [("email", ASCENDING)],
        unique=True,
        name="uq_email",
    )

    database["customers"].create_index(
        [("is_active", ASCENDING), ("created_at", DESCENDING)],
        name="idx_active_created_at",
    )

    database["products"].create_index(
        [("sku", ASCENDING)],
        unique=True,
        name="uq_sku",
    )

    database["products"].create_index(
        [("category", ASCENDING), ("created_at", DESCENDING)],
        name="idx_category_created_at",
    )

    database["orders"].create_index(
        [("customer_id", ASCENDING), ("created_at", DESCENDING)],
        name="idx_customer_created_at",
    )

    database["orders"].create_index(
        [("status", ASCENDING), ("created_at", DESCENDING)],
        name="idx_status_created_at",
    )


def seed_database() -> None:
    """Seed the database with representative, repeatable development data."""
    ping_database()

    ensure_seed_indexes()

    customer_ids = seed_customers()
    product_ids = seed_products()

    seed_orders(
        customer_ids=customer_ids,
        product_ids=product_ids,
    )


def main() -> None:
    """Run the database seed operation."""
    try:
        seed_database()
        print("MongoDB seed data created successfully.")
    except PyMongoError as exc:
        raise RuntimeError("MongoDB seed operation failed.") from exc


if __name__ == "__main__":
    main()

"""Seed representative data for the MongoDB data modeling application."""

from __future__ import annotations

from decimal import Decimal

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError

from database.connection import get_database, ping_database
from models.customer import build_customer
from models.order import build_order
from models.product import build_product


def seed_customers() -> dict[str, ObjectId]:
    """Create representative customers and return their identifiers."""
    collection = get_database()["customers"]

    customers = [
        {
            "name": "Alice Johnson",
            "email": "alice.johnson@example.com",
            "phone": "+1-555-0101",
        },
        {
            "name": "Bob Smith",
            "email": "bob.smith@example.com",
            "phone": "+1-555-0102",
        },
        {
            "name": "Carol Williams",
            "email": "carol.williams@example.com",
            "phone": "+1-555-0103",
        },
    ]

    customer_ids: dict[str, ObjectId] = {}

    for customer in customers:
        existing = collection.find_one(
            {"email": customer["email"]},
            projection={"_id": 1},
        )

        if existing is not None:
            customer_ids[customer["email"]] = existing["_id"]
            continue

        document = build_customer(**customer)

        try:
            collection.insert_one(document)
            customer_ids[customer["email"]] = document["_id"]
        except DuplicateKeyError:
            existing = collection.find_one(
                {"email": customer["email"]},
                projection={"_id": 1},
            )

            if existing is None:
                raise

            customer_ids[customer["email"]] = existing["_id"]

    return customer_ids


def seed_products() -> dict[str, ObjectId]:
    """Create representative products and return their identifiers."""
    collection = get_database()["products"]

    products = [
        {
            "name": "Mechanical Keyboard",
            "sku": "KB-MECH-001",
            "price": Decimal("129.99"),
            "category": "electronics",
            "stock_quantity": 50,
            "description": "Mechanical keyboard with programmable keys.",
        },
        {
            "name": "Wireless Mouse",
            "sku": "MS-WIRELESS-001",
            "price": Decimal("49.99"),
            "category": "electronics",
            "stock_quantity": 100,
            "description": "Ergonomic wireless mouse with adjustable DPI.",
        },
        {
            "name": "USB-C Dock",
            "sku": "DOCK-USBC-001",
            "price": Decimal("89.99"),
            "category": "accessories",
            "stock_quantity": 35,
            "description": "USB-C dock with HDMI, USB, and Ethernet ports.",
        },
    ]

    product_ids: dict[str, ObjectId] = {}

    for product in products:
        existing = collection.find_one(
            {"sku": product["sku"]},
            projection={"_id": 1},
        )

        if existing is not None:
            product_ids[product["sku"]] = existing["_id"]
            continue

        document = build_product(**product)

        try:
            collection.insert_one(document)
            product_ids[product["sku"]] = document["_id"]
        except DuplicateKeyError:
            existing = collection.find_one(
                {"sku": product["sku"]},
                projection={"_id": 1},
            )

            if existing is None:
                raise

            product_ids[product["sku"]] = existing["_id"]

    return product_ids


def seed_orders(
    customer_ids: dict[str, ObjectId],
    product_ids: dict[str, ObjectId],
) -> None:
    """Create representative orders using customer references and snapshots."""
    collection = get_database()["orders"]

    alice_id = customer_ids["alice.johnson@example.com"]
    bob_id = customer_ids["bob.smith@example.com"]

    keyboard_id = product_ids["KB-MECH-001"]
    mouse_id = product_ids["MS-WIRELESS-001"]
    dock_id = product_ids["DOCK-USBC-001"]

    orders = [
        {
            "customer_id": alice_id,
            "items": [
                {
                    "product_id": keyboard_id,
                    "name": "Mechanical Keyboard",
                    "quantity": 1,
                    "unit_price": Decimal("129.99"),
                },
                {
                    "product_id": mouse_id,
                    "name": "Wireless Mouse",
                    "quantity": 2,
                    "unit_price": Decimal("49.99"),
                },
            ],
            "currency": "USD",
        },
        {
            "customer_id": bob_id,
            "items": [
                {
                    "product_id": dock_id,
                    "name": "USB-C Dock",
                    "quantity": 1,
                    "unit_price": Decimal("89.99"),
                },
            ],
            "currency": "USD",
        },
    ]

    for order in orders:
        document = build_order(**order)

        existing = collection.find_one(
            {
                "customer_id": document["customer_id"],
                "items": {
                    "$elemMatch": {
                        "product_id": document["items"][0]["product_id"],
                    },
                },
                "subtotal": document["subtotal"],
            },
            projection={"_id": 1},
        )

        if existing is None:
            collection.insert_one(document)


def ensure_seed_indexes() -> None:
    """Create indexes required by the seeded access patterns."""
    database = get_database()

    database["customers"].create_index(
        [("email", ASCENDING)],
        unique=True,
        name="uq_email",
    )

    database["customers"].create_index(
        [("is_active", ASCENDING), ("created_at", DESCENDING)],
        name="idx_active_created_at",
    )

    database["products"].create_index(
        [("sku", ASCENDING)],
        unique=True,
        name="uq_sku",
    )

    database["products"].create_index(
        [("category", ASCENDING), ("created_at", DESCENDING)],
        name="idx_category_created_at",
    )

    database["orders"].create_index(
        [("customer_id", ASCENDING), ("created_at", DESCENDING)],
        name="idx_customer_created_at",
    )

    database["orders"].create_index(
        [("status", ASCENDING), ("created_at", DESCENDING)],
        name="idx_status_created_at",
    )


def seed_database() -> None:
    """Seed the database with representative, repeatable development data."""
    ping_database()

    ensure_seed_indexes()

    customer_ids = seed_customers()
    product_ids = seed_products()

    seed_orders(
        customer_ids=customer_ids,
        product_ids=product_ids,
    )


def main() -> None:
    """Run the database seed operation."""
    try:
        seed_database()
        print("MongoDB seed data created successfully.")
    except PyMongoError as exc:
        raise RuntimeError("MongoDB seed operation failed.") from exc


if __name__ == "__main__":
    main()