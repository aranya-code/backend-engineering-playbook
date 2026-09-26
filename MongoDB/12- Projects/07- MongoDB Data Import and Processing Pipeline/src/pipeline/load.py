"""Data loading stage for the MongoDB data import and processing pipeline."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from pymongo import InsertOne
from pymongo.collection import Collection
from pymongo.results import BulkWriteResult


def load_documents(
    collection: Collection[dict[str, Any]],
    documents: Iterable[Mapping[str, Any]],
    *,
    ordered: bool = False,
) -> BulkWriteResult:
    """Insert documents into MongoDB using a bulk write operation.

    Bulk writes reduce network round trips compared with issuing one insert
    request per document. Unordered writes allow MongoDB to process operations
    independently and are generally preferable for high-throughput imports
    when input ordering is not a business requirement.

    Args:
        collection: Destination MongoDB collection.
        documents: Validated documents to insert.
        ordered: Whether MongoDB must execute operations in input order.

    Returns:
        MongoDB bulk-write result containing inserted and error information.

    Raises:
        ValueError: If no documents are supplied.
    """
    operations = [
        InsertOne(dict(document))
        for document in documents
    ]

    if not operations:
        raise ValueError("documents must contain at least one document")

    return collection.bulk_write(
        operations,
        ordered=ordered,
    )


def load_documents_in_batches(
    collection: Collection[dict[str, Any]],
    documents: Iterable[Mapping[str, Any]],
    *,
    batch_size: int = 1_000,
    ordered: bool = False,
) -> int:
    """Load documents into MongoDB using bounded bulk-write batches.

    Batching limits application memory usage and keeps individual write
    requests bounded. This is suitable for large ETL/import workloads where
    loading the complete dataset into one bulk operation would be excessive.

    Args:
        collection: Destination MongoDB collection.
        documents: Validated documents to insert.
        batch_size: Maximum number of documents per bulk operation.
        ordered: Whether each bulk operation must preserve input ordering.

    Returns:
        Total number of successfully inserted documents.

    Raises:
        ValueError: If batch_size is not positive.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    inserted_count = 0
    batch: list[InsertOne] = []

    for document in documents:
        batch.append(InsertOne(dict(document)))

        if len(batch) >= batch_size:
            result = collection.bulk_write(
                batch,
                ordered=ordered,
            )
            inserted_count += result.inserted_count
            batch.clear()

    if batch:
        result = collection.bulk_write(
            batch,
            ordered=ordered,
        )
        inserted_count += result.inserted_count

    return inserted_count

"""Data loading stage for the MongoDB data import and processing pipeline."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from pymongo import InsertOne
from pymongo.collection import Collection
from pymongo.results import BulkWriteResult


def load_documents(
    collection: Collection[dict[str, Any]],
    documents: Iterable[Mapping[str, Any]],
    *,
    ordered: bool = False,
) -> BulkWriteResult:
    """Insert documents into MongoDB using a bulk write operation.

    Bulk writes reduce network round trips compared with issuing one insert
    request per document. Unordered writes allow MongoDB to process operations
    independently and are generally preferable for high-throughput imports
    when input ordering is not a business requirement.

    Args:
        collection: Destination MongoDB collection.
        documents: Validated documents to insert.
        ordered: Whether MongoDB must execute operations in input order.

    Returns:
        MongoDB bulk-write result containing inserted and error information.

    Raises:
        ValueError: If no documents are supplied.
    """
    operations = [
        InsertOne(dict(document))
        for document in documents
    ]

    if not operations:
        raise ValueError("documents must contain at least one document")

    return collection.bulk_write(
        operations,
        ordered=ordered,
    )


def load_documents_in_batches(
    collection: Collection[dict[str, Any]],
    documents: Iterable[Mapping[str, Any]],
    *,
    batch_size: int = 1_000,
    ordered: bool = False,
) -> int:
    """Load documents into MongoDB using bounded bulk-write batches.

    Batching limits application memory usage and keeps individual write
    requests bounded. This is suitable for large ETL/import workloads where
    loading the complete dataset into one bulk operation would be excessive.

    Args:
        collection: Destination MongoDB collection.
        documents: Validated documents to insert.
        batch_size: Maximum number of documents per bulk operation.
        ordered: Whether each bulk operation must preserve input ordering.

    Returns:
        Total number of successfully inserted documents.

    Raises:
        ValueError: If batch_size is not positive.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    inserted_count = 0
    batch: list[InsertOne] = []

    for document in documents:
        batch.append(InsertOne(dict(document)))

        if len(batch) >= batch_size:
            result = collection.bulk_write(
                batch,
                ordered=ordered,
            )
            inserted_count += result.inserted_count
            batch.clear()

    if batch:
        result = collection.bulk_write(
            batch,
            ordered=ordered,
        )
        inserted_count += result.inserted_count

    return inserted_count