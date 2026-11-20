"""Shared pytest fixtures for the Secure File Upload API test suite.

The fixtures provide isolated AWS credentials, a Moto-backed S3 environment,
sample upload data, and a FastAPI test client.

No real AWS account or credentials are required for these tests.
"""

from __future__ import annotations

import importlib
import os
from collections.abc import Iterator
from typing import Any

import boto3
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from moto import mock_aws


TEST_AWS_ACCESS_KEY_ID = "testing-access-key"
TEST_AWS_SECRET_ACCESS_KEY = "testing-secret-key"
TEST_AWS_SESSION_TOKEN = "testing-session-token"
TEST_AWS_REGION = "ap-south-1"

TEST_BUCKET_NAME = "secure-file-upload-test-bucket"
TEST_UPLOAD_PREFIX = "uploads/"

TEST_JWT_SECRET_KEY = (
    "test-only-jwt-secret-key-that-must-never-be-used-in-production"
)

TEST_MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
TEST_PRESIGNED_URL_EXPIRATION_SECONDS = 300

SAMPLE_FILE_CONTENT = b"Secure file upload API test content."
SAMPLE_FILENAME = "test-document.pdf"
SAMPLE_CONTENT_TYPE = "application/pdf"
SAMPLE_OBJECT_KEY = f"{TEST_UPLOAD_PREFIX}test-user/test-object/{SAMPLE_FILENAME}"

SAMPLE_METADATA = {
    "source": "pytest",
    "purpose": "integration-test",
}


@pytest.fixture(autouse=True)
def aws_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configure isolated AWS and application settings for every test.

    Dummy AWS credentials prevent Boto3 from resolving real credentials
    through the local AWS configuration or instance metadata service.
    """
    environment = {
        "AWS_ACCESS_KEY_ID": TEST_AWS_ACCESS_KEY_ID,
        "AWS_SECRET_ACCESS_KEY": TEST_AWS_SECRET_ACCESS_KEY,
        "AWS_SESSION_TOKEN": TEST_AWS_SESSION_TOKEN,
        "AWS_DEFAULT_REGION": TEST_AWS_REGION,
        "AWS_REGION": TEST_AWS_REGION,
        "AWS_EC2_METADATA_DISABLED": "true",
        "S3_BUCKET_NAME": TEST_BUCKET_NAME,
        "S3_UPLOAD_PREFIX": TEST_UPLOAD_PREFIX,
        "S3_KMS_KEY_ID": "",
        "MAX_UPLOAD_SIZE_BYTES": str(TEST_MAX_UPLOAD_SIZE_BYTES),
        "ALLOWED_CONTENT_TYPES": '["application/pdf","image/jpeg","image/png"]',
        "PRESIGNED_URL_EXPIRATION_SECONDS": str(
            TEST_PRESIGNED_URL_EXPIRATION_SECONDS
        ),
        "JWT_SECRET_KEY": TEST_JWT_SECRET_KEY,
        "JWT_ALGORITHM": "HS256",
    }

    for name, value in environment.items():
        monkeypatch.setenv(name, value)


@pytest.fixture
def mocked_aws() -> Iterator[None]:
    """Start an isolated Moto AWS environment for the current test."""
    with mock_aws():
        yield


@pytest.fixture
def s3_client(mocked_aws: None) -> Any:
    """Create a Boto3 S3 client backed by Moto."""
    return boto3.client(
        "s3",
        region_name=TEST_AWS_REGION,
        aws_access_key_id=TEST_AWS_ACCESS_KEY_ID,
        aws_secret_access_key=TEST_AWS_SECRET_ACCESS_KEY,
        aws_session_token=TEST_AWS_SESSION_TOKEN,
    )


@pytest.fixture
def s3_bucket(s3_client: Any) -> str:
    """Create the application test bucket and return its name."""
    create_bucket_params: dict[str, Any] = {
        "Bucket": TEST_BUCKET_NAME,
    }

    if TEST_AWS_REGION != "us-east-1":
        create_bucket_params["CreateBucketConfiguration"] = {
            "LocationConstraint": TEST_AWS_REGION,
        }

    s3_client.create_bucket(**create_bucket_params)

    return TEST_BUCKET_NAME


@pytest.fixture
def sample_file_content() -> bytes:
    """Return deterministic file content for upload tests."""
    return SAMPLE_FILE_CONTENT


@pytest.fixture
def sample_filename() -> str:
    """Return a representative client-provided filename."""
    return SAMPLE_FILENAME


@pytest.fixture
def sample_content_type() -> str:
    """Return an allowed MIME content type."""
    return SAMPLE_CONTENT_TYPE


@pytest.fixture
def sample_object_key() -> str:
    """Return a representative application-managed S3 object key."""
    return SAMPLE_OBJECT_KEY


@pytest.fixture
def sample_metadata() -> dict[str, str]:
    """Return representative custom S3 object metadata."""
    return SAMPLE_METADATA.copy()


@pytest.fixture
def uploaded_s3_object(
    s3_client: Any,
    s3_bucket: str,
    sample_object_key: str,
    sample_file_content: bytes,
    sample_content_type: str,
    sample_metadata: dict[str, str],
) -> dict[str, Any]:
    """Create a sample object in the Moto-backed test bucket."""
    s3_client.put_object(
        Bucket=s3_bucket,
        Key=sample_object_key,
        Body=sample_file_content,
        ContentType=sample_content_type,
        Metadata=sample_metadata,
    )

    return s3_client.head_object(
        Bucket=s3_bucket,
        Key=sample_object_key,
    )


@pytest.fixture
def app(aws_environment: None, s3_bucket: str) -> FastAPI:
    """Load the FastAPI application after test configuration is initialized.

    The S3 bucket is created before application initialization so that
    application lifespan hooks can safely use the Moto-backed environment.
    """
    from app.config import get_settings

    if hasattr(get_settings, "cache_clear"):
        get_settings.cache_clear()

    main_module = importlib.import_module("app.main")

    application = getattr(main_module, "app", None)

    if not isinstance(application, FastAPI):
        raise RuntimeError(
            "app.main must expose a FastAPI instance named 'app'."
        )

    return application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """Provide a FastAPI TestClient with application lifespan management."""
    with TestClient(app) as test_client:
        yield test_client