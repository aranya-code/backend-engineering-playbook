#!/usr/bin/env python3
"""Upload partitioned sample event data to an Amazon S3 data lake."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


LOGGER = logging.getLogger("data_lake.ingestion")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "samples" / "sample_events.json"
DEFAULT_REGION = os.getenv("AWS_REGION", "ap-south-1")
DEFAULT_PREFIX = os.getenv("DATA_LAKE_RAW_PREFIX", "raw/events")
DEFAULT_BUCKET = os.getenv("DATA_LAKE_BUCKET_NAME")

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


class DatasetValidationError(ValueError):
    """Raised when the input dataset does not match the expected schema."""


def configure_logging(verbose: bool = False) -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate sample event records, partition them by event date, "
            "and upload JSON Lines files to Amazon S3."
        )
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Input JSON dataset. Default: {DEFAULT_SOURCE}",
    )
    parser.add_argument(
        "--bucket",
        default=DEFAULT_BUCKET,
        help="Target S3 bucket. Defaults to DATA_LAKE_BUCKET_NAME.",
    )
    parser.add_argument(
        "--prefix",
        default=DEFAULT_PREFIX,
        help=f"S3 destination prefix. Default: {DEFAULT_PREFIX}",
    )
    parser.add_argument(
        "--region",
        default=DEFAULT_REGION,
        help=f"AWS Region. Default: {DEFAULT_REGION}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and report planned uploads without writing to S3.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging.",
    )

    return parser.parse_args()


def load_dataset(source_path: Path) -> list[dict[str, Any]]:
    """Load a JSON array of event records from disk."""
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
            f"Invalid JSON in {source_path}: {exc}"
        ) from exc

    if not isinstance(records, list):
        raise DatasetValidationError(
            "The dataset root must be a JSON array of event objects."
        )

    if not records:
        raise DatasetValidationError(
            "The dataset contains no event records."
        )

    return records


def validate_event(record: Any, index: int) -> dict[str, Any]:
    """Validate the structure and partition date of one event."""
    if not isinstance(record, dict):
        raise DatasetValidationError(
            f"Record at index {index} must be a JSON object."
        )

    missing_fields = REQUIRED_FIELDS.difference(record)
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise DatasetValidationError(
            f"Record at index {index} is missing fields: {missing}"
        )

    for field in (
        "event_id",
        "tenant_id",
        "event_type",
        "user_id",
        "currency",
        "source",
    ):
        value = record[field]
        if not isinstance(value, str) or not value.strip():
            raise DatasetValidationError(
                f"Record at index {index} has an invalid {field}."
            )

    if not isinstance(record["attributes"], dict):
        raise DatasetValidationError(
            f"Record at index {index} must have object-valued attributes."
        )

    event_date_value = record["event_date"]
    if not isinstance(event_date_value, str):
        raise DatasetValidationError(
            f"Record at index {index} has an invalid event_date."
        )

    try:
        parsed_date = date.fromisoformat(event_date_value)
    except ValueError as exc:
        raise DatasetValidationError(
            f"Record at index {index} has an invalid event_date: "
            f"{event_date_value!r}"
        ) from exc

    timestamp_value = record["event_timestamp"]
    if not isinstance(timestamp_value, str):
        raise DatasetValidationError(
            f"Record at index {index} has an invalid event_timestamp."
        )

    try:
        normalized_timestamp = timestamp_value.replace("Z", "+00:00")
        parsed_timestamp = datetime.fromisoformat(normalized_timestamp)
    except ValueError as exc:
        raise DatasetValidationError(
            f"Record at index {index} has an invalid event_timestamp: "
            f"{timestamp_value!r}"
        ) from exc

    if parsed_timestamp.tzinfo is None:
        raise DatasetValidationError(
            f"Record at index {index} must use a timezone-aware timestamp."
        )

    if parsed_timestamp.date() != parsed_date:
        raise DatasetValidationError(
            f"Record at index {index} has an event_date that does not "
            "match the date portion of event_timestamp."
        )

    amount = record["amount"]
    if not isinstance(amount, str):
        raise DatasetValidationError(
            f"Record at index {index} must represent amount as a string."
        )

    try:
        amount_value = float(amount)
    except ValueError as exc:
        raise DatasetValidationError(
            f"Record at index {index} has an invalid amount: {amount!r}"
        ) from exc

    if not __import__("math").isfinite(amount_value):
        raise DatasetValidationError(
            f"Record at index {index} has a non-finite amount."
        )

    if not isinstance(record["currency"], str):
        raise DatasetValidationError(
            f"Record at index {index} has an invalid currency."
        )

    return record


def validate_dataset(
    records: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Validate records and group them by event date."""
    partitions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_event_ids: set[str] = set()

    for index, raw_record in enumerate(records):
        record = validate_event(raw_record, index)
        event_id = record["event_id"]

        if event_id in seen_event_ids:
            raise DatasetValidationError(
                f"Duplicate event_id found: {event_id}"
            )

        seen_event_ids.add(event_id)
        partitions[record["event_date"]].append(record)

    return dict(sorted(partitions.items()))


