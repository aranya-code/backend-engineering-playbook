"""Document processing event handler.

Consumes document-processing messages from Amazon SQS and coordinates
document retrieval, processing, status updates, and failure handling.

The handler is designed for AWS Lambda SQS event-source mappings. Processing
logic is kept separate from the Lambda entry point to support unit testing
and local execution.
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Mapping
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from processing.document_processor import DocumentProcessor
from processing.processing_status import ProcessingStatus, ProcessingStatusManager

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

DEFAULT_MAX_EVENT_RECORDS = 100

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
METADATA_TABLE_NAME = os.getenv("METADATA_TABLE_NAME")
PROCESSING_STATUS_TABLE_NAME = os.getenv(
    "PROCESSING_STATUS_TABLE_NAME",
    METADATA_TABLE_NAME,
)

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
s3_client = boto3.client("s3", region_name=AWS_REGION)

metadata_table = (
    dynamodb.Table(METADATA_TABLE_NAME)
    if METADATA_TABLE_NAME
    else None
)

status_table = (
    dynamodb.Table(PROCESSING_STATUS_TABLE_NAME)
    if PROCESSING_STATUS_TABLE_NAME
    else None
)

document_processor = DocumentProcessor()


class ProcessingError(RuntimeError):
    """Raised when document processing cannot be completed."""


class ProcessingMessageError(ValueError):
    """Raised when an SQS processing message is invalid."""


def _required_mapping_value(
    mapping: Mapping[str, Any],
    key: str,
    *,
    field_name: str,
) -> str:
    """Return a required non-empty string from a message mapping."""
    value = mapping.get(key)

    if not isinstance(value, str) or not value.strip():
        raise ProcessingMessageError(
            f"Processing message field {field_name!r} "
            "must be a non-empty string."
        )

    return value


def _parse_message_body(body: str) -> dict[str, Any]:
    """Decode and validate an SQS processing message."""
    if not isinstance(body, str) or not body.strip():
        raise ProcessingMessageError(
            "SQS message body must be a non-empty string."
        )

    try:
        message = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ProcessingMessageError(
            "SQS message body contains invalid JSON."
        ) from exc

    if not isinstance(message, dict):
        raise ProcessingMessageError(
            "SQS message body must contain a JSON object."
        )

    required_fields = {
        "object_id": "object_id",
        "bucket_name": "bucket_name",
        "object_key": "object_key",
        "etag": "etag",
    }

    for field, field_name in required_fields.items():
        _required_mapping_value(
            message,
            field,
            field_name=field_name,
        )

    version_id = message.get("version_id")

    if version_id is not None and (
        not isinstance(version_id, str) or not version_id.strip()
    ):
        raise ProcessingMessageError(
            "Processing message field 'version_id' must be a "
            "non-empty string when provided."
        )

    return message


def _parse_sqs_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Extract and validate the message body from an SQS event record."""
    try:
        body = record["body"]
    except KeyError as exc:
        raise ProcessingMessageError(
            "SQS event record does not contain a message body."
        ) from exc

    return _parse_message_body(body)


def _build_s3_request(message: Mapping[str, Any]) -> dict[str, str]:
    """Build an S3 GetObject request from a validated message."""
    request = {
        "Bucket": str(message["bucket_name"]),
        "Key": str(message["object_key"]),
    }

    version_id = message.get("version_id")

    if version_id is not None:
        request["VersionId"] = str(version_id)

    return request


def _download_document(message: Mapping[str, Any]) -> bytes:
    """Retrieve the exact S3 object version referenced by the message."""
    request = _build_s3_request(message)

    try:
        response = s3_client.get_object(**request)
    except (ClientError, BotoCoreError) as exc:
        raise ProcessingError(
            "Failed to retrieve the document from S3."
        ) from exc

    body = response.get("Body")

    if body is None:
        raise ProcessingError(
            "S3 returned no response body for the requested document."
        )

    try:
        document_content = body.read()
    except Exception as exc:
        raise ProcessingError(
            "Failed to read the document response body."
        ) from exc
    finally:
        body.close()

    if not isinstance(document_content, bytes) or not document_content:
        raise ProcessingError(
            "Retrieved document is empty or has an invalid response body."
        )

    expected_etag = str(message["etag"]).strip('"')
    actual_etag = str(response.get("ETag", "")).strip('"')

    if expected_etag and actual_etag and expected_etag != actual_etag:
        raise ProcessingError(
            "Retrieved S3 object ETag does not match the processing message."
        )

    expected_version_id = message.get("version_id")
    actual_version_id = response.get("VersionId")

    if (
        expected_version_id is not None
        and actual_version_id != expected_version_id
    ):
        raise ProcessingError(
            "Retrieved S3 object version does not match the processing message."
        )

    return document_content


def _load_metadata_item(
    message: Mapping[str, Any],
) -> dict[str, Any]:
    """Retrieve the ingestion metadata record from DynamoDB."""
    if metadata_table is None:
        raise ProcessingError(
            "METADATA_TABLE_NAME is not configured."
        )

    try:
        response = metadata_table.get_item(
            Key={"object_id": message["object_id"]},
            ConsistentRead=True,
        )
    except (ClientError, BotoCoreError) as exc:
        raise ProcessingError(
            "Failed to retrieve document metadata from DynamoDB."
        ) from exc

    item = response.get("Item")

    if not isinstance(item, dict):
        raise ProcessingError(
            "No ingestion metadata record exists for the requested document."
        )

    if item.get("etag") != str(message["etag"]).strip('"'):
        raise ProcessingError(
            "DynamoDB metadata ETag does not match the processing message."
        )

    message_version_id = message.get("version_id")

    if (
        message_version_id is not None
        and item.get("version_id") != message_version_id
    ):
        raise ProcessingError(
            "DynamoDB metadata version does not match the processing message."
        )

    return item


