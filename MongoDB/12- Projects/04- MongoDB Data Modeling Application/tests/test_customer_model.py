"""Tests for MongoDB customer data models."""

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId

from models.customer import build_customer, update_customer_fields


def test_build_customer_creates_valid_document() -> None:
    """Build a customer document with normalized and required fields."""
    document = build_customer(
        name=" Alice Johnson ",
        email=" ALICE.JOHNSON@EXAMPLE.COM ",
        phone=" +1-555-0101 ",
    )

    assert isinstance(document["_id"], ObjectId)
    assert document["name"] == "Alice Johnson"
    assert document["email"] == "alice.johnson@example.com"
    assert document["phone"] == "+1-555-0101"
    assert document["is_active"] is True
    assert isinstance(document["created_at"], datetime)
    assert isinstance(document["updated_at"], datetime)
    assert document["created_at"].tzinfo == timezone.utc
    assert document["updated_at"].tzinfo == timezone.utc


def test_build_customer_uses_default_values() -> None:
    """Apply the model defaults when optional values are omitted."""
    document = build_customer(
        name="Alice Johnson",
        email="alice@example.com",
    )

    assert document["phone"] is None
    assert document["is_active"] is True


def test_build_customer_preserves_inactive_status() -> None:
    """Allow callers to explicitly create an inactive customer."""
    document = build_customer(
        name="Alice Johnson",
        email="alice@example.com",
        is_active=False,
    )

    assert document["is_active"] is False


def test_build_customer_normalizes_email_case_and_whitespace() -> None:
    """Normalize email addresses before persistence."""
    document = build_customer(
        name="Alice Johnson",
        email="  Alice.Johnson@Example.COM  ",
    )

    assert document["email"] == "alice.johnson@example.com"


def test_build_customer_strips_optional_phone() -> None:
    """Normalize a provided phone number by removing surrounding whitespace."""
    document = build_customer(
        name="Alice Johnson",
        email="alice@example.com",
        phone="  +1-555-0101  ",
    )

    assert document["phone"] == "+1-555-0101"


def test_build_customer_keeps_missing_phone_as_none() -> None:
    """Represent an omitted phone number as null in the document."""
    document = build_customer(
        name="Alice Johnson",
        email="alice@example.com",
    )

    assert document["phone"] is None


def test_build_customer_generates_unique_object_ids() -> None:
    """Generate a distinct ObjectId for each newly built customer."""
    first = build_customer(
        name="Alice Johnson",
        email="alice@example.com",
    )
    second = build_customer(
        name="Bob Smith",
        email="bob@example.com",
    )

    assert first["_id"] != second["_id"]


def test_build_customer_sets_creation_and_update_timestamps() -> None:
    """Initialize both lifecycle timestamps for a new customer."""
    before = datetime.now(timezone.utc)

    document = build_customer(
        name="Alice Johnson",
        email="alice@example.com",
    )

    after = datetime.now(timezone.utc)

    assert before <= document["created_at"] <= after
    assert before <= document["updated_at"] <= after


def test_update_customer_fields_updates_only_provided_fields() -> None:
    """Build a partial update containing only requested mutable fields."""
    updates = update_customer_fields(
        name=" Alice Smith ",
        email=" ALICE.SMITH@EXAMPLE.COM ",
    )

    assert updates["name"] == "Alice Smith"
    assert updates["email"] == "alice.smith@example.com"
    assert "phone" not in updates
    assert "is_active" not in updates
    assert isinstance(updates["updated_at"], datetime)
    assert updates["updated_at"].tzinfo == timezone.utc


def test_update_customer_fields_normalizes_phone() -> None:
    """Normalize whitespace in an updated phone number."""
    updates = update_customer_fields(
        phone="  +1-555-0101  ",
    )

    assert updates["phone"] == "+1-555-0101"


def test_update_customer_fields_allows_inactive_status() -> None:
    """Include an explicit false value for is_active."""
    updates = update_customer_fields(
        is_active=False,
    )

    assert updates["is_active"] is False


def test_update_customer_fields_always_updates_timestamp() -> None:
    """Set updated_at even when no mutable field is supplied."""
    before = datetime.now(timezone.utc)

    updates = update_customer_fields()

    after = datetime.now(timezone.utc)

    assert before <= updates["updated_at"] <= after

