"""Tests for the extraction, transformation, validation, and loading stages."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from pipeline.extract import (
    extract_documents,
    extract_documents_in_batches,
)
from pipeline.load import (
    load_documents,
    load_documents_in_batches,
)
from pipeline.transform import (
    transform_batch,
    transform_document,
    transform_documents,
)
from pipeline.validate import (
    is_valid_document,
    validate_document,
    validate_documents,
)


def test_extract_documents_returns_documents() -> None:
    """Documents are streamed from a MongoDB collection."""
    collection = MagicMock()
    collection.find.return_value = iter(
        [
            {"_id": 1, "name": "Alice"},
            {"_id": 2, "name": "Bob"},
        ]
    )

    documents = list(
        extract_documents(
            collection,
            batch_size=100,
        )
    )

    assert documents == [
        {"_id": 1, "name": "Alice"},
        {"_id": 2, "name": "Bob"},
    ]

    collection.find.assert_called_once_with(
        {},
        None,
        batch_size=100,
    )


def test_extract_documents_applies_filter_and_projection() -> None:
    """Extraction passes MongoDB filtering and projection to the cursor."""
    collection = MagicMock()
    collection.find.return_value = iter(
        [{"_id": 1, "email": "alice@example.com"}]
    )

    documents = list(
        extract_documents(
            collection,
            {"active": True},
            projection={"_id": 1, "email": 1},
            batch_size=50,
        )
    )

    assert documents == [
        {"_id": 1, "email": "alice@example.com"},
    ]

    collection.find.assert_called_once_with(
        {"active": True},
        {"_id": 1, "email": 1},
        batch_size=50,
    )


def test_extract_documents_rejects_invalid_batch_size() -> None:
    """Extraction rejects non-positive batch sizes."""
    collection = MagicMock()

    with pytest.raises(ValueError, match="batch_size"):
        list(extract_documents(collection, batch_size=0))


def test_extract_documents_in_batches() -> None:
    """Extraction groups documents into bounded application batches."""
    collection = MagicMock()
    collection.find.return_value = iter(
        [
            {"_id": 1},
            {"_id": 2},
            {"_id": 3},
            {"_id": 4},
            {"_id": 5},
        ]
    )

    batches = list(
        extract_documents_in_batches(
            collection,
            batch_size=2,
        )
    )

    assert batches == [
        [{"_id": 1}, {"_id": 2}],
        [{"_id": 3}, {"_id": 4}],
        [{"_id": 5}],
    ]


def test_transform_document_normalizes_strings() -> None:
    """Transformation strips strings and normalizes email addresses."""
    document = {
        "_id": 1,
        "name": "  Alice  ",
        "email": " ALICE@EXAMPLE.COM ",
    }

    transformed = transform_document(document)

    assert transformed["_id"] == 1
    assert transformed["name"] == "Alice"
    assert transformed["email"] == "alice@example.com"
    assert "processed_at" in transformed
    assert document["name"] == "  Alice  "
    assert document["email"] == " ALICE@EXAMPLE.COM "


def test_transform_documents_is_lazy() -> None:
    """Document transformation can be consumed incrementally."""
    documents = [
        {"_id": 1, "name": " Alice "},
        {"_id": 2, "name": " Bob "},
    ]

    transformed = transform_documents(documents)

    first = next(transformed)

    assert first["_id"] == 1
    assert first["name"] == "Alice"


def test_transform_batch_returns_transformed_documents() -> None:
    """Batch transformation returns a concrete list."""
    documents = [
        {"_id": 1, "name": " Alice "},
        {"_id": 2, "name": " Bob "},
    ]

    transformed = transform_batch(documents)

    assert [document["name"] for document in transformed] == [
        "Alice",
        "Bob",
    ]


def test_validate_document_accepts_valid_document() -> None:
    """A document containing the required fields is valid."""
    result = validate_document(
        {
            "_id": 1,
            "email": "alice@example.com",
        }
    )

    assert result.valid is True
    assert result.errors == ()


def test_validate_document_rejects_empty_document() -> None:
    """Empty documents fail validation."""
    result = validate_document({})

    assert result.valid is False
    assert "document must not be empty" in result.errors
    assert "document must contain '_id'" in result.errors


def test_validate_document_rejects_invalid_email() -> None:
    """An explicitly supplied invalid email value fails validation."""
    result = validate_document(
        {
            "_id": 1,
            "email": "",
        }
    )

    assert result.valid is False
    assert "email must be a non-empty string when provided" in result.errors


def test_is_valid_document_returns_boolean() -> None:
    """The convenience validator returns a boolean result."""
    assert is_valid_document({"_id": 1}) is True
    assert is_valid_document({}) is False


def test_validate_documents_separates_invalid_records() -> None:
    """Batch validation preserves valid records and validation results."""
    documents = [
        {"_id": 1, "name": "Alice"},
        {"name": "Missing ID"},
        {"_id": 3, "email": "bob@example.com"},
    ]

    valid_documents, results = validate_documents(documents)

    assert valid_documents == [
        {"_id": 1, "name": "Alice"},
        {"_id": 3, "email": "bob@example.com"},
    ]

    assert len(results) == 3
    assert [result.valid for result in results] == [
        True,
        False,
        True,
    ]


def test_load_documents_uses_bulk_write() -> None:
    """Loading uses one MongoDB bulk-write operation."""
    collection = MagicMock()
    bulk_result = MagicMock()
    collection.bulk_write.return_value = bulk_result

    documents = [
        {"_id": 1, "name": "Alice"},
        {"_id": 2, "name": "Bob"},
    ]

    result = load_documents(
        collection,
        documents,
        ordered=False,
    )

    assert result is bulk_result
    collection.bulk_write.assert_called_once()

    operations = collection.bulk_write.call_args.args[0]

    assert len(operations) == 2
    assert operations[0]._doc == {"_id": 1, "name": "Alice"}
    assert operations[1]._doc == {"_id": 2, "name": "Bob"}

    assert collection.bulk_write.call_args.kwargs == {
        "ordered": False,
    }


def test_load_documents_rejects_empty_input() -> None:
    """A bulk load requires at least one document."""
    collection = MagicMock()

    with pytest.raises(ValueError, match="at least one document"):
        load_documents(collection, [])


def test_load_documents_in_batches() -> None:
    """Large loads are split into bounded MongoDB bulk operations."""
    collection = MagicMock()

    first_result = MagicMock()
    first_result.inserted_count = 2

    second_result = MagicMock()
    second_result.inserted_count = 2

    collection.bulk_write.side_effect = [
        first_result,
        second_result,
    ]

    documents = [
        {"_id": 1},
        {"_id": 2},
        {"_id": 3},
        {"_id": 4},
    ]

    inserted_count = load_documents_in_batches(
        collection,
        documents,
        batch_size=2,
    )

    assert inserted_count == 4
    assert collection.bulk_write.call_count == 2

    first_operations = collection.bulk_write.call_args_list[0].args[0]
    second_operations = collection.bulk_write.call_args_list[1].args[0]

    assert len(first_operations) == 2
    assert len(second_operations) == 2


def test_load_documents_in_batches_handles_partial_final_batch() -> None:
    """The final incomplete batch is still written."""
    collection = MagicMock()

    result = MagicMock()
    result.inserted_count = 3
    collection.bulk_write.return_value = result

    documents = [
        {"_id": 1},
        {"_id": 2},
        {"_id": 3},
    ]

    inserted_count = load_documents_in_batches(
        collection,
        documents,
        batch_size=10,
    )

    assert inserted_count == 3
    assert collection.bulk_write.call_count == 1


def test_load_documents_in_batches_supports_empty_input() -> None:
    """An empty iterable produces no MongoDB writes."""
    collection = MagicMock()

    inserted_count = load_documents_in_batches(
        collection,
        [],
        batch_size=10,
    )

    assert inserted_count == 0
    collection.bulk_write.assert_not_called()


def test_load_documents_in_batches_rejects_invalid_batch_size() -> None:
    """Batch loading rejects non-positive batch sizes."""
    collection = MagicMock()

    with pytest.raises(ValueError, match="batch_size"):
        load_documents_in_batches(
            collection,
            [{"_id": 1}],
            batch_size=0,
        )


def test_pipeline_stages_can_be_composed() -> None:
    """Extraction, transformation, and validation compose cleanly."""
    collection = MagicMock()
    collection.find.return_value = iter(
        [
            {"_id": 1, "name": " Alice "},
            {"_id": 2, "name": " Bob "},
            {"name": " Invalid "},
        ]
    )

    extracted = extract_documents(
        collection,
        batch_size=10,
    )
    transformed = transform_documents(extracted)
    valid_documents, results = validate_documents(transformed)

    assert valid_documents[0]["name"] == "Alice"
    assert valid_documents[1]["name"] == "Bob"
    assert len(valid_documents) == 2
    assert sum(not result.valid for result in results) == 1


def test_pipeline_preserves_non_string_values() -> None:
    """Transformation does not coerce non-string values unexpectedly."""
    document: dict[str, Any] = {
        "_id": 1,
        "age": 30,
        "active": True,
        "score": 10.5,
    }

    transformed = transform_document(document)

    assert transformed["age"] == 30
    assert transformed["active"] is True
    assert transformed["score"] == 10.5

"""Tests for the extraction, transformation, validation, and loading stages."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from pipeline.extract import (
    extract_documents,
    extract_documents_in_batches,
)
from pipeline.load import (
    load_documents,
    load_documents_in_batches,
)
from pipeline.transform import (
    transform_batch,
    transform_document,
    transform_documents,
)
from pipeline.validate import (
    is_valid_document,
    validate_document,
    validate_documents,
)


