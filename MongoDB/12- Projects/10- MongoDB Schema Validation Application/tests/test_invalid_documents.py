"""Tests for invalid MongoDB documents rejected by schema validation."""

from __future__ import annotations

from typing import Any

import pytest
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import OperationFailure

from database.validators import create_validated_collection
from schemas.customer import CUSTOMER_SCHEMA
from schemas.product import PRODUCT_SCHEMA


@pytest.fixture
def customer_collection(
    database: Database[dict[str, Any]],
) -> Collection[dict[str, Any]]:
    """Create a customer collection with strict schema validation."""
    return create_validated_collection(
        database,
        "customers",
        CUSTOMER_SCHEMA,
    )


@pytest.fixture
def product_collection(
    database: Database[dict[str, Any]],
) -> Collection[dict[str, Any]]:
    """Create a product collection with strict schema validation."""
    return create_validated_collection(
        database,
        "products",
        PRODUCT_SCHEMA,
    )


def valid_customer() -> dict[str, Any]:
    """Return a valid customer document."""
    return {
        "customer_id": "customer-001",
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@example.com",
        "status": "active",
        "phone": "+919876543210",
        "address": {
            "line1": "10 Park Street",
            "city": "Kolkata",
            "state": "West Bengal",
            "postal_code": "700016",
            "country": "IN",
        },
        "tags": ["premium", "verified"],
    }


def valid_product() -> dict[str, Any]:
    """Return a valid product document."""
    return {
        "product_id": "product-001",
        "name": "Mechanical Keyboard",
        "sku": "KB-001",
        "price": 7499,
        "currency": "INR",
        "category": "electronics",
        "status": "active",
        "description": "Mechanical keyboard",
        "stock_quantity": 50,
        "tags": ["keyboard", "electronics"],
        "dimensions": {
            "length": 35.0,
            "width": 13.0,
            "height": 4.0,
        },
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("customer_id", 123),
        ("first_name", 123),
        ("last_name", 123),
        ("email", 123),
        ("status", 123),
    ],
)
def test_customer_rejects_invalid_field_types(
    customer_collection: Collection[dict[str, Any]],
    field: str,
    value: Any,
) -> None:
    """Customer fields must use the BSON types defined by the schema."""
    document = valid_customer()
    document[field] = value

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


@pytest.mark.parametrize(
    "field",
    [
        "customer_id",
        "first_name",
        "last_name",
    ],
)
def test_customer_rejects_empty_required_strings(
    customer_collection: Collection[dict[str, Any]],
    field: str,
) -> None:
    """Required customer strings must not be empty."""
    document = valid_customer()
    document[field] = ""

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


@pytest.mark.parametrize(
    "email",
    [
        "",
        "alice",
        "alice@",
        "@example.com",
        "alice@example",
    ],
)
def test_customer_rejects_invalid_email_values(
    customer_collection: Collection[dict[str, Any]],
    email: str,
) -> None:
    """Customer email values must satisfy the configured pattern."""
    document = valid_customer()
    document["email"] = email

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


