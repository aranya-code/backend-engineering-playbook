"""Persistent event-store abstractions for webhook event lifecycle management."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Protocol

from src.events.models import EventStatus, WebhookEvent


class EventStoreError(RuntimeError):
    """Base exception for event-store failures."""


class EventAlreadyExistsError(EventStoreError):
    """Raised when an event with the same provider ID already exists."""


class EventNotFoundError(EventStoreError):
    """Raised when a requested webhook event does not exist."""


class EventStore(Protocol):
    """Define the persistence contract required by the webhook service."""

    async def get(self, event_id: str) -> WebhookEvent | None:
        """Return an event by provider event ID, if it exists."""
        ...

    async def create(self, event: WebhookEvent) -> WebhookEvent:
        """Persist a newly received webhook event."""
        ...

    async def update(self, event: WebhookEvent) -> WebhookEvent:
        """Persist an updated webhook event."""
        ...


class InMemoryEventStore:
    """Provide an in-memory event store for development and automated tests.

    The implementation deliberately exposes the same asynchronous contract
    expected from a database-backed store. Production deployments should
    replace it with a transactional PostgreSQL or equivalent implementation.
    """

    def __init__(self) -> None:
        self._events: dict[str, WebhookEvent] = {}
        self._lock = asyncio.Lock()

    async def get(self, event_id: str) -> WebhookEvent | None:
        """Return an event by provider event ID, if it exists."""
        normalized_event_id = self._normalize_event_id(event_id)

        async with self._lock:
            return self._events.get(normalized_event_id)

    async def create(self, event: WebhookEvent) -> WebhookEvent:
        """Persist an event while enforcing provider-event uniqueness."""
        normalized_event_id = self._normalize_event_id(event.event_id)

        async with self._lock:
            if normalized_event_id in self._events:
                raise EventAlreadyExistsError(
                    f"Webhook event {normalized_event_id!r} already exists."
                )

            self._events[normalized_event_id] = event
            return event

    async def update(self, event: WebhookEvent) -> WebhookEvent:
        """Persist a lifecycle update for an existing event."""
        normalized_event_id = self._normalize_event_id(event.event_id)

        async with self._lock:
            if normalized_event_id not in self._events:
                raise EventNotFoundError(
                    f"Webhook event {normalized_event_id!r} was not found."
                )

            self._events[normalized_event_id] = event
            return event

    async def create_if_absent(
        self,
        event: WebhookEvent,
    ) -> tuple[WebhookEvent, bool]:
        """Atomically create an event or return the existing event.

        The boolean result is True when this call created the event and False
        when the event was already present. This operation models the
        idempotency pattern required when webhook providers retry delivery.
        """
        normalized_event_id = self._normalize_event_id(event.event_id)

        async with self._lock:
            existing_event = self._events.get(normalized_event_id)

            if existing_event is not None:
                return existing_event, False

            self._events[normalized_event_id] = event
            return event, True

    async def transition(
        self,
        event_id: str,
        *,
        status: EventStatus,
        attempt_count: int | None = None,
    ) -> WebhookEvent:
        """Atomically update an event's processing state."""
        normalized_event_id = self._normalize_event_id(event_id)

        if attempt_count is not None and attempt_count < 0:
            raise ValueError("attempt_count must not be negative.")

        async with self._lock:
            event = self._events.get(normalized_event_id)

            if event is None:
                raise EventNotFoundError(
                    f"Webhook event {normalized_event_id!r} was not found."
                )

            updated_event = WebhookEvent(
                event_id=event.event_id,
                event_type=event.event_type,
                payload=dict(event.payload),
                received_at=event.received_at,
                status=status,
                attempt_count=(
                    event.attempt_count
                    if attempt_count is None
                    else attempt_count
                ),
                id=event.id,
            )

            self._events[normalized_event_id] = updated_event
            return updated_event

    async def all(self) -> list[WebhookEvent]:
        """Return a snapshot of all stored events."""
        async with self._lock:
            return list(self._events.values())

    async def count(self, *, status: EventStatus | None = None) -> int:
        """Return the number of stored events, optionally filtered by status."""
        async with self._lock:
            if status is None:
                return len(self._events)

            return sum(event.status == status for event in self._events.values())

    async def delete(self, event_id: str) -> None:
        """Delete an event by provider event ID."""
        normalized_event_id = self._normalize_event_id(event_id)

        async with self._lock:
            if normalized_event_id not in self._events:
                raise EventNotFoundError(
                    f"Webhook event {normalized_event_id!r} was not found."
                )

            del self._events[normalized_event_id]

    @staticmethod
    def _normalize_event_id(event_id: str) -> str:
        """Normalize and validate a provider-supplied event identifier."""
        if not isinstance(event_id, str):
            raise TypeError("event_id must be a string.")

        normalized_event_id = event_id.strip()

        if not normalized_event_id:
            raise ValueError("event_id must not be empty.")

        return normalized_event_id


def event_to_record(event: WebhookEvent) -> Mapping[str, object]:
    """Convert an event into a persistence-friendly record."""
    return {
        "id": str(event.id),
        "event_id": event.event_id,
        "event_type": event.event_type,
        "payload": dict(event.payload),
        "received_at": event.received_at,
        "status": event.status.value,
        "attempt_count": event.attempt_count,
    }