def test_extract_documents_returns_documents() -> None:
    """Documents are streamed from a MongoDB collection."""
    collection = MagicMock()
    collection.find.return_value = iter(
        [
            {"_id": 1, "name": "Alice"},
            {"_id": 2, "name": "Bob"},
        ]
    )

    documents = list(
        extract_documents(
            collection,
            batch_size=100,
        )
    )

    assert documents == [
        {"_id": 1, "name": "Alice"},
        {"_id": 2, "name": "Bob"},
    ]

    collection.find.assert_called_once_with(
        {},
        None,
        batch_size=100,
    )


def test_extract_documents_applies_filter_and_projection() -> None:
    """Extraction passes MongoDB filtering and projection to the cursor."""
    collection = MagicMock()
    collection.find.return_value = iter(
        [{"_id": 1, "email": "alice@example.com"}]
    )

    documents = list(
        extract_documents(
            collection,
            {"active": True},
            projection={"_id": 1, "email": 1},
            batch_size=50,
        )
    )

    assert documents == [
        {"_id": 1, "email": "alice@example.com"},
    ]

    collection.find.assert_called_once_with(
        {"active": True},
        {"_id": 1, "email": 1},
        batch_size=50,
    )


def test_extract_documents_rejects_invalid_batch_size() -> None:
    """Extraction rejects non-positive batch sizes."""
    collection = MagicMock()

    with pytest.raises(ValueError, match="batch_size"):
        list(extract_documents(collection, batch_size=0))


def test_extract_documents_in_batches() -> None:
    """Extraction groups documents into bounded application batches."""
    collection = MagicMock()
    collection.find.return_value = iter(
        [
            {"_id": 1},
            {"_id": 2},
            {"_id": 3},
            {"_id": 4},
            {"_id": 5},
        ]
    )

    batches = list(
        extract_documents_in_batches(
            collection,
            batch_size=2,
        )
    )

    assert batches == [
        [{"_id": 1}, {"_id": 2}],
        [{"_id": 3}, {"_id": 4}],
        [{"_id": 5}],
    ]


def test_transform_document_normalizes_strings() -> None:
    """Transformation strips strings and normalizes email addresses."""
    document = {
        "_id": 1,
        "name": "  Alice  ",
        "email": " ALICE@EXAMPLE.COM ",
    }

    transformed = transform_document(document)

    assert transformed["_id"] == 1
    assert transformed["name"] == "Alice"
    assert transformed["email"] == "alice@example.com"
    assert "processed_at" in transformed
    assert document["name"] == "  Alice  "
    assert document["email"] == " ALICE@EXAMPLE.COM "


def test_transform_documents_is_lazy() -> None:
    """Document transformation can be consumed incrementally."""
    documents = [
        {"_id": 1, "name": " Alice "},
        {"_id": 2, "name": " Bob "},
    ]

    transformed = transform_documents(documents)

    first = next(transformed)

    assert first["_id"] == 1
    assert first["name"] == "Alice"


def test_transform_batch_returns_transformed_documents() -> None:
    """Batch transformation returns a concrete list."""
    documents = [
        {"_id": 1, "name": " Alice "},
        {"_id": 2, "name": " Bob "},
    ]

    transformed = transform_batch(documents)

    assert [document["name"] for document in transformed] == [
        "Alice",
        "Bob",
    ]


def test_validate_document_accepts_valid_document() -> None:
    """A document containing the required fields is valid."""
    result = validate_document(
        {
            "_id": 1,
            "email": "alice@example.com",
        }
    )

    assert result.valid is True
    assert result.errors == ()


def test_validate_document_rejects_empty_document() -> None:
    """Empty documents fail validation."""
    result = validate_document({})

    assert result.valid is False
    assert "document must not be empty" in result.errors
    assert "document must contain '_id'" in result.errors


def test_validate_document_rejects_invalid_email() -> None:
    """An explicitly supplied invalid email value fails validation."""
    result = validate_document(
        {
            "_id": 1,
            "email": "",
        }
    )

    assert result.valid is False
    assert "email must be a non-empty string when provided" in result.errors


def test_is_valid_document_returns_boolean() -> None:
    """The convenience validator returns a boolean result."""
    assert is_valid_document({"_id": 1}) is True
    assert is_valid_document({}) is False


