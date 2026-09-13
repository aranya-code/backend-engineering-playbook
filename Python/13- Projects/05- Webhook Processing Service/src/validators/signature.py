"""Webhook signature validation utilities."""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass


class SignatureValidationError(ValueError):
    """Raised when webhook signature validation fails."""


@dataclass(frozen=True, slots=True)
class SignatureValidator:
    """Validate HMAC-signed webhook requests and their timestamps."""

    secret: str
    replay_window_seconds: int = 300
    algorithm: str = "sha256"

    def __post_init__(self) -> None:
        """Validate validator configuration."""
        if not self.secret:
            raise ValueError("Webhook signing secret must not be empty.")

        if self.replay_window_seconds <= 0:
            raise ValueError("replay_window_seconds must be greater than zero.")

        if self.algorithm.lower() != "sha256":
            raise ValueError("Only SHA-256 signatures are supported.")

    def validate(
        self,
        payload: bytes,
        signature: str,
        timestamp: str,
        *,
        now: float | None = None,
    ) -> None:
        """Validate a webhook signature and reject stale requests."""
        timestamp_value = self._parse_timestamp(timestamp)
        current_time = time.time() if now is None else now

        if abs(current_time - timestamp_value) > self.replay_window_seconds:
            raise SignatureValidationError(
                "Webhook timestamp is outside the allowed replay window."
            )

        expected_signature = self._build_signature(
            payload,
            timestamp,
        )

        provided_signature = signature.removeprefix("sha256=")

        if not hmac.compare_digest(expected_signature, provided_signature):
            raise SignatureValidationError("Invalid webhook signature.")

    def _build_signature(self, payload: bytes, timestamp: str) -> str:
        """Generate the expected HMAC-SHA256 signature."""
        signed_payload = timestamp.encode("utf-8") + b"." + payload

        return hmac.new(
            self.secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _parse_timestamp(timestamp: str) -> int:
        """Parse a Unix timestamp from a webhook request."""
        try:
            return int(timestamp)
        except (TypeError, ValueError) as exc:
            raise SignatureValidationError(
                "Webhook timestamp must be a valid Unix timestamp."
            ) from exc

"""Webhook signature validation utilities."""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass


class SignatureValidationError(ValueError):
    """Raised when webhook signature validation fails."""


@dataclass(frozen=True, slots=True)
class SignatureValidator:
    """Validate HMAC-signed webhook requests and their timestamps."""

    secret: str
    replay_window_seconds: int = 300
    algorithm: str = "sha256"

    def __post_init__(self) -> None:
        """Validate validator configuration."""
        if not self.secret:
            raise ValueError("Webhook signing secret must not be empty.")

        if self.replay_window_seconds <= 0:
            raise ValueError("replay_window_seconds must be greater than zero.")

        if self.algorithm.lower() != "sha256":
            raise ValueError("Only SHA-256 signatures are supported.")

    def validate(
        self,
        payload: bytes,
        signature: str,
        timestamp: str,
        *,
        now: float | None = None,
    ) -> None:
        """Validate a webhook signature and reject stale requests."""
        timestamp_value = self._parse_timestamp(timestamp)
        current_time = time.time() if now is None else now

        if abs(current_time - timestamp_value) > self.replay_window_seconds:
            raise SignatureValidationError(
                "Webhook timestamp is outside the allowed replay window."
            )

        expected_signature = self._build_signature(
            payload,
            timestamp,
        )

        provided_signature = signature.removeprefix("sha256=")

        if not hmac.compare_digest(expected_signature, provided_signature):
            raise SignatureValidationError("Invalid webhook signature.")

    def _build_signature(self, payload: bytes, timestamp: str) -> str:
        """Generate the expected HMAC-SHA256 signature."""
        signed_payload = timestamp.encode("utf-8") + b"." + payload

        return hmac.new(
            self.secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _parse_timestamp(timestamp: str) -> int:
        """Parse a Unix timestamp from a webhook request."""
        try:
            return int(timestamp)
        except (TypeError, ValueError) as exc:
            raise SignatureValidationError(
                "Webhook timestamp must be a valid Unix timestamp."
            ) from exc