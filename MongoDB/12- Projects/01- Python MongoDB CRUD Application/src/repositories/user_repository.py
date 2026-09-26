"""Repository layer for MongoDB user persistence operations."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from pymongo.collection import Collection
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

from src.models.user import build_user_document, update_user_document


class UserRepository:
    """Provide database operations for the users collection."""

    def __init__(self, collection: Collection) -> None:
        self._collection = collection

    def create(
        self,
        *,
        name: str,
        email: str,
        active: bool = True,
    ) -> ObjectId:
        """Create a user and return its MongoDB identifier."""
        document = build_user_document(
            name=name,
            email=email,
            active=active,
        )

        result: InsertOneResult = self._collection.insert_one(document)
        return result.inserted_id

    def get_by_id(self, user_id: ObjectId) -> dict[str, Any] | None:
        """Return a user by ObjectId."""
        return self._collection.find_one({"_id": user_id})

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        """Return a user by normalized email address."""
        return self._collection.find_one({"email": email.strip().lower()})

    def list_users(
        self,
        *,
        active: bool | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Return users using bounded offset pagination."""
        if skip < 0:
            raise ValueError("skip must be greater than or equal to zero")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        query: dict[str, Any] = {}

        if active is not None:
            query["active"] = active

        cursor = (
            self._collection.find(query)
            .sort("_id", 1)
            .skip(skip)
            .limit(limit)
        )

        return list(cursor)

    def update(
        self,
        user_id: ObjectId,
        *,
        name: str | None = None,
        active: bool | None = None,
    ) -> UpdateResult:
        """Update mutable user fields."""
        update = update_user_document(
            name=name,
            active=active,
        )

        return self._collection.update_one(
            {"_id": user_id},
            update,
        )

    def delete(self, user_id: ObjectId) -> DeleteResult:
        """Delete a user by ObjectId."""
        return self._collection.delete_one({"_id": user_id})

"""Repository layer for MongoDB user persistence operations."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from pymongo.collection import Collection
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

from src.models.user import build_user_document, update_user_document


class UserRepository:
    """Provide database operations for the users collection."""

    def __init__(self, collection: Collection) -> None:
        self._collection = collection

    def create(
        self,
        *,
        name: str,
        email: str,
        active: bool = True,
    ) -> ObjectId:
        """Create a user and return its MongoDB identifier."""
        document = build_user_document(
            name=name,
            email=email,
            active=active,
        )

        result: InsertOneResult = self._collection.insert_one(document)
        return result.inserted_id

    def get_by_id(self, user_id: ObjectId) -> dict[str, Any] | None:
        """Return a user by ObjectId."""
        return self._collection.find_one({"_id": user_id})

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        """Return a user by normalized email address."""
        return self._collection.find_one({"email": email.strip().lower()})

    def list_users(
        self,
        *,
        active: bool | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Return users using bounded offset pagination."""
        if skip < 0:
            raise ValueError("skip must be greater than or equal to zero")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        query: dict[str, Any] = {}

        if active is not None:
            query["active"] = active

        cursor = (
            self._collection.find(query)
            .sort("_id", 1)
            .skip(skip)
            .limit(limit)
        )

        return list(cursor)

    def update(
        self,
        user_id: ObjectId,
        *,
        name: str | None = None,
        active: bool | None = None,
    ) -> UpdateResult:
        """Update mutable user fields."""
        update = update_user_document(
            name=name,
            active=active,
        )

        return self._collection.update_one(
            {"_id": user_id},
            update,
        )

    def delete(self, user_id: ObjectId) -> DeleteResult:
        """Delete a user by ObjectId."""
        return self._collection.delete_one({"_id": user_id})