"""Integration tests for the S3 document ingestion API.

These tests exercise the document submission workflow through FastAPI's
HTTP interface while using Moto to emulate S3. No real AWS resources
or credentials are required.

Run from the project root with:

    PYTHONPATH=src pytest tests/integration/test_document_ingestion.py -v
"""

from __future__ import annotations

import os
from io import BytesIO
from typing import Iterator
from unittest.mock import patch

import boto3
import pytest
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient
from moto import mock_aws

from api.main import app
from api.routes import documents as documents_route


AWS_REGION = "ap-south-1"
BUCKET_NAME = "document-ingestion-integration-tests"
UPLOAD_PREFIX = "incoming"

PDF_CONTENT_TYPE = "application/pdf"
DOCX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument."
    "wordprocessingml.document"
)
XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
TEXT_CONTENT_TYPE = "text/plain"
CSV_CONTENT_TYPE = "text/csv"


@pytest.fixture
def s3_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[object]:
    """Provide an isolated Moto-backed S3 environment."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", AWS_REGION)
    monkeypatch.setenv("AWS_REGION", AWS_REGION)
    monkeypatch.setenv("DOCUMENTS_BUCKET_NAME", BUCKET_NAME)
    monkeypatch.setenv("DOCUMENTS_UPLOAD_PREFIX", UPLOAD_PREFIX)

    documents_route._get_s3_client.cache_clear()

    with mock_aws():
        s3_client = boto3.client(
            "s3",
            region_name=AWS_REGION,
        )
        s3_client.create_bucket(
            Bucket=BUCKET_NAME,
            CreateBucketConfiguration={
                "LocationConstraint": AWS_REGION,
            },
        )

        yield s3_client

    documents_route._get_s3_client.cache_clear()


@pytest.fixture
def client(
    s3_environment: object,
) -> Iterator[TestClient]:
    """Provide a FastAPI test client with mocked S3 storage."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_pdf() -> bytes:
    """Return a minimal PDF with a valid file signature."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n"
        b"<< /Type /Catalog /Pages 2 0 R >>\n"
        b"endobj\n"
        b"2 0 obj\n"
        b"<< /Type /Pages /Kids [] /Count 0 >>\n"
        b"endobj\n"
        b"trailer\n"
        b"<< /Root 1 0 R >>\n"
        b"%%EOF\n"
    )


@pytest.fixture
def sample_text() -> bytes:
    """Return representative UTF-8 text content."""
    return (
        "Document Ingestion Integration Test\n"
        "This document verifies the S3 upload workflow.\n"
        "Unicode content: café, résumé, 東京.\n"
    ).encode("utf-8")


@pytest.fixture
def sample_csv() -> bytes:
    """Return representative CSV content."""
    return (
        "employee_id,name,department\n"
        "1,Alice,Engineering\n"
        "2,Bob,Finance\n"
    ).encode("utf-8")


def upload_document(
    client: TestClient,
    *,
    filename: str,
    content: bytes,
    content_type: str,
):
    """Submit a document through the public upload endpoint."""
    return client.post(
        "/documents",
        files={
            "file": (
                filename,
                BytesIO(content),
                content_type,
            ),
        },
    )


class TestDocumentUploadIntegration:
    """Tests for the complete HTTP-to-S3 upload workflow."""

    def test_uploads_valid_pdf_to_s3(
        self,
        client: TestClient,
        s3_environment: object,
        sample_pdf: bytes,
    ) -> None:
        response = upload_document(
            client,
            filename="report.pdf",
            content=sample_pdf,
            content_type=PDF_CONTENT_TYPE,
        )

        assert response.status_code == 202

        payload = response.json()

        assert payload["bucket_name"] == BUCKET_NAME
        assert payload["filename"] == "report.pdf"
        assert payload["content_type"] == PDF_CONTENT_TYPE
        assert payload["size_bytes"] == len(sample_pdf)
        assert payload["processing_status"] == "PENDING"
        assert payload["object_id"] == (
            f"{BUCKET_NAME}/{payload['object_key']}"
        )
        assert payload["object_key"].startswith(
            f"{UPLOAD_PREFIX}/"
        )

        stored_object = s3_environment.get_object(
            Bucket=BUCKET_NAME,
            Key=payload["object_key"],
        )

        assert stored_object["Body"].read() == sample_pdf
        assert stored_object["ContentType"] == PDF_CONTENT_TYPE

    def test_uploads_valid_text_document(
        self,
        client: TestClient,
        s3_environment: object,
        sample_text: bytes,
    ) -> None:
        response = upload_document(
            client,
            filename="notes.txt",
            content=sample_text,
            content_type=TEXT_CONTENT_TYPE,
        )

        assert response.status_code == 202

        payload = response.json()

        stored_object = s3_environment.get_object(
            Bucket=BUCKET_NAME,
            Key=payload["object_key"],
        )

        assert stored_object["Body"].read() == sample_text
        assert stored_object["ContentType"] == TEXT_CONTENT_TYPE

    def test_uploads_valid_csv_document(
        self,
        client: TestClient,
        s3_environment: object,
        sample_csv: bytes,
    ) -> None:
        response = upload_document(
            client,
            filename="employees.csv",
            content=sample_csv,
            content_type=CSV_CONTENT_TYPE,
        )

        assert response.status_code == 202

        payload = response.json()

        stored_object = s3_environment.get_object(
            Bucket=BUCKET_NAME,
            Key=payload["object_key"],
        )

        assert stored_object["Body"].read() == sample_csv
        assert stored_object["ContentType"] == CSV_CONTENT_TYPE

    def test_generates_unique_object_keys_for_same_filename(
        self,
        client: TestClient,
        sample_text: bytes,
    ) -> None:
        first_response = upload_document(
            client,
            filename="duplicate.txt",
            content=sample_text,
            content_type=TEXT_CONTENT_TYPE,
        )
        second_response = upload_document(
            client,
            filename="duplicate.txt",
            content=sample_text,
            content_type=TEXT_CONTENT_TYPE,
        )

        assert first_response.status_code == 202
        assert second_response.status_code == 202

        first_key = first_response.json()["object_key"]
        second_key = second_response.json()["object_key"]

        assert first_key != second_key

    def test_does_not_use_user_filename_as_object_key(
        self,
        client: TestClient,
        sample_text: bytes,
    ) -> None:
        response = upload_document(
            client,
            filename="../../private/report.txt",
            content=sample_text,
            content_type=TEXT_CONTENT_TYPE,
        )

        assert response.status_code == 202

        object_key = response.json()["object_key"]

        assert object_key.startswith(f"{UPLOAD_PREFIX}/")
        assert ".." not in object_key
        assert "\\" not in object_key
        assert object_key.endswith(".txt")

    def test_preserves_original_filename_in_object_metadata(
        self,
        client: TestClient,
        s3_environment: object,
        sample_text: bytes,
    ) -> None:
        filename = "quarterly report.txt"

        response = upload_document(
            client,
            filename=filename,
            content=sample_text,
            content_type=TEXT_CONTENT_TYPE,
        )

        assert response.status_code == 202

        object_key = response.json()["object_key"]

        stored_object = s3_environment.head_object(
            Bucket=BUCKET_NAME,
            Key=object_key,
        )

        assert stored_object["Metadata"]["original-filename"] == (
            "quarterly%20report.txt"
        )

        assert stored_object["ContentDisposition"] == (
            "attachment; filename*=UTF-8''quarterly%20report.txt"
        )

    def test_returns_pending_status_after_upload(
        self,
        client: TestClient,
        sample_text: bytes,
    ) -> None:
        response = upload_document(
            client,
            filename="pending.txt",
            content=sample_text,
            content_type=TEXT_CONTENT_TYPE,
        )

        assert response.status_code == 202
        assert response.json()["processing_status"] == "PENDING"


class TestDocumentUploadValidationIntegration:
    """Tests for validation failures exposed through the upload API."""

    def test_rejects_missing_file(
        self,
        client: TestClient,
    ) -> None:
        response = client.post("/documents")

        assert response.status_code == 422

    def test_rejects_empty_filename(
        self,
        client: TestClient,
    ) -> None:
        response = upload_document(
            client,
            filename="",
            content=b"document content",
            content_type=TEXT_CONTENT_TYPE,
        )

        assert response.status_code == 422

    def test_rejects_unsupported_extension(
        self,
        client: TestClient,
    ) -> None:
        response = upload_document(
            client,
            filename="payload.exe",
            content=b"executable content",
            content_type="application/octet-stream",
        )

        assert response.status_code == 422

    def test_rejects_filename_content_type_mismatch(
        self,
        client: TestClient,
    ) -> None:
        response = upload_document(
            client,
            filename="report.txt",
            content=b"%PDF-1.4\ninvalid",
            content_type=PDF_CONTENT_TYPE,
        )

        assert response.status_code == 422

    def test_rejects_invalid_pdf_signature(
        self,
        client: TestClient,
    ) -> None:
        response = upload_document(
            client,
            filename="report.pdf",
            content=b"This is not a PDF document.",
            content_type=PDF_CONTENT_TYPE,
        )

        assert response.status_code == 422

    def test_rejects_empty_document(
        self,
        client: TestClient,
    ) -> None:
        response = upload_document(
            client,
            filename="empty.txt",
            content=b"",
            content_type=TEXT_CONTENT_TYPE,
        )

        assert response.status_code == 422

    def test_rejects_document_exceeding_configured_size_limit(
        self,
        client: TestClient,
    ) -> None:
        oversized_content = b"A" * (
            documents_route.DEFAULT_MAX_DOCUMENT_SIZE_BYTES + 1
        )

        response = upload_document(
            client,
            filename="oversized.txt",
            content=oversized_content,
            content_type=TEXT_CONTENT_TYPE,
        )

        assert response.status_code == 413

    def test_rejects_missing_content_type(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            "/documents",
            files={
                "file": (
                    "report.txt",
                    BytesIO(b"document content"),
                    "",
                ),
            },
        )

        assert response.status_code in {415, 422}


class TestDocumentUploadConfigurationIntegration:
    """Tests for missing and invalid storage configuration."""

    def test_returns_service_unavailable_without_bucket_configuration(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv(
            "DOCUMENTS_BUCKET_NAME",
            raising=False,
        )

        response = upload_document(
            client,
            filename="report.txt",
            content=b"document content",
            content_type=TEXT_CONTENT_TYPE,
        )

        assert response.status_code == 503

    def test_rejects_bucket_name_with_surrounding_whitespace(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv(
            "DOCUMENTS_BUCKET_NAME",
            f" {BUCKET_NAME}",
        )

        response = upload_document(
            client,
            filename="report.txt",
            content=b"document content",
            content_type=TEXT_CONTENT_TYPE,
        )

        assert response.status_code == 500

    def test_rejects_invalid_upload_prefix(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv(
            "DOCUMENTS_UPLOAD_PREFIX",
            "incoming/../private",
        )

        response = upload_document(
            client,
            filename="report.txt",
            content=b"document content",
            content_type=TEXT_CONTENT_TYPE,
        )

        assert response.status_code == 500


class TestS3FailureHandlingIntegration:
    """Tests for S3 errors translated into API responses."""

    def test_returns_gateway_error_when_s3_upload_fails(
        self,
        client: TestClient,
        sample_text: bytes,
    ) -> None:
        with patch.object(
            documents_route,
            "_get_s3_client",
        ) as get_s3_client:
            get_s3_client.return_value.put_object.side_effect = (
                ClientError(
                    {
                        "Error": {
                            "Code": "AccessDenied",
                            "Message": "Access denied",
                        },
                        "ResponseMetadata": {
                            "HTTPStatusCode": 403,
                        },
                    },
                    "PutObject",
                )
            )

            response = upload_document(
                client,
                filename="report.txt",
                content=sample_text,
                content_type=TEXT_CONTENT_TYPE,
            )

        assert response.status_code == 502
        assert response.json()["detail"] == (
            "Document storage operation failed."
        )

    def test_returns_gateway_error_for_s3_transport_failure(
        self,
        client: TestClient,
        sample_text: bytes,
    ) -> None:
        from botocore.exceptions import EndpointConnectionError

        with patch.object(
            documents_route,
            "_get_s3_client",
        ) as get_s3_client:
            get_s3_client.return_value.put_object.side_effect = (
                EndpointConnectionError(
                    endpoint_url="https://s3.ap-south-1.amazonaws.com"
                )
            )

            response = upload_document(
                client,
                filename="report.txt",
                content=sample_text,
                content_type=TEXT_CONTENT_TYPE,
            )

        assert response.status_code == 502


class TestS3UploadIsolationIntegration:
    """Tests for object isolation and stored object integrity."""

    def test_uploads_two_documents_without_overwriting(
        self,
        client: TestClient,
        s3_environment: object,
    ) -> None:
        first_content = b"First document content"
        second_content = b"Second document content"

        first_response = upload_document(
            client,
            filename="report.txt",
            content=first_content,
            content_type=TEXT_CONTENT_TYPE,
        )
        second_response = upload_document(
            client,
            filename="report.txt",
            content=second_content,
            content_type=TEXT_CONTENT_TYPE,
        )

        assert first_response.status_code == 202
        assert second_response.status_code == 202

        first_key = first_response.json()["object_key"]
        second_key = second_response.json()["object_key"]

        assert first_key != second_key

        first_object = s3_environment.get_object(
            Bucket=BUCKET_NAME,
            Key=first_key,
        )
        second_object = s3_environment.get_object(
            Bucket=BUCKET_NAME,
            Key=second_key,
        )

        assert first_object["Body"].read() == first_content
        assert second_object["Body"].read() == second_content

    def test_uploaded_object_has_expected_content_length(
        self,
        client: TestClient,
        s3_environment: object,
        sample_text: bytes,
    ) -> None:
        response = upload_document(
            client,
            filename="report.txt",
            content=sample_text,
            content_type=TEXT_CONTENT_TYPE,
        )

        assert response.status_code == 202

        object_key = response.json()["object_key"]

        stored_object = s3_environment.head_object(
            Bucket=BUCKET_NAME,
            Key=object_key,
        )

        assert stored_object["ContentLength"] == len(sample_text)

    def test_uploaded_object_is_stored_under_configured_prefix(
        self,
        client: TestClient,
        s3_environment: object,
        sample_text: bytes,
    ) -> None:
        response = upload_document(
            client,
            filename="report.txt",
            content=sample_text,
            content_type=TEXT_CONTENT_TYPE,
        )

        assert response.status_code == 202

        objects = s3_environment.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=UPLOAD_PREFIX,
        )

        assert objects["KeyCount"] == 1
        assert objects["Contents"][0]["Key"] == (
            response.json()["object_key"]
        )