"""Data transformation stage for the MongoDB data import and processing pipeline."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from datetime import datetime, timezone
from typing import Any


def transform_document(document: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a source document for downstream processing.

    The transformation is intentionally deterministic and non-mutating.
    Source documents are copied before fields are normalized so that callers
    can safely reuse the documents returned by the extraction stage.

    The transformation:
    - removes leading and trailing whitespace from string values;
    - normalizes an optional ``email`` field to lowercase;
    - adds a UTC ``processed_at`` timestamp;
    - preserves fields that are not explicitly transformed.

    Args:
        document: Source MongoDB document.

    Returns:
        A transformed document suitable for the loading stage.
    """
    transformed = dict(document)

    for key, value in transformed.items():
        if isinstance(value, str):
            transformed[key] = value.strip()

    email = transformed.get("email")
    if isinstance(email, str):
        transformed["email"] = email.lower()

    transformed["processed_at"] = datetime.now(timezone.utc)

    return transformed


def transform_documents(
    documents: Iterable[Mapping[str, Any]],
) -> Iterator[dict[str, Any]]:
    """Transform documents lazily without accumulating the full dataset."""
    for document in documents:
        yield transform_document(document)


def transform_batch(
    documents: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Transform a bounded batch of documents.

    Use this function when downstream loading or validation is performed
    batch-by-batch and a concrete list is required by the caller.
    """
    return list(transform_documents(documents))

"""Data transformation stage for the MongoDB data import and processing pipeline."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from datetime import datetime, timezone
from typing import Any


def transform_document(document: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a source document for downstream processing.

    The transformation is intentionally deterministic and non-mutating.
    Source documents are copied before fields are normalized so that callers
    can safely reuse the documents returned by the extraction stage.

    The transformation:
    - removes leading and trailing whitespace from string values;
    - normalizes an optional ``email`` field to lowercase;
    - adds a UTC ``processed_at`` timestamp;
    - preserves fields that are not explicitly transformed.

    Args:
        document: Source MongoDB document.

    Returns:
        A transformed document suitable for the loading stage.
    """
    transformed = dict(document)

    for key, value in transformed.items():
        if isinstance(value, str):
            transformed[key] = value.strip()

    email = transformed.get("email")
    if isinstance(email, str):
        transformed["email"] = email.lower()

    transformed["processed_at"] = datetime.now(timezone.utc)

    return transformed


def transform_documents(
    documents: Iterable[Mapping[str, Any]],
) -> Iterator[dict[str, Any]]:
    """Transform documents lazily without accumulating the full dataset."""
    for document in documents:
        yield transform_document(document)


def transform_batch(
    documents: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Transform a bounded batch of documents.

    Use this function when downstream loading or validation is performed
    batch-by-batch and a concrete list is required by the caller.
    """
    return list(transform_documents(documents))