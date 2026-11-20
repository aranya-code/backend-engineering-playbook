#!/usr/bin/env python3
"""Validate event datasets before ingestion into the S3 data lake."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger("data_lake.validation")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "samples" / "sample_events.json"

REQUIRED_FIELDS = {
    "event_id",
    "event_timestamp",
    "event_date",
    "tenant_id",
    "event_type",
    "user_id",
    "amount",
    "currency",
    "source",
    "attributes",
}

REQUIRED_STRING_FIELDS = {
    "event_id",
    "tenant_id",
    "event_type",
    "user_id",
    "event_date",
    "event_timestamp",
    "amount",
    "currency",
    "source",
}

SUPPORTED_EVENT_TYPES = {
    "purchase",
    "page_view",
    "refund",
    "signup",
}

SUPPORTED_SOURCES = {
    "web",
    "mobile",
    "api",
}

CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")


class DatasetValidationError(ValueError):
    """Raised when a dataset cannot be validated."""


class EventValidationError(ValueError):
    """Raised when an individual event violates the dataset schema."""


def configure_logging(verbose: bool = False) -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def load_dataset(source_path: Path) -> list[dict[str, Any]]:
    """Load a JSON array containing event records."""
    if not source_path.exists():
        raise FileNotFoundError(
            f"Dataset file does not exist: {source_path}"
        )

    if not source_path.is_file():
        raise ValueError(
            f"Dataset path is not a regular file: {source_path}"
        )

    try:
        with source_path.open("r", encoding="utf-8") as source_file:
            records = json.load(source_file)
    except json.JSONDecodeError as exc:
        raise DatasetValidationError(
            f"Invalid JSON at line {exc.lineno}, column {exc.colno}: "
            f"{exc.msg}"
        ) from exc

    if not isinstance(records, list):
        raise DatasetValidationError(
            "The dataset root must be a JSON array."
        )

    if not records:
        raise DatasetValidationError(
            "The dataset must contain at least one event."
        )

    return records


def validate_required_fields(
    record: dict[str, Any],
    record_number: int,
) -> None:
    """Validate required fields and their basic types."""
    missing_fields = REQUIRED_FIELDS.difference(record)

    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise EventValidationError(
            f"Record {record_number}: missing required fields: {missing}"
        )

    for field in REQUIRED_STRING_FIELDS:
        value = record[field]

        if not isinstance(value, str) or not value.strip():
            raise EventValidationError(
                f"Record {record_number}: {field} must be a "
                "non-empty string."
            )

    if not isinstance(record["attributes"], dict):
        raise EventValidationError(
            f"Record {record_number}: attributes must be a JSON object."
        )


def validate_event_timestamp(
    record: dict[str, Any],
    record_number: int,
) -> tuple[date, datetime]:
    """Validate the event timestamp and partition date."""
    try:
        event_date = date.fromisoformat(record["event_date"])
    except ValueError as exc:
        raise EventValidationError(
            f"Record {record_number}: event_date must use YYYY-MM-DD format."
        ) from exc

    timestamp_value = record["event_timestamp"]
    normalized_timestamp = (
        timestamp_value[:-1] + "+00:00"
        if timestamp_value.endswith("Z")
        else timestamp_value
    )

    try:
        event_timestamp = datetime.fromisoformat(normalized_timestamp)
    except ValueError as exc:
        raise EventValidationError(
            f"Record {record_number}: event_timestamp must be a valid "
            "ISO 8601 timestamp."
        ) from exc

    if event_timestamp.tzinfo is None:
        raise EventValidationError(
            f"Record {record_number}: event_timestamp must include "
            "a timezone or UTC offset."
        )

    if event_timestamp.date() != event_date:
        raise EventValidationError(
            f"Record {record_number}: event_date does not match the "
            "calendar date in event_timestamp."
        )

    return event_date, event_timestamp


def validate_amount(
    value: str,
    record_number: int,
) -> Decimal:
    """Validate an amount represented as a decimal string."""
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise EventValidationError(
            f"Record {record_number}: amount must be a valid decimal string."
        ) from exc

    if not amount.is_finite():
        raise EventValidationError(
            f"Record {record_number}: amount must be finite."
        )

    return amount


def validate_currency(
    currency: str,
    record_number: int,
) -> None:
    """Validate the three-letter uppercase currency representation."""
    if not CURRENCY_PATTERN.fullmatch(currency):
        raise EventValidationError(
            f"Record {record_number}: currency must contain exactly "
            "three uppercase letters."
        )


def validate_event(
    record: Any,
    record_number: int,
) -> dict[str, Any]:
    """Validate one event record against the project schema."""
    if not isinstance(record, dict):
        raise EventValidationError(
            f"Record {record_number}: each event must be a JSON object."
        )

    validate_required_fields(record, record_number)
    validate_event_timestamp(record, record_number)
    validate_amount(record["amount"], record_number)
    validate_currency(record["currency"], record_number)

    if record["event_type"] not in SUPPORTED_EVENT_TYPES:
        raise EventValidationError(
            f"Record {record_number}: unsupported event_type "
            f"{record['event_type']!r}."
        )

    if record["source"] not in SUPPORTED_SOURCES:
        raise EventValidationError(
            f"Record {record_number}: unsupported source "
            f"{record['source']!r}."
        )

    return record


def validate_unique_event_ids(
    records: list[dict[str, Any]],
) -> None:
    """Reject duplicate event identifiers."""
    event_ids = [record["event_id"] for record in records]
    duplicates = [
        event_id
        for event_id, count in Counter(event_ids).items()
        if count > 1
    ]

    if duplicates:
        duplicate_list = ", ".join(sorted(duplicates))
        raise DatasetValidationError(
            f"Duplicate event_id values found: {duplicate_list}"
        )


def validate_dataset_records(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate all records and return dataset statistics."""
    if not isinstance(records, list):
        raise DatasetValidationError(
            "The dataset must be represented as a list of event records."
        )

    if not records:
        raise DatasetValidationError(
            "The dataset must contain at least one event."
        )

    validated_records = [
        validate_event(record, index)
        for index, record in enumerate(records, start=1)
    ]

    validate_unique_event_ids(validated_records)

    event_type_counts = Counter(
        record["event_type"]
        for record in validated_records
    )
    source_counts = Counter(
        record["source"]
        for record in validated_records
    )
    tenant_counts = Counter(
        record["tenant_id"]
        for record in validated_records
    )
    date_counts = Counter(
        record["event_date"]
        for record in validated_records
    )

    statistics = {
        "record_count": len(validated_records),
        "distinct_event_ids": len(
            {record["event_id"] for record in validated_records}
        ),
        "distinct_tenants": len(tenant_counts),
        "partition_count": len(date_counts),
        "event_types": dict(sorted(event_type_counts.items())),
        "sources": dict(sorted(source_counts.items())),
        "tenants": dict(sorted(tenant_counts.items())),
        "event_dates": dict(sorted(date_counts.items())),
    }

    return statistics


