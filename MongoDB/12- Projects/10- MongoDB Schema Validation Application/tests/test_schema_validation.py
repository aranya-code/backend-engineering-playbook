"""Integration and unit tests for MongoDB schema validation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4

import pytest
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DocumentTooLarge, OperationFailure

from database.validators import (
    apply_validator,
    create_validated_collection,
    get_validator_options,
)
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
    """Return an isolated test database."""
    database_name = f"schema_validation_test_{uuid4().hex}"

    database = mongodb_client[database_name]

    yield database

    mongodb_client.drop_database(database_name)


@pytest.fixture
def customer_collection(
    database: Database[dict[str, Any]],
) -> Collection[dict[str, Any]]:
    """Create a collection configured with the customer validator."""
    return create_validated_collection(
        database,
        "customers",
        CUSTOMER_SCHEMA,
    )


@pytest.fixture
def product_collection(
    database: Database[dict[str, Any]],
) -> Collection[dict[str, Any]]:
    """Create a collection configured with the product validator."""
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
        "description": "Mechanical keyboard for backend developers.",
        "stock_quantity": 50,
        "tags": ["keyboard", "electronics"],
        "dimensions": {
            "length": 35.0,
            "width": 13.0,
            "height": 4.0,
        },
    }


def test_customer_collection_has_strict_validation(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Customer collections use strict error-based validation."""
    options = get_validator_options(customer_collection)

    assert options["validator"] == CUSTOMER_SCHEMA
    assert options["validationLevel"] == "strict"
    assert options["validationAction"] == "error"


