"""Tests for webhook HMAC signature and replay-window validation."""

from __future__ import annotations

import hashlib
import hmac
import time

import pytest

from src.validators.signature import (
    SignatureValidationError,
    SignatureValidator,
)


SECRET = "test-webhook-secret"
PAYLOAD = b'{"id":"evt_123","type":"payment.created"}'


def build_signature(
    payload: bytes,
    *,
    timestamp: str,
    secret: str = SECRET,
) -> str:
    """Generate an HMAC-SHA256 signature for a webhook payload."""
    signed_payload = timestamp.encode("utf-8") + b"." + payload

    return hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()


@pytest.fixture
def validator() -> SignatureValidator:
    """Create a signature validator with a deterministic test secret."""
    return SignatureValidator(
        secret=SECRET,
        replay_window_seconds=300,
    )


def test_validate_accepts_valid_signature(
    validator: SignatureValidator,
) -> None:
    """Accept a correctly signed webhook within the replay window."""
    now = 1_700_000_000.0
    timestamp = str(int(now))
    signature = build_signature(PAYLOAD, timestamp=timestamp)

    validator.validate(
        PAYLOAD,
        signature,
        timestamp,
        now=now,
    )


def test_validate_accepts_sha256_prefixed_signature(
    validator: SignatureValidator,
) -> None:
    """Accept signatures using the conventional sha256= prefix."""
    now = 1_700_000_000.0
    timestamp = str(int(now))
    signature = build_signature(PAYLOAD, timestamp=timestamp)

    validator.validate(
        PAYLOAD,
        f"sha256={signature}",
        timestamp,
        now=now,
    )


def test_validate_rejects_invalid_signature(
    validator: SignatureValidator,
) -> None:
    """Reject a signature that does not match the payload."""
    now = 1_700_000_000.0
    timestamp = str(int(now))

    with pytest.raises(
        SignatureValidationError,
        match="Invalid webhook signature",
    ):
        validator.validate(
            PAYLOAD,
            "invalid-signature",
            timestamp,
            now=now,
        )


def test_validate_rejects_signature_for_modified_payload(
    validator: SignatureValidator,
) -> None:
    """Reject a valid signature when the request body has been modified."""
    now = 1_700_000_000.0
    timestamp = str(int(now))
    signature = build_signature(PAYLOAD, timestamp=timestamp)

    modified_payload = PAYLOAD + b" "

    with pytest.raises(
        SignatureValidationError,
        match="Invalid webhook signature",
    ):
        validator.validate(
            modified_payload,
            signature,
            timestamp,
            now=now,
        )


def test_validate_rejects_signature_for_modified_timestamp(
    validator: SignatureValidator,
) -> None:
    """Reject a signature when the signed timestamp is changed."""
    now = 1_700_000_000.0
    signed_timestamp = str(int(now))
    signature = build_signature(
        PAYLOAD,
        timestamp=signed_timestamp,
    )

    with pytest.raises(
        SignatureValidationError,
        match="Invalid webhook signature",
    ):
        validator.validate(
            PAYLOAD,
            signature,
            str(int(now) + 1),
            now=now,
        )


@pytest.mark.parametrize(
    "timestamp",
    [
        "not-a-timestamp",
        "",
        "1.5",
        "123abc",
    ],
)
def test_validate_rejects_invalid_timestamp(
    validator: SignatureValidator,
    timestamp: str,
) -> None:
    """Reject timestamps that cannot be parsed as Unix timestamps."""
    with pytest.raises(
        SignatureValidationError,
        match="valid Unix timestamp",
    ):
        validator.validate(
            PAYLOAD,
            "irrelevant",
            timestamp,
            now=1_700_000_000.0,
        )


@pytest.mark.parametrize(
    "timestamp_offset",
    [
        -301,
        301,
    ],
)
def test_validate_rejects_timestamp_outside_replay_window(
    validator: SignatureValidator,
    timestamp_offset: int,
) -> None:
    """Reject requests whose timestamps exceed the configured replay window."""
    now = 1_700_000_000.0
    timestamp = str(int(now + timestamp_offset))
    signature = build_signature(PAYLOAD, timestamp=timestamp)

    with pytest.raises(
        SignatureValidationError,
        match="outside the allowed replay window",
    ):
        validator.validate(
            PAYLOAD,
            signature,
            timestamp,
            now=now,
        )


