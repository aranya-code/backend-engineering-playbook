"""Business service layer for user operations."""

from __future__ import annotations

from typing import Any

from pymongo.errors import DuplicateKeyError

from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate, UserResponse, UserUpdate


class UserService:
    """Coordinate user business operations and repository access."""

    def __init__(self, repository: UserRepository) -> None:
        """Initialize the service with a user repository."""
        self.repository = repository

    def create_user(self, user: UserCreate) -> UserResponse:
        """Create a user after enforcing business-level uniqueness."""
        if self.repository.get_by_email(str(user.email)) is not None:
            raise ValueError("A user with this email already exists")

        try:
            document = self.repository.create(user)
        except DuplicateKeyError as exc:
            raise ValueError("A user with this email already exists") from exc

        return self._to_response(document)

    def get_user(self, user_id: str) -> UserResponse | None:
        """Return a user by ID, or None when the user does not exist."""
        document = self.repository.get_by_id(user_id)

        if document is None:
            return None

        return self._to_response(document)

    def get_user_by_email(self, email: str) -> UserResponse | None:
        """Return a user by email address."""
        document = self.repository.get_by_email(email)

        if document is None:
            return None

        return self._to_response(document)

    def list_users(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        active: bool | None = None,
    ) -> list[UserResponse]:
        """Return users using repository-level pagination."""
        if skip < 0:
            raise ValueError("skip must be greater than or equal to zero")

        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")

        documents = self.repository.list(
            skip=skip,
            limit=limit,
            active=active,
        )

        return [self._to_response(document) for document in documents]

    def update_user(
        self,
        user_id: str,
        user: UserUpdate,
    ) -> UserResponse | None:
        """Update a user and return the updated representation."""
        if user.email is not None:
            existing = self.repository.get_by_email(str(user.email))

            if existing is not None and str(existing["_id"]) != user_id:
                raise ValueError("A user with this email already exists")

        try:
            document = self.repository.update(user_id, user)
        except DuplicateKeyError as exc:
            raise ValueError("A user with this email already exists") from exc

        if document is None:
            return None

        return self._to_response(document)

    def delete_user(self, user_id: str) -> bool:
        """Delete a user and return whether deletion occurred."""
        return self.repository.delete(user_id)

    def count_users(self, *, active: bool | None = None) -> int:
        """Return the number of users matching the supplied filter."""
        return self.repository.count(active=active)

    @staticmethod
    def _to_response(document: dict[str, Any]) -> UserResponse:
        """Convert a MongoDB document into an API response schema."""
        return UserResponse(
            id=str(document["_id"]),
            name=document["name"],
            email=document["email"],
            active=document["active"],
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )

"""Business service layer for user operations."""

from __future__ import annotations

from typing import Any

from pymongo.errors import DuplicateKeyError

from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate, UserResponse, UserUpdate


class UserService:
    """Coordinate user business operations and repository access."""

    def __init__(self, repository: UserRepository) -> None:
        """Initialize the service with a user repository."""
        self.repository = repository

    def create_user(self, user: UserCreate) -> UserResponse:
        """Create a user after enforcing business-level uniqueness."""
        if self.repository.get_by_email(str(user.email)) is not None:
            raise ValueError("A user with this email already exists")

        try:
            document = self.repository.create(user)
        except DuplicateKeyError as exc:
            raise ValueError("A user with this email already exists") from exc

        return self._to_response(document)

    def get_user(self, user_id: str) -> UserResponse | None:
        """Return a user by ID, or None when the user does not exist."""
        document = self.repository.get_by_id(user_id)

        if document is None:
            return None

        return self._to_response(document)

    def get_user_by_email(self, email: str) -> UserResponse | None:
        """Return a user by email address."""
        document = self.repository.get_by_email(email)

        if document is None:
            return None

        return self._to_response(document)

    def list_users(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        active: bool | None = None,
    ) -> list[UserResponse]:
        """Return users using repository-level pagination."""
        if skip < 0:
            raise ValueError("skip must be greater than or equal to zero")

        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")

        documents = self.repository.list(
            skip=skip,
            limit=limit,
            active=active,
        )

        return [self._to_response(document) for document in documents]

    def update_user(
        self,
        user_id: str,
        user: UserUpdate,
    ) -> UserResponse | None:
        """Update a user and return the updated representation."""
        if user.email is not None:
            existing = self.repository.get_by_email(str(user.email))

            if existing is not None and str(existing["_id"]) != user_id:
                raise ValueError("A user with this email already exists")

        try:
            document = self.repository.update(user_id, user)
        except DuplicateKeyError as exc:
            raise ValueError("A user with this email already exists") from exc

        if document is None:
            return None

        return self._to_response(document)

    def delete_user(self, user_id: str) -> bool:
        """Delete a user and return whether deletion occurred."""
        return self.repository.delete(user_id)

    def count_users(self, *, active: bool | None = None) -> int:
        """Return the number of users matching the supplied filter."""
        return self.repository.count(active=active)

    @staticmethod
    def _to_response(document: dict[str, Any]) -> UserResponse:
        """Convert a MongoDB document into an API response schema."""
        return UserResponse(
            id=str(document["_id"]),
            name=document["name"],
            email=document["email"],
            active=document["active"],
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )