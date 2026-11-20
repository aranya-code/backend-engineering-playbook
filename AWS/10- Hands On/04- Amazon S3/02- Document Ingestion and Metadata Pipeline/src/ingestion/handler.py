"""S3 document ingestion event handler.

This module processes S3 ObjectCreated events and coordinates document
validation, metadata extraction, storage inspection, and downstream event
publication.

The handler is designed for AWS Lambda but keeps its processing logic
independent of the Lambda runtime so it can also be tested locally.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.parse
from collections.abc import Mapping
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from ingestion.document_validator import DocumentValidationError, DocumentValidator
from ingestion.metadata_extractor import MetadataExtractor
from ingestion.s3_storage import S3Storage

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

DEFAULT_MAX_EVENT_RECORDS = 100
DEFAULT_MAX_OBJECT_SIZE_BYTES = 50 * 1024 * 1024

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
METADATA_TABLE_NAME = os.getenv("METADATA_TABLE_NAME")
PROCESSING_QUEUE_URL = os.getenv("PROCESSING_QUEUE_URL")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
sqs = boto3.client("sqs", region_name=AWS_REGION)

metadata_table = (
    dynamodb.Table(METADATA_TABLE_NAME)
    if METADATA_TABLE_NAME
    else None
)

s3_storage = S3Storage()
document_validator = DocumentValidator()
metadata_extractor = MetadataExtractor()


class IngestionError(RuntimeError):
    """Raised when an S3 document ingestion operation fails."""


def _required_environment_variable(name: str) -> str:
    """Return a required environment variable."""
    value = os.getenv(name)

    if not value:
        raise IngestionError(
            f"Required environment variable {name!r} is not configured."
        )

    return value


def _decode_s3_object_key(raw_key: str) -> str:
    """Decode an S3 event object key using form-style URL decoding."""
    if not raw_key:
        raise ValueError("S3 event object key cannot be empty.")

    return urllib.parse.unquote_plus(raw_key, encoding="utf-8")


def _parse_s3_record(record: Mapping[str, Any]) -> tuple[str, str]:
    """Extract and validate the bucket name and object key from an event."""
    try:
        s3_data = record["s3"]
        bucket_name = s3_data["bucket"]["name"]
        raw_key = s3_data["object"]["key"]
    except (KeyError, TypeError) as exc:
        raise ValueError("Invalid S3 event record structure.") from exc

    if not isinstance(bucket_name, str) or not bucket_name:
        raise ValueError("S3 event contains an invalid bucket name.")

    if not isinstance(raw_key, str):
        raise ValueError("S3 event contains an invalid object key.")

    return bucket_name, _decode_s3_object_key(raw_key)


def _parse_object_size(record: Mapping[str, Any]) -> int | None:
    """Extract the object size from an S3 event record."""
    try:
        size = record["s3"]["object"].get("size")
    except (KeyError, TypeError, AttributeError):
        return None

    if size is None:
        return None

    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise ValueError("S3 event contains an invalid object size.")

    return size


def _get_s3_client() -> Any:
    """Return an S3 client using the configured AWS credential chain."""
    return boto3.client("s3", region_name=AWS_REGION)


def _verify_object_size(
    bucket_name: str,
    object_key: str,
    event_size: int | None,
) -> dict[str, Any]:
    """Retrieve authoritative object metadata and enforce size constraints."""
    head_response = s3_storage.head_object(
        bucket_name=bucket_name,
        object_key=object_key,
    )

    actual_size = head_response.get("ContentLength")

    if (
        isinstance(actual_size, bool)
        or not isinstance(actual_size, int)
        or actual_size < 0
    ):
        raise IngestionError(
            f"S3 returned an invalid object size for {object_key!r}."
        )

    if event_size is not None and event_size != actual_size:
        raise IngestionError(
            f"Object size mismatch for {object_key!r}: "
            f"event reported {event_size}, S3 reported {actual_size}."
        )

    max_size = int(
        os.getenv(
            "MAX_DOCUMENT_SIZE_BYTES",
            str(DEFAULT_MAX_OBJECT_SIZE_BYTES),
        )
    )

    if actual_size > max_size:
        raise DocumentValidationError(
            f"Document exceeds the maximum allowed size of {max_size} bytes."
        )

    return head_response


def _build_metadata_item(
    bucket_name: str,
    object_key: str,
    object_metadata: Mapping[str, Any],
    extracted_metadata: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the metadata record persisted in DynamoDB."""
    etag = object_metadata.get("ETag", "")
    version_id = object_metadata.get("VersionId")

    item: dict[str, Any] = {
        "object_id": f"{bucket_name}/{object_key}",
        "bucket_name": bucket_name,
        "object_key": object_key,
        "size_bytes": int(object_metadata["ContentLength"]),
        "content_type": object_metadata.get(
            "ContentType",
            "application/octet-stream",
        ),
        "etag": etag.strip('"') if isinstance(etag, str) else "",
        "metadata": dict(extracted_metadata),
        "processing_status": "PENDING",
    }

    if version_id is not None:
        item["version_id"] = version_id

    last_modified = object_metadata.get("LastModified")

    if last_modified is not None:
        item["last_modified"] = last_modified.isoformat()

    return item


def _persist_metadata(item: Mapping[str, Any]) -> None:
    """Persist extracted document metadata in DynamoDB."""
    if metadata_table is None:
        raise IngestionError(
            "METADATA_TABLE_NAME is not configured."
        )

    try:
        metadata_table.put_item(
            Item=dict(item),
            ConditionExpression=(
                "attribute_not_exists(object_id) "
                "OR etag = :etag"
            ),
            ExpressionAttributeValues={
                ":etag": item["etag"],
            },
        )
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")

        if error_code == "ConditionalCheckFailedException":
            logger.info(
                "Metadata record already exists with the same ETag.",
                extra={
                    "bucket_name": item["bucket_name"],
                    "object_key": item["object_key"],
                    "etag": item["etag"],
                },
            )
            return

        raise IngestionError(
            "Failed to persist document metadata."
        ) from exc


def _publish_processing_event(item: Mapping[str, Any]) -> None:
    """Publish a document processing message to SQS."""
    if not PROCESSING_QUEUE_URL:
        raise IngestionError(
            "PROCESSING_QUEUE_URL is not configured."
        )

    message = {
        "object_id": item["object_id"],
        "bucket_name": item["bucket_name"],
        "object_key": item["object_key"],
        "etag": item["etag"],
        "version_id": item.get("version_id"),
    }

    try:
        sqs.send_message(
            QueueUrl=PROCESSING_QUEUE_URL,
            MessageBody=json.dumps(message),
        )
    except (ClientError, BotoCoreError) as exc:
        raise IngestionError(
            "Failed to publish document processing event."
        ) from exc


def process_document_record(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and ingest one S3 ObjectCreated event record."""
    bucket_name, object_key = _parse_s3_record(record)
    event_size = _parse_object_size(record)

    logger.info(
        "Starting document ingestion.",
        extra={
            "bucket_name": bucket_name,
            "object_key": object_key,
        },
    )

    object_metadata = _verify_object_size(
        bucket_name=bucket_name,
        object_key=object_key,
        event_size=event_size,
    )

    content_type = object_metadata.get(
        "ContentType",
        "application/octet-stream",
    )

    document_validator.validate_document(
        filename=object_key.rsplit("/", maxsplit=1)[-1],
        content_type=content_type,
        size_bytes=object_metadata["ContentLength"],
    )

    document_content = s3_storage.get_object(
        bucket_name=bucket_name,
        object_key=object_key,
    )

    extracted_metadata = metadata_extractor.extract_metadata(
        document=document_content,
        filename=object_key.rsplit("/", maxsplit=1)[-1],
        content_type=content_type,
    )

    metadata_item = _build_metadata_item(
        bucket_name=bucket_name,
        object_key=object_key,
        object_metadata=object_metadata,
        extracted_metadata=extracted_metadata,
    )

    _persist_metadata(metadata_item)
    _publish_processing_event(metadata_item)

    logger.info(
        "Document ingestion completed.",
        extra={
            "bucket_name": bucket_name,
            "object_key": object_key,
            "etag": metadata_item["etag"],
        },
    )

    return {
        "object_id": metadata_item["object_id"],
        "processing_status": metadata_item["processing_status"],
    }


def lambda_handler(
    event: Mapping[str, Any],
    context: Any,
) -> dict[str, Any]:
    """AWS Lambda entry point for S3 ObjectCreated notifications.

    Raises an exception when any record fails so the invoking event source
    can apply its configured retry and failure-handling behavior.
    """
    del context

    records = event.get("Records")

    if not isinstance(records, list) or not records:
        raise ValueError("Event must contain a non-empty Records list.")

    if len(records) > DEFAULT_MAX_EVENT_RECORDS:
        raise ValueError(
            f"Event contains more than {DEFAULT_MAX_EVENT_RECORDS} records."
        )

    processed_records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for record in records:
        if not isinstance(record, Mapping):
            failures.append(
                {
                    "object_key": "<unknown>",
                    "error": "Invalid S3 event record.",
                }
            )
            continue

        try:
            result = process_document_record(record)
            processed_records.append(result)
        except (
            BotoCoreError,
            ClientError,
            DocumentValidationError,
            IngestionError,
            ValueError,
        ) as exc:
            try:
                bucket_name, object_key = _parse_s3_record(record)
            except (ValueError, KeyError, TypeError):
                bucket_name = "<unknown>"
                object_key = "<unknown>"

            logger.exception(
                "Document ingestion failed.",
                extra={
                    "bucket_name": bucket_name,
                    "object_key": object_key,
                },
            )

            failures.append(
                {
                    "object_key": object_key,
                    "error": type(exc).__name__,
                }
            )

    if failures:
        raise IngestionError(
            f"Document ingestion failed for {len(failures)} "
            f"of {len(records)} S3 event records: "
            f"{json.dumps(failures)}"
        )

    return {
        "status": "SUCCESS",
        "processed_count": len(processed_records),
        "records": processed_records,
    }