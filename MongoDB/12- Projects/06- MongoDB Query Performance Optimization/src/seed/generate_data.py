"""Generate controlled MongoDB datasets for query performance testing."""

from __future__ import annotations

import argparse
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection

from config.settings import MONGODB_DATABASE, MONGODB_URI

DEFAULT_COLLECTION = "orders"
DEFAULT_BATCH_SIZE = 1_000

STATUSES = ("pending", "processing", "completed", "cancelled", "refunded")
PRODUCT_CATEGORIES = (
    "electronics",
    "books",
    "home",
    "fitness",
    "software",
    "office",
    "fashion",
)


def random_customer_id(rng: random.Random) -> str:
    """Generate a stable-format synthetic customer identifier."""
    return f"customer_{rng.randint(1, 100_000):06d}"


def random_product(rng: random.Random) -> dict[str, Any]:
    """Generate a synthetic order item."""
    category = rng.choice(PRODUCT_CATEGORIES)

    return {
        "sku": f"SKU-{rng.randint(1, 50_000):06d}",
        "name": f"{category}-{rng.randint(1, 10_000):04d}",
        "category": category,
        "quantity": rng.randint(1, 5),
        "unit_price": round(rng.uniform(10.0, 1_000.0), 2),
    }


def generate_order(rng: random.Random, index: int) -> dict[str, Any]:
    """Generate one realistic synthetic order document."""
    now = datetime.now(timezone.utc)
    created_at = now - timedelta(
        days=rng.randint(0, 730),
        hours=rng.randint(0, 23),
        minutes=rng.randint(0, 59),
    )

    items = [random_product(rng) for _ in range(rng.randint(1, 5))]
    total = round(
        sum(item["quantity"] * item["unit_price"] for item in items),
        2,
    )

    return {
        "order_number": f"ORD-{index:010d}",
        "customer_id": random_customer_id(rng),
        "status": rng.choice(STATUSES),
        "created_at": created_at,
        "updated_at": created_at + timedelta(minutes=rng.randint(1, 120)),
        "total": total,
        "currency": "USD",
        "shipping": {
            "country": rng.choice(("US", "CA", "GB", "DE", "AU")),
            "postal_code": "".join(rng.choices(string.digits, k=5)),
        },
        "items": items,
        "metadata": {
            "source": rng.choice(("web", "mobile", "api")),
            "campaign": rng.choice(
                ("organic", "email", "search", "affiliate", "direct")
            ),
        },
    }


def generate_orders(
    collection: Collection[dict[str, Any]],
    *,
    count: int,
    batch_size: int = DEFAULT_BATCH_SIZE,
    seed: int | None = 42,
) -> int:
    """Generate and insert orders in bounded batches."""
    if count <= 0:
        raise ValueError("count must be greater than zero")

    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    rng = random.Random(seed)
    inserted = 0

    while inserted < count:
        current_batch_size = min(batch_size, count - inserted)

        documents = [
            generate_order(rng, inserted + offset + 1)
            for offset in range(current_batch_size)
        ]

        result = collection.insert_many(
            documents,
            ordered=False,
        )
        inserted += len(result.inserted_ids)

    return inserted


def build_indexes(collection: Collection[dict[str, Any]]) -> None:
    """Create indexes used by the optimized query examples."""
    collection.create_index(
        [
            ("customer_id", 1),
            ("status", 1),
            ("created_at", -1),
        ],
        name="customer_status_created_at",
    )

    collection.create_index(
        [
            ("status", 1),
            ("created_at", -1),
        ],
        name="status_created_at",
    )

    collection.create_index(
        [
            ("items.category", 1),
            ("created_at", -1),
        ],
        name="items_category_created_at",
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line options for dataset generation."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic MongoDB performance-test data.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100_000,
        help="Number of documents to generate.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Number of documents inserted per batch.",
    )
    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
        help="Target MongoDB collection.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible datasets.",
    )
    parser.add_argument(
        "--create-indexes",
        action="store_true",
        help="Create indexes used by optimized query examples.",
    )
    return parser.parse_args()


def main() -> None:
    """Generate the requested performance-test dataset."""
    args = parse_args()

    client = MongoClient(MONGODB_URI)
    collection = client[MONGODB_DATABASE][args.collection]

    try:
        inserted = generate_orders(
            collection,
            count=args.count,
            batch_size=args.batch_size,
            seed=args.seed,
        )

        if args.create_indexes:
            build_indexes(collection)

        print(f"Inserted {inserted:,} documents into '{args.collection}'.")
    finally:
        client.close()


