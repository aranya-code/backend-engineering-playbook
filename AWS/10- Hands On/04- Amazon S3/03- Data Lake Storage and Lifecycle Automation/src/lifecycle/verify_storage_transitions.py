#!/usr/bin/env python3
"""Verify S3 object storage classes and lifecycle transition outcomes."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


LOGGER = logging.getLogger("data_lake.lifecycle")

DEFAULT_REGION = os.getenv("AWS_REGION", "ap-south-1")
DEFAULT_BUCKET_NAME = os.getenv("DATA_LAKE_BUCKET_NAME")
DEFAULT_PREFIX = os.getenv("DATA_LAKE_RAW_PREFIX", "raw/events")

DEFAULT_PAGE_SIZE = 1000
MAX_PAGE_SIZE = 1000

KNOWN_STORAGE_CLASSES = {
    "STANDARD",
    "REDUCED_REDUNDANCY",
    "STANDARD_IA",
    "ONEZONE_IA",
    "INTELLIGENT_TIERING",
    "GLACIER",
    "DEEP_ARCHIVE",
    "GLACIER_IR",
    "EXPRESS_ONEZONE",
}


class StorageTransitionVerificationError(RuntimeError):
    """Raised when storage transition verification cannot be completed."""


def configure_logging(verbose: bool = False) -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def validate_bucket_name(bucket_name: str) -> str:
    """Validate the configured S3 bucket name."""
    normalized_name = bucket_name.strip()

    if not normalized_name:
        raise ValueError("S3 bucket name cannot be empty.")

    if normalized_name.startswith("s3://"):
        raise ValueError(
            "Provide a bucket name, not an S3 URI."
        )

    if "/" in normalized_name:
        raise ValueError(
            "Bucket name must not contain an object key or prefix."
        )

    return normalized_name


def validate_region(region: str) -> str:
    """Validate and normalize the AWS Region."""
    normalized_region = region.strip()

    if not normalized_region:
        raise ValueError("AWS Region cannot be empty.")

    return normalized_region


def validate_prefix(prefix: str | None) -> str:
    """Normalize an optional object-key prefix."""
    if prefix is None:
        return ""

    normalized_prefix = prefix.strip().lstrip("/")

    if normalized_prefix.startswith("s3://"):
        raise ValueError(
            "Prefix must be an object-key prefix, not an S3 URI."
        )

    return normalized_prefix


def validate_page_size(page_size: int) -> int:
    """Validate the maximum number of objects requested per page."""
    if not 1 <= page_size <= MAX_PAGE_SIZE:
        raise ValueError(
            f"Page size must be between 1 and {MAX_PAGE_SIZE}."
        )

    return page_size


def validate_max_objects(max_objects: int | None) -> int | None:
    """Validate an optional object inspection limit."""
    if max_objects is not None and max_objects < 1:
        raise ValueError("Maximum object count must be positive.")

    return max_objects


def create_s3_client(region: str) -> Any:
    """Create an S3 client using the standard AWS credential chain."""
    client_config = Config(
        retries={
            "mode": "standard",
            "max_attempts": 5,
        },
        connect_timeout=10,
        read_timeout=60,
    )

    return boto3.client(
        "s3",
        region_name=region,
        config=client_config,
    )


def get_bucket_versioning(
    s3_client: Any,
    bucket_name: str,
) -> str:
    """Return the bucket versioning state."""
    response = s3_client.get_bucket_versioning(
        Bucket=bucket_name,
    )

    return response.get("Status", "Disabled")


def get_object_storage_class(
    s3_client: Any,
    bucket_name: str,
    object_key: str,
    version_id: str | None = None,
) -> str:
    """Retrieve the storage class of an object or object version."""
    request: dict[str, Any] = {
        "Bucket": bucket_name,
        "Key": object_key,
    }

    if version_id:
        request["VersionId"] = version_id

    response = s3_client.head_object(**request)

    return response.get("StorageClass", "STANDARD")


def list_current_objects(
    s3_client: Any,
    bucket_name: str,
    prefix: str,
    page_size: int,
    max_objects: int | None = None,
):
    """
    Yield current object metadata using ListObjectsV2 pagination.

    This enumerates current objects only. It does not inspect
    noncurrent versions or delete markers.
    """
    paginator = s3_client.get_paginator("list_objects_v2")

    pagination_config: dict[str, Any] = {
        "PageSize": page_size,
    }

    if max_objects is not None:
        pagination_config["MaxItems"] = max_objects

    pages = paginator.paginate(
        Bucket=bucket_name,
        Prefix=prefix,
        PaginationConfig=pagination_config,
    )

    for page in pages:
        for object_metadata in page.get("Contents", []):
            yield object_metadata


def list_object_versions(
    s3_client: Any,
    bucket_name: str,
    prefix: str,
    page_size: int,
    max_objects: int | None = None,
):
    """
    Yield object versions and delete markers.

    The paginator is used only when version inspection is requested.
    Each yielded record identifies whether it represents a current
    version or a noncurrent version.
    """
    paginator = s3_client.get_paginator("list_object_versions")

    pagination_config: dict[str, Any] = {
        "PageSize": page_size,
    }

    if max_objects is not None:
        pagination_config["MaxItems"] = max_objects

    pages = paginator.paginate(
        Bucket=bucket_name,
        Prefix=prefix,
        PaginationConfig=pagination_config,
    )

    for page in pages:
        for version in page.get("Versions", []):
            yield {
                "record_type": "version",
                "key": version["Key"],
                "version_id": version.get("VersionId"),
                "is_latest": version.get("IsLatest", False),
                "last_modified": version.get("LastModified"),
                "size": version.get("Size", 0),
                "storage_class": version.get(
                    "StorageClass",
                    "STANDARD",
                ),
            }

        for marker in page.get("DeleteMarkers", []):
            yield {
                "record_type": "delete_marker",
                "key": marker["Key"],
                "version_id": marker.get("VersionId"),
                "is_latest": marker.get("IsLatest", False),
                "last_modified": marker.get("LastModified"),
                "size": 0,
                "storage_class": None,
            }


def inspect_object(
    s3_client: Any,
    bucket_name: str,
    object_record: dict[str, Any],
) -> dict[str, Any]:
    """
    Inspect an object or version using HeadObject.

    List operations provide storage-class metadata. HeadObject is used
    to verify the object metadata for the exact version when possible.
    """
    record_type = object_record.get("record_type", "current")

    if record_type == "delete_marker":
        return {
            **object_record,
            "head_status": "not_applicable",
            "head_error": None,
        }

    request: dict[str, Any] = {
        "Bucket": bucket_name,
        "Key": object_record["key"],
    }

    version_id = object_record.get("version_id")

    if version_id:
        request["VersionId"] = version_id

    try:
        response = s3_client.head_object(**request)
    except ClientError as exc:
        error = exc.response.get("Error", {})
        error_code = error.get("Code", "Unknown")

        return {
            **object_record,
            "head_status": "failed",
            "head_error": {
                "code": error_code,
                "message": error.get("Message", str(exc)),
            },
        }

    storage_class = response.get("StorageClass", "STANDARD")

    return {
        **object_record,
        "size": response.get(
            "ContentLength",
            object_record.get("size", 0),
        ),
        "storage_class": storage_class,
        "last_modified": response.get(
            "LastModified",
            object_record.get("last_modified"),
        ),
        "etag": response.get("ETag"),
        "server_side_encryption": response.get(
            "ServerSideEncryption"
        ),
        "ssekms_key_id": response.get("SSEKMSKeyId"),
        "head_status": "verified",
        "head_error": None,
    }


def normalize_timestamp(value: Any) -> str | None:
    """Convert a datetime or timestamp-like value to ISO 8601."""
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()

    if value is None:
        return None

    return str(value)


def summarize_objects(
    objects: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build aggregate storage-class and inspection statistics."""
    storage_class_counts: Counter[str] = Counter()
    storage_class_bytes: Counter[str] = Counter()
    record_type_counts: Counter[str] = Counter()

    verified_count = 0
    failed_count = 0
    delete_marker_count = 0
    total_bytes = 0

    for item in objects:
        record_type = item.get("record_type", "current")
        record_type_counts[record_type] += 1

        if record_type == "delete_marker":
            delete_marker_count += 1
            continue

        storage_class = item.get("storage_class", "STANDARD")
        size = int(item.get("size", 0))

        storage_class_counts[storage_class] += 1
        storage_class_bytes[storage_class] += size
        total_bytes += size

        if item.get("head_status") == "verified":
            verified_count += 1
        elif item.get("head_status") == "failed":
            failed_count += 1

    return {
        "object_count": sum(
            count
            for record_type, count in record_type_counts.items()
            if record_type != "delete_marker"
        ),
        "delete_marker_count": delete_marker_count,
        "verified_count": verified_count,
        "head_failure_count": failed_count,
        "total_bytes": total_bytes,
        "storage_class_counts": dict(
            sorted(storage_class_counts.items())
        ),
        "storage_class_bytes": dict(
            sorted(storage_class_bytes.items())
        ),
        "record_type_counts": dict(
            sorted(record_type_counts.items())
        ),
    }


def evaluate_transition_expectations(
    objects: list[dict[str, Any]],
    expected_storage_class: str | None,
) -> list[dict[str, Any]]:
    """
    Compare inspected objects with an optional expected storage class.

    This verifies current object metadata. It does not infer whether an
    object should already have transitioned based on lifecycle age.
    """
    findings: list[dict[str, Any]] = []

    if expected_storage_class is None:
        return findings

    normalized_expected = expected_storage_class.strip().upper()

    if normalized_expected not in KNOWN_STORAGE_CLASSES:
        raise ValueError(
            f"Unsupported expected storage class: "
            f"{expected_storage_class!r}."
        )

    for item in objects:
        if item.get("record_type") == "delete_marker":
            continue

        if item.get("head_status") != "verified":
            findings.append(
                {
                    "severity": "error",
                    "key": item["key"],
                    "version_id": item.get("version_id"),
                    "message": (
                        "Object metadata could not be verified. "
                        "Expected storage class cannot be confirmed."
                    ),
                }
            )
            continue

        actual_storage_class = item.get(
            "storage_class",
            "STANDARD",
        )

        if actual_storage_class != normalized_expected:
            findings.append(
                {
                    "severity": "warning",
                    "key": item["key"],
                    "version_id": item.get("version_id"),
                    "expected_storage_class": normalized_expected,
                    "actual_storage_class": actual_storage_class,
                    "message": (
                        "Object storage class differs from the "
                        "configured expectation."
                    ),
                }
            )

    return findings


