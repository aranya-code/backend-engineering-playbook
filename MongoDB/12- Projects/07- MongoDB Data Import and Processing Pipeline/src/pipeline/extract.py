"""Data extraction stage for the MongoDB data import and processing pipeline."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from pymongo.collection import Collection
from pymongo.cursor import Cursor


def extract_documents(
    collection: Collection[dict[str, Any]],
    filter_query: dict[str, Any] | None = None,
    *,
    projection: dict[str, int] | None = None,
    batch_size: int = 1_000,
) -> Iterator[dict[str, Any]]:
    """Stream documents from MongoDB for downstream pipeline processing.

    MongoDB cursors are lazy, so documents are fetched incrementally instead
    of loading the complete collection into application memory. This is the
    preferred approach for large import and processing workloads.

    Args:
        collection: MongoDB collection to read from.
        filter_query: Optional MongoDB filter. Defaults to all documents.
        projection: Optional projection controlling returned fields.
        batch_size: Number of documents requested per network batch.

    Yields:
        Documents returned by MongoDB.

    Raises:
        ValueError: If batch_size is not positive.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    cursor: Cursor[dict[str, Any]] = collection.find(
        filter_query or {},
        projection,
        batch_size=batch_size,
    )

    try:
        yield from cursor
    finally:
        cursor.close()


def extract_documents_in_batches(
    collection: Collection[dict[str, Any]],
    filter_query: dict[str, Any] | None = None,
    *,
    projection: dict[str, int] | None = None,
    batch_size: int = 1_000,
) -> Iterator[list[dict[str, Any]]]:
    """Yield MongoDB documents as bounded application-level batches.

    The MongoDB cursor controls database/network fetching while this function
    controls the amount of data handed to downstream processing stages.
    Keeping these concerns separate prevents large result sets from being
    accumulated in memory.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    batch: list[dict[str, Any]] = []

    for document in extract_documents(
        collection,
        filter_query,
        projection=projection,
        batch_size=batch_size,
    ):
        batch.append(document)

        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch

"""Data extraction stage for the MongoDB data import and processing pipeline."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from pymongo.collection import Collection
from pymongo.cursor import Cursor


def extract_documents(
    collection: Collection[dict[str, Any]],
    filter_query: dict[str, Any] | None = None,
    *,
    projection: dict[str, int] | None = None,
    batch_size: int = 1_000,
) -> Iterator[dict[str, Any]]:
    """Stream documents from MongoDB for downstream pipeline processing.

    MongoDB cursors are lazy, so documents are fetched incrementally instead
    of loading the complete collection into application memory. This is the
    preferred approach for large import and processing workloads.

    Args:
        collection: MongoDB collection to read from.
        filter_query: Optional MongoDB filter. Defaults to all documents.
        projection: Optional projection controlling returned fields.
        batch_size: Number of documents requested per network batch.

    Yields:
        Documents returned by MongoDB.

    Raises:
        ValueError: If batch_size is not positive.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    cursor: Cursor[dict[str, Any]] = collection.find(
        filter_query or {},
        projection,
        batch_size=batch_size,
    )

    try:
        yield from cursor
    finally:
        cursor.close()


def extract_documents_in_batches(
    collection: Collection[dict[str, Any]],
    filter_query: dict[str, Any] | None = None,
    *,
    projection: dict[str, int] | None = None,
    batch_size: int = 1_000,
) -> Iterator[list[dict[str, Any]]]:
    """Yield MongoDB documents as bounded application-level batches.

    The MongoDB cursor controls database/network fetching while this function
    controls the amount of data handed to downstream processing stages.
    Keeping these concerns separate prevents large result sets from being
    accumulated in memory.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    batch: list[dict[str, Any]] = []

    for document in extract_documents(
        collection,
        filter_query,
        projection=projection,
        batch_size=batch_size,
    ):
        batch.append(document)

        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch