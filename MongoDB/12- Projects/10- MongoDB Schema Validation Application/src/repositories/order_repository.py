"""Repository for order document persistence and queries."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

from config.settings import MONGODB_COLLECTION


class OrderRepository:
    """Provide persistence operations for order documents."""

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
        order: dict[str, Any],
    ) -> InsertOneResult:
        """Insert an order document.

        MongoDB schema validation is enforced at the collection boundary.
        """
        return self._collection.insert_one(order)

    def get_by_order_id(
        self,
        order_id: str,
    ) -> dict[str, Any] | None:
        """Return an order by its application-level identifier."""
        return self._collection.find_one({"order_id": order_id})

    def get_by_customer_id(
        self,
        customer_id: str,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return orders belonging to a customer."""
        if not customer_id:
            raise ValueError("customer_id must not be empty")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        cursor = (
            self._collection
            .find({"customer_id": customer_id})
            .sort("order_date", -1)
            .limit(limit)
        )

        return list(cursor)

    def list_by_status(
        self,
        status: str,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return orders with the requested status."""
        if not status:
            raise ValueError("status must not be empty")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        cursor = (
            self._collection
            .find({"status": status})
            .sort("order_date", -1)
            .limit(limit)
        )

        return list(cursor)

    def list_by_date_range(
        self,
        start: datetime,
        end: datetime,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return orders created within a half-open date range."""
        if start >= end:
            raise ValueError("start must be earlier than end")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        cursor = (
            self._collection
            .find(
                {
                    "order_date": {
                        "$gte": start,
                        "$lt": end,
                    }
                }
            )
            .sort("order_date", -1)
            .limit(limit)
        )

        return list(cursor)

    def update_status(
        self,
        order_id: str,
        status: str,
        *,
        updated_at: datetime | None = None,
    ) -> UpdateResult:
        """Update an order's status and optional modification timestamp."""
        if not order_id:
            raise ValueError("order_id must not be empty")

        if not status:
            raise ValueError("status must not be empty")

        updates: dict[str, Any] = {"status": status}

        if updated_at is not None:
            updates["updated_at"] = updated_at

        return self._collection.update_one(
            {"order_id": order_id},
            {"$set": updates},
        )

    def update_by_order_id(
        self,
        order_id: str,
        updates: dict[str, Any],
    ) -> UpdateResult:
        """Update order fields using MongoDB's $set operator."""
        if not order_id:
            raise ValueError("order_id must not be empty")

        if not updates:
            raise ValueError("updates must not be empty")

        return self._collection.update_one(
            {"order_id": order_id},
            {"$set": updates},
        )

    def delete_by_order_id(
        self,
        order_id: str,
    ) -> DeleteResult:
        """Delete an order by its application-level identifier."""
        return self._collection.delete_one({"order_id": order_id})

    def exists(
        self,
        order_id: str,
    ) -> bool:
        """Check whether an order exists without loading the document."""
        return (
            self._collection.count_documents(
                {"order_id": order_id},
                limit=1,
            )
            > 0
        )

"""Repository for order document persistence and queries."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

from config.settings import MONGODB_COLLECTION


class OrderRepository:
    """Provide persistence operations for order documents."""

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
        order: dict[str, Any],
    ) -> InsertOneResult:
        """Insert an order document.

        MongoDB schema validation is enforced at the collection boundary.
        """
        return self._collection.insert_one(order)

    def get_by_order_id(
        self,
        order_id: str,
    ) -> dict[str, Any] | None:
        """Return an order by its application-level identifier."""
        return self._collection.find_one({"order_id": order_id})

    def get_by_customer_id(
        self,
        customer_id: str,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return orders belonging to a customer."""
        if not customer_id:
            raise ValueError("customer_id must not be empty")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        cursor = (
            self._collection
            .find({"customer_id": customer_id})
            .sort("order_date", -1)
            .limit(limit)
        )

        return list(cursor)

    def list_by_status(
        self,
        status: str,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return orders with the requested status."""
        if not status:
            raise ValueError("status must not be empty")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        cursor = (
            self._collection
            .find({"status": status})
            .sort("order_date", -1)
            .limit(limit)
        )

        return list(cursor)

    def list_by_date_range(
        self,
        start: datetime,
        end: datetime,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return orders created within a half-open date range."""
        if start >= end:
            raise ValueError("start must be earlier than end")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        cursor = (
            self._collection
            .find(
                {
                    "order_date": {
                        "$gte": start,
                        "$lt": end,
                    }
                }
            )
            .sort("order_date", -1)
            .limit(limit)
        )

        return list(cursor)

    def update_status(
        self,
        order_id: str,
        status: str,
        *,
        updated_at: datetime | None = None,
    ) -> UpdateResult:
        """Update an order's status and optional modification timestamp."""
        if not order_id:
            raise ValueError("order_id must not be empty")

        if not status:
            raise ValueError("status must not be empty")

        updates: dict[str, Any] = {"status": status}

        if updated_at is not None:
            updates["updated_at"] = updated_at

        return self._collection.update_one(
            {"order_id": order_id},
            {"$set": updates},
        )

    def update_by_order_id(
        self,
        order_id: str,
        updates: dict[str, Any],
    ) -> UpdateResult:
        """Update order fields using MongoDB's $set operator."""
        if not order_id:
            raise ValueError("order_id must not be empty")

        if not updates:
            raise ValueError("updates must not be empty")

        return self._collection.update_one(
            {"order_id": order_id},
            {"$set": updates},
        )

    def delete_by_order_id(
        self,
        order_id: str,
    ) -> DeleteResult:
        """Delete an order by its application-level identifier."""
        return self._collection.delete_one({"order_id": order_id})

    def exists(
        self,
        order_id: str,
    ) -> bool:
        """Check whether an order exists without loading the document."""
        return (
            self._collection.count_documents(
                {"order_id": order_id},
                limit=1,
            )
            > 0
        )