def validate_dataset_file(source_path: Path) -> dict[str, Any]:
    """Load and validate a dataset file."""
    records = load_dataset(source_path)
    statistics = validate_dataset_records(records)

    return {
        "source": str(source_path.resolve()),
        "status": "valid",
        **statistics,
    }


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate the structure, identifiers, timestamps, and "
            "partition dates of an event dataset."
        )
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Input JSON dataset. Default: {DEFAULT_SOURCE}",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging.",
    )

    return parser.parse_args()


def main() -> int:
    """Run dataset validation and print a machine-readable report."""
    arguments = parse_arguments()
    configure_logging(arguments.verbose)

    try:
        report = validate_dataset_file(arguments.file)
    except (
        DatasetValidationError,
        EventValidationError,
        FileNotFoundError,
        ValueError,
    ) as exc:
        LOGGER.error("Dataset validation failed: %s", exc)

        error_report = {
            "status": "invalid",
            "source": str(arguments.file),
            "error": str(exc),
        }
        print(json.dumps(error_report, indent=2))
        return 1
    except OSError as exc:
        LOGGER.exception("Unable to read the dataset: %s", exc)
        return 1

    LOGGER.info(
        "Validated %d records across %d date partitions.",
        report["record_count"],
        report["partition_count"],
    )
    print(json.dumps(report, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())