def serialize_partition(
    records: list[dict[str, Any]],
) -> bytes:
    """Serialize event records as UTF-8 JSON Lines."""
    lines = [
        json.dumps(
            record,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        for record in records
    ]

    return ("\n".join(lines) + "\n").encode("utf-8")


def normalize_prefix(prefix: str) -> str:
    """Normalize and validate an S3 key prefix."""
    normalized = prefix.strip().strip("/")

    if not normalized:
        raise ValueError("The S3 destination prefix cannot be empty.")

    segments = normalized.split("/")
    if any(segment in {".", ".."} for segment in segments):
        raise ValueError(
            "The S3 destination prefix cannot contain '.' or '..' segments."
        )

    if any(not segment for segment in segments):
        raise ValueError(
            "The S3 destination prefix cannot contain empty path segments."
        )

    return normalized


def build_object_key(
    prefix: str,
    event_date: str,
    payload: bytes,
) -> str:
    """Build a deterministic partition key for the serialized records."""
    content_hash = hashlib.sha256(payload).hexdigest()
    filename = f"events-{content_hash}.jsonl"

    return f"{prefix}/event_date={event_date}/{filename}"


def create_s3_client(region: str) -> Any:
    """Create an S3 client using the standard AWS credential provider chain."""
    client_config = Config(
        region_name=region,
        retries={
            "max_attempts": 5,
            "mode": "standard",
        },
        connect_timeout=10,
        read_timeout=60,
        max_pool_connections=10,
    )

    return boto3.client("s3", config=client_config)


def upload_partition(
    s3_client: Any,
    bucket: str,
    object_key: str,
    payload: bytes,
    event_date: str,
    record_count: int,
) -> dict[str, Any]:
    """Upload one JSON Lines partition to S3."""
    checksum = hashlib.sha256(payload).hexdigest()

    response = s3_client.put_object(
        Bucket=bucket,
        Key=object_key,
        Body=payload,
        ContentType="application/x-ndjson",
        Metadata={
            "event-date": event_date,
            "record-count": str(record_count),
            "sha256": checksum,
            "dataset-format": "jsonl",
        },
    )

    return {
        "bucket": bucket,
        "key": object_key,
        "record_count": record_count,
        "size_bytes": len(payload),
        "etag": response.get("ETag"),
        "version_id": response.get("VersionId"),
        "sha256": checksum,
    }


def ingest_dataset(
    source_path: Path,
    bucket: str,
    prefix: str,
    region: str,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Validate, partition, and upload the dataset."""
    records = load_dataset(source_path)
    partitions = validate_dataset(records)
    normalized_prefix = normalize_prefix(prefix)

    LOGGER.info(
        "Validated %d records across %d event-date partitions.",
        len(records),
        len(partitions),
    )

    s3_client = None if dry_run else create_s3_client(region)
    results: list[dict[str, Any]] = []

    for event_date, partition_records in partitions.items():
        payload = serialize_partition(partition_records)
        object_key = build_object_key(
            normalized_prefix,
            event_date,
            payload,
        )

        if dry_run:
            result = {
                "bucket": bucket,
                "key": object_key,
                "record_count": len(partition_records),
                "size_bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "dry_run": True,
            }
        else:
            result = upload_partition(
                s3_client=s3_client,
                bucket=bucket,
                object_key=object_key,
                payload=payload,
                event_date=event_date,
                record_count=len(partition_records),
            )

        results.append(result)

        LOGGER.info(
            "%s s3://%s/%s (%d records, %d bytes)",
            "Planned" if dry_run else "Uploaded",
            bucket,
            object_key,
            len(partition_records),
            len(payload),
        )

    return results


def main() -> int:
    """Run the dataset ingestion command."""
    arguments = parse_arguments()
    configure_logging(arguments.verbose)

    if not arguments.bucket:
        LOGGER.error(
            "An S3 bucket is required. Set DATA_LAKE_BUCKET_NAME "
            "or provide --bucket."
        )
        return 2

    if not arguments.region:
        LOGGER.error("An AWS Region is required.")
        return 2

    try:
        results = ingest_dataset(
            source_path=arguments.file,
            bucket=arguments.bucket,
            prefix=arguments.prefix,
            region=arguments.region,
            dry_run=arguments.dry_run,
        )
    except (
        DatasetValidationError,
        FileNotFoundError,
        ValueError,
    ) as exc:
        LOGGER.error("Dataset ingestion validation failed: %s", exc)
        return 2
    except (BotoCoreError, ClientError) as exc:
        LOGGER.exception("S3 ingestion failed: %s", exc)
        return 1
    except OSError as exc:
        LOGGER.exception("Local file operation failed: %s", exc)
        return 1

    output = {
        "status": "planned" if arguments.dry_run else "uploaded",
        "bucket": arguments.bucket,
        "partition_count": len(results),
        "record_count": sum(
            result["record_count"] for result in results
        ),
        "objects": results,
    }

    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())