"""Tests for MongoDB customer data models."""

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId

from models.customer import build_customer, update_customer_fields


def test_build_customer_creates_valid_document() -> None:
    """Build a customer document with normalized and required fields."""
    document = build_customer(
        name=" Alice Johnson ",
        email=" ALICE.JOHNSON@EXAMPLE.COM ",
        phone=" +1-555-0101 ",
    )

    assert isinstance(document["_id"], ObjectId)
    assert document["name"] == "Alice Johnson"
    assert document["email"] == "alice.johnson@example.com"
    assert document["phone"] == "+1-555-0101"
    assert document["is_active"] is True
    assert isinstance(document["created_at"], datetime)
    assert isinstance(document["updated_at"], datetime)
    assert document["created_at"].tzinfo == timezone.utc
    assert document["updated_at"].tzinfo == timezone.utc


def test_build_customer_uses_default_values() -> None:
    """Apply the model defaults when optional values are omitted."""
    document = build_customer(
        name="Alice Johnson",
        email="alice@example.com",
    )

    assert document["phone"] is None
    assert document["is_active"] is True


def test_build_customer_preserves_inactive_status() -> None:
    """Allow callers to explicitly create an inactive customer."""
    document = build_customer(
        name="Alice Johnson",
        email="alice@example.com",
        is_active=False,
    )

    assert document["is_active"] is False


def test_build_customer_normalizes_email_case_and_whitespace() -> None:
    """Normalize email addresses before persistence."""
    document = build_customer(
        name="Alice Johnson",
        email="  Alice.Johnson@Example.COM  ",
    )

    assert document["email"] == "alice.johnson@example.com"


def test_build_customer_strips_optional_phone() -> None:
    """Normalize a provided phone number by removing surrounding whitespace."""
    document = build_customer(
        name="Alice Johnson",
        email="alice@example.com",
        phone="  +1-555-0101  ",
    )

    assert document["phone"] == "+1-555-0101"


def test_build_customer_keeps_missing_phone_as_none() -> None:
    """Represent an omitted phone number as null in the document."""
    document = build_customer(
        name="Alice Johnson",
        email="alice@example.com",
    )

    assert document["phone"] is None


def test_build_customer_generates_unique_object_ids() -> None:
    """Generate a distinct ObjectId for each newly built customer."""
    first = build_customer(
        name="Alice Johnson",
        email="alice@example.com",
    )
    second = build_customer(
        name="Bob Smith",
        email="bob@example.com",
    )

    assert first["_id"] != second["_id"]


def test_build_customer_sets_creation_and_update_timestamps() -> None:
    """Initialize both lifecycle timestamps for a new customer."""
    before = datetime.now(timezone.utc)

    document = build_customer(
        name="Alice Johnson",
        email="alice@example.com",
    )

    after = datetime.now(timezone.utc)

    assert before <= document["created_at"] <= after
    assert before <= document["updated_at"] <= after


def test_update_customer_fields_updates_only_provided_fields() -> None:
    """Build a partial update containing only requested mutable fields."""
    updates = update_customer_fields(
        name=" Alice Smith ",
        email=" ALICE.SMITH@EXAMPLE.COM ",
    )

    assert updates["name"] == "Alice Smith"
    assert updates["email"] == "alice.smith@example.com"
    assert "phone" not in updates
    assert "is_active" not in updates
    assert isinstance(updates["updated_at"], datetime)
    assert updates["updated_at"].tzinfo == timezone.utc


def test_update_customer_fields_normalizes_phone() -> None:
    """Normalize whitespace in an updated phone number."""
    updates = update_customer_fields(
        phone="  +1-555-0101  ",
    )

    assert updates["phone"] == "+1-555-0101"


def test_update_customer_fields_allows_inactive_status() -> None:
    """Include an explicit false value for is_active."""
    updates = update_customer_fields(
        is_active=False,
    )

    assert updates["is_active"] is False


def test_update_customer_fields_always_updates_timestamp() -> None:
    """Set updated_at even when no mutable field is supplied."""
    before = datetime.now(timezone.utc)

    updates = update_customer_fields()

    after = datetime.now(timezone.utc)

    assert before <= updates["updated_at"] <= after