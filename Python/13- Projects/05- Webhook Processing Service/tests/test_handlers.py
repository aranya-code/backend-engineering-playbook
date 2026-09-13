"""Tests for webhook event dispatch and idempotent event handling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from src.events.models import EventStatus, WebhookEvent
from src.handlers.event_handler import (
    EventHandler,
    EventHandlerError,
    UnknownEventTypeError,
)


def make_event(
    *,
    event_id: str = "evt_123",
    event_type: str = "payment.created",
    payload: dict[str, Any] | None = None,
    status: EventStatus = EventStatus.RECEIVED,
    attempt_count: int = 0,
) -> WebhookEvent:
    """Create a webhook event suitable for handler tests."""
    from datetime import datetime, timezone

    return WebhookEvent(
        event_id=event_id,
        event_type=event_type,
        payload=payload or {"payment_id": "pay_123"},
        received_at=datetime.now(timezone.utc),
        status=status,
        attempt_count=attempt_count,
    )


@dataclass
class FakeEventStore:
    """Provide an in-memory event store double for handler tests."""

    events: dict[str, WebhookEvent]

    def __init__(self) -> None:
        self.events = {}

    async def get(self, event_id: str) -> WebhookEvent | None:
        """Return a stored event by ID."""
        return self.events.get(event_id)

    async def create(self, event: WebhookEvent) -> WebhookEvent:
        """Store a new event."""
        self.events[event.event_id] = event
        return event

    async def update(self, event: WebhookEvent) -> WebhookEvent:
        """Update an existing event."""
        self.events[event.event_id] = event
        return event


@dataclass
class FakeHandler:
    """Record event-handler invocations for assertions."""

    calls: list[WebhookEvent]

    def __init__(self) -> None:
        self.calls = []

    async def handle(self, event: WebhookEvent) -> None:
        """Record a processed event."""
        self.calls.append(event)


@pytest.fixture
def event_store() -> FakeEventStore:
    """Create an isolated event-store test double."""
    return FakeEventStore()


@pytest.fixture
def payment_handler() -> FakeHandler:
    """Create a handler for payment-created events."""
    return FakeHandler()


@pytest.fixture
def webhook_handler(
    event_store: FakeEventStore,
    payment_handler: FakeHandler,
) -> EventHandler:
    """Create an event handler with a registered event-type handler."""
    return EventHandler(
        event_store=event_store,
        handlers={
            "payment.created": payment_handler.handle,
        },
    )


@pytest.mark.asyncio
async def test_handle_dispatches_event_to_registered_handler(
    webhook_handler: EventHandler,
    event_store: FakeEventStore,
    payment_handler: FakeHandler,
) -> None:
    """Dispatch a received event to the handler registered for its type."""
    event = make_event()
    await event_store.create(event)

    result = await webhook_handler.handle(event)

    assert result.status == EventStatus.PROCESSED
    assert result.event_id == event.event_id
    assert result.duplicate is False
    assert payment_handler.calls == [event]


@pytest.mark.asyncio
async def test_handle_marks_event_as_processed_after_success(
    webhook_handler: EventHandler,
    event_store: FakeEventStore,
) -> None:
    """Persist the processed state after successful event handling."""
    event = make_event()
    await event_store.create(event)

    await webhook_handler.handle(event)

    stored_event = await event_store.get(event.event_id)

    assert stored_event is not None
    assert stored_event.status == EventStatus.PROCESSED


@pytest.mark.asyncio
async def test_handle_rejects_unknown_event_type(
    webhook_handler: EventHandler,
    event_store: FakeEventStore,
) -> None:
    """Reject events for which no business handler is registered."""
    event = make_event(event_type="subscription.deleted")
    await event_store.create(event)

    with pytest.raises(
        UnknownEventTypeError,
        match="subscription.deleted",
    ):
        await webhook_handler.handle(event)


@pytest.mark.asyncio
async def test_handle_does_not_process_duplicate_completed_event(
    webhook_handler: EventHandler,
    event_store: FakeEventStore,
    payment_handler: FakeHandler,
) -> None:
    """Avoid executing business logic for an already processed event."""
    event = make_event(status=EventStatus.PROCESSED)
    await event_store.create(event)

    result = await webhook_handler.handle(event)

    assert result.status == EventStatus.PROCESSED
    assert result.duplicate is True
    assert payment_handler.calls == []


@pytest.mark.asyncio
async def test_handle_processes_failed_event_for_retry(
    webhook_handler: EventHandler,
    event_store: FakeEventStore,
    payment_handler: FakeHandler,
) -> None:
    """Allow a previously failed event to be retried."""
    event = make_event(
        status=EventStatus.FAILED,
        attempt_count=1,
    )
    await event_store.create(event)

    result = await webhook_handler.handle(event)

    assert result.status == EventStatus.PROCESSED
    assert result.duplicate is False
    assert payment_handler.calls == [event]


@pytest.mark.asyncio
async def test_handle_rejects_dead_lettered_event(
    webhook_handler: EventHandler,
    event_store: FakeEventStore,
    payment_handler: FakeHandler,
) -> None:
    """Do not reprocess an event that has reached the dead-letter state."""
    event = make_event(status=EventStatus.DEAD_LETTERED)
    await event_store.create(event)

    result = await webhook_handler.handle(event)

    assert result.status == EventStatus.DEAD_LETTERED
    assert result.duplicate is True
    assert payment_handler.calls == []


@pytest.mark.asyncio
async def test_handle_marks_event_failed_when_handler_raises(
    event_store: FakeEventStore,
) -> None:
    """Persist a failed state when business processing raises an error."""

    async def failing_handler(event: WebhookEvent) -> None:
        """Simulate a transient business-processing failure."""
        raise RuntimeError("downstream service unavailable")

    webhook_handler = EventHandler(
        event_store=event_store,
        handlers={"payment.created": failing_handler},
    )
    event = make_event()
    await event_store.create(event)

    with pytest.raises(EventHandlerError, match="evt_123"):
        await webhook_handler.handle(event)

    stored_event = await event_store.get(event.event_id)

    assert stored_event is not None
    assert stored_event.status == EventStatus.FAILED


@pytest.mark.asyncio
async def test_handle_preserves_original_event_payload(
    webhook_handler: EventHandler,
    event_store: FakeEventStore,
    payment_handler: FakeHandler,
) -> None:
    """Pass the complete normalized payload to the business handler."""
    event = make_event(
        payload={
            "payment_id": "pay_456",
            "amount": 4999,
            "currency": "USD",
        },
    )
    await event_store.create(event)

    await webhook_handler.handle(event)

    assert payment_handler.calls[0].payload == {
        "payment_id": "pay_456",
        "amount": 4999,
        "currency": "USD",
    }


@pytest.mark.asyncio
async def test_handle_requires_persisted_event(
    webhook_handler: EventHandler,
) -> None:
    """Reject processing when the event does not exist in storage."""
    event = make_event()

    with pytest.raises(EventHandlerError, match="evt_123"):
        await webhook_handler.handle(event)


@pytest.mark.asyncio
async def test_handle_is_idempotent_under_concurrent_duplicate_delivery(
    event_store: FakeEventStore,
) -> None:
    """Ensure concurrent delivery attempts do not execute business logic twice."""
    import asyncio

    calls = 0

    async def process_payment(event: WebhookEvent) -> None:
        """Count business-handler executions."""
        nonlocal calls
        await asyncio.sleep(0)
        calls += 1

    event = make_event()
    await event_store.create(event)

    webhook_handler = EventHandler(
        event_store=event_store,
        handlers={"payment.created": process_payment},
    )

    results = await asyncio.gather(
        webhook_handler.handle(event),
        webhook_handler.handle(event),
    )

    assert sum(result.duplicate for result in results) >= 1
    assert calls == 1


@pytest.mark.asyncio
async def test_handle_does_not_swallow_cancellation(
    event_store: FakeEventStore,
) -> None:
    """Propagate task cancellation instead of treating it as a business failure."""
    import asyncio

    async def cancelling_handler(event: WebhookEvent) -> None:
        """Simulate cancellation during downstream processing."""
        raise asyncio.CancelledError

    webhook_handler = EventHandler(
        event_store=event_store,
        handlers={"payment.created": cancelling_handler},
    )
    event = make_event()
    await event_store.create(event)

    with pytest.raises(asyncio.CancelledError):
        await webhook_handler.handle(event)

"""Tests for webhook event dispatch and idempotent event handling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from src.events.models import EventStatus, WebhookEvent
from src.handlers.event_handler import (
    EventHandler,
    EventHandlerError,
    UnknownEventTypeError,
)


