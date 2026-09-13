"""Application services for user-related business operations."""

from __future__ import annotations

from uuid import UUID, uuid4

from src.models.user import User
from src.repositories.user_repository import UserRepository


class UserService:
    """Coordinate user-related business logic and persistence."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def create_user(self, email: str, name: str) -> User:
        """Create and persist a new user after validating business rules."""
        normalized_email = email.strip().lower()
        normalized_name = name.strip()

        if not normalized_email:
            raise ValueError("Email must not be empty.")

        if not normalized_name:
            raise ValueError("Name must not be empty.")

        if self._repository.get_by_email(normalized_email) is not None:
            raise ValueError("A user with this email already exists.")

        user = User(
            id=uuid4(),
            email=normalized_email,
            name=normalized_name,
            is_active=True,
            created_at=self._repository.utcnow(),
            updated_at=self._repository.utcnow(),
        )

        return self._repository.create(user)

    def get_user(self, user_id: UUID) -> User | None:
        """Return a user by identifier, or None when it does not exist."""
        return self._repository.get_by_id(user_id)

    def deactivate_user(self, user_id: UUID) -> User:
        """Deactivate an existing user."""
        user = self._repository.get_by_id(user_id)

        if user is None:
            raise ValueError("User not found.")

        if not user.is_active:
            return user

        deactivated_user = User(
            id=user.id,
            email=user.email,
            name=user.name,
            is_active=False,
            created_at=user.created_at,
            updated_at=self._repository.utcnow(),
        )

        return self._repository.update(deactivated_user)

"""Application services for user-related business operations."""

from __future__ import annotations

from uuid import UUID, uuid4

from src.models.user import User
from src.repositories.user_repository import UserRepository


class UserService:
    """Coordinate user-related business logic and persistence."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def create_user(self, email: str, name: str) -> User:
        """Create and persist a new user after validating business rules."""
        normalized_email = email.strip().lower()
        normalized_name = name.strip()

        if not normalized_email:
            raise ValueError("Email must not be empty.")

        if not normalized_name:
            raise ValueError("Name must not be empty.")

        if self._repository.get_by_email(normalized_email) is not None:
            raise ValueError("A user with this email already exists.")

        user = User(
            id=uuid4(),
            email=normalized_email,
            name=normalized_name,
            is_active=True,
            created_at=self._repository.utcnow(),
            updated_at=self._repository.utcnow(),
        )

        return self._repository.create(user)

    def get_user(self, user_id: UUID) -> User | None:
        """Return a user by identifier, or None when it does not exist."""
        return self._repository.get_by_id(user_id)

    def deactivate_user(self, user_id: UUID) -> User:
        """Deactivate an existing user."""
        user = self._repository.get_by_id(user_id)

        if user is None:
            raise ValueError("User not found.")

        if not user.is_active:
            return user

        deactivated_user = User(
            id=user.id,
            email=user.email,
            name=user.name,
            is_active=False,
            created_at=user.created_at,
            updated_at=self._repository.utcnow(),
        )

        return self._repository.update(deactivated_user)