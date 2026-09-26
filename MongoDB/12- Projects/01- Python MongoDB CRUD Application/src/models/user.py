"""MongoDB user model definitions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


def build_user_document(
    *,
    name: str,
    email: str,
    active: bool = True,
) -> dict[str, Any]:
    """Build a MongoDB-compatible user document.

    Application validation should be performed before persisting the document.
    The email field is normalized because the database index treats values as
    distinct unless collation or application-level normalization is applied.
    """
    normalized_name = name.strip()
    normalized_email = email.strip().lower()

    if not normalized_name:
        raise ValueError("name must not be empty")

    if not normalized_email:
        raise ValueError("email must not be empty")

    now = datetime.now(timezone.utc)

    return {
        "_id": ObjectId(),
        "name": normalized_name,
        "email": normalized_email,
        "active": active,
        "created_at": now,
        "updated_at": now,
    }


def update_user_document(
    *,
    name: str | None = None,
    active: bool | None = None,
) -> dict[str, Any]:
    """Build an update document for mutable user fields."""
    updates: dict[str, Any] = {}

    if name is not None:
        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError("name must not be empty")

        updates["name"] = normalized_name

    if active is not None:
        updates["active"] = active

    updates["updated_at"] = datetime.now(timezone.utc)

    return {"$set": updates}

"""MongoDB user model definitions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


def build_user_document(
    *,
    name: str,
    email: str,
    active: bool = True,
) -> dict[str, Any]:
    """Build a MongoDB-compatible user document.

    Application validation should be performed before persisting the document.
    The email field is normalized because the database index treats values as
    distinct unless collation or application-level normalization is applied.
    """
    normalized_name = name.strip()
    normalized_email = email.strip().lower()

    if not normalized_name:
        raise ValueError("name must not be empty")

    if not normalized_email:
        raise ValueError("email must not be empty")

    now = datetime.now(timezone.utc)

    return {
        "_id": ObjectId(),
        "name": normalized_name,
        "email": normalized_email,
        "active": active,
        "created_at": now,
        "updated_at": now,
    }


def update_user_document(
    *,
    name: str | None = None,
    active: bool | None = None,
) -> dict[str, Any]:
    """Build an update document for mutable user fields."""
    updates: dict[str, Any] = {}

    if name is not None:
        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError("name must not be empty")

        updates["name"] = normalized_name

    if active is not None:
        updates["active"] = active

    updates["updated_at"] = datetime.now(timezone.utc)

    return {"$set": updates}