def make_event(
    *,
    event_id: str = "evt_123",
    event_type: str = "payment.created",
    payload: dict[str, Any] | None = None,
    status: EventStatus = EventStatus.RECEIVED,
    attempt_count: int = 0,
) -> WebhookEvent:
    """Create a webhook event suitable for handler tests."""
    from datetime import datetime, timezone

    return WebhookEvent(
        event_id=event_id,
        event_type=event_type,
        payload=payload or {"payment_id": "pay_123"},
        received_at=datetime.now(timezone.utc),
        status=status,
        attempt_count=attempt_count,
    )


@dataclass
class FakeEventStore:
    """Provide an in-memory event store double for handler tests."""

    events: dict[str, WebhookEvent]

    def __init__(self) -> None:
        self.events = {}

    async def get(self, event_id: str) -> WebhookEvent | None:
        """Return a stored event by ID."""
        return self.events.get(event_id)

    async def create(self, event: WebhookEvent) -> WebhookEvent:
        """Store a new event."""
        self.events[event.event_id] = event
        return event

    async def update(self, event: WebhookEvent) -> WebhookEvent:
        """Update an existing event."""
        self.events[event.event_id] = event
        return event


@dataclass
class FakeHandler:
    """Record event-handler invocations for assertions."""

    calls: list[WebhookEvent]

    def __init__(self) -> None:
        self.calls = []

    async def handle(self, event: WebhookEvent) -> None:
        """Record a processed event."""
        self.calls.append(event)