def verify_storage_transitions(
    bucket_name: str,
    region: str,
    prefix: str = "",
    page_size: int = DEFAULT_PAGE_SIZE,
    max_objects: int | None = None,
    include_versions: bool = False,
    expected_storage_class: str | None = None,
) -> dict[str, Any]:
    """
    Inspect S3 storage classes for current objects or object versions.

    The operation is read-only. It does not modify lifecycle rules,
    initiate transitions, restore archived objects, or delete data.
    """
    s3_client = create_s3_client(region)

    versioning_status = get_bucket_versioning(
        s3_client=s3_client,
        bucket_name=bucket_name,
    )

    if include_versions:
        raw_records = list(
            list_object_versions(
                s3_client=s3_client,
                bucket_name=bucket_name,
                prefix=prefix,
                page_size=page_size,
                max_objects=max_objects,
            )
        )
    else:
        raw_records = [
            {
                "record_type": "current",
                "key": object_metadata["Key"],
                "version_id": None,
                "is_latest": True,
                "last_modified": object_metadata.get("LastModified"),
                "size": object_metadata.get("Size", 0),
                "storage_class": object_metadata.get(
                    "StorageClass",
                    "STANDARD",
                ),
            }
            for object_metadata in list_current_objects(
                s3_client=s3_client,
                bucket_name=bucket_name,
                prefix=prefix,
                page_size=page_size,
                max_objects=max_objects,
            )
        ]

    inspected_objects = [
        inspect_object(
            s3_client=s3_client,
            bucket_name=bucket_name,
            object_record=record,
        )
        for record in raw_records
    ]

    findings = evaluate_transition_expectations(
        objects=inspected_objects,
        expected_storage_class=expected_storage_class,
    )

    summary = summarize_objects(inspected_objects)

    head_failure_count = summary["head_failure_count"]

    if head_failure_count:
        status = "completed_with_errors"
    elif any(
        finding["severity"] == "warning"
        for finding in findings
    ):
        status = "completed_with_warnings"
    else:
        status = "passed"

    return {
        "status": status,
        "bucket": bucket_name,
        "region": region,
        "prefix": prefix,
        "evaluated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "versioning_status": versioning_status,
        "inspection_mode": (
            "all_versions_and_delete_markers"
            if include_versions
            else "current_objects_only"
        ),
        "expected_storage_class": (
            expected_storage_class.strip().upper()
            if expected_storage_class
            else None
        ),
        "page_size": page_size,
        "max_objects": max_objects,
        "summary": summary,
        "findings": findings,
        "objects": [
            {
                **item,
                "last_modified": normalize_timestamp(
                    item.get("last_modified")
                ),
            }
            for item in inspected_objects
        ],
        "limitations": [
            (
                "Lifecycle transitions are asynchronous. A configured "
                "transition date does not guarantee that an object will "
                "change storage class at that exact time."
            ),
            (
                "This tool reports the storage class currently recorded "
                "for each inspected object or version."
            ),
            (
                "An expected storage class is a caller-supplied check, "
                "not a prediction derived from lifecycle rules."
            ),
            (
                "Object eligibility can depend on filters, tags, object "
                "size, version state, minimum storage duration, and "
                "other lifecycle constraints."
            ),
            (
                "Archived objects may require a restore request before "
                "their contents can be retrieved. This verifier does "
                "not initiate restores."
            ),
            (
                "Large buckets can require substantial LIST and HEAD "
                "requests. Use --prefix and --max-objects to constrain "
                "inspection scope."
            ),
        ],
    }


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Verify current S3 object storage classes and inspect "
            "lifecycle transition outcomes."
        )
    )
    parser.add_argument(
        "--bucket",
        default=DEFAULT_BUCKET_NAME,
        help=(
            "S3 bucket name. Defaults to DATA_LAKE_BUCKET_NAME."
        ),
    )
    parser.add_argument(
        "--region",
        default=DEFAULT_REGION,
        help=f"AWS Region. Default: {DEFAULT_REGION}",
    )
    parser.add_argument(
        "--prefix",
        default=DEFAULT_PREFIX,
        help=(
            "Object-key prefix to inspect. "
            f"Default: {DEFAULT_PREFIX}"
        ),
    )
    parser.add_argument(
        "--expected-storage-class",
        choices=sorted(KNOWN_STORAGE_CLASSES),
        default=None,
        help=(
            "Optional expected storage class. Objects that differ "
            "from this class are reported as warnings."
        ),
    )
    parser.add_argument(
        "--include-versions",
        action="store_true",
        help=(
            "Inspect object versions and delete markers instead of "
            "current objects only."
        ),
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help=(
            "Maximum objects requested per listing page. "
            f"Range: 1-{MAX_PAGE_SIZE}."
        ),
    )
    parser.add_argument(
        "--max-objects",
        type=int,
        default=None,
        help=(
            "Optional maximum number of records to inspect. "
            "Useful for bounded checks on large buckets."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging.",
    )

    return parser.parse_args()


def main() -> int:
    """Execute S3 storage transition verification."""
    arguments = parse_arguments()
    configure_logging(arguments.verbose)

    try:
        if not arguments.bucket:
            raise ValueError(
                "S3 bucket is required. Set DATA_LAKE_BUCKET_NAME "
                "or provide --bucket."
            )

        bucket_name = validate_bucket_name(arguments.bucket)
        region = validate_region(arguments.region)
        prefix = validate_prefix(arguments.prefix)
        page_size = validate_page_size(arguments.page_size)
        max_objects = validate_max_objects(arguments.max_objects)

        LOGGER.info(
            "Inspecting S3 storage classes in bucket %s with prefix %r.",
            bucket_name,
            prefix,
        )

        result = verify_storage_transitions(
            bucket_name=bucket_name,
            region=region,
            prefix=prefix,
            page_size=page_size,
            max_objects=max_objects,
            include_versions=arguments.include_versions,
            expected_storage_class=arguments.expected_storage_class,
        )

    except ValueError as exc:
        LOGGER.error("Invalid configuration: %s", exc)
        return 1
    except StorageTransitionVerificationError as exc:
        LOGGER.error("%s", exc)
        return 1
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get(
            "Code",
            "Unknown",
        )
        error_message = exc.response.get("Error", {}).get(
            "Message",
            str(exc),
        )
        LOGGER.error(
            "AWS S3 request failed: %s: %s",
            error_code,
            error_message,
        )
        return 1
    except BotoCoreError as exc:
        LOGGER.error("AWS SDK request failed: %s", exc)
        return 1

    print(json.dumps(result, indent=2, default=str))

    if result["status"] == "completed_with_errors":
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())