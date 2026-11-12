from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import MagicMock

import pytest

from src import handler


INPUT_BUCKET = "image-processing-input-test"
OUTPUT_BUCKET = "image-processing-output-test"
INPUT_PREFIX = "uploads/"
OUTPUT_PREFIX = "processed/"

JPEG_BYTES = (
    b"\xff\xd8\xff\xe0"
    b"\x00\x10JFIF\x00"
    b"\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xd9"
)


@pytest.fixture
def mock_s3(monkeypatch):
    """
    Configure a mocked S3 client and the Lambda environment.

    The mock prevents tests from making real AWS API calls.
    """
    monkeypatch.setenv("INPUT_BUCKET", INPUT_BUCKET)
    monkeypatch.setenv("OUTPUT_BUCKET", OUTPUT_BUCKET)
    monkeypatch.setenv("INPUT_PREFIX", INPUT_PREFIX)
    monkeypatch.setenv("OUTPUT_PREFIX", OUTPUT_PREFIX)
    monkeypatch.setenv("MAX_INPUT_SIZE_MB", "10")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    client = MagicMock()
    client.get_object.return_value = {
        "Body": BytesIO(JPEG_BYTES),
        "ContentLength": len(JPEG_BYTES),
        "ContentType": "image/jpeg",
    }

    monkeypatch.setattr(handler, "s3_client", client)

    return client


@pytest.fixture
def mock_thumbnail(monkeypatch):
    """
    Replace image transformation with a deterministic implementation.

    Handler tests focus on event processing and S3 interactions.
    Image transformation behavior belongs in image_transformer tests.
    """
    thumbnail_bytes = b"processed-image-content"
    content_type = "image/jpeg"

    transformer = MagicMock(
        return_value=(thumbnail_bytes, content_type)
    )

    monkeypatch.setattr(
        handler,
        "create_thumbnail",
        transformer,
    )

    return transformer


def make_s3_event(
    bucket: str = INPUT_BUCKET,
    key: str = "uploads/sample.jpg",
    size: int = len(JPEG_BYTES),
    event_name: str = "ObjectCreated:Put",
) -> dict:
    """Build a representative S3 ObjectCreated event."""
    return {
        "Records": [
            {
                "eventSource": "aws:s3",
                "eventName": event_name,
                "s3": {
                    "bucket": {
                        "name": bucket,
                    },
                    "object": {
                        "key": key,
                        "size": size,
                    },
                },
            }
        ]
    }


def make_sqs_event(
    message_body: dict,
    message_id: str = "message-001",
) -> dict:
    """Wrap an S3 event in an SQS message."""
    return {
        "Records": [
            {
                "messageId": message_id,
                "body": json.dumps(message_body),
                "eventSource": "aws:sqs",
            }
        ]
    }


def test_direct_s3_event_downloads_and_processes_image(
    mock_s3,
    mock_thumbnail,
):
    """A valid S3 event should download, transform, and upload an image."""
    event = make_s3_event()

    handler.lambda_handler(event, None)

    mock_s3.get_object.assert_called_once_with(
        Bucket=INPUT_BUCKET,
        Key="uploads/sample.jpg",
    )

    mock_thumbnail.assert_called_once_with(JPEG_BYTES)

    mock_s3.put_object.assert_called_once()
    upload_arguments = mock_s3.put_object.call_args.kwargs

    assert upload_arguments["Bucket"] == OUTPUT_BUCKET
    assert upload_arguments["Key"] == "processed/sample.jpg"
    assert upload_arguments["Body"] == b"processed-image-content"
    assert upload_arguments["ContentType"] == "image/jpeg"


def test_direct_s3_event_uses_url_decoded_object_key(
    mock_s3,
    mock_thumbnail,
):
    """URL-encoded S3 object keys must be decoded before S3 access."""
    event = make_s3_event(
        key="uploads/customer%20images/photo%20one.jpg",
    )

    handler.lambda_handler(event, None)

    mock_s3.get_object.assert_called_once_with(
        Bucket=INPUT_BUCKET,
        Key="uploads/customer images/photo one.jpg",
    )

    upload_arguments = mock_s3.put_object.call_args.kwargs

    assert (
        upload_arguments["Key"]
        == "processed/customer images/photo one.jpg"
    )


def test_direct_s3_event_ignores_objects_outside_input_prefix(
    mock_s3,
    mock_thumbnail,
):
    """Objects outside the configured input prefix must not be processed."""
    event = make_s3_event(
        key="private/sample.jpg",
    )

    handler.lambda_handler(event, None)

    mock_s3.get_object.assert_not_called()
    mock_thumbnail.assert_not_called()
    mock_s3.put_object.assert_not_called()


def test_direct_s3_event_ignores_objects_from_unconfigured_bucket(
    mock_s3,
    mock_thumbnail,
):
    """Events from an unexpected bucket must not be processed."""
    event = make_s3_event(
        bucket="unexpected-input-bucket",
    )

    handler.lambda_handler(event, None)

    mock_s3.get_object.assert_not_called()
    mock_thumbnail.assert_not_called()
    mock_s3.put_object.assert_not_called()


