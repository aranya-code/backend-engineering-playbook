"""Application services for reliable webhook event processing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.events.models import EventStatus, WebhookEvent, WebhookResult
from src.queue.publisher import QueuePublisher, publish_webhook_event


class EventServiceError(RuntimeError):
    """Base exception for webhook event service failures."""


class DuplicateEventError(EventServiceError):
    """Raised when an event is already known and duplicates are rejected."""


class EventPersistenceError(EventServiceError):
    """Raised when an event cannot be persisted."""


class EventRepository:
    """Define the persistence operations required by the event service."""

    async def get_by_event_id(self, event_id: str) -> WebhookEvent | None:
        """Return an event by its provider-supplied identifier."""
        raise NotImplementedError

    async def create(self, event: WebhookEvent) -> WebhookEvent:
        """Persist and return a newly received event."""
        raise NotImplementedError

    async def update(self, event: WebhookEvent) -> WebhookEvent:
        """Persist an updated event state."""
        raise NotImplementedError


@dataclass(slots=True)
class InMemoryEventRepository(EventRepository):
    """Provide an in-memory repository for local development and tests."""

    events: dict[str, WebhookEvent]

    @classmethod
    def create(cls) -> InMemoryEventRepository:
        """Create an empty event repository."""
        return cls(events={})

    async def get_by_event_id(self, event_id: str) -> WebhookEvent | None:
        """Return an event by its provider-supplied identifier."""
        return self.events.get(event_id)

    async def create(self, event: WebhookEvent) -> WebhookEvent:
        """Persist a new event while enforcing event-ID uniqueness."""
        if event.event_id in self.events:
            raise EventPersistenceError(
                f"Event {event.event_id!r} already exists."
            )

        self.events[event.event_id] = event
        return event

    async def update(self, event: WebhookEvent) -> WebhookEvent:
        """Persist an updated event."""
        if event.event_id not in self.events:
            raise EventPersistenceError(
                f"Event {event.event_id!r} does not exist."
            )

        self.events[event.event_id] = event
        return event


@dataclass(slots=True)
class WebhookEventService:
    """Coordinate webhook persistence, idempotency, and queue publication."""

    repository: EventRepository
    publisher: QueuePublisher

    async def accept(
        self,
        *,
        event_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> WebhookResult:
        """Persist a webhook event and publish it for asynchronous processing."""
        normalized_event_id = event_id.strip()
        normalized_event_type = event_type.strip()

        if not normalized_event_id:
            raise ValueError("event_id must not be empty.")

        if not normalized_event_type:
            raise ValueError("event_type must not be empty.")

        existing_event = await self.repository.get_by_event_id(
            normalized_event_id
        )

        if existing_event is not None:
            return WebhookResult(
                event_id=normalized_event_id,
                status=existing_event.status,
                duplicate=True,
                message="Webhook event has already been accepted.",
            )

        from datetime import datetime, timezone

        event = WebhookEvent(
            event_id=normalized_event_id,
            event_type=normalized_event_type,
            payload=payload.copy(),
            received_at=datetime.now(timezone.utc),
        )

        try:
            await self.repository.create(event)
            await publish_webhook_event(
                self.publisher,
                event_id=event.event_id,
                event_type=event.event_type,
                payload=event.payload,
                attempt=event.attempt_count,
            )
        except Exception as exc:
            raise EventServiceError(
                f"Failed to accept webhook event {event.event_id!r}."
            ) from exc

        return WebhookResult(
            event_id=event.event_id,
            status=EventStatus.RECEIVED,
            message="Webhook event accepted for processing.",
        )

    async def mark_processing(self, event_id: str) -> WebhookEvent:
        """Transition an accepted event into the processing state."""
        event = await self._get_event(event_id)

        if event.status not in {
            EventStatus.RECEIVED,
            EventStatus.FAILED,
        }:
            raise EventServiceError(
                f"Event {event.event_id!r} cannot enter processing from "
                f"{event.status.value!r}."
            )

        updated_event = WebhookEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            payload=event.payload.copy(),
            received_at=event.received_at,
            status=EventStatus.PROCESSING,
            attempt_count=event.attempt_count + 1,
            id=event.id,
        )

        return await self.repository.update(updated_event)

    async def mark_processed(self, event_id: str) -> WebhookEvent:
        """Mark a successfully handled webhook event as processed."""
        event = await self._get_event(event_id)

        if event.status != EventStatus.PROCESSING:
            raise EventServiceError(
                f"Event {event.event_id!r} cannot be marked processed from "
                f"{event.status.value!r}."
            )

        updated_event = WebhookEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            payload=event.payload.copy(),
            received_at=event.received_at,
            status=EventStatus.PROCESSED,
            attempt_count=event.attempt_count,
            id=event.id,
        )

        return await self.repository.update(updated_event)

    async def mark_failed(
        self,
        event_id: str,
        *,
        dead_letter: bool = False,
    ) -> WebhookEvent:
        """Record a failed processing attempt and optionally dead-letter it."""
        event = await self._get_event(event_id)

        if event.status != EventStatus.PROCESSING:
            raise EventServiceError(
                f"Event {event.event_id!r} cannot be marked failed from "
                f"{event.status.value!r}."
            )

        status = (
            EventStatus.DEAD_LETTERED
            if dead_letter
            else EventStatus.FAILED
        )

        updated_event = WebhookEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            payload=event.payload.copy(),
            received_at=event.received_at,
            status=status,
            attempt_count=event.attempt_count,
            id=event.id,
        )

        return await self.repository.update(updated_event)

    async def _get_event(self, event_id: str) -> WebhookEvent:
        """Load an event or raise a service-level error."""
        normalized_event_id = event_id.strip()

        if not normalized_event_id:
            raise ValueError("event_id must not be empty.")

        event = await self.repository.get_by_event_id(normalized_event_id)

        if event is None:
            raise EventServiceError(
                f"Webhook event {normalized_event_id!r} was not found."
            )

        return event

"""Application services for reliable webhook event processing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.events.models import EventStatus, WebhookEvent, WebhookResult
from src.queue.publisher import QueuePublisher, publish_webhook_event


class EventServiceError(RuntimeError):
    """Base exception for webhook event service failures."""


class DuplicateEventError(EventServiceError):
    """Raised when an event is already known and duplicates are rejected."""


class EventPersistenceError(EventServiceError):
    """Raised when an event cannot be persisted."""


class EventRepository:
    """Define the persistence operations required by the event service."""

    async def get_by_event_id(self, event_id: str) -> WebhookEvent | None:
        """Return an event by its provider-supplied identifier."""
        raise NotImplementedError

    async def create(self, event: WebhookEvent) -> WebhookEvent:
        """Persist and return a newly received event."""
        raise NotImplementedError

    async def update(self, event: WebhookEvent) -> WebhookEvent:
        """Persist an updated event state."""
        raise NotImplementedError


@dataclass(slots=True)
class InMemoryEventRepository(EventRepository):
    """Provide an in-memory repository for local development and tests."""

    events: dict[str, WebhookEvent]

    @classmethod
    def create(cls) -> InMemoryEventRepository:
        """Create an empty event repository."""
        return cls(events={})

    async def get_by_event_id(self, event_id: str) -> WebhookEvent | None:
        """Return an event by its provider-supplied identifier."""
        return self.events.get(event_id)

    async def create(self, event: WebhookEvent) -> WebhookEvent:
        """Persist a new event while enforcing event-ID uniqueness."""
        if event.event_id in self.events:
            raise EventPersistenceError(
                f"Event {event.event_id!r} already exists."
            )

        self.events[event.event_id] = event
        return event

    async def update(self, event: WebhookEvent) -> WebhookEvent:
        """Persist an updated event."""
        if event.event_id not in self.events:
            raise EventPersistenceError(
                f"Event {event.event_id!r} does not exist."
            )

        self.events[event.event_id] = event
        return event


