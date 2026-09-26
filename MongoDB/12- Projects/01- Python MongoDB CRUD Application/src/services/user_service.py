"""Service layer for MongoDB user business operations."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from src.repositories.user_repository import UserRepository


class UserService:
    """Coordinate user validation, business rules, and persistence."""

    def __init__(self, collection: Collection) -> None:
        self._repository = UserRepository(collection)

    def create_user(
        self,
        *,
        name: str,
        email: str,
        active: bool = True,
    ) -> ObjectId:
        """Create a user while enforcing application-level business rules."""
        try:
            return self._repository.create(
                name=name,
                email=email,
                active=active,
            )
        except DuplicateKeyError as exc:
            raise ValueError("A user with this email already exists") from exc

    def get_user(self, user_id: ObjectId) -> dict[str, Any] | None:
        """Return a user by identifier."""
        return self._repository.get_by_id(user_id)

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Return a user by email address."""
        return self._repository.get_by_email(email)

    def list_users(
        self,
        *,
        active: bool | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Return a bounded page of users."""
        return self._repository.list_users(
            active=active,
            skip=skip,
            limit=limit,
        )

    def update_user(
        self,
        user_id: ObjectId,
        *,
        name: str | None = None,
        active: bool | None = None,
    ) -> bool:
        """Update a user and return whether a document was modified."""
        if name is None and active is None:
            raise ValueError("At least one field must be provided for update")

        result = self._repository.update(
            user_id,
            name=name,
            active=active,
        )

        return result.modified_count == 1

    def delete_user(self, user_id: ObjectId) -> bool:
        """Delete a user and return whether a document was deleted."""
        result = self._repository.delete(user_id)
        return result.deleted_count == 1

"""Service layer for MongoDB user business operations."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from src.repositories.user_repository import UserRepository


class UserService:
    """Coordinate user validation, business rules, and persistence."""

    def __init__(self, collection: Collection) -> None:
        self._repository = UserRepository(collection)

    def create_user(
        self,
        *,
        name: str,
        email: str,
        active: bool = True,
    ) -> ObjectId:
        """Create a user while enforcing application-level business rules."""
        try:
            return self._repository.create(
                name=name,
                email=email,
                active=active,
            )
        except DuplicateKeyError as exc:
            raise ValueError("A user with this email already exists") from exc

    def get_user(self, user_id: ObjectId) -> dict[str, Any] | None:
        """Return a user by identifier."""
        return self._repository.get_by_id(user_id)

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Return a user by email address."""
        return self._repository.get_by_email(email)

    def list_users(
        self,
        *,
        active: bool | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Return a bounded page of users."""
        return self._repository.list_users(
            active=active,
            skip=skip,
            limit=limit,
        )

    def update_user(
        self,
        user_id: ObjectId,
        *,
        name: str | None = None,
        active: bool | None = None,
    ) -> bool:
        """Update a user and return whether a document was modified."""
        if name is None and active is None:
            raise ValueError("At least one field must be provided for update")

        result = self._repository.update(
            user_id,
            name=name,
            active=active,
        )

        return result.modified_count == 1

    def delete_user(self, user_id: ObjectId) -> bool:
        """Delete a user and return whether a document was deleted."""
        result = self._repository.delete(user_id)
        return result.deleted_count == 1