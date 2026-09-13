"""Persistence repositories for the REST API service."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from src.models.user import User


class UserRepository:
    """Provide persistence operations for User domain models."""

    def __init__(self) -> None:
        self._users: dict[UUID, User] = {}

    @staticmethod
    def utcnow() -> datetime:
        """Return the current timezone-aware UTC timestamp."""
        return datetime.now(timezone.utc)

    def create(self, user: User) -> User:
        """Persist and return a new user."""
        if user.id in self._users:
            raise ValueError("A user with this ID already exists.")

        self._users[user.id] = user
        return user

    def get_by_id(self, user_id: UUID) -> User | None:
        """Return a user by ID, or None when it does not exist."""
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        """Return a user by normalized email, or None when absent."""
        normalized_email = email.strip().lower()

        return next(
            (user for user in self._users.values() if user.email == normalized_email),
            None,
        )

    def update(self, user: User) -> User:
        """Update an existing user and return the persisted value."""
        if user.id not in self._users:
            raise ValueError("User not found.")

        self._users[user.id] = user
        return user

"""Persistence repositories for the REST API service."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from src.models.user import User


class UserRepository:
    """Provide persistence operations for User domain models."""

    def __init__(self) -> None:
        self._users: dict[UUID, User] = {}

    @staticmethod
    def utcnow() -> datetime:
        """Return the current timezone-aware UTC timestamp."""
        return datetime.now(timezone.utc)

    def create(self, user: User) -> User:
        """Persist and return a new user."""
        if user.id in self._users:
            raise ValueError("A user with this ID already exists.")

        self._users[user.id] = user
        return user

    def get_by_id(self, user_id: UUID) -> User | None:
        """Return a user by ID, or None when it does not exist."""
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        """Return a user by normalized email, or None when absent."""
        normalized_email = email.strip().lower()

        return next(
            (user for user in self._users.values() if user.email == normalized_email),
            None,
        )

    def update(self, user: User) -> User:
        """Update an existing user and return the persisted value."""
        if user.id not in self._users:
            raise ValueError("User not found.")

        self._users[user.id] = user
        return user