@pytest.mark.parametrize(
    "status",
    [
        "",
        "pending",
        "deleted",
        "unknown",
    ],
)
def test_customer_rejects_invalid_status_values(
    customer_collection: Collection[dict[str, Any]],
    status: str,
) -> None:
    """Customer status must belong to the configured enum."""
    document = valid_customer()
    document["status"] = status

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_invalid_phone_type(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Optional phone values must be strings."""
    document = valid_customer()
    document["phone"] = 9876543210

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_phone_that_is_too_short(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Phone values shorter than the configured minimum are rejected."""
    document = valid_customer()
    document["phone"] = "123456"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_invalid_nested_address_type(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Address must be represented as a BSON object."""
    document = valid_customer()
    document["address"] = "10 Park Street, Kolkata"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_address_without_required_city(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Nested addresses require a city."""
    document = valid_customer()
    document["address"].pop("city")

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_address_without_required_country(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Nested addresses require a country."""
    document = valid_customer()
    document["address"].pop("country")

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_unknown_address_property(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Nested address objects reject undeclared properties."""
    document = valid_customer()
    document["address"]["district"] = "Kolkata"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_non_string_tag(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Customer tags must contain only strings."""
    document = valid_customer()
    document["tags"] = ["premium", 123]

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_non_array_tags(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Customer tags must be represented as an array."""
    document = valid_customer()
    document["tags"] = "premium"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_unknown_top_level_property(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Customer documents reject undeclared top-level properties."""
    document = valid_customer()
    document["unexpected_field"] = "not allowed"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


@pytest.mark.parametrize(
    "field",
    [
        "customer_id",
        "first_name",
        "last_name",
        "email",
        "status",
    ],
)
def test_customer_rejects_missing_required_fields(
    customer_collection: Collection[dict[str, Any]],
    field: str,
) -> None:
    """Every required customer field must be present."""
    document = valid_customer()
    document.pop(field)

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("product_id", 123),
        ("name", 123),
        ("sku", 123),
        ("currency", 123),
        ("category", 123),
        ("status", 123),
    ],
)
def test_product_rejects_invalid_field_types(
    product_collection: Collection[dict[str, Any]],
    field: str,
    value: Any,
) -> None:
    """Product fields must use the BSON types defined by the schema."""
    document = valid_product()
    document[field] = value

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


@pytest.mark.parametrize(
    "field",
    [
        "product_id",
        "name",
        "sku",
        "category",
    ],
)
def test_product_rejects_empty_required_strings(
    product_collection: Collection[dict[str, Any]],
    field: str,
) -> None:
    """Required product strings must not be empty."""
    document = valid_product()
    document[field] = ""

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


@pytest.mark.parametrize(
    "price",
    [
        -1,
        -0.01,
    ],
)
def test_product_rejects_negative_prices(
    product_collection: Collection[dict[str, Any]],
    price: float,
) -> None:
    """Product prices cannot be negative."""
    document = valid_product()
    document["price"] = price

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


@pytest.mark.parametrize(
    "currency",
    [
        "",
        "JPY",
        "AUD",
        "invalid",
    ],
)
def test_product_rejects_invalid_currency_values(
    product_collection: Collection[dict[str, Any]],
    currency: str,
) -> None:
    """Product currency must belong to the configured enum."""
    document = valid_product()
    document["currency"] = currency

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


@pytest.mark.parametrize(
    "status",
    [
        "",
        "pending",
        "deleted",
        "unknown",
    ],
)
def test_product_rejects_invalid_status_values(
    product_collection: Collection[dict[str, Any]],
    status: str,
) -> None:
    """Product status must belong to the configured enum."""
    document = valid_product()
    document["status"] = status

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


@pytest.mark.parametrize(
    "stock_quantity",
    [
        -1,
        -100,
    ],
)
def test_product_rejects_negative_stock_quantity(
    product_collection: Collection[dict[str, Any]],
    stock_quantity: int,
) -> None:
    """Stock quantity cannot be negative."""
    document = valid_product()
    document["stock_quantity"] = stock_quantity

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_non_integer_stock_quantity(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Stock quantity must use the BSON int type."""
    document = valid_product()
    document["stock_quantity"] = 10.5

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_invalid_description_type(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Optional product descriptions must be strings."""
    document = valid_product()
    document["description"] = 123

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_description_longer_than_limit(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product descriptions must respect the configured maximum length."""
    document = valid_product()
    document["description"] = "x" * 5001

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_non_array_tags(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product tags must be represented as an array."""
    document = valid_product()
    document["tags"] = "electronics"

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_non_string_tag(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product tags must contain only strings."""
    document = valid_product()
    document["tags"] = ["electronics", 123]

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_invalid_dimensions_type(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Dimensions must be represented as a BSON object."""
    document = valid_product()
    document["dimensions"] = "35x13x4"

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


@pytest.mark.parametrize(
    "dimension",
    [
        "length",
        "width",
        "height",
    ],
)
def test_product_rejects_negative_dimension(
    product_collection: Collection[dict[str, Any]],
    dimension: str,
) -> None:
    """Product dimensions cannot be negative."""
    document = valid_product()
    document["dimensions"][dimension] = -1

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


@pytest.mark.parametrize(
    "field",
    [
        "product_id",
        "name",
        "sku",
        "price",
        "currency",
        "category",
        "status",
    ],
)
def test_product_rejects_missing_required_fields(
    product_collection: Collection[dict[str, Any]],
    field: str,
) -> None:
    """Every required product field must be present."""
    document = valid_product()
    document.pop(field)

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_rejected_documents_are_not_persisted(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """A document rejected by validation must not be persisted."""
    document = valid_customer()
    document["email"] = "not-an-email"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)

    assert (
        customer_collection.count_documents(
            {"customer_id": document["customer_id"]}
        )
        == 0
    )

"""Tests for invalid MongoDB documents rejected by schema validation."""

from __future__ import annotations

from typing import Any

import pytest
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import OperationFailure

from database.validators import create_validated_collection
from schemas.customer import CUSTOMER_SCHEMA
from schemas.product import PRODUCT_SCHEMA


@pytest.fixture
def customer_collection(
    database: Database[dict[str, Any]],
) -> Collection[dict[str, Any]]:
    """Create a customer collection with strict schema validation."""
    return create_validated_collection(
        database,
        "customers",
        CUSTOMER_SCHEMA,
    )


@pytest.fixture
def product_collection(
    database: Database[dict[str, Any]],
) -> Collection[dict[str, Any]]:
    """Create a product collection with strict schema validation."""
    return create_validated_collection(
        database,
        "products",
        PRODUCT_SCHEMA,
    )


def valid_customer() -> dict[str, Any]:
    """Return a valid customer document."""
    return {
        "customer_id": "customer-001",
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@example.com",
        "status": "active",
        "phone": "+919876543210",
        "address": {
            "line1": "10 Park Street",
            "city": "Kolkata",
            "state": "West Bengal",
            "postal_code": "700016",
            "country": "IN",
        },
        "tags": ["premium", "verified"],
    }


def valid_product() -> dict[str, Any]:
    """Return a valid product document."""
    return {
        "product_id": "product-001",
        "name": "Mechanical Keyboard",
        "sku": "KB-001",
        "price": 7499,
        "currency": "INR",
        "category": "electronics",
        "status": "active",
        "description": "Mechanical keyboard",
        "stock_quantity": 50,
        "tags": ["keyboard", "electronics"],
        "dimensions": {
            "length": 35.0,
            "width": 13.0,
            "height": 4.0,
        },
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("customer_id", 123),
        ("first_name", 123),
        ("last_name", 123),
        ("email", 123),
        ("status", 123),
    ],
)
def test_customer_rejects_invalid_field_types(
    customer_collection: Collection[dict[str, Any]],
    field: str,
    value: Any,
) -> None:
    """Customer fields must use the BSON types defined by the schema."""
    document = valid_customer()
    document[field] = value

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


@pytest.mark.parametrize(
    "field",
    [
        "customer_id",
        "first_name",
        "last_name",
    ],
)
def test_customer_rejects_empty_required_strings(
    customer_collection: Collection[dict[str, Any]],
    field: str,
) -> None:
    """Required customer strings must not be empty."""
    document = valid_customer()
    document[field] = ""

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


@pytest.mark.parametrize(
    "email",
    [
        "",
        "alice",
        "alice@",
        "@example.com",
        "alice@example",
    ],
)
def test_customer_rejects_invalid_email_values(
    customer_collection: Collection[dict[str, Any]],
    email: str,
) -> None:
    """Customer email values must satisfy the configured pattern."""
    document = valid_customer()
    document["email"] = email

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


@pytest.mark.parametrize(
    "status",
    [
        "",
        "pending",
        "deleted",
        "unknown",
    ],
)
def test_customer_rejects_invalid_status_values(
    customer_collection: Collection[dict[str, Any]],
    status: str,
) -> None:
    """Customer status must belong to the configured enum."""
    document = valid_customer()
    document["status"] = status

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_invalid_phone_type(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Optional phone values must be strings."""
    document = valid_customer()
    document["phone"] = 9876543210

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_phone_that_is_too_short(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Phone values shorter than the configured minimum are rejected."""
    document = valid_customer()
    document["phone"] = "123456"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_invalid_nested_address_type(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Address must be represented as a BSON object."""
    document = valid_customer()
    document["address"] = "10 Park Street, Kolkata"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_address_without_required_city(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Nested addresses require a city."""
    document = valid_customer()
    document["address"].pop("city")

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_address_without_required_country(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Nested addresses require a country."""
    document = valid_customer()
    document["address"].pop("country")

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_unknown_address_property(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Nested address objects reject undeclared properties."""
    document = valid_customer()
    document["address"]["district"] = "Kolkata"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_non_string_tag(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Customer tags must contain only strings."""
    document = valid_customer()
    document["tags"] = ["premium", 123]

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_non_array_tags(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Customer tags must be represented as an array."""
    document = valid_customer()
    document["tags"] = "premium"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_unknown_top_level_property(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Customer documents reject undeclared top-level properties."""
    document = valid_customer()
    document["unexpected_field"] = "not allowed"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


@pytest.mark.parametrize(
    "field",
    [
        "customer_id",
        "first_name",
        "last_name",
        "email",
        "status",
    ],
)
def test_customer_rejects_missing_required_fields(
    customer_collection: Collection[dict[str, Any]],
    field: str,
) -> None:
    """Every required customer field must be present."""
    document = valid_customer()
    document.pop(field)

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("product_id", 123),
        ("name", 123),
        ("sku", 123),
        ("currency", 123),
        ("category", 123),
        ("status", 123),
    ],
)
def test_product_rejects_invalid_field_types(
    product_collection: Collection[dict[str, Any]],
    field: str,
    value: Any,
) -> None:
    """Product fields must use the BSON types defined by the schema."""
    document = valid_product()
    document[field] = value

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


@pytest.mark.parametrize(
    "field",
    [
        "product_id",
        "name",
        "sku",
        "category",
    ],
)
def test_product_rejects_empty_required_strings(
    product_collection: Collection[dict[str, Any]],
    field: str,
) -> None:
    """Required product strings must not be empty."""
    document = valid_product()
    document[field] = ""

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


@pytest.mark.parametrize(
    "price",
    [
        -1,
        -0.01,
    ],
)
def test_product_rejects_negative_prices(
    product_collection: Collection[dict[str, Any]],
    price: float,
) -> None:
    """Product prices cannot be negative."""
    document = valid_product()
    document["price"] = price

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


@pytest.mark.parametrize(
    "currency",
    [
        "",
        "JPY",
        "AUD",
        "invalid",
    ],
)
def test_product_rejects_invalid_currency_values(
    product_collection: Collection[dict[str, Any]],
    currency: str,
) -> None:
    """Product currency must belong to the configured enum."""
    document = valid_product()
    document["currency"] = currency

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


@pytest.mark.parametrize(
    "status",
    [
        "",
        "pending",
        "deleted",
        "unknown",
    ],
)
def test_product_rejects_invalid_status_values(
    product_collection: Collection[dict[str, Any]],
    status: str,
) -> None:
    """Product status must belong to the configured enum."""
    document = valid_product()
    document["status"] = status

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


@pytest.mark.parametrize(
    "stock_quantity",
    [
        -1,
        -100,
    ],
)
def test_product_rejects_negative_stock_quantity(
    product_collection: Collection[dict[str, Any]],
    stock_quantity: int,
) -> None:
    """Stock quantity cannot be negative."""
    document = valid_product()
    document["stock_quantity"] = stock_quantity

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_non_integer_stock_quantity(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Stock quantity must use the BSON int type."""
    document = valid_product()
    document["stock_quantity"] = 10.5

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_invalid_description_type(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Optional product descriptions must be strings."""
    document = valid_product()
    document["description"] = 123

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_description_longer_than_limit(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product descriptions must respect the configured maximum length."""
    document = valid_product()
    document["description"] = "x" * 5001

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_non_array_tags(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product tags must be represented as an array."""
    document = valid_product()
    document["tags"] = "electronics"

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_non_string_tag(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product tags must contain only strings."""
    document = valid_product()
    document["tags"] = ["electronics", 123]

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_invalid_dimensions_type(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Dimensions must be represented as a BSON object."""
    document = valid_product()
    document["dimensions"] = "35x13x4"

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


@pytest.mark.parametrize(
    "dimension",
    [
        "length",
        "width",
        "height",
    ],
)
def test_product_rejects_negative_dimension(
    product_collection: Collection[dict[str, Any]],
    dimension: str,
) -> None:
    """Product dimensions cannot be negative."""
    document = valid_product()
    document["dimensions"][dimension] = -1

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


@pytest.mark.parametrize(
    "field",
    [
        "product_id",
        "name",
        "sku",
        "price",
        "currency",
        "category",
        "status",
    ],
)
def test_product_rejects_missing_required_fields(
    product_collection: Collection[dict[str, Any]],
    field: str,
) -> None:
    """Every required product field must be present."""
    document = valid_product()
    document.pop(field)

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_rejected_documents_are_not_persisted(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """A document rejected by validation must not be persisted."""
    document = valid_customer()
    document["email"] = "not-an-email"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)

    assert (
        customer_collection.count_documents(
            {"customer_id": document["customer_id"]}
        )
        == 0
    )