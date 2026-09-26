"""Service layer for customer business operations."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from repositories.customer_repository import (
    create_customer,
    delete_customer,
    get_customer_by_email,
    get_customer_by_id,
    list_customers,
    update_customer,
)


def create_customer_service(
    *,
    name: str,
    email: str,
    is_active: bool = True,
    phone: str | None = None,
) -> dict[str, Any]:
    """Create a customer after applying service-level business rules."""
    normalized_name = name.strip()
    normalized_email = email.strip().lower()

    if not normalized_name:
        raise ValueError("Customer name cannot be empty.")

    if not normalized_email:
        raise ValueError("Customer email cannot be empty.")

    if "@" not in normalized_email:
        raise ValueError("Customer email must be valid.")

    if phone is not None:
        phone = phone.strip() or None

    if get_customer_by_email(normalized_email) is not None:
        raise ValueError("A customer with this email already exists.")

    try:
        return create_customer(
            name=normalized_name,
            email=normalized_email,
            is_active=is_active,
            phone=phone,
        )
    except DuplicateKeyError as exc:
        # Protect against a race between the existence check and insert.
        raise ValueError(
            "A customer with this email already exists.",
        ) from exc


def get_customer_service(
    customer_id: ObjectId,
) -> dict[str, Any] | None:
    """Return a customer by identifier."""
    return get_customer_by_id(customer_id)


def get_customer_by_email_service(
    email: str,
) -> dict[str, Any] | None:
    """Return a customer by normalized email address."""
    normalized_email = email.strip().lower()

    if not normalized_email:
        raise ValueError("Customer email cannot be empty.")

    return get_customer_by_email(normalized_email)


def list_customers_service(
    *,
    skip: int = 0,
    limit: int = 50,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    """Return customers using bounded pagination."""
    if skip < 0:
        raise ValueError("skip cannot be negative.")

    if limit <= 0 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    return list_customers(
        skip=skip,
        limit=limit,
        is_active=is_active,
    )


def update_customer_service(
    customer_id: ObjectId,
    *,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    is_active: bool | None = None,
) -> dict[str, Any] | None:
    """Update a customer after validating business rules."""
    if name is not None and not name.strip():
        raise ValueError("Customer name cannot be empty.")

    normalized_email: str | None = None

    if email is not None:
        normalized_email = email.strip().lower()

        if not normalized_email:
            raise ValueError("Customer email cannot be empty.")

        if "@" not in normalized_email:
            raise ValueError("Customer email must be valid.")

        existing_customer = get_customer_by_email(normalized_email)

        if (
            existing_customer is not None
            and existing_customer["_id"] != customer_id
        ):
            raise ValueError(
                "A customer with this email already exists.",
            )

    if phone is not None:
        phone = phone.strip() or None

    try:
        return update_customer(
            customer_id,
            name=name,
            email=normalized_email,
            phone=phone,
            is_active=is_active,
        )
    except DuplicateKeyError as exc:
        raise ValueError(
            "A customer with this email already exists.",
        ) from exc


def delete_customer_service(customer_id: ObjectId) -> bool:
    """Delete a customer by identifier."""
    return delete_customer(customer_id)

"""Service layer for customer business operations."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from repositories.customer_repository import (
    create_customer,
    delete_customer,
    get_customer_by_email,
    get_customer_by_id,
    list_customers,
    update_customer,
)


def create_customer_service(
    *,
    name: str,
    email: str,
    is_active: bool = True,
    phone: str | None = None,
) -> dict[str, Any]:
    """Create a customer after applying service-level business rules."""
    normalized_name = name.strip()
    normalized_email = email.strip().lower()

    if not normalized_name:
        raise ValueError("Customer name cannot be empty.")

    if not normalized_email:
        raise ValueError("Customer email cannot be empty.")

    if "@" not in normalized_email:
        raise ValueError("Customer email must be valid.")

    if phone is not None:
        phone = phone.strip() or None

    if get_customer_by_email(normalized_email) is not None:
        raise ValueError("A customer with this email already exists.")

    try:
        return create_customer(
            name=normalized_name,
            email=normalized_email,
            is_active=is_active,
            phone=phone,
        )
    except DuplicateKeyError as exc:
        # Protect against a race between the existence check and insert.
        raise ValueError(
            "A customer with this email already exists.",
        ) from exc


def get_customer_service(
    customer_id: ObjectId,
) -> dict[str, Any] | None:
    """Return a customer by identifier."""
    return get_customer_by_id(customer_id)


def get_customer_by_email_service(
    email: str,
) -> dict[str, Any] | None:
    """Return a customer by normalized email address."""
    normalized_email = email.strip().lower()

    if not normalized_email:
        raise ValueError("Customer email cannot be empty.")

    return get_customer_by_email(normalized_email)


def list_customers_service(
    *,
    skip: int = 0,
    limit: int = 50,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    """Return customers using bounded pagination."""
    if skip < 0:
        raise ValueError("skip cannot be negative.")

    if limit <= 0 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    return list_customers(
        skip=skip,
        limit=limit,
        is_active=is_active,
    )


def update_customer_service(
    customer_id: ObjectId,
    *,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    is_active: bool | None = None,
) -> dict[str, Any] | None:
    """Update a customer after validating business rules."""
    if name is not None and not name.strip():
        raise ValueError("Customer name cannot be empty.")

    normalized_email: str | None = None

    if email is not None:
        normalized_email = email.strip().lower()

        if not normalized_email:
            raise ValueError("Customer email cannot be empty.")

        if "@" not in normalized_email:
            raise ValueError("Customer email must be valid.")

        existing_customer = get_customer_by_email(normalized_email)

        if (
            existing_customer is not None
            and existing_customer["_id"] != customer_id
        ):
            raise ValueError(
                "A customer with this email already exists.",
            )

    if phone is not None:
        phone = phone.strip() or None

    try:
        return update_customer(
            customer_id,
            name=name,
            email=normalized_email,
            phone=phone,
            is_active=is_active,
        )
    except DuplicateKeyError as exc:
        raise ValueError(
            "A customer with this email already exists.",
        ) from exc


def delete_customer_service(customer_id: ObjectId) -> bool:
    """Delete a customer by identifier."""
    return delete_customer(customer_id)