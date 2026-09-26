"""Repository for customer document persistence and queries."""

from __future__ import annotations

from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

from config.settings import MONGODB_COLLECTION


class CustomerRepository:
    """Provide persistence operations for customer documents."""

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
        customer: dict[str, Any],
    ) -> InsertOneResult:
        """Insert a customer document.

        MongoDB schema validation is enforced at the collection boundary.
        """
        return self._collection.insert_one(customer)

    def get_by_customer_id(
        self,
        customer_id: str,
    ) -> dict[str, Any] | None:
        """Return a customer by its application-level identifier."""
        return self._collection.find_one(
            {"customer_id": customer_id}
        )

    def get_by_email(
        self,
        email: str,
    ) -> dict[str, Any] | None:
        """Return a customer by email address."""
        return self._collection.find_one(
            {"email": email}
        )

    def list_active(
        self,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return active customers up to the requested limit."""
        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        cursor = (
            self._collection
            .find({"status": "active"})
            .sort("customer_id", 1)
            .limit(limit)
        )

        return list(cursor)

    def update_by_customer_id(
        self,
        customer_id: str,
        updates: dict[str, Any],
    ) -> UpdateResult:
        """Update customer fields using MongoDB's $set operator."""
        if not updates:
            raise ValueError("updates must not be empty")

        return self._collection.update_one(
            {"customer_id": customer_id},
            {"$set": updates},
        )

    def delete_by_customer_id(
        self,
        customer_id: str,
    ) -> DeleteResult:
        """Delete a customer by its application-level identifier."""
        return self._collection.delete_one(
            {"customer_id": customer_id}
        )

    def exists(
        self,
        customer_id: str,
    ) -> bool:
        """Check whether a customer exists without loading the document."""
        return (
            self._collection.count_documents(
                {"customer_id": customer_id},
                limit=1,
            )
            > 0
        )

"""Repository for customer document persistence and queries."""

from __future__ import annotations

from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

from config.settings import MONGODB_COLLECTION


class CustomerRepository:
    """Provide persistence operations for customer documents."""

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
        customer: dict[str, Any],
    ) -> InsertOneResult:
        """Insert a customer document.

        MongoDB schema validation is enforced at the collection boundary.
        """
        return self._collection.insert_one(customer)

    def get_by_customer_id(
        self,
        customer_id: str,
    ) -> dict[str, Any] | None:
        """Return a customer by its application-level identifier."""
        return self._collection.find_one(
            {"customer_id": customer_id}
        )

    def get_by_email(
        self,
        email: str,
    ) -> dict[str, Any] | None:
        """Return a customer by email address."""
        return self._collection.find_one(
            {"email": email}
        )

    def list_active(
        self,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return active customers up to the requested limit."""
        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        cursor = (
            self._collection
            .find({"status": "active"})
            .sort("customer_id", 1)
            .limit(limit)
        )

        return list(cursor)

    def update_by_customer_id(
        self,
        customer_id: str,
        updates: dict[str, Any],
    ) -> UpdateResult:
        """Update customer fields using MongoDB's $set operator."""
        if not updates:
            raise ValueError("updates must not be empty")

        return self._collection.update_one(
            {"customer_id": customer_id},
            {"$set": updates},
        )

    def delete_by_customer_id(
        self,
        customer_id: str,
    ) -> DeleteResult:
        """Delete a customer by its application-level identifier."""
        return self._collection.delete_one(
            {"customer_id": customer_id}
        )

    def exists(
        self,
        customer_id: str,
    ) -> bool:
        """Check whether a customer exists without loading the document."""
        return (
            self._collection.count_documents(
                {"customer_id": customer_id},
                limit=1,
            )
            > 0
        )