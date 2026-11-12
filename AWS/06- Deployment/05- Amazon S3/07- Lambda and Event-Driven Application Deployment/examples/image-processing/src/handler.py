"""AWS Lambda handler for S3-triggered image processing.

Supported invocation formats:
- SQS messages containing S3 event notification payloads.
- Direct S3 event notifications (useful for local testing).

The handler delegates image transformation to ``image_transformer``.
That module must expose:

    create_thumbnail(image_bytes: bytes) -> tuple[bytes, str]

The return value contains the transformed image bytes and their MIME type.

For SQS event source mappings, enable ReportBatchItemFailures so that
failed messages can be retried independently.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote_plus

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from image_transformer import create_thumbnail


logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the image-processing function."""

    output_bucket: str
    input_bucket: str | None
    input_prefix: str
    output_prefix: str
    max_input_size_bytes: int

    @classmethod
    def from_environment(cls) -> Settings:
        """Load and validate configuration from Lambda environment variables."""

        output_bucket = os.getenv("OUTPUT_BUCKET", "").strip()

        if not output_bucket:
            raise ValueError("OUTPUT_BUCKET environment variable is required")

        input_bucket = os.getenv("INPUT_BUCKET", "").strip() or None

        input_prefix = os.getenv("INPUT_PREFIX", "uploads/").strip()
        output_prefix = os.getenv("OUTPUT_PREFIX", "processed/").strip()

        max_input_size_mb = int(
            os.getenv("MAX_INPUT_SIZE_MB", "10")
        )

        if max_input_size_mb <= 0:
            raise ValueError("MAX_INPUT_SIZE_MB must be greater than zero")

        if input_prefix and not input_prefix.endswith("/"):
            input_prefix += "/"

        if output_prefix and not output_prefix.endswith("/"):
            output_prefix += "/"

        if input_prefix == output_prefix:
            raise ValueError(
                "INPUT_PREFIX and OUTPUT_PREFIX must be different"
            )

        return cls(
            output_bucket=output_bucket,
            input_bucket=input_bucket,
            input_prefix=input_prefix,
            output_prefix=output_prefix,
            max_input_size_bytes=max_input_size_mb * 1024 * 1024,
        )


def create_s3_client():
    """Create a reusable S3 client with bounded retry behavior."""

    config = Config(
        retries={
            "mode": "standard",
            "max_attempts": 3,
        },
        connect_timeout=5,
        read_timeout=30,
    )

    return boto3.client("s3", config=config)


# Reuse the SDK client across warm Lambda invocations.
s3_client = create_s3_client()


def log_event(
    level: int,
    message: str,
    **context: Any,
) -> None:
    """Write structured context through the Lambda logging system."""

    logger.log(
        level,
        json.dumps(
            {
                "message": message,
                **context,
            },
            default=str,
        ),
    )


