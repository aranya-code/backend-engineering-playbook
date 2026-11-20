"""Integration tests for the authenticated S3 upload-initiation workflow.

These tests exercise the FastAPI upload endpoint and verify that it generates
a usable presigned S3 PUT URL without uploading file contents through the API.
The actual S3 upload is performed with the required headers returned by the
API, then verified against the Moto-backed bucket.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import get_settings


pytestmark = pytest.mark.integration


def _create_access_token(subject: str = "integration-test-user") -> str:
    """Create a short-lived JWT accepted by the application's auth dependency."""
    settings = get_settings()

    if settings.jwt_secret_key is None:
        raise RuntimeError("JWT authentication is not configured for integration tests.")

    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=5),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


@pytest.fixture
def authorization_headers() -> dict[str, str]:
    """Return valid bearer authentication headers."""
    return {
        "Authorization": f"Bearer {_create_access_token()}",
    }


@pytest.fixture
def upload_request_payload(
    sample_filename: str,
    sample_content_type: str,
    sample_file_content: bytes,
) -> dict[str, Any]:
    """Build a valid upload-initiation request using shared test fixtures."""
    return {
        "filename": sample_filename,
        "content_type": sample_content_type,
        "size_bytes": len(sample_file_content),
    }


def _extract_presigned_url(response_data: dict[str, Any]) -> str:
    """Extract the presigned URL from the API response."""
    upload_url = response_data.get("upload_url")

    assert isinstance(upload_url, str)
    assert upload_url.startswith("http")

    return upload_url


def _extract_required_headers(response_data: dict[str, Any]) -> dict[str, str]:
    """Extract the HTTP headers required by the presigned PUT request."""
    required_headers = response_data.get("required_headers")

    assert isinstance(required_headers, dict)
    assert all(
        isinstance(name, str) and isinstance(value, str)
        for name, value in required_headers.items()
    )

    return required_headers


def test_authenticated_user_can_initiate_upload(
    client: TestClient,
    authorization_headers: dict[str, str],
    upload_request_payload: dict[str, Any],
) -> None:
    """An authenticated user can request a presigned upload URL."""
    response = client.post(
        "/objects/upload",
        headers=authorization_headers,
        json=upload_request_payload,
    )

    assert response.status_code in {200, 201}

    response_data = response.json()

    upload_url = _extract_presigned_url(response_data)
    required_headers = _extract_required_headers(response_data)

    assert "object_key" in response_data
    assert isinstance(response_data["object_key"], str)
    assert response_data["object_key"]

    assert "Content-Type" in required_headers
    assert required_headers["Content-Type"] == upload_request_payload["content_type"]

    parsed_url = urlparse(upload_url)
    query_parameters = parse_qs(parsed_url.query)

    assert parsed_url.scheme == "https"
    assert parsed_url.netloc
    assert "X-Amz-Algorithm" in query_parameters
    assert "X-Amz-Credential" in query_parameters
    assert "X-Amz-Signature" in query_parameters


def test_upload_initiation_requires_authentication(
    client: TestClient,
    upload_request_payload: dict[str, Any],
) -> None:
    """Unauthenticated callers cannot request presigned upload URLs."""
    response = client.post(
        "/objects/upload",
        json=upload_request_payload,
    )

    assert response.status_code == 401


def test_upload_initiation_rejects_invalid_bearer_token(
    client: TestClient,
    upload_request_payload: dict[str, Any],
) -> None:
    """Invalid bearer credentials cannot initiate an upload."""
    response = client.post(
        "/objects/upload",
        headers={
            "Authorization": "Bearer invalid.integration.token",
        },
        json=upload_request_payload,
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("payload_override", "expected_status"),
    [
        ({"filename": ""}, 422),
        ({"filename": "../unsafe.txt"}, 422),
        ({"content_type": "application/x-executable"}, 422),
        ({"size_bytes": 0}, 422),
        ({"size_bytes": -1}, 422),
    ],
)
def test_upload_initiation_rejects_invalid_metadata(
    client: TestClient,
    authorization_headers: dict[str, str],
    upload_request_payload: dict[str, Any],
    payload_override: dict[str, Any],
    expected_status: int,
) -> None:
    """Invalid filenames, content types, and sizes are rejected."""
    payload = {
        **upload_request_payload,
        **payload_override,
    }

    response = client.post(
        "/objects/upload",
        headers=authorization_headers,
        json=payload,
    )

    assert response.status_code == expected_status


def test_upload_initiation_rejects_file_exceeding_configured_limit(
    client: TestClient,
    authorization_headers: dict[str, str],
    upload_request_payload: dict[str, Any],
) -> None:
    """Declared upload sizes above the configured maximum are rejected."""
    settings = get_settings()
    payload = {
        **upload_request_payload,
        "size_bytes": settings.max_upload_size_bytes + 1,
    }

    response = client.post(
        "/objects/upload",
        headers=authorization_headers,
        json=payload,
    )

    assert response.status_code == 422


def test_upload_initiation_rejects_missing_required_fields(
    client: TestClient,
    authorization_headers: dict[str, str],
) -> None:
    """The upload endpoint rejects requests without required metadata."""
    response = client.post(
        "/objects/upload",
        headers=authorization_headers,
        json={},
    )

    assert response.status_code == 422


def test_upload_initiation_does_not_upload_object_to_s3(
    client: TestClient,
    authorization_headers: dict[str, str],
    upload_request_payload: dict[str, Any],
    s3_client: Any,
    s3_bucket: str,
) -> None:
    """Initiating an upload generates a URL but does not store file contents."""
    response = client.post(
        "/objects/upload",
        headers=authorization_headers,
        json=upload_request_payload,
    )

    assert response.status_code in {200, 201}

    response_data = response.json()
    object_key = response_data["object_key"]

    with pytest.raises(s3_client.exceptions.NoSuchKey):
        s3_client.get_object(
            Bucket=s3_bucket,
            Key=object_key,
        )


def test_presigned_upload_url_can_upload_to_s3(
    client: TestClient,
    authorization_headers: dict[str, str],
    upload_request_payload: dict[str, Any],
    sample_file_content: bytes,
    s3_client: Any,
    s3_bucket: str,
) -> None:
    """A generated presigned URL accepts a PUT using its required headers."""
    response = client.post(
        "/objects/upload",
        headers=authorization_headers,
        json=upload_request_payload,
    )

    assert response.status_code in {200, 201}

    response_data = response.json()
    upload_url = _extract_presigned_url(response_data)
    required_headers = _extract_required_headers(response_data)
    object_key = response_data["object_key"]

    upload_response = httpx.put(
        upload_url,
        content=sample_file_content,
        headers=required_headers,
        timeout=10.0,
    )

    assert upload_response.status_code in {200, 204}

    stored_object = s3_client.get_object(
        Bucket=s3_bucket,
        Key=object_key,
    )

    assert stored_object["Body"].read() == sample_file_content
    assert stored_object["ContentType"] == upload_request_payload["content_type"]


def test_presigned_upload_url_uses_application_upload_prefix(
    client: TestClient,
    authorization_headers: dict[str, str],
    upload_request_payload: dict[str, Any],
) -> None:
    """Generated object keys remain within the configured upload prefix."""
    settings = get_settings()

    response = client.post(
        "/objects/upload",
        headers=authorization_headers,
        json=upload_request_payload,
    )

    assert response.status_code in {200, 201}

    object_key = response.json()["object_key"]
    configured_prefix = settings.s3_upload_prefix.rstrip("/")

    assert object_key.startswith(f"{configured_prefix}/")
    assert ".." not in object_key
    assert not object_key.startswith("/")