if __name__ == "__main__":
    main()

"""Generate controlled MongoDB datasets for query performance testing."""

from __future__ import annotations

import argparse
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection

from config.settings import MONGODB_DATABASE, MONGODB_URI

DEFAULT_COLLECTION = "orders"
DEFAULT_BATCH_SIZE = 1_000

STATUSES = ("pending", "processing", "completed", "cancelled", "refunded")
PRODUCT_CATEGORIES = (
    "electronics",
    "books",
    "home",
    "fitness",
    "software",
    "office",
    "fashion",
)


def random_customer_id(rng: random.Random) -> str:
    """Generate a stable-format synthetic customer identifier."""
    return f"customer_{rng.randint(1, 100_000):06d}"


def random_product(rng: random.Random) -> dict[str, Any]:
    """Generate a synthetic order item."""
    category = rng.choice(PRODUCT_CATEGORIES)

    return {
        "sku": f"SKU-{rng.randint(1, 50_000):06d}",
        "name": f"{category}-{rng.randint(1, 10_000):04d}",
        "category": category,
        "quantity": rng.randint(1, 5),
        "unit_price": round(rng.uniform(10.0, 1_000.0), 2),
    }


def generate_order(rng: random.Random, index: int) -> dict[str, Any]:
    """Generate one realistic synthetic order document."""
    now = datetime.now(timezone.utc)
    created_at = now - timedelta(
        days=rng.randint(0, 730),
        hours=rng.randint(0, 23),
        minutes=rng.randint(0, 59),
    )

    items = [random_product(rng) for _ in range(rng.randint(1, 5))]
    total = round(
        sum(item["quantity"] * item["unit_price"] for item in items),
        2,
    )

    return {
        "order_number": f"ORD-{index:010d}",
        "customer_id": random_customer_id(rng),
        "status": rng.choice(STATUSES),
        "created_at": created_at,
        "updated_at": created_at + timedelta(minutes=rng.randint(1, 120)),
        "total": total,
        "currency": "USD",
        "shipping": {
            "country": rng.choice(("US", "CA", "GB", "DE", "AU")),
            "postal_code": "".join(rng.choices(string.digits, k=5)),
        },
        "items": items,
        "metadata": {
            "source": rng.choice(("web", "mobile", "api")),
            "campaign": rng.choice(
                ("organic", "email", "search", "affiliate", "direct")
            ),
        },
    }


def generate_orders(
    collection: Collection[dict[str, Any]],
    *,
    count: int,
    batch_size: int = DEFAULT_BATCH_SIZE,
    seed: int | None = 42,
) -> int:
    """Generate and insert orders in bounded batches."""
    if count <= 0:
        raise ValueError("count must be greater than zero")

    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    rng = random.Random(seed)
    inserted = 0

    while inserted < count:
        current_batch_size = min(batch_size, count - inserted)

        documents = [
            generate_order(rng, inserted + offset + 1)
            for offset in range(current_batch_size)
        ]

        result = collection.insert_many(
            documents,
            ordered=False,
        )
        inserted += len(result.inserted_ids)

    return inserted


def build_indexes(collection: Collection[dict[str, Any]]) -> None:
    """Create indexes used by the optimized query examples."""
    collection.create_index(
        [
            ("customer_id", 1),
            ("status", 1),
            ("created_at", -1),
        ],
        name="customer_status_created_at",
    )

    collection.create_index(
        [
            ("status", 1),
            ("created_at", -1),
        ],
        name="status_created_at",
    )

    collection.create_index(
        [
            ("items.category", 1),
            ("created_at", -1),
        ],
        name="items_category_created_at",
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line options for dataset generation."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic MongoDB performance-test data.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100_000,
        help="Number of documents to generate.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Number of documents inserted per batch.",
    )
    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
        help="Target MongoDB collection.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible datasets.",
    )
    parser.add_argument(
        "--create-indexes",
        action="store_true",
        help="Create indexes used by optimized query examples.",
    )
    return parser.parse_args()


def main() -> None:
    """Generate the requested performance-test dataset."""
    args = parse_args()

    client = MongoClient(MONGODB_URI)
    collection = client[MONGODB_DATABASE][args.collection]

    try:
        inserted = generate_orders(
            collection,
            count=args.count,
            batch_size=args.batch_size,
            seed=args.seed,
        )

        if args.create_indexes:
            build_indexes(collection)

        print(f"Inserted {inserted:,} documents into '{args.collection}'.")
    finally:
        client.close()


if __name__ == "__main__":
    main()