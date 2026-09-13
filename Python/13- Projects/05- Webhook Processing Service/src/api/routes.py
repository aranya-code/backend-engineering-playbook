"""HTTP API routes for webhook ingestion."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request, status

from src.config import WebhookServiceConfig

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

_config = WebhookServiceConfig.from_environment()


def _verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify an HMAC-SHA256 webhook signature."""
    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    provided = signature.removeprefix("sha256=")

    return hmac.compare_digest(expected, provided)


def _validate_timestamp(timestamp: str) -> None:
    """Reject webhook requests outside the configured replay window."""
    try:
        received_at = int(timestamp)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook timestamp.",
        ) from exc

    if abs(time.time() - received_at) > _config.replay_window_seconds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Webhook timestamp is outside the allowed replay window.",
        )


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
)
async def receive_webhook(
    request: Request,
    x_webhook_signature: Annotated[str | None, Header()] = None,
    x_webhook_timestamp: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    """Validate and accept an incoming webhook for asynchronous processing."""
    payload = await request.body()

    if _config.signature_validation_enabled:
        if not x_webhook_signature or not x_webhook_timestamp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing webhook authentication headers.",
            )

        _validate_timestamp(x_webhook_timestamp)

        webhook_secret = request.app.state.webhook_secret

        if not isinstance(webhook_secret, str) or not webhook_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Webhook authentication is not configured.",
            )

        signed_payload = f"{x_webhook_timestamp}.".encode("utf-8") + payload

        if not _verify_signature(
            signed_payload,
            x_webhook_signature,
            webhook_secret,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature.",
            )

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook payload must not be empty.",
        )

    # Persistence and queue publication should be performed by injected
    # application services. The HTTP layer should acknowledge only after
    # the event has crossed the configured durability boundary.
    return {
        "status": "accepted",
        "message": "Webhook accepted for processing.",
    }

"""HTTP API routes for webhook ingestion."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request, status

from src.config import WebhookServiceConfig

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

_config = WebhookServiceConfig.from_environment()


def _verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify an HMAC-SHA256 webhook signature."""
    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    provided = signature.removeprefix("sha256=")

    return hmac.compare_digest(expected, provided)


def _validate_timestamp(timestamp: str) -> None:
    """Reject webhook requests outside the configured replay window."""
    try:
        received_at = int(timestamp)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook timestamp.",
        ) from exc

    if abs(time.time() - received_at) > _config.replay_window_seconds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Webhook timestamp is outside the allowed replay window.",
        )


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
)
async def receive_webhook(
    request: Request,
    x_webhook_signature: Annotated[str | None, Header()] = None,
    x_webhook_timestamp: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    """Validate and accept an incoming webhook for asynchronous processing."""
    payload = await request.body()

    if _config.signature_validation_enabled:
        if not x_webhook_signature or not x_webhook_timestamp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing webhook authentication headers.",
            )

        _validate_timestamp(x_webhook_timestamp)

        webhook_secret = request.app.state.webhook_secret

        if not isinstance(webhook_secret, str) or not webhook_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Webhook authentication is not configured.",
            )

        signed_payload = f"{x_webhook_timestamp}.".encode("utf-8") + payload

        if not _verify_signature(
            signed_payload,
            x_webhook_signature,
            webhook_secret,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature.",
            )

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook payload must not be empty.",
        )

    # Persistence and queue publication should be performed by injected
    # application services. The HTTP layer should acknowledge only after
    # the event has crossed the configured durability boundary.
    return {
        "status": "accepted",
        "message": "Webhook accepted for processing.",
    }