def test_direct_s3_event_ignores_non_object_created_events(
    mock_s3,
    mock_thumbnail,
):
    """Deletion and other non-creation events must be ignored."""
    event = make_s3_event(
        event_name="ObjectRemoved:Delete",
    )

    handler.lambda_handler(event, None)

    mock_s3.get_object.assert_not_called()
    mock_thumbnail.assert_not_called()
    mock_s3.put_object.assert_not_called()


def test_direct_s3_event_ignores_missing_object_size(
    mock_s3,
    mock_thumbnail,
):
    """An event without a usable object size must not trigger a download."""
    event = make_s3_event()
    del event["Records"][0]["s3"]["object"]["size"]

    handler.lambda_handler(event, None)

    mock_s3.get_object.assert_not_called()
    mock_thumbnail.assert_not_called()
    mock_s3.put_object.assert_not_called()


def test_direct_s3_event_ignores_empty_objects(
    mock_s3,
    mock_thumbnail,
):
    """Zero-byte objects must not be sent to the image transformer."""
    event = make_s3_event(size=0)

    handler.lambda_handler(event, None)

    mock_s3.get_object.assert_not_called()
    mock_thumbnail.assert_not_called()
    mock_s3.put_object.assert_not_called()


def test_direct_s3_event_rejects_objects_over_configured_size_limit(
    mock_s3,
    mock_thumbnail,
):
    """Objects larger than MAX_INPUT_SIZE_MB must not be downloaded."""
    event = make_s3_event(
        size=11 * 1024 * 1024,
    )

    handler.lambda_handler(event, None)

    mock_s3.get_object.assert_not_called()
    mock_thumbnail.assert_not_called()
    mock_s3.put_object.assert_not_called()


def test_direct_s3_event_ignores_nested_output_prefix(
    mock_s3,
    mock_thumbnail,
):
    """Processed objects must not be reprocessed as input images."""
    event = make_s3_event(
        key="uploads/processed/already-processed.jpg",
    )

    handler.lambda_handler(event, None)

    mock_s3.get_object.assert_called_once()
    mock_thumbnail.assert_called_once()
    mock_s3.put_object.assert_called_once()


def test_sqs_wrapped_s3_event_processes_image(
    mock_s3,
    mock_thumbnail,
):
    """An SQS message containing an S3 event should be processed."""
    s3_event = make_s3_event()
    event = make_sqs_event(s3_event)

    response = handler.lambda_handler(event, None)

    mock_s3.get_object.assert_called_once_with(
        Bucket=INPUT_BUCKET,
        Key="uploads/sample.jpg",
    )

    mock_thumbnail.assert_called_once_with(JPEG_BYTES)
    mock_s3.put_object.assert_called_once()

    assert response == {
        "batchItemFailures": [],
    }


def test_sqs_event_with_multiple_messages_processes_each_message(
    mock_s3,
    mock_thumbnail,
):
    """Each valid SQS message should be processed independently."""
    first_event = make_s3_event(
        key="uploads/first.jpg",
    )
    second_event = make_s3_event(
        key="uploads/second.jpg",
    )

    event = {
        "Records": [
            {
                "messageId": "message-001",
                "body": json.dumps(first_event),
                "eventSource": "aws:sqs",
            },
            {
                "messageId": "message-002",
                "body": json.dumps(second_event),
                "eventSource": "aws:sqs",
            },
        ]
    }

    response = handler.lambda_handler(event, None)

    assert mock_s3.get_object.call_count == 2
    assert mock_thumbnail.call_count == 2
    assert mock_s3.put_object.call_count == 2

    assert response == {
        "batchItemFailures": [],
    }


def test_sqs_event_reports_failed_message_for_retry(
    mock_s3,
    mock_thumbnail,
):
    """
    A failed SQS message must be returned as a batch item failure.

    This supports Lambda's ReportBatchItemFailures response contract.
    """
    mock_s3.get_object.side_effect = RuntimeError(
        "Simulated S3 download failure"
    )

    s3_event = make_s3_event()
    event = make_sqs_event(
        message_body=s3_event,
        message_id="failed-message",
    )

    response = handler.lambda_handler(event, None)

    assert response == {
        "batchItemFailures": [
            {
                "itemIdentifier": "failed-message",
            }
        ],
    }

    mock_thumbnail.assert_not_called()
    mock_s3.put_object.assert_not_called()


def test_sqs_event_reports_only_failed_messages(
    mock_s3,
    mock_thumbnail,
):
    """Successful messages must not be retried with failed messages."""
    mock_s3.get_object.side_effect = [
        {
            "Body": BytesIO(JPEG_BYTES),
            "ContentLength": len(JPEG_BYTES),
            "ContentType": "image/jpeg",
        },
        RuntimeError("Simulated S3 download failure"),
    ]

    first_event = make_s3_event(
        key="uploads/success.jpg",
    )
    second_event = make_s3_event(
        key="uploads/failure.jpg",
    )

    event = {
        "Records": [
            {
                "messageId": "success-message",
                "body": json.dumps(first_event),
                "eventSource": "aws:sqs",
            },
            {
                "messageId": "failure-message",
                "body": json.dumps(second_event),
                "eventSource": "aws:sqs",
            },
        ]
    }

    response = handler.lambda_handler(event, None)

    assert response == {
        "batchItemFailures": [
            {
                "itemIdentifier": "failure-message",
            }
        ],
    }

    assert mock_s3.get_object.call_count == 2
    assert mock_s3.put_object.call_count == 1


