"""Integration tests for the authenticated S3 download flow.

These tests exercise the download API against a Moto-backed S3 bucket. They
verify authentication, successful presigned URL generation, object metadata,
and handling of missing objects.

The tests assume the download endpoint is:

    GET /objects/{object_key}/download-url

The successful response is expected to contain a ``download_url`` field.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, quote, urlparse

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from moto import mock_aws

from app.config import get_settings


pytestmark = pytest.mark.integration

JWT_TEST_SECRET = "integration-test-secret-that-is-long-enough"
JWT_TEST_ALGORITHM = "HS256"


def create_access_token(
    subject: str = "integration-test-user",
) -> str:
    """Create a short-lived JWT accepted by the application."""
    settings = get_settings()

    secret = settings.jwt_secret_key
    if secret is None:
        signing_key = JWT_TEST_SECRET
    else:
        signing_key = secret.get_secret_value()

    now = datetime.now(UTC)

    payload = {
        "sub": subject,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=5),
    }

    return jwt.encode(
        payload,
        signing_key,
        algorithm=settings.jwt_algorithm or JWT_TEST_ALGORITHM,
    )


@pytest.fixture
def authorization_headers() -> dict[str, str]:
    """Return valid bearer authentication headers."""
    return {
        "Authorization": f"Bearer {create_access_token()}",
    }


@pytest.fixture
def download_object(
    s3_client: Any,
    s3_bucket: str,
    sample_object_key: str,
    sample_file_content: bytes,
    sample_content_type: str,
) -> dict[str, str]:
    """Create an object in the mocked S3 bucket for download tests."""
    s3_client.put_object(
        Bucket=s3_bucket,
        Key=sample_object_key,
        Body=sample_file_content,
        ContentType=sample_content_type,
        Metadata={
            "uploaded-by": "integration-test-user",
        },
    )

    return {
        "bucket": s3_bucket,
        "key": sample_object_key,
        "content_type": sample_content_type,
    }


def build_download_path(object_key: str) -> str:
    """Build a URL-safe download endpoint path for an S3 object key."""
    encoded_key = quote(object_key, safe="")
    return f"/objects/{encoded_key}/download-url"


def assert_valid_presigned_get_url(
    download_url: str,
    expected_bucket: str,
    expected_object_key: str,
) -> None:
    """Validate the structure and signing parameters of a presigned GET URL."""
    parsed_url = urlparse(download_url)
    query_parameters = parse_qs(parsed_url.query)

    assert parsed_url.scheme in {"http", "https"}
    assert parsed_url.netloc
    assert parsed_url.path

    assert "X-Amz-Algorithm" in query_parameters
    assert "X-Amz-Credential" in query_parameters
    assert "X-Amz-Date" in query_parameters
    assert "X-Amz-Expires" in query_parameters
    assert "X-Amz-SignedHeaders" in query_parameters
    assert "X-Amz-Signature" in query_parameters

    assert query_parameters["X-Amz-Algorithm"] == [
        "AWS4-HMAC-SHA256",
    ]

    assert query_parameters["X-Amz-Expires"][0].isdigit()
    assert int(query_parameters["X-Amz-Expires"][0]) > 0

    assert expected_bucket in parsed_url.path
    assert expected_object_key.split("/")[-1] in parsed_url.path


def test_authenticated_user_can_request_download_url(
    client: TestClient,
    authorization_headers: dict[str, str],
    download_object: dict[str, str],
) -> None:
    """An authenticated user can obtain a presigned URL for an existing object."""
    response = client.get(
        build_download_path(download_object["key"]),
        headers=authorization_headers,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert "download_url" in response_data
    assert isinstance(response_data["download_url"], str)
    assert response_data["download_url"]


def test_download_url_contains_valid_signature_parameters(
    client: TestClient,
    authorization_headers: dict[str, str],
    download_object: dict[str, str],
) -> None:
    """The generated download URL contains the expected SigV4 parameters."""
    response = client.get(
        build_download_path(download_object["key"]),
        headers=authorization_headers,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert_valid_presigned_get_url(
        download_url=response_data["download_url"],
        expected_bucket=download_object["bucket"],
        expected_object_key=download_object["key"],
    )


def test_download_request_requires_authentication(
    client: TestClient,
    download_object: dict[str, str],
) -> None:
    """Unauthenticated callers cannot obtain download URLs."""
    response = client.get(
        build_download_path(download_object["key"]),
    )

    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Bearer"


def test_download_request_rejects_invalid_token(
    client: TestClient,
    download_object: dict[str, str],
) -> None:
    """Invalid bearer tokens cannot obtain download URLs."""
    response = client.get(
        build_download_path(download_object["key"]),
        headers={
            "Authorization": "Bearer invalid.integration.token",
        },
    )

    assert response.status_code == 401


def test_download_request_returns_not_found_for_missing_object(
    client: TestClient,
    authorization_headers: dict[str, str],
) -> None:
    """A missing S3 object must not produce a usable download URL."""
    response = client.get(
        build_download_path("uploads/missing-object.txt"),
        headers=authorization_headers,
    )

    assert response.status_code == 404


def test_download_url_is_generated_for_the_requested_object(
    client: TestClient,
    authorization_headers: dict[str, str],
    download_object: dict[str, str],
) -> None:
    """The returned URL must identify the requested S3 object."""
    response = client.get(
        build_download_path(download_object["key"]),
        headers=authorization_headers,
    )

    assert response.status_code == 200

    download_url = response.json()["download_url"]
    parsed_url = urlparse(download_url)

    assert download_object["key"].split("/")[-1] in parsed_url.path


def test_download_request_does_not_modify_stored_object(
    client: TestClient,
    authorization_headers: dict[str, str],
    download_object: dict[str, str],
    s3_client: Any,
) -> None:
    """Generating a download URL must not modify the stored object."""
    before = s3_client.head_object(
        Bucket=download_object["bucket"],
        Key=download_object["key"],
    )

    response = client.get(
        build_download_path(download_object["key"]),
        headers=authorization_headers,
    )

    assert response.status_code == 200

    after = s3_client.head_object(
        Bucket=download_object["bucket"],
        Key=download_object["key"],
    )

    assert after["ETag"] == before["ETag"]
    assert after["ContentLength"] == before["ContentLength"]
    assert after["ContentType"] == before["ContentType"]
    assert after["Metadata"] == before["Metadata"]


def test_download_url_expiration_is_within_configured_limit(
    client: TestClient,
    authorization_headers: dict[str, str],
    download_object: dict[str, str],
) -> None:
    """The presigned URL expiry must match the configured application limit."""
    response = client.get(
        build_download_path(download_object["key"]),
        headers=authorization_headers,
    )

    assert response.status_code == 200

    download_url = response.json()["download_url"]
    query_parameters = parse_qs(urlparse(download_url).query)

    settings = get_settings()
    configured_expiration = settings.presigned_url_expiration_seconds
    actual_expiration = int(query_parameters["X-Amz-Expires"][0])

    assert actual_expiration == configured_expiration