@pytest.fixture
def event_store() -> FakeEventStore:
    """Create an isolated event-store test double."""
    return FakeEventStore()


@pytest.fixture
def payment_handler() -> FakeHandler:
    """Create a handler for payment-created events."""
    return FakeHandler()


@pytest.fixture
def webhook_handler(
    event_store: FakeEventStore,
    payment_handler: FakeHandler,
) -> EventHandler:
    """Create an event handler with a registered event-type handler."""
    return EventHandler(
        event_store=event_store,
        handlers={
            "payment.created": payment_handler.handle,
        },
    )


@pytest.mark.asyncio
async def test_handle_dispatches_event_to_registered_handler(
    webhook_handler: EventHandler,
    event_store: FakeEventStore,
    payment_handler: FakeHandler,
) -> None:
    """Dispatch a received event to the handler registered for its type."""
    event = make_event()
    await event_store.create(event)

    result = await webhook_handler.handle(event)

    assert result.status == EventStatus.PROCESSED
    assert result.event_id == event.event_id
    assert result.duplicate is False
    assert payment_handler.calls == [event]


@pytest.mark.asyncio
async def test_handle_marks_event_as_processed_after_success(
    webhook_handler: EventHandler,
    event_store: FakeEventStore,
) -> None:
    """Persist the processed state after successful event handling."""
    event = make_event()
    await event_store.create(event)

    await webhook_handler.handle(event)

    stored_event = await event_store.get(event.event_id)

    assert stored_event is not None
    assert stored_event.status == EventStatus.PROCESSED


@pytest.mark.asyncio
async def test_handle_rejects_unknown_event_type(
    webhook_handler: EventHandler,
    event_store: FakeEventStore,
) -> None:
    """Reject events for which no business handler is registered."""
    event = make_event(event_type="subscription.deleted")
    await event_store.create(event)

    with pytest.raises(
        UnknownEventTypeError,
        match="subscription.deleted",
    ):
        await webhook_handler.handle(event)


@pytest.mark.asyncio
async def test_handle_does_not_process_duplicate_completed_event(
    webhook_handler: EventHandler,
    event_store: FakeEventStore,
    payment_handler: FakeHandler,
) -> None:
    """Avoid executing business logic for an already processed event."""
    event = make_event(status=EventStatus.PROCESSED)
    await event_store.create(event)

    result = await webhook_handler.handle(event)

    assert result.status == EventStatus.PROCESSED
    assert result.duplicate is True
    assert payment_handler.calls == []


