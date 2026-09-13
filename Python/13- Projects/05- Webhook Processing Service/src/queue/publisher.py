"""Publish validated webhook events to the configured processing queue."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID


class QueuePublishError(RuntimeError):
    """Raised when a webhook event cannot be published."""


class QueuePublisher(Protocol):
    """Define the interface required by webhook queue publishers."""

    async def publish(
        self,
        message: dict[str, Any],
        *,
        message_id: str,
    ) -> None:
        """Publish a message using a stable identifier for deduplication."""
        ...


@dataclass(slots=True)
class InMemoryQueuePublisher:
    """Provide an asynchronous queue publisher for local development and tests."""

    queue: asyncio.Queue[tuple[str, bytes]]

    @classmethod
    def create(cls, *, maxsize: int = 1000) -> InMemoryQueuePublisher:
        """Create a bounded in-memory queue."""
        if maxsize <= 0:
            raise ValueError("maxsize must be greater than zero.")

        return cls(queue=asyncio.Queue(maxsize=maxsize))

    async def publish(
        self,
        message: dict[str, Any],
        *,
        message_id: str,
    ) -> None:
        """Serialize and enqueue one webhook event."""
        if not message_id.strip():
            raise ValueError("message_id must not be empty.")

        try:
            payload = json.dumps(
                message,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise QueuePublishError(
                "Webhook event could not be serialized."
            ) from exc

        await self.queue.put((message_id, payload))


async def publish_webhook_event(
    publisher: QueuePublisher,
    *,
    event_id: str | UUID,
    event_type: str,
    payload: dict[str, Any],
    attempt: int = 0,
) -> None:
    """Publish a normalized webhook event after validating its envelope."""
    normalized_event_id = str(event_id).strip()
    normalized_event_type = event_type.strip()

    if not normalized_event_id:
        raise ValueError("event_id must not be empty.")

    if not normalized_event_type:
        raise ValueError("event_type must not be empty.")

    if attempt < 0:
        raise ValueError("attempt must not be negative.")

    message = {
        "event_id": normalized_event_id,
        "event_type": normalized_event_type,
        "payload": payload,
        "attempt": attempt,
    }

    await publisher.publish(
        message,
        message_id=normalized_event_id,
    )

"""Publish validated webhook events to the configured processing queue."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID


class QueuePublishError(RuntimeError):
    """Raised when a webhook event cannot be published."""


class QueuePublisher(Protocol):
    """Define the interface required by webhook queue publishers."""

    async def publish(
        self,
        message: dict[str, Any],
        *,
        message_id: str,
    ) -> None:
        """Publish a message using a stable identifier for deduplication."""
        ...


@dataclass(slots=True)
class InMemoryQueuePublisher:
    """Provide an asynchronous queue publisher for local development and tests."""

    queue: asyncio.Queue[tuple[str, bytes]]

    @classmethod
    def create(cls, *, maxsize: int = 1000) -> InMemoryQueuePublisher:
        """Create a bounded in-memory queue."""
        if maxsize <= 0:
            raise ValueError("maxsize must be greater than zero.")

        return cls(queue=asyncio.Queue(maxsize=maxsize))

    async def publish(
        self,
        message: dict[str, Any],
        *,
        message_id: str,
    ) -> None:
        """Serialize and enqueue one webhook event."""
        if not message_id.strip():
            raise ValueError("message_id must not be empty.")

        try:
            payload = json.dumps(
                message,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise QueuePublishError(
                "Webhook event could not be serialized."
            ) from exc

        await self.queue.put((message_id, payload))


async def publish_webhook_event(
    publisher: QueuePublisher,
    *,
    event_id: str | UUID,
    event_type: str,
    payload: dict[str, Any],
    attempt: int = 0,
) -> None:
    """Publish a normalized webhook event after validating its envelope."""
    normalized_event_id = str(event_id).strip()
    normalized_event_type = event_type.strip()

    if not normalized_event_id:
        raise ValueError("event_id must not be empty.")

    if not normalized_event_type:
        raise ValueError("event_type must not be empty.")

    if attempt < 0:
        raise ValueError("attempt must not be negative.")

    message = {
        "event_id": normalized_event_id,
        "event_type": normalized_event_type,
        "payload": payload,
        "attempt": attempt,
    }

    await publisher.publish(
        message,
        message_id=normalized_event_id,
    )