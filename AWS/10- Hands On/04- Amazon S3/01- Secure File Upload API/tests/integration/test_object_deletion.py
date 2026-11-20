"""Integration tests for authenticated S3 object deletion.

The tests use the application's FastAPI client and Moto-backed S3 bucket.
They verify successful deletion, authentication enforcement, missing-object
behavior, and the resulting S3 object state.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import get_settings


pytestmark = pytest.mark.integration


def _create_access_token(subject: str = "integration-test-user") -> str:
    """Create a short-lived JWT using the application's configured credentials."""
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
def deletion_object(
    s3_client: Any,
    s3_bucket: str,
    sample_object_key: str,
    sample_file_content: bytes,
    sample_content_type: str,
) -> dict[str, str]:
    """Create an S3 object that can be used by deletion integration tests."""
    s3_client.put_object(
        Bucket=s3_bucket,
        Key=sample_object_key,
        Body=sample_file_content,
        ContentType=sample_content_type,
        Metadata={
            "created-by": "integration-test",
        },
    )

    return {
        "bucket": s3_bucket,
        "key": sample_object_key,
    }


def _delete_path(object_key: str) -> str:
    """Build a URL-safe object deletion endpoint path."""
    return f"/objects/{quote(object_key, safe='')}"


def test_authenticated_user_can_delete_object(
    client: TestClient,
    authorization_headers: dict[str, str],
    deletion_object: dict[str, str],
    s3_client: Any,
) -> None:
    """An authenticated user can delete an existing S3 object."""
    response = client.delete(
        _delete_path(deletion_object["key"]),
        headers=authorization_headers,
    )

    assert response.status_code in {200, 204}

    with pytest.raises(s3_client.exceptions.NoSuchKey):
        s3_client.get_object(
            Bucket=deletion_object["bucket"],
            Key=deletion_object["key"],
        )


def test_delete_request_requires_authentication(
    client: TestClient,
    deletion_object: dict[str, str],
    s3_client: Any,
) -> None:
    """Unauthenticated callers cannot delete stored objects."""
    response = client.delete(_delete_path(deletion_object["key"]))

    assert response.status_code == 401

    stored_object = s3_client.get_object(
        Bucket=deletion_object["bucket"],
        Key=deletion_object["key"],
    )
    assert stored_object["Body"].read()


def test_delete_request_rejects_invalid_token(
    client: TestClient,
    deletion_object: dict[str, str],
    s3_client: Any,
) -> None:
    """Invalid bearer tokens cannot delete stored objects."""
    response = client.delete(
        _delete_path(deletion_object["key"]),
        headers={
            "Authorization": "Bearer invalid.integration.token",
        },
    )

    assert response.status_code == 401

    stored_object = s3_client.get_object(
        Bucket=deletion_object["bucket"],
        Key=deletion_object["key"],
    )
    assert stored_object["Body"].read()


def test_delete_request_returns_not_found_for_missing_object(
    client: TestClient,
    authorization_headers: dict[str, str],
) -> None:
    """Deleting an object that does not exist returns HTTP 404."""
    response = client.delete(
        _delete_path("uploads/missing-object.txt"),
        headers=authorization_headers,
    )

    assert response.status_code == 404


def test_delete_request_does_not_delete_another_object(
    client: TestClient,
    authorization_headers: dict[str, str],
    deletion_object: dict[str, str],
    s3_client: Any,
) -> None:
    """Deleting one key must not affect other objects in the bucket."""
    unrelated_key = "uploads/unrelated-object.txt"
    unrelated_content = b"This object must remain untouched."

    s3_client.put_object(
        Bucket=deletion_object["bucket"],
        Key=unrelated_key,
        Body=unrelated_content,
    )

    response = client.delete(
        _delete_path(deletion_object["key"]),
        headers=authorization_headers,
    )

    assert response.status_code in {200, 204}

    unrelated_object = s3_client.get_object(
        Bucket=deletion_object["bucket"],
        Key=unrelated_key,
    )

    assert unrelated_object["Body"].read() == unrelated_content


def test_delete_request_preserves_object_when_authentication_fails(
    client: TestClient,
    deletion_object: dict[str, str],
    s3_client: Any,
) -> None:
    """A failed authentication attempt must leave the object unchanged."""
    original_object = s3_client.get_object(
        Bucket=deletion_object["bucket"],
        Key=deletion_object["key"],
    )
    original_content = original_object["Body"].read()

    response = client.delete(
        _delete_path(deletion_object["key"]),
        headers={
            "Authorization": "Bearer invalid.integration.token",
        },
    )

    assert response.status_code == 401

    remaining_object = s3_client.get_object(
        Bucket=deletion_object["bucket"],
        Key=deletion_object["key"],
    )

    assert remaining_object["Body"].read() == original_content