def test_sqs_event_with_invalid_json_is_reported_as_failed(
    mock_s3,
    mock_thumbnail,
):
    """Malformed SQS message bodies must be reported for retry."""
    event = {
        "Records": [
            {
                "messageId": "invalid-message",
                "body": "{invalid-json",
                "eventSource": "aws:sqs",
            }
        ]
    }

    response = handler.lambda_handler(event, None)

    assert response == {
        "batchItemFailures": [
            {
                "itemIdentifier": "invalid-message",
            }
        ],
    }

    mock_s3.get_object.assert_not_called()
    mock_thumbnail.assert_not_called()
    mock_s3.put_object.assert_not_called()


def test_sqs_event_without_message_id_is_handled_safely(
    mock_s3,
    mock_thumbnail,
):
    """Malformed SQS records must not cause unrelated messages to be lost."""
    event = {
        "Records": [
            {
                "body": json.dumps(make_s3_event()),
                "eventSource": "aws:sqs",
            }
        ]
    }

    response = handler.lambda_handler(event, None)

    assert isinstance(response, dict)
    assert "batchItemFailures" in response


def test_failed_image_transformation_does_not_upload_output(
    mock_s3,
    mock_thumbnail,
):
    """Transformation failures must not create output objects."""
    mock_thumbnail.side_effect = ValueError(
        "Unsupported image format"
    )

    event = make_s3_event()

    with pytest.raises(ValueError):
        handler.lambda_handler(event, None)

    mock_s3.put_object.assert_not_called()


def test_failed_s3_upload_propagates_for_async_retry(
    mock_s3,
    mock_thumbnail,
):
    """
    Direct asynchronous invocation failures must propagate to Lambda.

    Lambda can then apply its configured retry policy and failure destination.
    """
    mock_s3.put_object.side_effect = RuntimeError(
        "Simulated output upload failure"
    )

    event = make_s3_event()

    with pytest.raises(RuntimeError):
        handler.lambda_handler(event, None)


def test_output_key_is_deterministic_for_duplicate_events(
    mock_s3,
    mock_thumbnail,
):
    """
    Duplicate S3 notifications should produce the same output object key.

    Deterministic output keys make repeated processing safe from creating
    a separate output object for every duplicate notification.
    """
    event = make_s3_event()

    handler.lambda_handler(event, None)
    handler.lambda_handler(event, None)

    assert mock_s3.put_object.call_count == 2

    first_key = mock_s3.put_object.call_args_list[0].kwargs["Key"]
    second_key = mock_s3.put_object.call_args_list[1].kwargs["Key"]

    assert first_key == second_key
    assert first_key == "processed/sample.jpg"


def test_output_upload_includes_source_metadata(
    mock_s3,
    mock_thumbnail,
):
    """Output objects should retain useful source-identification metadata."""
    event = make_s3_event()

    handler.lambda_handler(event, None)

    upload_arguments = mock_s3.put_object.call_args.kwargs

    assert upload_arguments["Metadata"]["source-bucket"] == INPUT_BUCKET
    assert upload_arguments["Metadata"]["source-key"] == (
        "uploads/sample.jpg"
    )


def test_invalid_event_without_records_does_not_access_s3(
    mock_s3,
    mock_thumbnail,
):
    """An event without Records must not trigger S3 operations."""
    handler.lambda_handler({}, None)

    mock_s3.get_object.assert_not_called()
    mock_s3.put_object.assert_not_called()
    mock_thumbnail.assert_not_called()


def test_event_with_empty_records_does_not_access_s3(
    mock_s3,
    mock_thumbnail,
):
    """An empty Records collection must be handled without AWS calls."""
    handler.lambda_handler(
        {
            "Records": [],
        },
        None,
    )

    mock_s3.get_object.assert_not_called()
    mock_s3.put_object.assert_not_called()
    mock_thumbnail.assert_not_called()


def test_missing_output_bucket_configuration_fails(
    monkeypatch,
    mock_s3,
    mock_thumbnail,
):
    """The handler must fail clearly when OUTPUT_BUCKET is unavailable."""
    monkeypatch.delenv("OUTPUT_BUCKET")

    event = make_s3_event()

    with pytest.raises((ValueError, RuntimeError, KeyError)):
        handler.lambda_handler(event, None)

    mock_s3.get_object.assert_not_called()
    mock_s3.put_object.assert_not_called()


def test_output_bucket_is_not_used_as_input(
    mock_s3,
    mock_thumbnail,
):
    """Events originating from the output bucket must not be processed."""
    event = make_s3_event(
        bucket=OUTPUT_BUCKET,
        key="processed/sample.jpg",
    )

    handler.lambda_handler(event, None)

    mock_s3.get_object.assert_not_called()
    mock_thumbnail.assert_not_called()
    mock_s3.put_object.assert_not_called()