def test_validate_accepts_timestamp_at_replay_window_boundary(
    validator: SignatureValidator,
) -> None:
    """Accept a request exactly at the configured replay-window boundary."""
    now = 1_700_000_000.0
    timestamp = str(int(now - validator.replay_window_seconds))
    signature = build_signature(PAYLOAD, timestamp=timestamp)

    validator.validate(
        PAYLOAD,
        signature,
        timestamp,
        now=now,
    )


def test_validate_uses_supplied_current_time(
    validator: SignatureValidator,
) -> None:
    """Use the injected clock when validating replay protection."""
    fixed_now = 1_700_000_000.0
    timestamp = str(int(fixed_now - 100))
    signature = build_signature(PAYLOAD, timestamp=timestamp)

    validator.validate(
        PAYLOAD,
        signature,
        timestamp,
        now=fixed_now,
    )


def test_validate_rejects_wrong_secret() -> None:
    """Reject a signature generated with a different secret."""
    validator = SignatureValidator(secret=SECRET)
    timestamp = str(int(time.time()))
    signature = build_signature(
        PAYLOAD,
        timestamp=timestamp,
        secret="different-secret",
    )

    with pytest.raises(
        SignatureValidationError,
        match="Invalid webhook signature",
    ):
        validator.validate(
            PAYLOAD,
            signature,
            timestamp,
        )


def test_validator_rejects_empty_secret() -> None:
    """Reject construction with an empty signing secret."""
    with pytest.raises(
        ValueError,
        match="signing secret must not be empty",
    ):
        SignatureValidator(secret="")


def test_validator_rejects_non_positive_replay_window() -> None:
    """Reject an invalid replay-window configuration."""
    with pytest.raises(
        ValueError,
        match="replay_window_seconds must be greater than zero",
    ):
        SignatureValidator(
            secret=SECRET,
            replay_window_seconds=0,
        )


def test_validator_rejects_unsupported_algorithm() -> None:
    """Reject algorithms that the validator does not implement."""
    with pytest.raises(
        ValueError,
        match="Only SHA-256 signatures are supported",
    ):
        SignatureValidator(
            secret=SECRET,
            algorithm="sha512",
        )

"""Tests for webhook HMAC signature and replay-window validation."""

from __future__ import annotations

import hashlib
import hmac
import time

import pytest

from src.validators.signature import (
    SignatureValidationError,
    SignatureValidator,
)


SECRET = "test-webhook-secret"
PAYLOAD = b'{"id":"evt_123","type":"payment.created"}'


def build_signature(
    payload: bytes,
    *,
    timestamp: str,
    secret: str = SECRET,
) -> str:
    """Generate an HMAC-SHA256 signature for a webhook payload."""
    signed_payload = timestamp.encode("utf-8") + b"." + payload

    return hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()


@pytest.fixture
def validator() -> SignatureValidator:
    """Create a signature validator with a deterministic test secret."""
    return SignatureValidator(
        secret=SECRET,
        replay_window_seconds=300,
    )


def test_validate_accepts_valid_signature(
    validator: SignatureValidator,
) -> None:
    """Accept a correctly signed webhook within the replay window."""
    now = 1_700_000_000.0
    timestamp = str(int(now))
    signature = build_signature(PAYLOAD, timestamp=timestamp)

    validator.validate(
        PAYLOAD,
        signature,
        timestamp,
        now=now,
    )


def test_validate_accepts_sha256_prefixed_signature(
    validator: SignatureValidator,
) -> None:
    """Accept signatures using the conventional sha256= prefix."""
    now = 1_700_000_000.0
    timestamp = str(int(now))
    signature = build_signature(PAYLOAD, timestamp=timestamp)

    validator.validate(
        PAYLOAD,
        f"sha256={signature}",
        timestamp,
        now=now,
    )


def test_validate_rejects_invalid_signature(
    validator: SignatureValidator,
) -> None:
    """Reject a signature that does not match the payload."""
    now = 1_700_000_000.0
    timestamp = str(int(now))

    with pytest.raises(
        SignatureValidationError,
        match="Invalid webhook signature",
    ):
        validator.validate(
            PAYLOAD,
            "invalid-signature",
            timestamp,
            now=now,
        )


