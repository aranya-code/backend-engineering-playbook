"""Integration tests for S3 document event ingestion.

The tests exercise the ingestion Lambda workflow against Moto-backed S3,
DynamoDB, and SQS services. They verify event parsing, object retrieval,
metadata persistence, and downstream processing-event publication without
requiring an AWS account.

Run from the project root with:

    PYTHONPATH=src pytest tests/integration/test_event_processing.py -v
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from ingestion import handler as ingestion_handler


AWS_REGION = "ap-south-1"
BUCKET_NAME = "document-ingestion-event-tests"
METADATA_TABLE_NAME = "document-metadata-event-tests"
QUEUE_NAME = "document-processing-event-tests"
DOCUMENT_KEY_PREFIX = "incoming"

TEXT_CONTENT_TYPE = "text/plain"
SAMPLE_DOCUMENT = (
    b"Document ingestion event integration test.\n"
    b"Metadata extraction is verified independently.\n"
)

SAMPLE_EXTRACTED_METADATA = {
    "title": "Integration Test Document",
    "format": "txt",
    "text": (
        "Document ingestion event integration test. "
        "Metadata extraction is verified independently."
    ),
}


class MotoS3Storage:
    """Adapt a Moto-backed S3 client to the S3Storage interface."""

    def __init__(self, client: Any) -> None:
        self.client = client

    def head_object(
        self,
        *,
        bucket_name: str,
        object_key: str,
    ) -> dict[str, Any]:
        return self.client.head_object(
            Bucket=bucket_name,
            Key=object_key,
        )

    def get_object(
        self,
        *,
        bucket_name: str,
        object_key: str,
    ) -> bytes:
        response = self.client.get_object(
            Bucket=bucket_name,
            Key=object_key,
        )
        return response["Body"].read()


@pytest.fixture
def aws_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Any]:
    """Create isolated S3, DynamoDB, and SQS resources using Moto."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", AWS_REGION)
    monkeypatch.setenv("AWS_REGION", AWS_REGION)
    monkeypatch.setenv("METADATA_TABLE_NAME", METADATA_TABLE_NAME)

    with mock_aws():
        s3_client = boto3.client(
            "s3",
            region_name=AWS_REGION,
        )
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=AWS_REGION,
        )
        sqs_client = boto3.client(
            "sqs",
            region_name=AWS_REGION,
        )

        s3_client.create_bucket(
            Bucket=BUCKET_NAME,
            CreateBucketConfiguration={
                "LocationConstraint": AWS_REGION,
            },
        )

        metadata_table = dynamodb.create_table(
            TableName=METADATA_TABLE_NAME,
            KeySchema=[
                {
                    "AttributeName": "object_id",
                    "KeyType": "HASH",
                },
            ],
            AttributeDefinitions=[
                {
                    "AttributeName": "object_id",
                    "AttributeType": "S",
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        metadata_table.wait_until_exists()

        queue_response = sqs_client.create_queue(
            QueueName=QUEUE_NAME,
        )
        queue_url = queue_response["QueueUrl"]

        monkeypatch.setattr(
            ingestion_handler,
            "s3_storage",
            MotoS3Storage(s3_client),
        )
        monkeypatch.setattr(
            ingestion_handler,
            "metadata_table",
            metadata_table,
        )
        monkeypatch.setattr(
            ingestion_handler,
            "sqs",
            sqs_client,
        )
        monkeypatch.setattr(
            ingestion_handler,
            "PROCESSING_QUEUE_URL",
            queue_url,
        )
        monkeypatch.setattr(
            ingestion_handler,
            "metadata_extractor",
            ingestion_handler.MetadataExtractor(),
        )

        yield {
            "s3": s3_client,
            "dynamodb": dynamodb,
            "metadata_table": metadata_table,
            "sqs": sqs_client,
            "queue_url": queue_url,
        }


@pytest.fixture
def sample_document(
    aws_environment: dict[str, Any],
) -> dict[str, Any]:
    """Upload a sample document and return its S3 event details."""
    object_key = f"{DOCUMENT_KEY_PREFIX}/integration-report.txt"

    upload_response = aws_environment["s3"].put_object(
        Bucket=BUCKET_NAME,
        Key=object_key,
        Body=SAMPLE_DOCUMENT,
        ContentType=TEXT_CONTENT_TYPE,
        Metadata={
            "source": "integration-test",
        },
    )

    return {
        "bucket_name": BUCKET_NAME,
        "object_key": object_key,
        "etag": upload_response["ETag"].strip('"'),
        "content": SAMPLE_DOCUMENT,
        "content_type": TEXT_CONTENT_TYPE,
    }


def build_s3_event_record(
    *,
    bucket_name: str,
    object_key: str,
    size: int,
    event_name: str = "ObjectCreated:Put",
) -> dict[str, Any]:
    """Build an S3 notification record with URL-encoded object key."""
    return {
        "eventVersion": "2.1",
        "eventSource": "aws:s3",
        "awsRegion": AWS_REGION,
        "eventTime": datetime.now(
            timezone.utc
        ).isoformat(),
        "eventName": event_name,
        "s3": {
            "s3SchemaVersion": "1.0",
            "bucket": {
                "name": bucket_name,
                "arn": f"arn:aws:s3:::{bucket_name}",
            },
            "object": {
                "key": quote_plus(object_key),
                "size": size,
            },
        },
    }


def build_s3_event(
    *records: dict[str, Any],
) -> dict[str, Any]:
    """Wrap one or more S3 notification records."""
    return {
        "Records": list(records),
    }


def receive_processing_messages(
    aws_environment: dict[str, Any],
    *,
    max_messages: int = 10,
) -> list[dict[str, Any]]:
    """Receive and decode messages published to the processing queue."""
    response = aws_environment["sqs"].receive_message(
        QueueUrl=aws_environment["queue_url"],
        MaxNumberOfMessages=max_messages,
        WaitTimeSeconds=0,
    )

    return [
        json.loads(message["Body"])
        for message in response.get("Messages", [])
    ]


class TestS3EventProcessingIntegration:
    """Verify the complete S3-to-metadata-to-SQS ingestion workflow."""

    def test_processes_s3_object_created_event(
        self,
        aws_environment: dict[str, Any],
        sample_document: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            ingestion_handler.metadata_extractor,
            "extract_metadata",
            lambda **kwargs: SAMPLE_EXTRACTED_METADATA,
        )

        record = build_s3_event_record(
            bucket_name=sample_document["bucket_name"],
            object_key=sample_document["object_key"],
            size=len(sample_document["content"]),
        )

        result = ingestion_handler.lambda_handler(
            build_s3_event(record),
            None,
        )

        expected_object_id = (
            f"{BUCKET_NAME}/{sample_document['object_key']}"
        )

        assert result["status"] == "SUCCESS"
        assert result["processed_count"] == 1
        assert result["records"] == [
            {
                "object_id": expected_object_id,
                "processing_status": "PENDING",
            },
        ]

        stored_metadata = aws_environment[
            "metadata_table"
        ].get_item(
            Key={
                "object_id": expected_object_id,
            },
            ConsistentRead=True,
        )["Item"]

        assert stored_metadata["object_id"] == expected_object_id
        assert stored_metadata["bucket_name"] == BUCKET_NAME
        assert stored_metadata["object_key"] == (
            sample_document["object_key"]
        )
        assert stored_metadata["size_bytes"] == len(
            sample_document["content"]
        )
        assert stored_metadata["content_type"] == TEXT_CONTENT_TYPE
        assert stored_metadata["etag"] == sample_document["etag"]
        assert stored_metadata["metadata"] == SAMPLE_EXTRACTED_METADATA
        assert stored_metadata["processing_status"] == "PENDING"

        messages = receive_processing_messages(aws_environment)

        assert len(messages) == 1
        assert messages[0] == {
            "object_id": expected_object_id,
            "bucket_name": BUCKET_NAME,
            "object_key": sample_document["object_key"],
            "etag": sample_document["etag"],
            "version_id": None,
        }

    def test_decodes_url_encoded_object_key(
        self,
        aws_environment: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        object_key = (
            f"{DOCUMENT_KEY_PREFIX}/quarterly report "
            "café.txt"
        )
        content = b"Encoded object key integration test."

        aws_environment["s3"].put_object(
            Bucket=BUCKET_NAME,
            Key=object_key,
            Body=content,
            ContentType=TEXT_CONTENT_TYPE,
        )

        monkeypatch.setattr(
            ingestion_handler.metadata_extractor,
            "extract_metadata",
            lambda **kwargs: SAMPLE_EXTRACTED_METADATA,
        )

        record = build_s3_event_record(
            bucket_name=BUCKET_NAME,
            object_key=object_key,
            size=len(content),
        )

        result = ingestion_handler.lambda_handler(
            build_s3_event(record),
            None,
        )

        assert result["status"] == "SUCCESS"
        assert result["records"][0]["object_id"] == (
            f"{BUCKET_NAME}/{object_key}"
        )

        messages = receive_processing_messages(aws_environment)

        assert messages[0]["object_key"] == object_key

    def test_processes_multiple_s3_records(
        self,
        aws_environment: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        object_keys = [
            f"{DOCUMENT_KEY_PREFIX}/first.txt",
            f"{DOCUMENT_KEY_PREFIX}/second.txt",
        ]

        records = []

        for object_key in object_keys:
            content = f"Content for {object_key}".encode("utf-8")

            aws_environment["s3"].put_object(
                Bucket=BUCKET_NAME,
                Key=object_key,
                Body=content,
                ContentType=TEXT_CONTENT_TYPE,
            )

            records.append(
                build_s3_event_record(
                    bucket_name=BUCKET_NAME,
                    object_key=object_key,
                    size=len(content),
                )
            )

        monkeypatch.setattr(
            ingestion_handler.metadata_extractor,
            "extract_metadata",
            lambda **kwargs: SAMPLE_EXTRACTED_METADATA,
        )

        result = ingestion_handler.lambda_handler(
            build_s3_event(*records),
            None,
        )

        assert result["status"] == "SUCCESS"
        assert result["processed_count"] == 2
        assert {
            record["object_id"]
            for record in result["records"]
        } == {
            f"{BUCKET_NAME}/{object_key}"
            for object_key in object_keys
        }

        messages = receive_processing_messages(aws_environment)

        assert len(messages) == 2
        assert {
            message["object_key"]
            for message in messages
        } == set(object_keys)

    def test_persists_metadata_before_publishing_event(
        self,
        aws_environment: dict[str, Any],
        sample_document: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            ingestion_handler.metadata_extractor,
            "extract_metadata",
            lambda **kwargs: SAMPLE_EXTRACTED_METADATA,
        )

        original_send_message = (
            ingestion_handler.sqs.send_message
        )
        observed_metadata: list[dict[str, Any]] = []

        def verify_metadata_before_publish(
            **kwargs: Any,
        ) -> dict[str, Any]:
            messages = receive_processing_messages(
                aws_environment,
            )
            assert messages == []

            object_id = json.loads(
                kwargs["MessageBody"]
            )["object_id"]

            item = aws_environment["metadata_table"].get_item(
                Key={
                    "object_id": object_id,
                },
                ConsistentRead=True,
            ).get("Item")

            assert item is not None
            observed_metadata.append(item)

            return original_send_message(**kwargs)

        monkeypatch.setattr(
            ingestion_handler.sqs,
            "send_message",
            verify_metadata_before_publish,
        )

        record = build_s3_event_record(
            bucket_name=sample_document["bucket_name"],
            object_key=sample_document["object_key"],
            size=len(sample_document["content"]),
        )

        result = ingestion_handler.lambda_handler(
            build_s3_event(record),
            None,
        )

        assert result["status"] == "SUCCESS"
        assert len(observed_metadata) == 1
        assert observed_metadata[0]["processing_status"] == "PENDING"


class TestS3EventValidationIntegration:
    """Verify malformed and inconsistent S3 events are rejected."""

    def test_rejects_event_without_records(
        self,
        aws_environment: dict[str, Any],
    ) -> None:
        with pytest.raises(
            ValueError,
            match="non-empty Records list",
        ):
            ingestion_handler.lambda_handler(
                {},
                None,
            )

    def test_rejects_empty_records_list(
        self,
        aws_environment: dict[str, Any],
    ) -> None:
        with pytest.raises(
            ValueError,
            match="non-empty Records list",
        ):
            ingestion_handler.lambda_handler(
                {"Records": []},
                None,
            )

    def test_rejects_non_list_records(
        self,
        aws_environment: dict[str, Any],
    ) -> None:
        with pytest.raises(
            ValueError,
            match="non-empty Records list",
        ):
            ingestion_handler.lambda_handler(
                {"Records": {}},
                None,
            )

    def test_rejects_event_exceeding_record_limit(
        self,
        aws_environment: dict[str, Any],
    ) -> None:
        records = [
            {}
            for _ in range(
                ingestion_handler.DEFAULT_MAX_EVENT_RECORDS + 1
            )
        ]

        with pytest.raises(
            ValueError,
            match="more than",
        ):
            ingestion_handler.lambda_handler(
                build_s3_event(*records),
                None,
            )

    def test_rejects_invalid_record_structure(
        self,
        aws_environment: dict[str, Any],
    ) -> None:
        with pytest.raises(
            ingestion_handler.IngestionError,
            match="Document ingestion failed",
        ):
            ingestion_handler.lambda_handler(
                build_s3_event(
                    {
                        "eventSource": "aws:s3",
                    }
                ),
                None,
            )

    def test_rejects_invalid_object_size(
        self,
        aws_environment: dict[str, Any],
        sample_document: dict[str, Any],
    ) -> None:
        record = build_s3_event_record(
            bucket_name=sample_document["bucket_name"],
            object_key=sample_document["object_key"],
            size=-1,
        )

        with pytest.raises(
            ingestion_handler.IngestionError,
            match="Document ingestion failed",
        ):
            ingestion_handler.lambda_handler(
                build_s3_event(record),
                None,
            )

    def test_rejects_boolean_object_size(
        self,
        aws_environment: dict[str, Any],
        sample_document: dict[str, Any],
    ) -> None:
        record = build_s3_event_record(
            bucket_name=sample_document["bucket_name"],
            object_key=sample_document["object_key"],
            size=1,
        )
        record["s3"]["object"]["size"] = True

        with pytest.raises(
            ingestion_handler.IngestionError,
            match="Document ingestion failed",
        ):
            ingestion_handler.lambda_handler(
                build_s3_event(record),
                None,
            )

    def test_rejects_event_size_mismatch(
        self,
        aws_environment: dict[str, Any],
        sample_document: dict[str, Any],
    ) -> None:
        record = build_s3_event_record(
            bucket_name=sample_document["bucket_name"],
            object_key=sample_document["object_key"],
            size=len(sample_document["content"]) + 1,
        )

        with pytest.raises(
            ingestion_handler.IngestionError,
            match="Document ingestion failed",
        ):
            ingestion_handler.lambda_handler(
                build_s3_event(record),
                None,
            )

    def test_rejects_event_for_missing_s3_object(
        self,
        aws_environment: dict[str, Any],
    ) -> None:
        object_key = f"{DOCUMENT_KEY_PREFIX}/missing.txt"

        record = build_s3_event_record(
            bucket_name=BUCKET_NAME,
            object_key=object_key,
            size=10,
        )

        with pytest.raises(
            ingestion_handler.IngestionError,
            match="Document ingestion failed",
        ):
            ingestion_handler.lambda_handler(
                build_s3_event(record),
                None,
            )

    def test_rejects_unsupported_document_type(
        self,
        aws_environment: dict[str, Any],
    ) -> None:
        object_key = f"{DOCUMENT_KEY_PREFIX}/unsupported.exe"
        content = b"Unsupported executable content."

        aws_environment["s3"].put_object(
            Bucket=BUCKET_NAME,
            Key=object_key,
            Body=content,
            ContentType="application/octet-stream",
        )

        record = build_s3_event_record(
            bucket_name=BUCKET_NAME,
            object_key=object_key,
            size=len(content),
        )

        with pytest.raises(
            ingestion_handler.IngestionError,
            match="Document ingestion failed",
        ):
            ingestion_handler.lambda_handler(
                build_s3_event(record),
                None,
            )


class TestMetadataPersistenceIntegration:
    """Verify metadata persistence and downstream publication behavior."""

    def test_persists_metadata_with_object_version_id(
        self,
        aws_environment: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        aws_environment["s3"].put_bucket_versioning(
            Bucket=BUCKET_NAME,
            VersioningConfiguration={
                "Status": "Enabled",
            },
        )

        object_key = f"{DOCUMENT_KEY_PREFIX}/versioned.txt"
        content = b"Versioned document content."

        upload_response = aws_environment["s3"].put_object(
            Bucket=BUCKET_NAME,
            Key=object_key,
            Body=content,
            ContentType=TEXT_CONTENT_TYPE,
        )

        monkeypatch.setattr(
            ingestion_handler.metadata_extractor,
            "extract_metadata",
            lambda **kwargs: SAMPLE_EXTRACTED_METADATA,
        )

        record = build_s3_event_record(
            bucket_name=BUCKET_NAME,
            object_key=object_key,
            size=len(content),
        )

        record["s3"]["object"]["versionId"] = upload_response[
            "VersionId"
        ]

        result = ingestion_handler.lambda_handler(
            build_s3_event(record),
            None,
        )

        assert result["status"] == "SUCCESS"

        object_id = f"{BUCKET_NAME}/{object_key}"

        stored_metadata = aws_environment[
            "metadata_table"
        ].get_item(
            Key={
                "object_id": object_id,
            },
            ConsistentRead=True,
        )["Item"]

        assert stored_metadata["version_id"] == (
            upload_response["VersionId"]
        )

        messages = receive_processing_messages(aws_environment)

        assert messages[0]["version_id"] == (
            upload_response["VersionId"]
        )

    def test_metadata_persistence_failure_prevents_success(
        self,
        aws_environment: dict[str, Any],
        sample_document: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            ingestion_handler.metadata_extractor,
            "extract_metadata",
            lambda **kwargs: SAMPLE_EXTRACTED_METADATA,
        )

        def fail_put_item(**kwargs: Any) -> None:
            raise ClientError(
                {
                    "Error": {
                        "Code": "AccessDeniedException",
                        "Message": "DynamoDB write denied",
                    },
                },
                "PutItem",
            )

        monkeypatch.setattr(
            ingestion_handler.metadata_table,
            "put_item",
            fail_put_item,
        )

        record = build_s3_event_record(
            bucket_name=sample_document["bucket_name"],
            object_key=sample_document["object_key"],
            size=len(sample_document["content"]),
        )

        with pytest.raises(
            ingestion_handler.IngestionError,
            match="Document ingestion failed",
        ):
            ingestion_handler.lambda_handler(
                build_s3_event(record),
                None,
            )

        assert receive_processing_messages(aws_environment) == []

    def test_sqs_publication_failure_fails_ingestion_invocation(
        self,
        aws_environment: dict[str, Any],
        sample_document: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            ingestion_handler.metadata_extractor,
            "extract_metadata",
            lambda **kwargs: SAMPLE_EXTRACTED_METADATA,
        )

        def fail_send_message(**kwargs: Any) -> None:
            raise ClientError(
                {
                    "Error": {
                        "Code": "AccessDenied",
                        "Message": "SQS send permission denied",
                    },
                },
                "SendMessage",
            )

        monkeypatch.setattr(
            ingestion_handler.sqs,
            "send_message",
            fail_send_message,
        )

        record = build_s3_event_record(
            bucket_name=sample_document["bucket_name"],
            object_key=sample_document["object_key"],
            size=len(sample_document["content"]),
        )

        with pytest.raises(
            ingestion_handler.IngestionError,
            match="Document ingestion failed",
        ):
            ingestion_handler.lambda_handler(
                build_s3_event(record),
                None,
            )

        object_id = (
            f"{BUCKET_NAME}/{sample_document['object_key']}"
        )

        stored_metadata = aws_environment[
            "metadata_table"
        ].get_item(
            Key={
                "object_id": object_id,
            },
            ConsistentRead=True,
        ).get("Item")

        assert stored_metadata is not None
        assert stored_metadata["processing_status"] == "PENDING"

    def test_duplicate_event_does_not_create_duplicate_metadata_items(
        self,
        aws_environment: dict[str, Any],
        sample_document: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            ingestion_handler.metadata_extractor,
            "extract_metadata",
            lambda **kwargs: SAMPLE_EXTRACTED_METADATA,
        )

        record = build_s3_event_record(
            bucket_name=sample_document["bucket_name"],
            object_key=sample_document["object_key"],
            size=len(sample_document["content"]),
        )
        event = build_s3_event(record)

        first_result = ingestion_handler.lambda_handler(
            event,
            None,
        )
        second_result = ingestion_handler.lambda_handler(
            event,
            None,
        )

        assert first_result["status"] == "SUCCESS"
        assert second_result["status"] == "SUCCESS"

        object_id = (
            f"{BUCKET_NAME}/{sample_document['object_key']}"
        )

        stored_metadata = aws_environment[
            "metadata_table"
        ].get_item(
            Key={
                "object_id": object_id,
            },
            ConsistentRead=True,
        ).get("Item")

        assert stored_metadata is not None
        assert stored_metadata["etag"] == sample_document["etag"]

        # The ingestion handler permits re-publication for the same ETag.
        # Queue-level or processing-level idempotency must handle duplicates.
        messages = receive_processing_messages(
            aws_environment,
            max_messages=10,
        )

        assert len(messages) == 2
        assert all(
            message["object_id"] == object_id
            for message in messages
        )


class TestIngestionConfigurationIntegration:
    """Verify required ingestion configuration and dependency failures."""

    def test_fails_when_metadata_table_is_not_configured(
        self,
        aws_environment: dict[str, Any],
        sample_document: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            ingestion_handler.metadata_extractor,
            "extract_metadata",
            lambda **kwargs: SAMPLE_EXTRACTED_METADATA,
        )
        monkeypatch.setattr(
            ingestion_handler,
            "metadata_table",
            None,
        )

        record = build_s3_event_record(
            bucket_name=sample_document["bucket_name"],
            object_key=sample_document["object_key"],
            size=len(sample_document["content"]),
        )

        with pytest.raises(
            ingestion_handler.IngestionError,
            match="METADATA_TABLE_NAME is not configured",
        ):
            ingestion_handler.process_document_record(record)

        assert receive_processing_messages(aws_environment) == []

    def test_fails_when_processing_queue_is_not_configured(
        self,
        aws_environment: dict[str, Any],
        sample_document: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            ingestion_handler.metadata_extractor,
            "extract_metadata",
            lambda **kwargs: SAMPLE_EXTRACTED_METADATA,
        )
        monkeypatch.setattr(
            ingestion_handler,
            "PROCESSING_QUEUE_URL",
            None,
        )

        record = build_s3_event_record(
            bucket_name=sample_document["bucket_name"],
            object_key=sample_document["object_key"],
            size=len(sample_document["content"]),
        )

        with pytest.raises(
            ingestion_handler.IngestionError,
            match="PROCESSING_QUEUE_URL is not configured",
        ):
            ingestion_handler.process_document_record(record)

        object_id = (
            f"{BUCKET_NAME}/{sample_document['object_key']}"
        )

        stored_metadata = aws_environment[
            "metadata_table"
        ].get_item(
            Key={
                "object_id": object_id,
            },
            ConsistentRead=True,
        ).get("Item")

        assert stored_metadata is not None
        assert stored_metadata["processing_status"] == "PENDING"