@dataclass(slots=True)
class WebhookEventService:
    """Coordinate webhook persistence, idempotency, and queue publication."""

    repository: EventRepository
    publisher: QueuePublisher

    async def accept(
        self,
        *,
        event_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> WebhookResult:
        """Persist a webhook event and publish it for asynchronous processing."""
        normalized_event_id = event_id.strip()
        normalized_event_type = event_type.strip()

        if not normalized_event_id:
            raise ValueError("event_id must not be empty.")

        if not normalized_event_type:
            raise ValueError("event_type must not be empty.")

        existing_event = await self.repository.get_by_event_id(
            normalized_event_id
        )

        if existing_event is not None:
            return WebhookResult(
                event_id=normalized_event_id,
                status=existing_event.status,
                duplicate=True,
                message="Webhook event has already been accepted.",
            )

        from datetime import datetime, timezone

        event = WebhookEvent(
            event_id=normalized_event_id,
            event_type=normalized_event_type,
            payload=payload.copy(),
            received_at=datetime.now(timezone.utc),
        )

        try:
            await self.repository.create(event)
            await publish_webhook_event(
                self.publisher,
                event_id=event.event_id,
                event_type=event.event_type,
                payload=event.payload,
                attempt=event.attempt_count,
            )
        except Exception as exc:
            raise EventServiceError(
                f"Failed to accept webhook event {event.event_id!r}."
            ) from exc

        return WebhookResult(
            event_id=event.event_id,
            status=EventStatus.RECEIVED,
            message="Webhook event accepted for processing.",
        )

    async def mark_processing(self, event_id: str) -> WebhookEvent:
        """Transition an accepted event into the processing state."""
        event = await self._get_event(event_id)

        if event.status not in {
            EventStatus.RECEIVED,
            EventStatus.FAILED,
        }:
            raise EventServiceError(
                f"Event {event.event_id!r} cannot enter processing from "
                f"{event.status.value!r}."
            )

        updated_event = WebhookEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            payload=event.payload.copy(),
            received_at=event.received_at,
            status=EventStatus.PROCESSING,
            attempt_count=event.attempt_count + 1,
            id=event.id,
        )

        return await self.repository.update(updated_event)

    async def mark_processed(self, event_id: str) -> WebhookEvent:
        """Mark a successfully handled webhook event as processed."""
        event = await self._get_event(event_id)

        if event.status != EventStatus.PROCESSING:
            raise EventServiceError(
                f"Event {event.event_id!r} cannot be marked processed from "
                f"{event.status.value!r}."
            )

        updated_event = WebhookEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            payload=event.payload.copy(),
            received_at=event.received_at,
            status=EventStatus.PROCESSED,
            attempt_count=event.attempt_count,
            id=event.id,
        )

        return await self.repository.update(updated_event)

    async def mark_failed(
        self,
        event_id: str,
        *,
        dead_letter: bool = False,
    ) -> WebhookEvent:
        """Record a failed processing attempt and optionally dead-letter it."""
        event = await self._get_event(event_id)

        if event.status != EventStatus.PROCESSING:
            raise EventServiceError(
                f"Event {event.event_id!r} cannot be marked failed from "
                f"{event.status.value!r}."
            )

        status = (
            EventStatus.DEAD_LETTERED
            if dead_letter
            else EventStatus.FAILED
        )

        updated_event = WebhookEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            payload=event.payload.copy(),
            received_at=event.received_at,
            status=status,
            attempt_count=event.attempt_count,
            id=event.id,
        )

        return await self.repository.update(updated_event)

    async def _get_event(self, event_id: str) -> WebhookEvent:
        """Load an event or raise a service-level error."""
        normalized_event_id = event_id.strip()

        if not normalized_event_id:
            raise ValueError("event_id must not be empty.")

        event = await self.repository.get_by_event_id(normalized_event_id)

        if event is None:
            raise EventServiceError(
                f"Webhook event {normalized_event_id!r} was not found."
            )

        return event