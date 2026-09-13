"""Tests for webhook ingestion API routes."""

from __future__ import annotations

import hashlib
import hmac
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes import router


WEBHOOK_SECRET = "test-webhook-secret"


@pytest.fixture
def app() -> FastAPI:
    """Create an isolated FastAPI application for route tests."""
    application = FastAPI()
    application.state.webhook_secret = WEBHOOK_SECRET
    application.include_router(router)
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a synchronous test client for the webhook API."""
    return TestClient(app)


def build_signature(
    payload: bytes,
    *,
    timestamp: str,
    secret: str = WEBHOOK_SECRET,
) -> str:
    """Build the HMAC-SHA256 signature expected by the webhook route."""
    signed_payload = timestamp.encode("utf-8") + b"." + payload

    return hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()


def test_receive_webhook_accepts_valid_signed_request(
    client: TestClient,
) -> None:
    """Return 202 when the webhook has valid authentication metadata."""
    payload = b'{"id":"evt_123","type":"payment.created"}'
    timestamp = str(int(time.time()))
    signature = build_signature(payload, timestamp=timestamp)

    response = client.post(
        "/webhooks",
        content=payload,
        headers={
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Timestamp": timestamp,
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "status": "accepted",
        "message": "Webhook accepted for processing.",
    }


def test_receive_webhook_rejects_missing_signature(
    client: TestClient,
) -> None:
    """Reject a webhook when the signature header is missing."""
    payload = b'{"id":"evt_123","type":"payment.created"}'
    timestamp = str(int(time.time()))

    response = client.post(
        "/webhooks",
        content=payload,
        headers={"X-Webhook-Timestamp": timestamp},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing webhook authentication headers."


def test_receive_webhook_rejects_missing_timestamp(
    client: TestClient,
) -> None:
    """Reject a webhook when the timestamp header is missing."""
    payload = b'{"id":"evt_123","type":"payment.created"}'
    signature = build_signature(
        payload,
        timestamp=str(int(time.time())),
    )

    response = client.post(
        "/webhooks",
        content=payload,
        headers={"X-Webhook-Signature": f"sha256={signature}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing webhook authentication headers."


def test_receive_webhook_rejects_invalid_signature(
    client: TestClient,
) -> None:
    """Reject a webhook when its HMAC signature does not match."""
    payload = b'{"id":"evt_123","type":"payment.created"}'
    timestamp = str(int(time.time()))

    response = client.post(
        "/webhooks",
        content=payload,
        headers={
            "X-Webhook-Signature": "sha256=invalid-signature",
            "X-Webhook-Timestamp": timestamp,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid webhook signature."


def test_receive_webhook_rejects_invalid_timestamp(
    client: TestClient,
) -> None:
    """Reject a webhook when its timestamp is not a Unix timestamp."""
    payload = b'{"id":"evt_123","type":"payment.created"}'
    timestamp = "not-a-timestamp"
    signature = build_signature(payload, timestamp=timestamp)

    response = client.post(
        "/webhooks",
        content=payload,
        headers={
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Timestamp": timestamp,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid webhook timestamp."


def test_receive_webhook_rejects_replayed_request(
    client: TestClient,
) -> None:
    """Reject a webhook whose timestamp falls outside the replay window."""
    payload = b'{"id":"evt_123","type":"payment.created"}'
    timestamp = str(int(time.time()) - 301)
    signature = build_signature(payload, timestamp=timestamp)

    response = client.post(
        "/webhooks",
        content=payload,
        headers={
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Timestamp": timestamp,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Webhook timestamp is outside the allowed replay window."
    )


def test_receive_webhook_rejects_empty_payload(
    client: TestClient,
) -> None:
    """Reject a request with an empty webhook body."""
    timestamp = str(int(time.time()))
    signature = build_signature(b"", timestamp=timestamp)

    response = client.post(
        "/webhooks",
        content=b"",
        headers={
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Timestamp": timestamp,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Webhook payload must not be empty."


@pytest.mark.parametrize(
    "signature",
    [
        "",
        "invalid",
        "sha256=",
        "sha256-invalid",
    ],
)
def test_receive_webhook_rejects_malformed_signature(
    client: TestClient,
    signature: str,
) -> None:
    """Reject malformed signature values without accepting the request."""
    payload = b'{"id":"evt_123","type":"payment.created"}'
    timestamp = str(int(time.time()))

    response = client.post(
        "/webhooks",
        content=payload,
        headers={
            "X-Webhook-Signature": signature,
            "X-Webhook-Timestamp": timestamp,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid webhook signature."


def test_receive_webhook_does_not_accept_signature_from_wrong_secret(
    client: TestClient,
) -> None:
    """Reject signatures generated with a different signing secret."""
    payload = b'{"id":"evt_123","type":"payment.created"}'
    timestamp = str(int(time.time()))
    signature = build_signature(
        payload,
        timestamp=timestamp,
        secret="wrong-secret",
    )

    response = client.post(
        "/webhooks",
        content=payload,
        headers={
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Timestamp": timestamp,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid webhook signature."

"""Tests for webhook ingestion API routes."""

from __future__ import annotations

import hashlib
import hmac
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes import router


WEBHOOK_SECRET = "test-webhook-secret"


@pytest.fixture
def app() -> FastAPI:
    """Create an isolated FastAPI application for route tests."""
    application = FastAPI()
    application.state.webhook_secret = WEBHOOK_SECRET
    application.include_router(router)
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a synchronous test client for the webhook API."""
    return TestClient(app)


