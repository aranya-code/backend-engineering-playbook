"""Customer data model definitions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


def build_customer(
    *,
    name: str,
    email: str,
    is_active: bool = True,
    phone: str | None = None,
) -> dict[str, Any]:
    """Build a MongoDB customer document.

    The model keeps application-level document construction separate from
    persistence. MongoDB-specific persistence operations belong in the
    repository layer.
    """
    now = datetime.now(timezone.utc)

    return {
        "_id": ObjectId(),
        "name": name.strip(),
        "email": email.strip().lower(),
        "phone": phone.strip() if phone else None,
        "is_active": is_active,
        "created_at": now,
        "updated_at": now,
    }


def update_customer_fields(
    *,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    is_active: bool | None = None,
) -> dict[str, Any]:
    """Build the mutable fields for a customer update."""
    updates: dict[str, Any] = {}

    if name is not None:
        updates["name"] = name.strip()

    if email is not None:
        updates["email"] = email.strip().lower()

    if phone is not None:
        updates["phone"] = phone.strip()

    if is_active is not None:
        updates["is_active"] = is_active

    updates["updated_at"] = datetime.now(timezone.utc)

    return updates

"""Customer data model definitions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


def build_customer(
    *,
    name: str,
    email: str,
    is_active: bool = True,
    phone: str | None = None,
) -> dict[str, Any]:
    """Build a MongoDB customer document.

    The model keeps application-level document construction separate from
    persistence. MongoDB-specific persistence operations belong in the
    repository layer.
    """
    now = datetime.now(timezone.utc)

    return {
        "_id": ObjectId(),
        "name": name.strip(),
        "email": email.strip().lower(),
        "phone": phone.strip() if phone else None,
        "is_active": is_active,
        "created_at": now,
        "updated_at": now,
    }


def update_customer_fields(
    *,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    is_active: bool | None = None,
) -> dict[str, Any]:
    """Build the mutable fields for a customer update."""
    updates: dict[str, Any] = {}

    if name is not None:
        updates["name"] = name.strip()

    if email is not None:
        updates["email"] = email.strip().lower()

    if phone is not None:
        updates["phone"] = phone.strip()

    if is_active is not None:
        updates["is_active"] = is_active

    updates["updated_at"] = datetime.now(timezone.utc)

    return updates