"""Persistent event-store abstractions for webhook event lifecycle management."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Protocol

from src.events.models import EventStatus, WebhookEvent


class EventStoreError(RuntimeError):
    """Base exception for event-store failures."""


class EventAlreadyExistsError(EventStoreError):
    """Raised when an event with the same provider ID already exists."""


class EventNotFoundError(EventStoreError):
    """Raised when a requested webhook event does not exist."""


class EventStore(Protocol):
    """Define the persistence contract required by the webhook service."""

    async def get(self, event_id: str) -> WebhookEvent | None:
        """Return an event by provider event ID, if it exists."""
        ...

    async def create(self, event: WebhookEvent) -> WebhookEvent:
        """Persist a newly received webhook event."""
        ...

    async def update(self, event: WebhookEvent) -> WebhookEvent:
        """Persist an updated webhook event."""
        ...


class InMemoryEventStore:
    """Provide an in-memory event store for development and automated tests.

    The implementation deliberately exposes the same asynchronous contract
    expected from a database-backed store. Production deployments should
    replace it with a transactional PostgreSQL or equivalent implementation.
    """

    def __init__(self) -> None:
        self._events: dict[str, WebhookEvent] = {}
        self._lock = asyncio.Lock()

    async def get(self, event_id: str) -> WebhookEvent | None:
        """Return an event by provider event ID, if it exists."""
        normalized_event_id = self._normalize_event_id(event_id)

        async with self._lock:
            return self._events.get(normalized_event_id)

    async def create(self, event: WebhookEvent) -> WebhookEvent:
        """Persist an event while enforcing provider-event uniqueness."""
        normalized_event_id = self._normalize_event_id(event.event_id)

        async with self._lock:
            if normalized_event_id in self._events:
                raise EventAlreadyExistsError(
                    f"Webhook event {normalized_event_id!r} already exists."
                )

            self._events[normalized_event_id] = event
            return event

    async def update(self, event: WebhookEvent) -> WebhookEvent:
        """Persist a lifecycle update for an existing event."""
        normalized_event_id = self._normalize_event_id(event.event_id)

        async with self._lock:
            if normalized_event_id not in self._events:
                raise EventNotFoundError(
                    f"Webhook event {normalized_event_id!r} was not found."
                )

            self._events[normalized_event_id] = event
            return event

    async def create_if_absent(
        self,
        event: WebhookEvent,
    ) -> tuple[WebhookEvent, bool]:
        """Atomically create an event or return the existing event.

        The boolean result is True when this call created the event and False
        when the event was already present. This operation models the
        idempotency pattern required when webhook providers retry delivery.
        """
        normalized_event_id = self._normalize_event_id(event.event_id)

        async with self._lock:
            existing_event = self._events.get(normalized_event_id)

            if existing_event is not None:
                return existing_event, False

            self._events[normalized_event_id] = event
            return event, True

    async def transition(
        self,
        event_id: str,
        *,
        status: EventStatus,
        attempt_count: int | None = None,
    ) -> WebhookEvent:
        """Atomically update an event's processing state."""
        normalized_event_id = self._normalize_event_id(event_id)

        if attempt_count is not None and attempt_count < 0:
            raise ValueError("attempt_count must not be negative.")

        async with self._lock:
            event = self._events.get(normalized_event_id)

            if event is None:
                raise EventNotFoundError(
                    f"Webhook event {normalized_event_id!r} was not found."
                )

            updated_event = WebhookEvent(
                event_id=event.event_id,
                event_type=event.event_type,
                payload=dict(event.payload),
                received_at=event.received_at,
                status=status,
                attempt_count=(
                    event.attempt_count
                    if attempt_count is None
                    else attempt_count
                ),
                id=event.id,
            )

            self._events[normalized_event_id] = updated_event
            return updated_event

    async def all(self) -> list[WebhookEvent]:
        """Return a snapshot of all stored events."""
        async with self._lock:
            return list(self._events.values())

    async def count(self, *, status: EventStatus | None = None) -> int:
        """Return the number of stored events, optionally filtered by status."""
        async with self._lock:
            if status is None:
                return len(self._events)

            return sum(event.status == status for event in self._events.values())

    async def delete(self, event_id: str) -> None:
        """Delete an event by provider event ID."""
        normalized_event_id = self._normalize_event_id(event_id)

        async with self._lock:
            if normalized_event_id not in self._events:
                raise EventNotFoundError(
                    f"Webhook event {normalized_event_id!r} was not found."
                )

            del self._events[normalized_event_id]

    @staticmethod
    def _normalize_event_id(event_id: str) -> str:
        """Normalize and validate a provider-supplied event identifier."""
        if not isinstance(event_id, str):
            raise TypeError("event_id must be a string.")

        normalized_event_id = event_id.strip()

        if not normalized_event_id:
            raise ValueError("event_id must not be empty.")

        return normalized_event_id


def event_to_record(event: WebhookEvent) -> Mapping[str, object]:
    """Convert an event into a persistence-friendly record."""
    return {
        "id": str(event.id),
        "event_id": event.event_id,
        "event_type": event.event_type,
        "payload": dict(event.payload),
        "received_at": event.received_at,
        "status": event.status.value,
        "attempt_count": event.attempt_count,
    }