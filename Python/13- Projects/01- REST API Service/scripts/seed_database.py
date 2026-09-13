"""Seed development data for the REST API service."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.repositories.user_repository import UserRepository
from src.services.user_service import UserService


SEED_USERS = (
    ("alice@example.com", "Alice Johnson"),
    ("bob@example.com", "Bob Smith"),
    ("carol@example.com", "Carol Williams"),
)


def seed_database() -> None:
    """Create deterministic development users when they do not exist."""
    repository = UserRepository()
    service = UserService(repository)

    for email, name in SEED_USERS:
        if repository.get_by_email(email) is not None:
            continue

        service.create_user(email=email, name=name)

    print(f"Seeded {len(SEED_USERS)} development users.")


if __name__ == "__main__":
    seed_database()

"""Seed development data for the REST API service."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.repositories.user_repository import UserRepository
from src.services.user_service import UserService


SEED_USERS = (
    ("alice@example.com", "Alice Johnson"),
    ("bob@example.com", "Bob Smith"),
    ("carol@example.com", "Carol Williams"),
)


def seed_database() -> None:
    """Create deterministic development users when they do not exist."""
    repository = UserRepository()
    service = UserService(repository)

    for email, name in SEED_USERS:
        if repository.get_by_email(email) is not None:
            continue

        service.create_user(email=email, name=name)

    print(f"Seeded {len(SEED_USERS)} development users.")


if __name__ == "__main__":
    seed_database()