def test_validate_documents_separates_invalid_records() -> None:
    """Batch validation preserves valid records and validation results."""
    documents = [
        {"_id": 1, "name": "Alice"},
        {"name": "Missing ID"},
        {"_id": 3, "email": "bob@example.com"},
    ]

    valid_documents, results = validate_documents(documents)

    assert valid_documents == [
        {"_id": 1, "name": "Alice"},
        {"_id": 3, "email": "bob@example.com"},
    ]

    assert len(results) == 3
    assert [result.valid for result in results] == [
        True,
        False,
        True,
    ]


def test_load_documents_uses_bulk_write() -> None:
    """Loading uses one MongoDB bulk-write operation."""
    collection = MagicMock()
    bulk_result = MagicMock()
    collection.bulk_write.return_value = bulk_result

    documents = [
        {"_id": 1, "name": "Alice"},
        {"_id": 2, "name": "Bob"},
    ]

    result = load_documents(
        collection,
        documents,
        ordered=False,
    )

    assert result is bulk_result
    collection.bulk_write.assert_called_once()

    operations = collection.bulk_write.call_args.args[0]

    assert len(operations) == 2
    assert operations[0]._doc == {"_id": 1, "name": "Alice"}
    assert operations[1]._doc == {"_id": 2, "name": "Bob"}

    assert collection.bulk_write.call_args.kwargs == {
        "ordered": False,
    }


def test_load_documents_rejects_empty_input() -> None:
    """A bulk load requires at least one document."""
    collection = MagicMock()

    with pytest.raises(ValueError, match="at least one document"):
        load_documents(collection, [])


def test_load_documents_in_batches() -> None:
    """Large loads are split into bounded MongoDB bulk operations."""
    collection = MagicMock()

    first_result = MagicMock()
    first_result.inserted_count = 2

    second_result = MagicMock()
    second_result.inserted_count = 2

    collection.bulk_write.side_effect = [
        first_result,
        second_result,
    ]

    documents = [
        {"_id": 1},
        {"_id": 2},
        {"_id": 3},
        {"_id": 4},
    ]

    inserted_count = load_documents_in_batches(
        collection,
        documents,
        batch_size=2,
    )

    assert inserted_count == 4
    assert collection.bulk_write.call_count == 2

    first_operations = collection.bulk_write.call_args_list[0].args[0]
    second_operations = collection.bulk_write.call_args_list[1].args[0]

    assert len(first_operations) == 2
    assert len(second_operations) == 2


def test_load_documents_in_batches_handles_partial_final_batch() -> None:
    """The final incomplete batch is still written."""
    collection = MagicMock()

    result = MagicMock()
    result.inserted_count = 3
    collection.bulk_write.return_value = result

    documents = [
        {"_id": 1},
        {"_id": 2},
        {"_id": 3},
    ]

    inserted_count = load_documents_in_batches(
        collection,
        documents,
        batch_size=10,
    )

    assert inserted_count == 3
    assert collection.bulk_write.call_count == 1


def test_load_documents_in_batches_supports_empty_input() -> None:
    """An empty iterable produces no MongoDB writes."""
    collection = MagicMock()

    inserted_count = load_documents_in_batches(
        collection,
        [],
        batch_size=10,
    )

    assert inserted_count == 0
    collection.bulk_write.assert_not_called()


def test_load_documents_in_batches_rejects_invalid_batch_size() -> None:
    """Batch loading rejects non-positive batch sizes."""
    collection = MagicMock()

    with pytest.raises(ValueError, match="batch_size"):
        load_documents_in_batches(
            collection,
            [{"_id": 1}],
            batch_size=0,
        )


def test_pipeline_stages_can_be_composed() -> None:
    """Extraction, transformation, and validation compose cleanly."""
    collection = MagicMock()
    collection.find.return_value = iter(
        [
            {"_id": 1, "name": " Alice "},
            {"_id": 2, "name": " Bob "},
            {"name": " Invalid "},
        ]
    )

    extracted = extract_documents(
        collection,
        batch_size=10,
    )
    transformed = transform_documents(extracted)
    valid_documents, results = validate_documents(transformed)

    assert valid_documents[0]["name"] == "Alice"
    assert valid_documents[1]["name"] == "Bob"
    assert len(valid_documents) == 2
    assert sum(not result.valid for result in results) == 1


def test_pipeline_preserves_non_string_values() -> None:
    """Transformation does not coerce non-string values unexpectedly."""
    document: dict[str, Any] = {
        "_id": 1,
        "age": 30,
        "active": True,
        "score": 10.5,
    }

    transformed = transform_document(document)

    assert transformed["age"] == 30
    assert transformed["active"] is True
    assert transformed["score"] == 10.5