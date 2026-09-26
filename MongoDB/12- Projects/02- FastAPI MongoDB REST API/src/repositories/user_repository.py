"""MongoDB repository for user persistence operations."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from src.schemas.user import UserCreate, UserUpdate


class UserRepository:
    """Provide persistence operations for users."""

    def __init__(self, collection: Collection) -> None:
        """Initialize the repository with a MongoDB collection."""
        self.collection = collection

    def create(self, user: UserCreate) -> dict[str, Any]:
        """Create a user and return the persisted document."""
        now = datetime.now(UTC)

        document = {
            "name": user.name,
            "email": str(user.email),
            "active": user.active,
            "created_at": now,
            "updated_at": now,
        }

        try:
            result = self.collection.insert_one(document)
        except DuplicateKeyError:
            raise

        document["_id"] = result.inserted_id
        return document

    def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        """Return a user by ObjectId, or None when it does not exist."""
        if not ObjectId.is_valid(user_id):
            return None

        return self.collection.find_one({"_id": ObjectId(user_id)})

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        """Return a user by its unique email address."""
        return self.collection.find_one({"email": email})

    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        active: bool | None = None,
    ) -> list[dict[str, Any]]:
        """Return users using bounded offset pagination."""
        filters: dict[str, Any] = {}

        if active is not None:
            filters["active"] = active

        cursor = (
            self.collection.find(filters)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        return list(cursor)

    def update(
        self,
        user_id: str,
        user: UserUpdate,
    ) -> dict[str, Any] | None:
        """Update mutable user fields and return the updated document."""
        if not ObjectId.is_valid(user_id):
            return None

        updates = user.model_dump(exclude_unset=True)

        if not updates:
            return self.get_by_id(user_id)

        updates["updated_at"] = datetime.now(UTC)

        result = self.collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": updates},
            return_document=True,
        )

        return result

    def delete(self, user_id: str) -> bool:
        """Delete a user and return whether a document was removed."""
        if not ObjectId.is_valid(user_id):
            return False

        result = self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count == 1

    def count(self, *, active: bool | None = None) -> int:
        """Count users, optionally filtering by active status."""
        filters: dict[str, Any] = {}

        if active is not None:
            filters["active"] = active

        return self.collection.count_documents(filters)

"""MongoDB repository for user persistence operations."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from src.schemas.user import UserCreate, UserUpdate


class UserRepository:
    """Provide persistence operations for users."""

    def __init__(self, collection: Collection) -> None:
        """Initialize the repository with a MongoDB collection."""
        self.collection = collection

    def create(self, user: UserCreate) -> dict[str, Any]:
        """Create a user and return the persisted document."""
        now = datetime.now(UTC)

        document = {
            "name": user.name,
            "email": str(user.email),
            "active": user.active,
            "created_at": now,
            "updated_at": now,
        }

        try:
            result = self.collection.insert_one(document)
        except DuplicateKeyError:
            raise

        document["_id"] = result.inserted_id
        return document

    def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        """Return a user by ObjectId, or None when it does not exist."""
        if not ObjectId.is_valid(user_id):
            return None

        return self.collection.find_one({"_id": ObjectId(user_id)})

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        """Return a user by its unique email address."""
        return self.collection.find_one({"email": email})

    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        active: bool | None = None,
    ) -> list[dict[str, Any]]:
        """Return users using bounded offset pagination."""
        filters: dict[str, Any] = {}

        if active is not None:
            filters["active"] = active

        cursor = (
            self.collection.find(filters)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        return list(cursor)

    def update(
        self,
        user_id: str,
        user: UserUpdate,
    ) -> dict[str, Any] | None:
        """Update mutable user fields and return the updated document."""
        if not ObjectId.is_valid(user_id):
            return None

        updates = user.model_dump(exclude_unset=True)

        if not updates:
            return self.get_by_id(user_id)

        updates["updated_at"] = datetime.now(UTC)

        result = self.collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": updates},
            return_document=True,
        )

        return result

    def delete(self, user_id: str) -> bool:
        """Delete a user and return whether a document was removed."""
        if not ObjectId.is_valid(user_id):
            return False

        result = self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count == 1

    def count(self, *, active: bool | None = None) -> int:
        """Count users, optionally filtering by active status."""
        filters: dict[str, Any] = {}

        if active is not None:
            filters["active"] = active

        return self.collection.count_documents(filters)