def extract_s3_records(event: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract S3 records from an SQS or direct S3 event."""

    if "Records" not in event:
        raise ValueError("Event does not contain a Records collection")

    records = event["Records"]

    if not isinstance(records, list):
        raise ValueError("Event Records must be a list")

    if not records:
        raise ValueError("Event Records collection is empty")

    s3_records = []

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Event record must be a JSON object")

        event_source = record.get("eventSource")

        if event_source == "aws:sqs":
            body = record.get("body")

            if not isinstance(body, str):
                raise ValueError("SQS message body must be a string")

            try:
                message = json.loads(body)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    "SQS message body contains invalid JSON"
                ) from exc

            if not isinstance(message, dict):
                raise ValueError("SQS message body must contain a JSON object")

            if message.get("Event") == "s3:TestEvent":
                log_event(
                    logging.INFO,
                    "Ignoring S3 test notification",
                    message_id=record.get("messageId"),
                )
                continue

            nested_records = message.get("Records")

            if not isinstance(nested_records, list):
                raise ValueError(
                    "SQS message does not contain S3 event Records"
                )

            s3_records.extend(nested_records)
            continue

        if event_source == "aws:s3":
            s3_records.append(record)
            continue

        raise ValueError(
            f"Unsupported event source: {event_source!r}"
        )

    return s3_records


def validate_s3_record(
    record: dict[str, Any],
    settings: Settings,
) -> tuple[str, str, str]:
    """Validate an S3 object-created event and return its identifiers."""

    if record.get("eventSource") != "aws:s3":
        raise ValueError("Record is not an S3 event")

    event_name = record.get("eventName", "")

    if not event_name.startswith("ObjectCreated:"):
        raise ValueError(
            f"Unsupported S3 event type: {event_name!r}"
        )

    s3_data = record.get("s3")

    if not isinstance(s3_data, dict):
        raise ValueError("S3 event does not contain an s3 object")

    bucket_data = s3_data.get("bucket", {})
    object_data = s3_data.get("object", {})

    bucket_name = bucket_data.get("name")
    encoded_key = object_data.get("key")

    if not isinstance(bucket_name, str) or not bucket_name:
        raise ValueError("S3 event contains an invalid bucket name")

    if not isinstance(encoded_key, str) or not encoded_key:
        raise ValueError("S3 event contains an invalid object key")

    object_key = unquote_plus(encoded_key)

    if not object_key:
        raise ValueError("Decoded S3 object key is empty")

    if settings.input_bucket and bucket_name != settings.input_bucket:
        raise ValueError(
            f"Unexpected source bucket: {bucket_name!r}"
        )

    if not object_key.startswith(settings.input_prefix):
        raise ValueError(
            f"Object key is outside the configured input prefix: "
            f"{object_key!r}"
        )

    if object_key.startswith(settings.output_prefix):
        raise ValueError(
            "Input object must not be inside the output prefix"
        )

    if object_data.get("size", 0) <= 0:
        raise ValueError("Input object is empty or has an invalid size")

    return bucket_name, object_key, event_name


def read_source_object(
    bucket_name: str,
    object_key: str,
    settings: Settings,
) -> bytes:
    """Read an S3 object while enforcing the configured size limit."""

    response = s3_client.get_object(
        Bucket=bucket_name,
        Key=object_key,
    )

    content_length = response.get("ContentLength")

    if content_length is None or content_length <= 0:
        raise ValueError(
            f"Source object has an invalid content length: {object_key}"
        )

    if content_length > settings.max_input_size_bytes:
        raise ValueError(
            f"Source object exceeds the configured limit of "
            f"{settings.max_input_size_bytes} bytes"
        )

    body = response["Body"]

    try:
        image_bytes = body.read(settings.max_input_size_bytes + 1)
    finally:
        body.close()

    if not image_bytes:
        raise ValueError(f"Source object is empty: {object_key}")

    if len(image_bytes) > settings.max_input_size_bytes:
        raise ValueError(
            f"Source object exceeds the configured limit of "
            f"{settings.max_input_size_bytes} bytes"
        )

    if len(image_bytes) != content_length:
        raise ValueError(
            f"Incomplete read for source object: {object_key}"
        )

    return image_bytes


def build_output_key(
    source_key: str,
    settings: Settings,
) -> str:
    """Create a deterministic output key for retry-safe processing."""

    relative_key = source_key[len(settings.input_prefix):]

    if not relative_key:
        raise ValueError("Source object key does not contain a filename")

    return f"{settings.output_prefix}{relative_key}"


def process_s3_record(
    record: dict[str, Any],
    settings: Settings,
) -> dict[str, str]:
    """Transform one source image and persist the result to S3."""

    bucket_name, source_key, event_name = validate_s3_record(
        record,
        settings,
    )

    output_key = build_output_key(source_key, settings)

    log_event(
        logging.INFO,
        "Starting image processing",
        source_bucket=bucket_name,
        source_key=source_key,
        output_bucket=settings.output_bucket,
        output_key=output_key,
        event_name=event_name,
    )

    source_bytes = read_source_object(
        bucket_name,
        source_key,
        settings,
    )

    thumbnail_bytes, content_type = create_thumbnail(source_bytes)

    if not isinstance(thumbnail_bytes, bytes) or not thumbnail_bytes:
        raise ValueError(
            "Image transformer returned empty or invalid image data"
        )

    if not isinstance(content_type, str) or not content_type:
        raise ValueError(
            "Image transformer returned an invalid content type"
        )

    source_metadata = {
        "source-bucket": bucket_name,
        "source-key": source_key,
    }

    source_version_id = record.get("s3", {}).get(
        "object",
        {},
    ).get("versionId")

    if source_version_id:
        source_metadata["source-version-id"] = source_version_id

    s3_client.put_object(
        Bucket=settings.output_bucket,
        Key=output_key,
        Body=thumbnail_bytes,
        ContentType=content_type,
        Metadata=source_metadata,
    )

    result = {
        "source_bucket": bucket_name,
        "source_key": source_key,
        "output_bucket": settings.output_bucket,
        "output_key": output_key,
    }

    log_event(
        logging.INFO,
        "Image processing completed",
        **result,
        output_size_bytes=len(thumbnail_bytes),
        content_type=content_type,
    )

    return result


def process_sqs_record(
    record: dict[str, Any],
    settings: Settings,
) -> None:
    """Process all S3 notifications contained in one SQS message."""

    body = record.get("body")

    if not isinstance(body, str):
        raise ValueError("SQS message body must be a string")

    try:
        message = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "SQS message body contains invalid JSON"
        ) from exc

    if not isinstance(message, dict):
        raise ValueError("SQS message body must contain a JSON object")

    if message.get("Event") == "s3:TestEvent":
        log_event(
            logging.INFO,
            "Ignoring S3 test notification",
            message_id=record.get("messageId"),
        )
        return

    nested_records = extract_s3_records(
        {
            "Records": [
                {
                    "eventSource": "aws:sqs",
                    "body": body,
                    "messageId": record.get("messageId"),
                }
            ]
        }
    )

    for s3_record in nested_records:
        process_s3_record(s3_record, settings)


def lambda_handler(
    event: dict[str, Any],
    context: Any,
) -> dict[str, Any]:
    """Process S3 image events delivered directly or through SQS.

    For SQS event source mappings, return failed message identifiers
    using the ReportBatchItemFailures response contract. This allows
    successfully processed messages to be acknowledged independently
    from failed messages.
    """

    settings = Settings.from_environment()

    records = event.get("Records", [])

    if not isinstance(records, list):
        raise ValueError("Event Records must be a list")

    if not records:
        log_event(
            logging.INFO,
            "No records to process",
            aws_request_id=getattr(context, "aws_request_id", None),
        )
        return {"batchItemFailures": []}

    is_sqs_event = all(
        isinstance(record, dict)
        and record.get("eventSource") == "aws:sqs"
        for record in records
    )

    if is_sqs_event:
        batch_item_failures = []

        for record in records:
            message_id = record.get("messageId")

            try:
                process_sqs_record(record, settings)
            except (ClientError, ValueError, TypeError):
                log_event(
                    logging.exception,
                    "SQS message processing failed",
                    message_id=message_id,
                    aws_request_id=getattr(
                        context,
                        "aws_request_id",
                        None,
                    ),
                )
                batch_item_failures.append(
                    {
                        "itemIdentifier": message_id,
                    }
                )
            except Exception:
                logger.exception(
                    "Unexpected SQS message processing failure",
                    extra={
                        "message_id": message_id,
                        "aws_request_id": getattr(
                            context,
                            "aws_request_id",
                            None,
                        ),
                    },
                )
                batch_item_failures.append(
                    {
                        "itemIdentifier": message_id,
                    }
                )

        log_event(
            logging.INFO,
            "SQS batch processing completed",
            record_count=len(records),
            failed_record_count=len(batch_item_failures),
            aws_request_id=getattr(context, "aws_request_id", None),
        )

        return {
            "batchItemFailures": batch_item_failures,
        }

    # Direct S3 invocation uses the standard Lambda asynchronous
    # failure behavior: an exception causes the invocation to fail.
    s3_records = extract_s3_records(event)

    results = []

    for record in s3_records:
        results.append(
            process_s3_record(record, settings)
        )

    log_event(
        logging.INFO,
        "Direct S3 event processing completed",
        processed_record_count=len(results),
        aws_request_id=getattr(context, "aws_request_id", None),
    )

    return {
        "processed_records": len(results),
        "results": results,
    }