def test_product_collection_has_strict_validation(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product collections use strict error-based validation."""
    options = get_validator_options(product_collection)

    assert options["validator"] == PRODUCT_SCHEMA
    assert options["validationLevel"] == "strict"
    assert options["validationAction"] == "error"


def test_valid_customer_is_accepted(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """A document satisfying the customer schema is accepted."""
    document = valid_customer()

    result = customer_collection.insert_one(document)

    assert result.inserted_id is not None


def test_customer_requires_customer_id(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Customer documents must contain customer_id."""
    document = valid_customer()
    document.pop("customer_id")

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_invalid_email(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Customer email values must match the configured pattern."""
    document = valid_customer()
    document["email"] = "invalid-email"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_invalid_status(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Customer status must use an allowed enum value."""
    document = valid_customer()
    document["status"] = "deleted"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_invalid_nested_address(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Nested address documents must satisfy their schema."""
    document = valid_customer()
    document["address"] = {
        "line1": "10 Park Street",
        "city": "Kolkata",
    }

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_invalid_array_element_type(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Customer tags must contain only strings."""
    document = valid_customer()
    document["tags"] = ["premium", 123]

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_unknown_top_level_property(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Customer schema rejects undeclared top-level properties."""
    document = valid_customer()
    document["unexpected_field"] = "not allowed"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_valid_product_is_accepted(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """A document satisfying the product schema is accepted."""
    document = valid_product()

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


def test_product_requires_product_id(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product documents must contain product_id."""
    document = valid_product()
    document.pop("product_id")

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_requires_name(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product documents must contain a non-empty name."""
    document = valid_product()
    document["name"] = ""

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_requires_sku(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product documents must contain a non-empty SKU."""
    document = valid_product()
    document["sku"] = ""

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_negative_price(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product prices cannot be negative."""
    document = valid_product()
    document["price"] = -1

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_unsupported_currency(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product currency must use an allowed value."""
    document = valid_product()
    document["currency"] = "JPY"

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_invalid_status(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product status must use an allowed enum value."""
    document = valid_product()
    document["status"] = "pending"

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_negative_stock(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product stock quantity cannot be negative."""
    document = valid_product()
    document["stock_quantity"] = -1

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_invalid_tag_type(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product tags must contain only strings."""
    document = valid_product()
    document["tags"] = ["electronics", 100]

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_allows_additional_top_level_properties(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """The current product schema permits additional properties."""
    document = valid_product()
    document["manufacturer"] = "Example Corp"

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


def test_apply_validator_replaces_existing_validator(
    database: Database[dict[str, Any]],
) -> None:
    """Applying a validator updates an existing collection."""
    collection = database.create_collection("customers")

    apply_validator(
        collection,
        CUSTOMER_SCHEMA,
    )

    options = get_validator_options(collection)

    assert options["validator"] == CUSTOMER_SCHEMA
    assert options["validationLevel"] == "strict"
    assert options["validationAction"] == "error"


def test_create_validated_collection_updates_existing_collection(
    database: Database[dict[str, Any]],
) -> None:
    """Creating an already existing collection applies the validator."""
    collection = database.create_collection("products")

    result = create_validated_collection(
        database,
        "products",
        PRODUCT_SCHEMA,
    )

    assert result.name == collection.name

    options = get_validator_options(result)
    assert options["validator"] == PRODUCT_SCHEMA


def test_create_validated_collection_rejects_empty_name(
    database: Database[dict[str, Any]],
) -> None:
    """Collection creation requires a non-empty collection name."""
    with pytest.raises(
        ValueError,
        match="collection_name must not be empty",
    ):
        create_validated_collection(
            database,
            "",
            CUSTOMER_SCHEMA,
        )


def test_apply_validator_rejects_invalid_validation_level(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Validation level must be a supported MongoDB value."""
    with pytest.raises(
        ValueError,
        match="validation_level must be one of",
    ):
        apply_validator(
            customer_collection,
            CUSTOMER_SCHEMA,
            validation_level="invalid",
        )


def test_apply_validator_rejects_invalid_validation_action(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Validation action must be a supported MongoDB value."""
    with pytest.raises(
        ValueError,
        match="validation_action must be one of",
    ):
        apply_validator(
            customer_collection,
            CUSTOMER_SCHEMA,
            validation_action="invalid",
        )


def test_customer_validation_does_not_mutate_input_schema(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Schema configuration remains unchanged after collection setup."""
    expected_schema = deepcopy(CUSTOMER_SCHEMA)

    options = get_validator_options(customer_collection)

    assert options["validator"] == expected_schema
    assert CUSTOMER_SCHEMA == expected_schema


def test_invalid_customer_document_is_not_persisted(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """A rejected customer document must not appear in the collection."""
    document = valid_customer()
    document["email"] = "invalid-email"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)

    assert (
        customer_collection.count_documents(
            {"customer_id": document["customer_id"]}
        )
        == 0
    )


def test_invalid_product_document_is_not_persisted(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """A rejected product document must not appear in the collection."""
    document = valid_product()
    document["price"] = -100

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)

    assert (
        product_collection.count_documents(
            {"product_id": document["product_id"]}
        )
        == 0
    )

"""Integration and unit tests for MongoDB schema validation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4

import pytest
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DocumentTooLarge, OperationFailure

from database.validators import (
    apply_validator,
    create_validated_collection,
    get_validator_options,
)
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
    """Return an isolated test database."""
    database_name = f"schema_validation_test_{uuid4().hex}"

    database = mongodb_client[database_name]

    yield database

    mongodb_client.drop_database(database_name)


@pytest.fixture
def customer_collection(
    database: Database[dict[str, Any]],
) -> Collection[dict[str, Any]]:
    """Create a collection configured with the customer validator."""
    return create_validated_collection(
        database,
        "customers",
        CUSTOMER_SCHEMA,
    )


@pytest.fixture
def product_collection(
    database: Database[dict[str, Any]],
) -> Collection[dict[str, Any]]:
    """Create a collection configured with the product validator."""
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
        "description": "Mechanical keyboard for backend developers.",
        "stock_quantity": 50,
        "tags": ["keyboard", "electronics"],
        "dimensions": {
            "length": 35.0,
            "width": 13.0,
            "height": 4.0,
        },
    }


def test_customer_collection_has_strict_validation(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Customer collections use strict error-based validation."""
    options = get_validator_options(customer_collection)

    assert options["validator"] == CUSTOMER_SCHEMA
    assert options["validationLevel"] == "strict"
    assert options["validationAction"] == "error"


def test_product_collection_has_strict_validation(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product collections use strict error-based validation."""
    options = get_validator_options(product_collection)

    assert options["validator"] == PRODUCT_SCHEMA
    assert options["validationLevel"] == "strict"
    assert options["validationAction"] == "error"


def test_valid_customer_is_accepted(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """A document satisfying the customer schema is accepted."""
    document = valid_customer()

    result = customer_collection.insert_one(document)

    assert result.inserted_id is not None


def test_customer_requires_customer_id(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Customer documents must contain customer_id."""
    document = valid_customer()
    document.pop("customer_id")

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_invalid_email(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Customer email values must match the configured pattern."""
    document = valid_customer()
    document["email"] = "invalid-email"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_invalid_status(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Customer status must use an allowed enum value."""
    document = valid_customer()
    document["status"] = "deleted"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_invalid_nested_address(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Nested address documents must satisfy their schema."""
    document = valid_customer()
    document["address"] = {
        "line1": "10 Park Street",
        "city": "Kolkata",
    }

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_invalid_array_element_type(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Customer tags must contain only strings."""
    document = valid_customer()
    document["tags"] = ["premium", 123]

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_customer_rejects_unknown_top_level_property(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Customer schema rejects undeclared top-level properties."""
    document = valid_customer()
    document["unexpected_field"] = "not allowed"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)


def test_valid_product_is_accepted(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """A document satisfying the product schema is accepted."""
    document = valid_product()

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


def test_product_requires_product_id(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product documents must contain product_id."""
    document = valid_product()
    document.pop("product_id")

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_requires_name(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product documents must contain a non-empty name."""
    document = valid_product()
    document["name"] = ""

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_requires_sku(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product documents must contain a non-empty SKU."""
    document = valid_product()
    document["sku"] = ""

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_negative_price(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product prices cannot be negative."""
    document = valid_product()
    document["price"] = -1

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_unsupported_currency(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product currency must use an allowed value."""
    document = valid_product()
    document["currency"] = "JPY"

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_invalid_status(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product status must use an allowed enum value."""
    document = valid_product()
    document["status"] = "pending"

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_negative_stock(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product stock quantity cannot be negative."""
    document = valid_product()
    document["stock_quantity"] = -1

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_rejects_invalid_tag_type(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """Product tags must contain only strings."""
    document = valid_product()
    document["tags"] = ["electronics", 100]

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)


def test_product_allows_additional_top_level_properties(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """The current product schema permits additional properties."""
    document = valid_product()
    document["manufacturer"] = "Example Corp"

    result = product_collection.insert_one(document)

    assert result.inserted_id is not None


def test_apply_validator_replaces_existing_validator(
    database: Database[dict[str, Any]],
) -> None:
    """Applying a validator updates an existing collection."""
    collection = database.create_collection("customers")

    apply_validator(
        collection,
        CUSTOMER_SCHEMA,
    )

    options = get_validator_options(collection)

    assert options["validator"] == CUSTOMER_SCHEMA
    assert options["validationLevel"] == "strict"
    assert options["validationAction"] == "error"


def test_create_validated_collection_updates_existing_collection(
    database: Database[dict[str, Any]],
) -> None:
    """Creating an already existing collection applies the validator."""
    collection = database.create_collection("products")

    result = create_validated_collection(
        database,
        "products",
        PRODUCT_SCHEMA,
    )

    assert result.name == collection.name

    options = get_validator_options(result)
    assert options["validator"] == PRODUCT_SCHEMA


def test_create_validated_collection_rejects_empty_name(
    database: Database[dict[str, Any]],
) -> None:
    """Collection creation requires a non-empty collection name."""
    with pytest.raises(
        ValueError,
        match="collection_name must not be empty",
    ):
        create_validated_collection(
            database,
            "",
            CUSTOMER_SCHEMA,
        )


def test_apply_validator_rejects_invalid_validation_level(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Validation level must be a supported MongoDB value."""
    with pytest.raises(
        ValueError,
        match="validation_level must be one of",
    ):
        apply_validator(
            customer_collection,
            CUSTOMER_SCHEMA,
            validation_level="invalid",
        )


def test_apply_validator_rejects_invalid_validation_action(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Validation action must be a supported MongoDB value."""
    with pytest.raises(
        ValueError,
        match="validation_action must be one of",
    ):
        apply_validator(
            customer_collection,
            CUSTOMER_SCHEMA,
            validation_action="invalid",
        )


def test_customer_validation_does_not_mutate_input_schema(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """Schema configuration remains unchanged after collection setup."""
    expected_schema = deepcopy(CUSTOMER_SCHEMA)

    options = get_validator_options(customer_collection)

    assert options["validator"] == expected_schema
    assert CUSTOMER_SCHEMA == expected_schema


def test_invalid_customer_document_is_not_persisted(
    customer_collection: Collection[dict[str, Any]],
) -> None:
    """A rejected customer document must not appear in the collection."""
    document = valid_customer()
    document["email"] = "invalid-email"

    with pytest.raises(OperationFailure):
        customer_collection.insert_one(document)

    assert (
        customer_collection.count_documents(
            {"customer_id": document["customer_id"]}
        )
        == 0
    )


def test_invalid_product_document_is_not_persisted(
    product_collection: Collection[dict[str, Any]],
) -> None:
    """A rejected product document must not appear in the collection."""
    document = valid_product()
    document["price"] = -100

    with pytest.raises(OperationFailure):
        product_collection.insert_one(document)

    assert (
        product_collection.count_documents(
            {"product_id": document["product_id"]}
        )
        == 0
    )