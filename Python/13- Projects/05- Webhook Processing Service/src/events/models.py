"""Domain models for webhook events and processing state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class EventStatus(StrEnum):
    """Represent the lifecycle state of a webhook event."""

    RECEIVED = "received"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"


@dataclass(frozen=True, slots=True)
class WebhookEvent:
    """Represent a normalized webhook event accepted by the service."""

    event_id: str
    event_type: str
    payload: dict[str, Any]
    received_at: datetime
    status: EventStatus = EventStatus.RECEIVED
    attempt_count: int = 0
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        """Validate invariants required by the event model."""
        if not self.event_id.strip():
            raise ValueError("event_id must not be empty.")

        if not self.event_type.strip():
            raise ValueError("event_type must not be empty.")

        if self.attempt_count < 0:
            raise ValueError("attempt_count must not be negative.")

        if self.received_at.tzinfo is None:
            raise ValueError("received_at must be timezone-aware.")


@dataclass(frozen=True, slots=True)
class WebhookDelivery:
    """Represent one delivery attempt of a webhook event."""

    event_id: str
    attempt: int
    delivered_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    success: bool = False
    error: str | None = None

    def __post_init__(self) -> None:
        """Validate delivery-attempt invariants."""
        if not self.event_id.strip():
            raise ValueError("event_id must not be empty.")

        if self.attempt <= 0:
            raise ValueError("attempt must be greater than zero.")

        if self.delivered_at.tzinfo is None:
            raise ValueError("delivered_at must be timezone-aware.")

        if self.success and self.error is not None:
            raise ValueError("A successful delivery cannot contain an error.")


@dataclass(frozen=True, slots=True)
class WebhookResult:
    """Represent the outcome of processing a webhook event."""

    event_id: str
    status: EventStatus
    duplicate: bool = False
    message: str | None = None

    def __post_init__(self) -> None:
        """Validate result invariants."""
        if not self.event_id.strip():
            raise ValueError("event_id must not be empty.")

        if self.status not in {
            EventStatus.PROCESSED,
            EventStatus.FAILED,
            EventStatus.DEAD_LETTERED,
        }:
            raise ValueError(
                "WebhookResult status must represent a completed processing state."
            )

"""Domain models for webhook events and processing state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class EventStatus(StrEnum):
    """Represent the lifecycle state of a webhook event."""

    RECEIVED = "received"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"


@dataclass(frozen=True, slots=True)
class WebhookEvent:
    """Represent a normalized webhook event accepted by the service."""

    event_id: str
    event_type: str
    payload: dict[str, Any]
    received_at: datetime
    status: EventStatus = EventStatus.RECEIVED
    attempt_count: int = 0
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        """Validate invariants required by the event model."""
        if not self.event_id.strip():
            raise ValueError("event_id must not be empty.")

        if not self.event_type.strip():
            raise ValueError("event_type must not be empty.")

        if self.attempt_count < 0:
            raise ValueError("attempt_count must not be negative.")

        if self.received_at.tzinfo is None:
            raise ValueError("received_at must be timezone-aware.")


@dataclass(frozen=True, slots=True)
class WebhookDelivery:
    """Represent one delivery attempt of a webhook event."""

    event_id: str
    attempt: int
    delivered_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    success: bool = False
    error: str | None = None

    def __post_init__(self) -> None:
        """Validate delivery-attempt invariants."""
        if not self.event_id.strip():
            raise ValueError("event_id must not be empty.")

        if self.attempt <= 0:
            raise ValueError("attempt must be greater than zero.")

        if self.delivered_at.tzinfo is None:
            raise ValueError("delivered_at must be timezone-aware.")

        if self.success and self.error is not None:
            raise ValueError("A successful delivery cannot contain an error.")


@dataclass(frozen=True, slots=True)
class WebhookResult:
    """Represent the outcome of processing a webhook event."""

    event_id: str
    status: EventStatus
    duplicate: bool = False
    message: str | None = None

    def __post_init__(self) -> None:
        """Validate result invariants."""
        if not self.event_id.strip():
            raise ValueError("event_id must not be empty.")

        if self.status not in {
            EventStatus.PROCESSED,
            EventStatus.FAILED,
            EventStatus.DEAD_LETTERED,
        }:
            raise ValueError(
                "WebhookResult status must represent a completed processing state."
            )