def test_validate_rejects_signature_for_modified_payload(
    validator: SignatureValidator,
) -> None:
    """Reject a valid signature when the request body has been modified."""
    now = 1_700_000_000.0
    timestamp = str(int(now))
    signature = build_signature(PAYLOAD, timestamp=timestamp)

    modified_payload = PAYLOAD + b" "

    with pytest.raises(
        SignatureValidationError,
        match="Invalid webhook signature",
    ):
        validator.validate(
            modified_payload,
            signature,
            timestamp,
            now=now,
        )


def test_validate_rejects_signature_for_modified_timestamp(
    validator: SignatureValidator,
) -> None:
    """Reject a signature when the signed timestamp is changed."""
    now = 1_700_000_000.0
    signed_timestamp = str(int(now))
    signature = build_signature(
        PAYLOAD,
        timestamp=signed_timestamp,
    )

    with pytest.raises(
        SignatureValidationError,
        match="Invalid webhook signature",
    ):
        validator.validate(
            PAYLOAD,
            signature,
            str(int(now) + 1),
            now=now,
        )


@pytest.mark.parametrize(
    "timestamp",
    [
        "not-a-timestamp",
        "",
        "1.5",
        "123abc",
    ],
)
def test_validate_rejects_invalid_timestamp(
    validator: SignatureValidator,
    timestamp: str,
) -> None:
    """Reject timestamps that cannot be parsed as Unix timestamps."""
    with pytest.raises(
        SignatureValidationError,
        match="valid Unix timestamp",
    ):
        validator.validate(
            PAYLOAD,
            "irrelevant",
            timestamp,
            now=1_700_000_000.0,
        )


@pytest.mark.parametrize(
    "timestamp_offset",
    [
        -301,
        301,
    ],
)
def test_validate_rejects_timestamp_outside_replay_window(
    validator: SignatureValidator,
    timestamp_offset: int,
) -> None:
    """Reject requests whose timestamps exceed the configured replay window."""
    now = 1_700_000_000.0
    timestamp = str(int(now + timestamp_offset))
    signature = build_signature(PAYLOAD, timestamp=timestamp)

    with pytest.raises(
        SignatureValidationError,
        match="outside the allowed replay window",
    ):
        validator.validate(
            PAYLOAD,
            signature,
            timestamp,
            now=now,
        )


def test_validate_accepts_timestamp_at_replay_window_boundary(
    validator: SignatureValidator,
) -> None:
    """Accept a request exactly at the configured replay-window boundary."""
    now = 1_700_000_000.0
    timestamp = str(int(now - validator.replay_window_seconds))
    signature = build_signature(PAYLOAD, timestamp=timestamp)

    validator.validate(
        PAYLOAD,
        signature,
        timestamp,
        now=now,
    )


def test_validate_uses_supplied_current_time(
    validator: SignatureValidator,
) -> None:
    """Use the injected clock when validating replay protection."""
    fixed_now = 1_700_000_000.0
    timestamp = str(int(fixed_now - 100))
    signature = build_signature(PAYLOAD, timestamp=timestamp)

    validator.validate(
        PAYLOAD,
        signature,
        timestamp,
        now=fixed_now,
    )


def test_validate_rejects_wrong_secret() -> None:
    """Reject a signature generated with a different secret."""
    validator = SignatureValidator(secret=SECRET)
    timestamp = str(int(time.time()))
    signature = build_signature(
        PAYLOAD,
        timestamp=timestamp,
        secret="different-secret",
    )

    with pytest.raises(
        SignatureValidationError,
        match="Invalid webhook signature",
    ):
        validator.validate(
            PAYLOAD,
            signature,
            timestamp,
        )


def test_validator_rejects_empty_secret() -> None:
    """Reject construction with an empty signing secret."""
    with pytest.raises(
        ValueError,
        match="signing secret must not be empty",
    ):
        SignatureValidator(secret="")


def test_validator_rejects_non_positive_replay_window() -> None:
    """Reject an invalid replay-window configuration."""
    with pytest.raises(
        ValueError,
        match="replay_window_seconds must be greater than zero",
    ):
        SignatureValidator(
            secret=SECRET,
            replay_window_seconds=0,
        )


def test_validator_rejects_unsupported_algorithm() -> None:
    """Reject algorithms that the validator does not implement."""
    with pytest.raises(
        ValueError,
        match="Only SHA-256 signatures are supported",
    ):
        SignatureValidator(
            secret=SECRET,
            algorithm="sha512",
        )