def _build_status_manager() -> ProcessingStatusManager:
    """Create a processing status manager for the configured table."""
    if status_table is None:
        raise ProcessingError(
            "PROCESSING_STATUS_TABLE_NAME is not configured."
        )

    return ProcessingStatusManager(table=status_table)


def _update_processing_status(
    status_manager: ProcessingStatusManager,
    *,
    object_id: str,
    status: ProcessingStatus,
    message: str | None = None,
) -> None:
    """Persist a document processing status transition."""
    try:
        status_manager.update_status(
            object_id=object_id,
            status=status,
            message=message,
        )
    except (ClientError, BotoCoreError, ValueError) as exc:
        raise ProcessingError(
            f"Failed to update processing status to {status.value}."
        ) from exc


def _mark_processing_failed(
    status_manager: ProcessingStatusManager,
    *,
    object_id: str,
    error: Exception,
) -> None:
    """Record a failed processing attempt without masking the original error."""
    try:
        _update_processing_status(
            status_manager,
            object_id=object_id,
            status=ProcessingStatus.FAILED,
            message=type(error).__name__,
        )
    except ProcessingError:
        logger.exception(
            "Failed to persist document processing failure status.",
            extra={"object_id": object_id},
        )


def process_document_message(
    message: Mapping[str, Any],
) -> dict[str, Any]:
    """Process one validated document-processing message.

    The method retrieves the original object, loads its ingestion metadata,
    invokes the document processor, and records the resulting status.

    Args:
        message: Validated SQS processing message.

    Returns:
        A dictionary containing the object identifier and final status.

    Raises:
        ProcessingMessageError: If the message is invalid.
        ProcessingError: If retrieval, processing, or status persistence fails.
    """
    normalized_message = _parse_message_body(
        json.dumps(dict(message))
    )

    object_id = normalized_message["object_id"]

    status_manager = _build_status_manager()

    logger.info(
        "Starting document processing.",
        extra={
            "object_id": object_id,
            "bucket_name": normalized_message["bucket_name"],
            "object_key": normalized_message["object_key"],
        },
    )

    _update_processing_status(
        status_manager,
        object_id=object_id,
        status=ProcessingStatus.PROCESSING,
    )

    try:
        metadata_item = _load_metadata_item(normalized_message)
        document_content = _download_document(normalized_message)

        processing_result = document_processor.process_document(
            document=document_content,
            metadata=metadata_item.get("metadata", {}),
            filename=normalized_message["object_key"].rsplit(
                "/",
                maxsplit=1,
            )[-1],
            content_type=metadata_item["content_type"],
        )

        if not isinstance(processing_result, Mapping):
            raise ProcessingError(
                "Document processor returned an invalid result."
            )

        _update_processing_status(
            status_manager,
            object_id=object_id,
            status=ProcessingStatus.COMPLETED,
        )

        logger.info(
            "Document processing completed.",
            extra={
                "object_id": object_id,
                "bucket_name": normalized_message["bucket_name"],
                "object_key": normalized_message["object_key"],
            },
        )

        return {
            "object_id": object_id,
            "processing_status": ProcessingStatus.COMPLETED.value,
            "result": dict(processing_result),
        }

    except Exception as exc:
        _mark_processing_failed(
            status_manager,
            object_id=object_id,
            error=exc,
        )

        logger.exception(
            "Document processing failed.",
            extra={
                "object_id": object_id,
                "bucket_name": normalized_message["bucket_name"],
                "object_key": normalized_message["object_key"],
            },
        )

        if isinstance(exc, (ProcessingError, ProcessingMessageError)):
            raise

        raise ProcessingError(
            f"Document processing failed for object {object_id!r}."
        ) from exc


def process_sqs_record(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and process one SQS event record."""
    message = _parse_sqs_record(record)

    return process_document_message(message)


def lambda_handler(
    event: Mapping[str, Any],
    context: Any,
) -> dict[str, Any]:
    """AWS Lambda entry point for an SQS event-source mapping.

    Uses Lambda partial batch response semantics. Failed message identifiers
    are returned in ``batchItemFailures`` so the event source mapping can
    retry individual messages without retrying successful records.

    The event source mapping must enable ``ReportBatchItemFailures`` for
    partial batch responses to be honored.
    """
    del context

    records = event.get("Records")

    if not isinstance(records, list) or not records:
        raise ValueError(
            "SQS event must contain a non-empty Records list."
        )

    if len(records) > DEFAULT_MAX_EVENT_RECORDS:
        raise ValueError(
            f"Event contains more than {DEFAULT_MAX_EVENT_RECORDS} records."
        )

    processed_count = 0
    batch_item_failures: list[dict[str, str]] = []

    for record in records:
        if not isinstance(record, Mapping):
            logger.error("Received an invalid SQS event record.")
            continue

        message_id = record.get("messageId")

        if not isinstance(message_id, str) or not message_id:
            logger.error(
                "SQS event record does not contain a valid messageId."
            )
            continue

        try:
            result = process_sqs_record(record)
            processed_count += 1

            logger.info(
                "SQS message processed successfully.",
                extra={
                    "message_id": message_id,
                    "object_id": result["object_id"],
                },
            )

        except (
            BotoCoreError,
            ClientError,
            ProcessingError,
            ProcessingMessageError,
            ValueError,
        ) as exc:
            logger.exception(
                "SQS message processing failed.",
                extra={"message_id": message_id},
            )

            batch_item_failures.append(
                {"itemIdentifier": message_id}
            )

    return {
        "batchItemFailures": batch_item_failures,
        "processed_count": processed_count,
        "failed_count": len(batch_item_failures),
    }