@pytest.mark.asyncio
async def test_handle_processes_failed_event_for_retry(
    webhook_handler: EventHandler,
    event_store: FakeEventStore,
    payment_handler: FakeHandler,
) -> None:
    """Allow a previously failed event to be retried."""
    event = make_event(
        status=EventStatus.FAILED,
        attempt_count=1,
    )
    await event_store.create(event)

    result = await webhook_handler.handle(event)

    assert result.status == EventStatus.PROCESSED
    assert result.duplicate is False
    assert payment_handler.calls == [event]


@pytest.mark.asyncio
async def test_handle_rejects_dead_lettered_event(
    webhook_handler: EventHandler,
    event_store: FakeEventStore,
    payment_handler: FakeHandler,
) -> None:
    """Do not reprocess an event that has reached the dead-letter state."""
    event = make_event(status=EventStatus.DEAD_LETTERED)
    await event_store.create(event)

    result = await webhook_handler.handle(event)

    assert result.status == EventStatus.DEAD_LETTERED
    assert result.duplicate is True
    assert payment_handler.calls == []


@pytest.mark.asyncio
async def test_handle_marks_event_failed_when_handler_raises(
    event_store: FakeEventStore,
) -> None:
    """Persist a failed state when business processing raises an error."""

    async def failing_handler(event: WebhookEvent) -> None:
        """Simulate a transient business-processing failure."""
        raise RuntimeError("downstream service unavailable")

    webhook_handler = EventHandler(
        event_store=event_store,
        handlers={"payment.created": failing_handler},
    )
    event = make_event()
    await event_store.create(event)

    with pytest.raises(EventHandlerError, match="evt_123"):
        await webhook_handler.handle(event)

    stored_event = await event_store.get(event.event_id)

    assert stored_event is not None
    assert stored_event.status == EventStatus.FAILED


@pytest.mark.asyncio
async def test_handle_preserves_original_event_payload(
    webhook_handler: EventHandler,
    event_store: FakeEventStore,
    payment_handler: FakeHandler,
) -> None:
    """Pass the complete normalized payload to the business handler."""
    event = make_event(
        payload={
            "payment_id": "pay_456",
            "amount": 4999,
            "currency": "USD",
        },
    )
    await event_store.create(event)

    await webhook_handler.handle(event)

    assert payment_handler.calls[0].payload == {
        "payment_id": "pay_456",
        "amount": 4999,
        "currency": "USD",
    }


@pytest.mark.asyncio
async def test_handle_requires_persisted_event(
    webhook_handler: EventHandler,
) -> None:
    """Reject processing when the event does not exist in storage."""
    event = make_event()

    with pytest.raises(EventHandlerError, match="evt_123"):
        await webhook_handler.handle(event)


@pytest.mark.asyncio
async def test_handle_is_idempotent_under_concurrent_duplicate_delivery(
    event_store: FakeEventStore,
) -> None:
    """Ensure concurrent delivery attempts do not execute business logic twice."""
    import asyncio

    calls = 0

    async def process_payment(event: WebhookEvent) -> None:
        """Count business-handler executions."""
        nonlocal calls
        await asyncio.sleep(0)
        calls += 1

    event = make_event()
    await event_store.create(event)

    webhook_handler = EventHandler(
        event_store=event_store,
        handlers={"payment.created": process_payment},
    )

    results = await asyncio.gather(
        webhook_handler.handle(event),
        webhook_handler.handle(event),
    )

    assert sum(result.duplicate for result in results) >= 1
    assert calls == 1


@pytest.mark.asyncio
async def test_handle_does_not_swallow_cancellation(
    event_store: FakeEventStore,
) -> None:
    """Propagate task cancellation instead of treating it as a business failure."""
    import asyncio

    async def cancelling_handler(event: WebhookEvent) -> None:
        """Simulate cancellation during downstream processing."""
        raise asyncio.CancelledError

    webhook_handler = EventHandler(
        event_store=event_store,
        handlers={"payment.created": cancelling_handler},
    )
    event = make_event()
    await event_store.create(event)

    with pytest.raises(asyncio.CancelledError):
        await webhook_handler.handle(event)