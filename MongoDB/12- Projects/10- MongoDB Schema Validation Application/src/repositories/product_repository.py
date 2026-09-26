"""Repository for product document persistence and queries."""

from __future__ import annotations

from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

from config.settings import MONGODB_COLLECTION


class ProductRepository:
    """Provide persistence operations for product documents."""

    def __init__(self, database: Database) -> None:
        """Initialize the repository with a MongoDB database."""
        self._collection: Collection[dict[str, Any]] = database[
            MONGODB_COLLECTION
        ]

    @property
    def collection(self) -> Collection[dict[str, Any]]:
        """Return the underlying MongoDB collection."""
        return self._collection

    def create(
        self,
        product: dict[str, Any],
    ) -> InsertOneResult:
        """Insert a product document.

        MongoDB schema validation is enforced at the collection boundary.
        """
        return self._collection.insert_one(product)

    def get_by_product_id(
        self,
        product_id: str,
    ) -> dict[str, Any] | None:
        """Return a product by its application-level identifier."""
        return self._collection.find_one(
            {"product_id": product_id}
        )

    def get_by_sku(
        self,
        sku: str,
    ) -> dict[str, Any] | None:
        """Return a product by stock keeping unit."""
        return self._collection.find_one({"sku": sku})

    def list_active(
        self,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return active products up to the requested limit."""
        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        cursor = (
            self._collection
            .find({"status": "active"})
            .sort("product_id", 1)
            .limit(limit)
        )

        return list(cursor)

    def list_by_category(
        self,
        category: str,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return products belonging to a category."""
        if not category:
            raise ValueError("category must not be empty")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        cursor = (
            self._collection
            .find(
                {
                    "category": category,
                    "status": "active",
                }
            )
            .sort("product_id", 1)
            .limit(limit)
        )

        return list(cursor)

    def update_by_product_id(
        self,
        product_id: str,
        updates: dict[str, Any],
    ) -> UpdateResult:
        """Update product fields using MongoDB's $set operator."""
        if not updates:
            raise ValueError("updates must not be empty")

        return self._collection.update_one(
            {"product_id": product_id},
            {"$set": updates},
        )

    def update_stock(
        self,
        product_id: str,
        stock_quantity: int,
    ) -> UpdateResult:
        """Set the stock quantity for a product."""
        if stock_quantity < 0:
            raise ValueError("stock_quantity must not be negative")

        return self._collection.update_one(
            {"product_id": product_id},
            {"$set": {"stock_quantity": stock_quantity}},
        )

    def delete_by_product_id(
        self,
        product_id: str,
    ) -> DeleteResult:
        """Delete a product by its application-level identifier."""
        return self._collection.delete_one(
            {"product_id": product_id}
        )

    def exists(
        self,
        product_id: str,
    ) -> bool:
        """Check whether a product exists without loading the document."""
        return (
            self._collection.count_documents(
                {"product_id": product_id},
                limit=1,
            )
            > 0
        )

"""Repository for product document persistence and queries."""

from __future__ import annotations

from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

from config.settings import MONGODB_COLLECTION


class ProductRepository:
    """Provide persistence operations for product documents."""

    def __init__(self, database: Database) -> None:
        """Initialize the repository with a MongoDB database."""
        self._collection: Collection[dict[str, Any]] = database[
            MONGODB_COLLECTION
        ]

    @property
    def collection(self) -> Collection[dict[str, Any]]:
        """Return the underlying MongoDB collection."""
        return self._collection

    def create(
        self,
        product: dict[str, Any],
    ) -> InsertOneResult:
        """Insert a product document.

        MongoDB schema validation is enforced at the collection boundary.
        """
        return self._collection.insert_one(product)

    def get_by_product_id(
        self,
        product_id: str,
    ) -> dict[str, Any] | None:
        """Return a product by its application-level identifier."""
        return self._collection.find_one(
            {"product_id": product_id}
        )

    def get_by_sku(
        self,
        sku: str,
    ) -> dict[str, Any] | None:
        """Return a product by stock keeping unit."""
        return self._collection.find_one({"sku": sku})

    def list_active(
        self,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return active products up to the requested limit."""
        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        cursor = (
            self._collection
            .find({"status": "active"})
            .sort("product_id", 1)
            .limit(limit)
        )

        return list(cursor)

    def list_by_category(
        self,
        category: str,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return products belonging to a category."""
        if not category:
            raise ValueError("category must not be empty")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        cursor = (
            self._collection
            .find(
                {
                    "category": category,
                    "status": "active",
                }
            )
            .sort("product_id", 1)
            .limit(limit)
        )

        return list(cursor)

    def update_by_product_id(
        self,
        product_id: str,
        updates: dict[str, Any],
    ) -> UpdateResult:
        """Update product fields using MongoDB's $set operator."""
        if not updates:
            raise ValueError("updates must not be empty")

        return self._collection.update_one(
            {"product_id": product_id},
            {"$set": updates},
        )

    def update_stock(
        self,
        product_id: str,
        stock_quantity: int,
    ) -> UpdateResult:
        """Set the stock quantity for a product."""
        if stock_quantity < 0:
            raise ValueError("stock_quantity must not be negative")

        return self._collection.update_one(
            {"product_id": product_id},
            {"$set": {"stock_quantity": stock_quantity}},
        )

    def delete_by_product_id(
        self,
        product_id: str,
    ) -> DeleteResult:
        """Delete a product by its application-level identifier."""
        return self._collection.delete_one(
            {"product_id": product_id}
        )

    def exists(
        self,
        product_id: str,
    ) -> bool:
        """Check whether a product exists without loading the document."""
        return (
            self._collection.count_documents(
                {"product_id": product_id},
                limit=1,
            )
            > 0
        )