"""Validation stage for the MongoDB data import and processing pipeline."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of validating a single pipeline document."""

    valid: bool
    errors: tuple[str, ...]


def validate_document(document: Mapping[str, Any]) -> ValidationResult:
    """Validate the minimum contract required by the processing pipeline.

    Validation is intentionally performed before loading so malformed
    documents do not reach the destination collection. The checks can be
    extended as the pipeline's target schema evolves.

    Args:
        document: Transformed MongoDB document.

    Returns:
        ValidationResult containing validity and validation errors.
    """
    errors: list[str] = []

    if not document:
        errors.append("document must not be empty")

    if "_id" not in document:
        errors.append("document must contain '_id'")

    email = document.get("email")
    if email is not None and (
        not isinstance(email, str) or not email.strip()
    ):
        errors.append("email must be a non-empty string when provided")

    processed_at = document.get("processed_at")
    if processed_at is not None and not hasattr(processed_at, "tzinfo"):
        errors.append("processed_at must be a datetime when provided")

    return ValidationResult(
        valid=not errors,
        errors=tuple(errors),
    )


def validate_documents(
    documents: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[ValidationResult]]:
    """Validate a collection of documents and separate valid records.

    Invalid records are not silently discarded. Their validation results are
    returned so callers can log, count, quarantine, or otherwise handle them
    according to the pipeline's operational policy.

    Args:
        documents: Transformed documents to validate.

    Returns:
        A tuple containing valid documents and validation results.
    """
    valid_documents: list[dict[str, Any]] = []
    results: list[ValidationResult] = []

    for document in documents:
        result = validate_document(document)
        results.append(result)

        if result.valid:
            valid_documents.append(dict(document))

    return valid_documents, results


def is_valid_document(document: Mapping[str, Any]) -> bool:
    """Return whether a document satisfies the pipeline validation rules."""
    return validate_document(document).valid

"""Validation stage for the MongoDB data import and processing pipeline."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of validating a single pipeline document."""

    valid: bool
    errors: tuple[str, ...]


def validate_document(document: Mapping[str, Any]) -> ValidationResult:
    """Validate the minimum contract required by the processing pipeline.

    Validation is intentionally performed before loading so malformed
    documents do not reach the destination collection. The checks can be
    extended as the pipeline's target schema evolves.

    Args:
        document: Transformed MongoDB document.

    Returns:
        ValidationResult containing validity and validation errors.
    """
    errors: list[str] = []

    if not document:
        errors.append("document must not be empty")

    if "_id" not in document:
        errors.append("document must contain '_id'")

    email = document.get("email")
    if email is not None and (
        not isinstance(email, str) or not email.strip()
    ):
        errors.append("email must be a non-empty string when provided")

    processed_at = document.get("processed_at")
    if processed_at is not None and not hasattr(processed_at, "tzinfo"):
        errors.append("processed_at must be a datetime when provided")

    return ValidationResult(
        valid=not errors,
        errors=tuple(errors),
    )


def validate_documents(
    documents: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[ValidationResult]]:
    """Validate a collection of documents and separate valid records.

    Invalid records are not silently discarded. Their validation results are
    returned so callers can log, count, quarantine, or otherwise handle them
    according to the pipeline's operational policy.

    Args:
        documents: Transformed documents to validate.

    Returns:
        A tuple containing valid documents and validation results.
    """
    valid_documents: list[dict[str, Any]] = []
    results: list[ValidationResult] = []

    for document in documents:
        result = validate_document(document)
        results.append(result)

        if result.valid:
            valid_documents.append(dict(document))

    return valid_documents, results


def is_valid_document(document: Mapping[str, Any]) -> bool:
    """Return whether a document satisfies the pipeline validation rules."""
    return validate_document(document).valid