def build_signature(
    payload: bytes,
    *,
    timestamp: str,
    secret: str = WEBHOOK_SECRET,
) -> str:
    """Build the HMAC-SHA256 signature expected by the webhook route."""
    signed_payload = timestamp.encode("utf-8") + b"." + payload

    return hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()


def test_receive_webhook_accepts_valid_signed_request(
    client: TestClient,
) -> None:
    """Return 202 when the webhook has valid authentication metadata."""
    payload = b'{"id":"evt_123","type":"payment.created"}'
    timestamp = str(int(time.time()))
    signature = build_signature(payload, timestamp=timestamp)

    response = client.post(
        "/webhooks",
        content=payload,
        headers={
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Timestamp": timestamp,
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "status": "accepted",
        "message": "Webhook accepted for processing.",
    }


def test_receive_webhook_rejects_missing_signature(
    client: TestClient,
) -> None:
    """Reject a webhook when the signature header is missing."""
    payload = b'{"id":"evt_123","type":"payment.created"}'
    timestamp = str(int(time.time()))

    response = client.post(
        "/webhooks",
        content=payload,
        headers={"X-Webhook-Timestamp": timestamp},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing webhook authentication headers."


def test_receive_webhook_rejects_missing_timestamp(
    client: TestClient,
) -> None:
    """Reject a webhook when the timestamp header is missing."""
    payload = b'{"id":"evt_123","type":"payment.created"}'
    signature = build_signature(
        payload,
        timestamp=str(int(time.time())),
    )

    response = client.post(
        "/webhooks",
        content=payload,
        headers={"X-Webhook-Signature": f"sha256={signature}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing webhook authentication headers."


def test_receive_webhook_rejects_invalid_signature(
    client: TestClient,
) -> None:
    """Reject a webhook when its HMAC signature does not match."""
    payload = b'{"id":"evt_123","type":"payment.created"}'
    timestamp = str(int(time.time()))

    response = client.post(
        "/webhooks",
        content=payload,
        headers={
            "X-Webhook-Signature": "sha256=invalid-signature",
            "X-Webhook-Timestamp": timestamp,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid webhook signature."


def test_receive_webhook_rejects_invalid_timestamp(
    client: TestClient,
) -> None:
    """Reject a webhook when its timestamp is not a Unix timestamp."""
    payload = b'{"id":"evt_123","type":"payment.created"}'
    timestamp = "not-a-timestamp"
    signature = build_signature(payload, timestamp=timestamp)

    response = client.post(
        "/webhooks",
        content=payload,
        headers={
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Timestamp": timestamp,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid webhook timestamp."


def test_receive_webhook_rejects_replayed_request(
    client: TestClient,
) -> None:
    """Reject a webhook whose timestamp falls outside the replay window."""
    payload = b'{"id":"evt_123","type":"payment.created"}'
    timestamp = str(int(time.time()) - 301)
    signature = build_signature(payload, timestamp=timestamp)

    response = client.post(
        "/webhooks",
        content=payload,
        headers={
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Timestamp": timestamp,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Webhook timestamp is outside the allowed replay window."
    )


def test_receive_webhook_rejects_empty_payload(
    client: TestClient,
) -> None:
    """Reject a request with an empty webhook body."""
    timestamp = str(int(time.time()))
    signature = build_signature(b"", timestamp=timestamp)

    response = client.post(
        "/webhooks",
        content=b"",
        headers={
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Timestamp": timestamp,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Webhook payload must not be empty."


@pytest.mark.parametrize(
    "signature",
    [
        "",
        "invalid",
        "sha256=",
        "sha256-invalid",
    ],
)
def test_receive_webhook_rejects_malformed_signature(
    client: TestClient,
    signature: str,
) -> None:
    """Reject malformed signature values without accepting the request."""
    payload = b'{"id":"evt_123","type":"payment.created"}'
    timestamp = str(int(time.time()))

    response = client.post(
        "/webhooks",
        content=payload,
        headers={
            "X-Webhook-Signature": signature,
            "X-Webhook-Timestamp": timestamp,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid webhook signature."


def test_receive_webhook_does_not_accept_signature_from_wrong_secret(
    client: TestClient,
) -> None:
    """Reject signatures generated with a different signing secret."""
    payload = b'{"id":"evt_123","type":"payment.created"}'
    timestamp = str(int(time.time()))
    signature = build_signature(
        payload,
        timestamp=timestamp,
        secret="wrong-secret",
    )

    response = client.post(
        "/webhooks",
        content=payload,
        headers={
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Timestamp": timestamp,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid webhook signature."