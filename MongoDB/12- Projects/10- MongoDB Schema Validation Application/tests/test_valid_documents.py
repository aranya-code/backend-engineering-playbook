"""Tests for valid MongoDB documents accepted by schema validation."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from database.validators import create_validated_collection
from schemas.customer import CUSTOMER_SCHEMA
from schemas.product import PRODUCT_SCHEMA


@pytest.fixture(scope="session")
def mongodb_client() -> MongoClient[dict[str, Any]]:
    """Create a MongoDB client for integration tests."""
    client = MongoClient(
        "mongodb://localhost:27017",
        serverSelectionTimeoutMS=1000,
    )

    try:
        client.admin.command("ping")
    except Exception as exc:
        client.close()
        pytest.skip(f"MongoDB is unavailable: {exc}")

    yield client
    client.close()


@pytest.fixture
def database(
    mongodb_client: MongoClient[dict[str, Any]],
) -> Database[dict[str, Any]]:
    """Create an isolated database for each test."""
    database_name = f"valid_documents_test_{uuid4().hex}"
    database = mongodb_client[database_name]

    yield database

    mongodb_client.drop_database(database_name)


@pytest.fixture
def customer_collection(
    database: Database[dict[str, Any]],
) -> Collection[dict[str, Any]]:
    """Create a customer collection with schema validation."""
    return create_validated_collection(
        database,
        "customers",
        CUSTOMER_SCHEMA,
    )


@pytest.fixture
def product_collection(
    database: Database[dict[str, Any]],
) -> Collection[dict[str, Any]]:
    """Create a product collection with schema validation."""
    return create_validated_collection(
        database,
        "products",
        PRODUCT_SCHEMA,
    )


def valid_customer() -> dict[str, Any]:
    """Return a complete valid customer document."""
    return {
        "customer_id": "customer-001",
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@example.com",
        "status": "active",
        "phone": "+919876543210",
        "address": {
            "line1": "10 Park Street",
            "line2": "Floor 2",
            "city": "Kolkata",
            "state": "West Bengal",
            "postal_code": "700016",
            "country": "IN",
        },
        "tags": ["premium", "verified"],
    }


def valid_product() -> dict[str, Any]:
    """Return a complete valid product document."""
    return {
        "product_id": "product-001",
        "name": "Mechanical Keyboard",
        "sku": "KB-001",
        "price": 7499,
        "currency": "INR",
        "category": "electronics",
        "status": "active",
        "description": "Mechanical keyboard for backend developers.",
        "stock_quantity": 50,
        "tags": ["keyboard", "electronics"],
        "dimensions": {
            "length": 35.0,
            "width": 13.0,
            "height": 4.0,
        },
    }


def test_valid_customer_is_accepted(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """A complete valid customer can be inserted."""
    document = valid_customer()

    result = customer_collection.insert_one(document)

    assert result.inserted_id is not None

    stored = customer_collection.find_one(
        {"customer_id": document["customer_id"]}
    )

    assert stored is not None
    assert stored["email"] == document["email"]
    assert stored["status"] == "active"


def test_valid_minimal_customer_is_accepted(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """A customer containing only required fields is accepted."""
    document = {
        "customer_id": "customer-minimal",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "status": "inactive",
    }

    result = customer_collection.insert_one(document)

    assert result.inserted_id is not None


@pytest.mark.parametrize(
    "status",
    [
        "active",
        "inactive",
        "suspended",
    ],
)
def test_all_supported_customer_statuses_are_accepted(
    customer_collection: Collection[dict[str, Any]],
    status: str,
) -> None:
    """Every customer status defined by the schema is accepted."""
    document = valid_customer()
    document["customer_id"] = f"customer-{status}"
    document["status"] = status

    result = customer_collection.insert_one(document)

    assert result.inserted_id is not None


@pytest.mark.parametrize(
    "phone",
    [
        "1234567",
        "+919876543210",
        "+1-212-555-0199",
    ],
)
def test_valid_phone_values_are_accepted(
    customer_collection: Collection[dict[str, Any]],
    phone: str,
) -> None:
    """Phone strings within the configured length range are accepted."""
    document = valid_customer()
    document["customer_id"] = f"customer-{uuid4().hex}"
    document["phone"] = phone

    result = customer_collection.insert_one(document)

    assert result.inserted_id is not None


def test_customer_with_nested_address_is_accepted(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """A customer with a fully populated nested address is accepted."""
    document = valid_customer()

    result = customer_collection.insert_one(document)

    assert result.inserted_id is not None

    stored = customer_collection.find_one(
        {"customer_id": document["customer_id"]}
    )

    assert stored is not None
    assert stored["address"]["city"] == "Kolkata"
    assert stored["address"]["country"] == "IN"


def test_customer_with_multiple_tags_is_accepted(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """An array containing only string tags is accepted."""
    document = valid_customer()
    document["tags"] = [
        "premium",
        "verified",
        "newsletter",
        "priority-support",
    ]

    result = customer_collection.insert_one(document)

    assert result.inserted_id is not None


def test_customer_with_empty_tags_is_accepted(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """The schema permits an empty tags array."""
    document = valid_customer()
    document["tags"] = []

    result = customer_collection.insert_one(document)

    assert result.inserted_id is not None


def test_valid_product_is_accepted(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """A complete valid product can be inserted."""
    document = valid_product()

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None

    stored = product_collection.find_one(
        {"product_id": document["product_id"]}
    )

    assert stored is not None
    assert stored["sku"] == document["sku"]
    assert stored["price"] == document["price"]


def test_valid_minimal_product_is_accepted(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """A product containing only required fields is accepted."""
    document = {
        "product_id": "product-minimal",
        "name": "USB Cable",
        "sku": "USB-001",
        "price": 499,
        "currency": "INR",
        "category": "electronics",
        "status": "active",
    }

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


@pytest.mark.parametrize(
    "currency",
    [
        "INR",
        "USD",
        "EUR",
        "GBP",
    ],
)
def test_all_supported_product_currencies_are_accepted(
    product_collection: Collection[dict[str, Any]],
    currency: str,
) -> None:
    """Every currency defined by the product schema is accepted."""
    document = valid_product()
    document["product_id"] = f"product-{currency.lower()}"
    document["currency"] = currency

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


@pytest.mark.parametrize(
    "status",
    [
        "active",
        "inactive",
        "discontinued",
    ],
)
def test_all_supported_product_statuses_are_accepted(
    product_collection: Collection[dict[str, Any]],
    status: str,
) -> None:
    """Every product status defined by the schema is accepted."""
    document = valid_product()
    document["product_id"] = f"product-{status}"
    document["status"] = status

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


@pytest.mark.parametrize(
    "price",
    [
        0,
        1,
        99.99,
        7499,
        Decimal("14999.95"),
    ],
)
def test_valid_product_prices_are_accepted(
    product_collection: Collection[dict[str, Any]],
    price: int | float | Decimal,
) -> None:
    """Supported non-negative numeric price values are accepted."""
    document = valid_product()
    document["product_id"] = f"product-{uuid4().hex}"
    document["price"] = price

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


@pytest.mark.parametrize(
    "stock_quantity",
    [
        0,
        1,
        50,
        100000,
    ],
)
def test_valid_stock_quantities_are_accepted(
    product_collection: Collection[dict[str, Any]],
    stock_quantity: int,
) -> None:
    """Non-negative BSON integer stock quantities are accepted."""
    document = valid_product()
    document["product_id"] = f"product-{uuid4().hex}"
    document["stock_quantity"] = stock_quantity

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


def test_product_with_description_is_accepted(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """A product with a description within the length limit is accepted."""
    document = valid_product()
    document["description"] = "A" * 5000

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


def test_product_with_empty_tags_is_accepted(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """The schema permits an empty tags array."""
    document = valid_product()
    document["tags"] = []

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


def test_product_with_dimensions_is_accepted(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """A product with valid non-negative dimensions is accepted."""
    document = valid_product()
    document["dimensions"] = {
        "length": 100,
        "width": 50.5,
        "height": Decimal("25.25"),
    }

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


def test_product_allows_partial_dimensions(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Dimensions may contain only the measurements supplied by the caller."""
    document = valid_product()
    document["dimensions"] = {
        "length": 100,
    }

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


def test_product_allows_additional_top_level_properties(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Additional product properties are allowed by the current schema."""
    document = valid_product()
    document["manufacturer"] = "Example Corp"
    document["warranty_months"] = 24

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


def test_customer_and_product_can_coexist(
    customer_collection: Collection[dict[str, Any]],
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Independent collections can validate their documents concurrently."""
    customer = valid_customer()
    product = valid_product()

    customer_result = customer_collection.insert_one(customer)
    product_result = product_collection.insert_one(product)

    assert customer_result.inserted_id is not None
    assert product_result.inserted_id is not None


def test_valid_documents_receive_mongodb_ids(
    customer_collection: Collection[dict[str, Any]],
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Valid documents are persisted with MongoDB-generated _id values."""
    customer_result = customer_collection.insert_one(valid_customer())
    product_result = product_collection.insert_one(valid_product())

    assert customer_result.inserted_id is not None
    assert product_result.inserted_id is not None


def test_customer_timestamp_values_can_be_stored_as_extra_fields(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Schema flexibility permits operational timestamp fields when declared."""
    document = valid_customer()
    timestamp = datetime.now(timezone.utc)
    document["created_at"] = timestamp
    document["updated_at"] = timestamp

    result = customer_collection.insert_one(document)

    assert result.inserted_id is not None


def test_valid_documents_are_retrievable_after_insert(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Successfully validated documents can be retrieved normally."""
    document = valid_customer()

    customer_collection.insert_one(document)

    stored = customer_collection.find_one(
        {"customer_id": document["customer_id"]}
    )

    assert stored is not None
    assert stored["customer_id"] == "customer-001"
    assert stored["first_name"] == "Alice"
    assert stored["last_name"] == "Smith"
    assert stored["email"] == "alice@example.com"
    assert stored["status"] == "active"

"""Tests for valid MongoDB documents accepted by schema validation."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from database.validators import create_validated_collection
from schemas.customer import CUSTOMER_SCHEMA
from schemas.product import PRODUCT_SCHEMA


@pytest.fixture(scope="session")
def mongodb_client() -> MongoClient[dict[str, Any]]:
    """Create a MongoDB client for integration tests."""
    client = MongoClient(
        "mongodb://localhost:27017",
        serverSelectionTimeoutMS=1000,
    )

    try:
        client.admin.command("ping")
    except Exception as exc:
        client.close()
        pytest.skip(f"MongoDB is unavailable: {exc}")

    yield client
    client.close()


@pytest.fixture
def database(
    mongodb_client: MongoClient[dict[str, Any]],
) -> Database[dict[str, Any]]:
    """Create an isolated database for each test."""
    database_name = f"valid_documents_test_{uuid4().hex}"
    database = mongodb_client[database_name]

    yield database

    mongodb_client.drop_database(database_name)


@pytest.fixture
def customer_collection(
    database: Database[dict[str, Any]],
) -> Collection[dict[str, Any]]:
    """Create a customer collection with schema validation."""
    return create_validated_collection(
        database,
        "customers",
        CUSTOMER_SCHEMA,
    )


@pytest.fixture
def product_collection(
    database: Database[dict[str, Any]],
) -> Collection[dict[str, Any]]:
    """Create a product collection with schema validation."""
    return create_validated_collection(
        database,
        "products",
        PRODUCT_SCHEMA,
    )


def valid_customer() -> dict[str, Any]:
    """Return a complete valid customer document."""
    return {
        "customer_id": "customer-001",
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@example.com",
        "status": "active",
        "phone": "+919876543210",
        "address": {
            "line1": "10 Park Street",
            "line2": "Floor 2",
            "city": "Kolkata",
            "state": "West Bengal",
            "postal_code": "700016",
            "country": "IN",
        },
        "tags": ["premium", "verified"],
    }


def valid_product() -> dict[str, Any]:
    """Return a complete valid product document."""
    return {
        "product_id": "product-001",
        "name": "Mechanical Keyboard",
        "sku": "KB-001",
        "price": 7499,
        "currency": "INR",
        "category": "electronics",
        "status": "active",
        "description": "Mechanical keyboard for backend developers.",
        "stock_quantity": 50,
        "tags": ["keyboard", "electronics"],
        "dimensions": {
            "length": 35.0,
            "width": 13.0,
            "height": 4.0,
        },
    }


def test_valid_customer_is_accepted(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """A complete valid customer can be inserted."""
    document = valid_customer()

    result = customer_collection.insert_one(document)

    assert result.inserted_id is not None

    stored = customer_collection.find_one(
        {"customer_id": document["customer_id"]}
    )

    assert stored is not None
    assert stored["email"] == document["email"]
    assert stored["status"] == "active"


def test_valid_minimal_customer_is_accepted(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """A customer containing only required fields is accepted."""
    document = {
        "customer_id": "customer-minimal",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "status": "inactive",
    }

    result = customer_collection.insert_one(document)

    assert result.inserted_id is not None


@pytest.mark.parametrize(
    "status",
    [
        "active",
        "inactive",
        "suspended",
    ],
)
def test_all_supported_customer_statuses_are_accepted(
    customer_collection: Collection[dict[str, Any]],
    status: str,
) -> None:
    """Every customer status defined by the schema is accepted."""
    document = valid_customer()
    document["customer_id"] = f"customer-{status}"
    document["status"] = status

    result = customer_collection.insert_one(document)

    assert result.inserted_id is not None


@pytest.mark.parametrize(
    "phone",
    [
        "1234567",
        "+919876543210",
        "+1-212-555-0199",
    ],
)
def test_valid_phone_values_are_accepted(
    customer_collection: Collection[dict[str, Any]],
    phone: str,
) -> None:
    """Phone strings within the configured length range are accepted."""
    document = valid_customer()
    document["customer_id"] = f"customer-{uuid4().hex}"
    document["phone"] = phone

    result = customer_collection.insert_one(document)

    assert result.inserted_id is not None


def test_customer_with_nested_address_is_accepted(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """A customer with a fully populated nested address is accepted."""
    document = valid_customer()

    result = customer_collection.insert_one(document)

    assert result.inserted_id is not None

    stored = customer_collection.find_one(
        {"customer_id": document["customer_id"]}
    )

    assert stored is not None
    assert stored["address"]["city"] == "Kolkata"
    assert stored["address"]["country"] == "IN"


def test_customer_with_multiple_tags_is_accepted(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """An array containing only string tags is accepted."""
    document = valid_customer()
    document["tags"] = [
        "premium",
        "verified",
        "newsletter",
        "priority-support",
    ]

    result = customer_collection.insert_one(document)

    assert result.inserted_id is not None


def test_customer_with_empty_tags_is_accepted(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """The schema permits an empty tags array."""
    document = valid_customer()
    document["tags"] = []

    result = customer_collection.insert_one(document)

    assert result.inserted_id is not None


def test_valid_product_is_accepted(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """A complete valid product can be inserted."""
    document = valid_product()

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None

    stored = product_collection.find_one(
        {"product_id": document["product_id"]}
    )

    assert stored is not None
    assert stored["sku"] == document["sku"]
    assert stored["price"] == document["price"]


def test_valid_minimal_product_is_accepted(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """A product containing only required fields is accepted."""
    document = {
        "product_id": "product-minimal",
        "name": "USB Cable",
        "sku": "USB-001",
        "price": 499,
        "currency": "INR",
        "category": "electronics",
        "status": "active",
    }

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


@pytest.mark.parametrize(
    "currency",
    [
        "INR",
        "USD",
        "EUR",
        "GBP",
    ],
)
def test_all_supported_product_currencies_are_accepted(
    product_collection: Collection[dict[str, Any]],
    currency: str,
) -> None:
    """Every currency defined by the product schema is accepted."""
    document = valid_product()
    document["product_id"] = f"product-{currency.lower()}"
    document["currency"] = currency

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


@pytest.mark.parametrize(
    "status",
    [
        "active",
        "inactive",
        "discontinued",
    ],
)
def test_all_supported_product_statuses_are_accepted(
    product_collection: Collection[dict[str, Any]],
    status: str,
) -> None:
    """Every product status defined by the schema is accepted."""
    document = valid_product()
    document["product_id"] = f"product-{status}"
    document["status"] = status

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


@pytest.mark.parametrize(
    "price",
    [
        0,
        1,
        99.99,
        7499,
        Decimal("14999.95"),
    ],
)
def test_valid_product_prices_are_accepted(
    product_collection: Collection[dict[str, Any]],
    price: int | float | Decimal,
) -> None:
    """Supported non-negative numeric price values are accepted."""
    document = valid_product()
    document["product_id"] = f"product-{uuid4().hex}"
    document["price"] = price

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


@pytest.mark.parametrize(
    "stock_quantity",
    [
        0,
        1,
        50,
        100000,
    ],
)
def test_valid_stock_quantities_are_accepted(
    product_collection: Collection[dict[str, Any]],
    stock_quantity: int,
) -> None:
    """Non-negative BSON integer stock quantities are accepted."""
    document = valid_product()
    document["product_id"] = f"product-{uuid4().hex}"
    document["stock_quantity"] = stock_quantity

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


def test_product_with_description_is_accepted(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """A product with a description within the length limit is accepted."""
    document = valid_product()
    document["description"] = "A" * 5000

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


def test_product_with_empty_tags_is_accepted(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """The schema permits an empty tags array."""
    document = valid_product()
    document["tags"] = []

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


def test_product_with_dimensions_is_accepted(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """A product with valid non-negative dimensions is accepted."""
    document = valid_product()
    document["dimensions"] = {
        "length": 100,
        "width": 50.5,
        "height": Decimal("25.25"),
    }

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


def test_product_allows_partial_dimensions(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Dimensions may contain only the measurements supplied by the caller."""
    document = valid_product()
    document["dimensions"] = {
        "length": 100,
    }

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


def test_product_allows_additional_top_level_properties(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Additional product properties are allowed by the current schema."""
    document = valid_product()
    document["manufacturer"] = "Example Corp"
    document["warranty_months"] = 24

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


def test_customer_and_product_can_coexist(
    customer_collection: Collection[dict[str, Any]],
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Independent collections can validate their documents concurrently."""
    customer = valid_customer()
    product = valid_product()

    customer_result = customer_collection.insert_one(customer)
    product_result = product_collection.insert_one(product)

    assert customer_result.inserted_id is not None
    assert product_result.inserted_id is not None


def test_valid_documents_receive_mongodb_ids(
    customer_collection: Collection[dict[str, Any]],
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Valid documents are persisted with MongoDB-generated _id values."""
    customer_result = customer_collection.insert_one(valid_customer())
    product_result = product_collection.insert_one(valid_product())

    assert customer_result.inserted_id is not None
    assert product_result.inserted_id is not None


def test_customer_timestamp_values_can_be_stored_as_extra_fields(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Schema flexibility permits operational timestamp fields when declared."""
    document = valid_customer()
    timestamp = datetime.now(timezone.utc)
    document["created_at"] = timestamp
    document["updated_at"] = timestamp

    result = customer_collection.insert_one(document)

    assert result.inserted_id is not None


def test_valid_documents_are_retrievable_after_insert(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Successfully validated documents can be retrieved normally."""
    document = valid_customer()

    customer_collection.insert_one(document)

    stored = customer_collection.find_one(
        {"customer_id": document["customer_id"]}
    )

    assert stored is not None
    assert stored["customer_id"] == "customer-001"
    assert stored["first_name"] == "Alice"
    assert stored["last_name"] == "Smith"
    assert stored["email"] == "alice@example.com"
    assert stored["status"] == "active"