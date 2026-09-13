"""Tests for webhook event persistence, idempotency, and lifecycle transitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from src.events.models import EventStatus, WebhookEvent
from src.services.event_service import (
    EventServiceError,
    InMemoryEventRepository,
    WebhookEventService,
)


@dataclass
class FakeQueuePublisher:
    """Record published webhook messages for assertions."""

    messages: list[tuple[str, dict[str, Any]]]

    def __init__(self) -> None:
        self.messages = []

    async def publish(
        self,
        message: dict[str, Any],
        *,
        message_id: str,
    ) -> None:
        """Record one published message."""
        self.messages.append((message_id, message))


@pytest.fixture
def repository() -> InMemoryEventRepository:
    """Create an isolated event repository."""
    return InMemoryEventRepository.create()


@pytest.fixture
def publisher() -> FakeQueuePublisher:
    """Create an isolated queue publisher double."""
    return FakeQueuePublisher()


@pytest.fixture
def service(
    repository: InMemoryEventRepository,
    publisher: FakeQueuePublisher,
) -> WebhookEventService:
    """Create an event service with isolated infrastructure."""
    return WebhookEventService(
        repository=repository,
        publisher=publisher,
    )


@pytest.mark.asyncio
async def test_accept_persists_new_event(
    service: WebhookEventService,
    repository: InMemoryEventRepository,
) -> None:
    """Persist a new webhook event with the received status."""
    result = await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )

    stored_event = await repository.get("evt_123")

    assert result.event_id == "evt_123"
    assert result.status == EventStatus.RECEIVED
    assert result.duplicate is False
    assert stored_event is not None
    assert stored_event.event_type == "payment.created"
    assert stored_event.payload == {"payment_id": "pay_123"}
    assert stored_event.status == EventStatus.RECEIVED
    assert stored_event.attempt_count == 0


@pytest.mark.asyncio
async def test_accept_publishes_persisted_event(
    service: WebhookEventService,
    publisher: FakeQueuePublisher,
) -> None:
    """Publish the normalized event after persistence."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )

    assert len(publisher.messages) == 1

    message_id, message = publisher.messages[0]

    assert message_id == "evt_123"
    assert message == {
        "event_id": "evt_123",
        "event_type": "payment.created",
        "payload": {"payment_id": "pay_123"},
        "attempt": 0,
    }


@pytest.mark.asyncio
async def test_accept_is_idempotent_for_duplicate_event(
    service: WebhookEventService,
    publisher: FakeQueuePublisher,
) -> None:
    """Return a duplicate result without publishing the event twice."""
    first_result = await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )

    second_result = await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )

    assert first_result.duplicate is False
    assert second_result.duplicate is True
    assert second_result.event_id == "evt_123"
    assert second_result.status == EventStatus.RECEIVED
    assert len(publisher.messages) == 1


@pytest.mark.asyncio
async def test_accept_normalizes_event_id_and_event_type(
    service: WebhookEventService,
    repository: InMemoryEventRepository,
    publisher: FakeQueuePublisher,
) -> None:
    """Trim provider identifiers and event types before persistence."""
    result = await service.accept(
        event_id="  evt_123  ",
        event_type="  payment.created  ",
        payload={"payment_id": "pay_123"},
    )

    stored_event = await repository.get("evt_123")

    assert result.event_id == "evt_123"
    assert stored_event is not None
    assert stored_event.event_id == "evt_123"
    assert stored_event.event_type == "payment.created"
    assert publisher.messages[0][0] == "evt_123"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("event_id", "event_type"),
    [
        ("", "payment.created"),
        ("   ", "payment.created"),
        ("evt_123", ""),
        ("evt_123", "   "),
    ],
)
async def test_accept_rejects_missing_event_identifiers(
    service: WebhookEventService,
    event_id: str,
    event_type: str,
) -> None:
    """Reject events without valid provider IDs or event types."""
    with pytest.raises(ValueError):
        await service.accept(
            event_id=event_id,
            event_type=event_type,
            payload={},
        )


@pytest.mark.asyncio
async def test_accept_copies_payload(
    service: WebhookEventService,
    repository: InMemoryEventRepository,
) -> None:
    """Prevent later caller mutations from changing stored payload state."""
    payload = {"payment_id": "pay_123", "amount": 100}
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload=payload,
    )

    payload["amount"] = 999

    stored_event = await repository.get("evt_123")

    assert stored_event is not None
    assert stored_event.payload["amount"] == 100


@pytest.mark.asyncio
async def test_mark_processing_transitions_received_event(
    service: WebhookEventService,
    repository: InMemoryEventRepository,
) -> None:
    """Transition a received event into processing and increment attempts."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )

    event = await service.mark_processing("evt_123")

    assert event.status == EventStatus.PROCESSING
    assert event.attempt_count == 1

    stored_event = await repository.get("evt_123")

    assert stored_event is not None
    assert stored_event.status == EventStatus.PROCESSING
    assert stored_event.attempt_count == 1


@pytest.mark.asyncio
async def test_mark_processing_can_retry_failed_event(
    service: WebhookEventService,
    repository: InMemoryEventRepository,
) -> None:
    """Allow failed events to re-enter processing."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )
    await service.mark_processing("evt_123")
    await service.mark_failed("evt_123")

    event = await service.mark_processing("evt_123")

    assert event.status == EventStatus.PROCESSING
    assert event.attempt_count == 2


@pytest.mark.asyncio
async def test_mark_processing_rejects_processed_event(
    service: WebhookEventService,
) -> None:
    """Prevent an already completed event from being processed again."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )
    await service.mark_processing("evt_123")
    await service.mark_processed("evt_123")

    with pytest.raises(
        EventServiceError,
        match="cannot enter processing",
    ):
        await service.mark_processing("evt_123")


@pytest.mark.asyncio
async def test_mark_processed_updates_event_status(
    service: WebhookEventService,
    repository: InMemoryEventRepository,
) -> None:
    """Mark an event as processed after successful business handling."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )
    await service.mark_processing("evt_123")

    event = await service.mark_processed("evt_123")

    assert event.status == EventStatus.PROCESSED
    assert event.attempt_count == 1

    stored_event = await repository.get("evt_123")

    assert stored_event is not None
    assert stored_event.status == EventStatus.PROCESSED


@pytest.mark.asyncio
async def test_mark_processed_rejects_received_event(
    service: WebhookEventService,
) -> None:
    """Require an event to enter processing before completion."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )

    with pytest.raises(
        EventServiceError,
        match="cannot be marked processed",
    ):
        await service.mark_processed("evt_123")


@pytest.mark.asyncio
async def test_mark_failed_updates_event_status(
    service: WebhookEventService,
    repository: InMemoryEventRepository,
) -> None:
    """Mark a processing event as failed for a future retry."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )
    await service.mark_processing("evt_123")

    event = await service.mark_failed("evt_123")

    assert event.status == EventStatus.FAILED
    assert event.attempt_count == 1

    stored_event = await repository.get("evt_123")

    assert stored_event is not None
    assert stored_event.status == EventStatus.FAILED


@pytest.mark.asyncio
async def test_mark_failed_can_dead_letter_event(
    service: WebhookEventService,
    repository: InMemoryEventRepository,
) -> None:
    """Transition a failed processing attempt into the dead-letter state."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )
    await service.mark_processing("evt_123")

    event = await service.mark_failed(
        "evt_123",
        dead_letter=True,
    )

    assert event.status == EventStatus.DEAD_LETTERED

    stored_event = await repository.get("evt_123")

    assert stored_event is not None
    assert stored_event.status == EventStatus.DEAD_LETTERED


@pytest.mark.asyncio
async def test_mark_failed_rejects_non_processing_event(
    service: WebhookEventService,
) -> None:
    """Prevent failure transitions from invalid lifecycle states."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )

    with pytest.raises(
        EventServiceError,
        match="cannot be marked failed",
    ):
        await service.mark_failed("evt_123")


@pytest.mark.asyncio
async def test_lifecycle_preserves_event_identity_and_payload(
    service: WebhookEventService,
) -> None:
    """Preserve immutable event data across lifecycle transitions."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )

    processing_event = await service.mark_processing("evt_123")
    processed_event = await service.mark_processed("evt_123")

    assert processed_event.id == processing_event.id
    assert processed_event.event_id == processing_event.event_id
    assert processed_event.event_type == processing_event.event_type
    assert processed_event.payload == processing_event.payload
    assert processed_event.received_at == processing_event.received_at


@pytest.mark.asyncio
async def test_mark_processing_rejects_missing_event(
    service: WebhookEventService,
) -> None:
    """Raise a service error when the requested event does not exist."""
    with pytest.raises(
        EventServiceError,
        match="evt_missing",
    ):
        await service.mark_processing("evt_missing")


@pytest.mark.asyncio
async def test_mark_processed_rejects_missing_event(
    service: WebhookEventService,
) -> None:
    """Raise a service error when processing a missing event."""
    with pytest.raises(
        EventServiceError,
        match="evt_missing",
    ):
        await service.mark_processed("evt_missing")


@pytest.mark.asyncio
async def test_mark_failed_rejects_missing_event(
    service: WebhookEventService,
) -> None:
    """Raise a service error when failing a missing event."""
    with pytest.raises(
        EventServiceError,
        match="evt_missing",
    ):
        await service.mark_failed("evt_missing")


@pytest.mark.asyncio
async def test_accept_wraps_publisher_failure(
    repository: InMemoryEventRepository,
) -> None:
    """Expose queue failures as service-level errors."""

    class FailingPublisher:
        """Simulate a queue backend failure."""

        async def publish(
            self,
            message: dict[str, Any],
            *,
            message_id: str,
        ) -> None:
            """Raise a simulated infrastructure failure."""
            raise RuntimeError("queue unavailable")

    service = WebhookEventService(
        repository=repository,
        publisher=FailingPublisher(),
    )

    with pytest.raises(
        EventServiceError,
        match="Failed to accept webhook event",
    ):
        await service.accept(
            event_id="evt_123",
            event_type="payment.created",
            payload={"payment_id": "pay_123"},
        )


@pytest.mark.asyncio
async def test_duplicate_accept_returns_existing_event_status(
    service: WebhookEventService,
    repository: InMemoryEventRepository,
) -> None:
    """Return the stored lifecycle status for duplicate deliveries."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )
    await service.mark_processing("evt_123")
    await service.mark_processed("evt_123")

    result = await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "different-payload"},
    )

    assert result.duplicate is True
    assert result.status == EventStatus.PROCESSED

    stored_event = await repository.get("evt_123")

    assert stored_event is not None
    assert stored_event.payload == {"payment_id": "pay_123"}


@pytest.mark.asyncio
async def test_repository_create_if_absent_is_atomic() -> None:
    """Return one winner when the same event is concurrently inserted."""
    import asyncio
    from datetime import datetime, timezone

    repository = InMemoryEventRepository.create()

    def build_event() -> WebhookEvent:
        """Create an event with the same provider identifier."""
        return WebhookEvent(
            event_id="evt_123",
            event_type="payment.created",
            payload={"payment_id": "pay_123"},
            received_at=datetime.now(timezone.utc),
        )

    results = await asyncio.gather(
        repository.create_if_absent(build_event()),
        repository.create_if_absent(build_event()),
    )

    assert sum(created for _, created in results) == 1
    assert sum(not created for _, created in results) == 1

"""Tests for webhook event persistence, idempotency, and lifecycle transitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from src.events.models import EventStatus, WebhookEvent
from src.services.event_service import (
    EventServiceError,
    InMemoryEventRepository,
    WebhookEventService,
)


@dataclass
class FakeQueuePublisher:
    """Record published webhook messages for assertions."""

    messages: list[tuple[str, dict[str, Any]]]

    def __init__(self) -> None:
        self.messages = []

    async def publish(
        self,
        message: dict[str, Any],
        *,
        message_id: str,
    ) -> None:
        """Record one published message."""
        self.messages.append((message_id, message))


@pytest.fixture
def repository() -> InMemoryEventRepository:
    """Create an isolated event repository."""
    return InMemoryEventRepository.create()


@pytest.fixture
def publisher() -> FakeQueuePublisher:
    """Create an isolated queue publisher double."""
    return FakeQueuePublisher()


@pytest.fixture
def service(
    repository: InMemoryEventRepository,
    publisher: FakeQueuePublisher,
) -> WebhookEventService:
    """Create an event service with isolated infrastructure."""
    return WebhookEventService(
        repository=repository,
        publisher=publisher,
    )


@pytest.mark.asyncio
async def test_accept_persists_new_event(
    service: WebhookEventService,
    repository: InMemoryEventRepository,
) -> None:
    """Persist a new webhook event with the received status."""
    result = await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )

    stored_event = await repository.get("evt_123")

    assert result.event_id == "evt_123"
    assert result.status == EventStatus.RECEIVED
    assert result.duplicate is False
    assert stored_event is not None
    assert stored_event.event_type == "payment.created"
    assert stored_event.payload == {"payment_id": "pay_123"}
    assert stored_event.status == EventStatus.RECEIVED
    assert stored_event.attempt_count == 0


@pytest.mark.asyncio
async def test_accept_publishes_persisted_event(
    service: WebhookEventService,
    publisher: FakeQueuePublisher,
) -> None:
    """Publish the normalized event after persistence."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )

    assert len(publisher.messages) == 1

    message_id, message = publisher.messages[0]

    assert message_id == "evt_123"
    assert message == {
        "event_id": "evt_123",
        "event_type": "payment.created",
        "payload": {"payment_id": "pay_123"},
        "attempt": 0,
    }


@pytest.mark.asyncio
async def test_accept_is_idempotent_for_duplicate_event(
    service: WebhookEventService,
    publisher: FakeQueuePublisher,
) -> None:
    """Return a duplicate result without publishing the event twice."""
    first_result = await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )

    second_result = await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )

    assert first_result.duplicate is False
    assert second_result.duplicate is True
    assert second_result.event_id == "evt_123"
    assert second_result.status == EventStatus.RECEIVED
    assert len(publisher.messages) == 1


@pytest.mark.asyncio
async def test_accept_normalizes_event_id_and_event_type(
    service: WebhookEventService,
    repository: InMemoryEventRepository,
    publisher: FakeQueuePublisher,
) -> None:
    """Trim provider identifiers and event types before persistence."""
    result = await service.accept(
        event_id="  evt_123  ",
        event_type="  payment.created  ",
        payload={"payment_id": "pay_123"},
    )

    stored_event = await repository.get("evt_123")

    assert result.event_id == "evt_123"
    assert stored_event is not None
    assert stored_event.event_id == "evt_123"
    assert stored_event.event_type == "payment.created"
    assert publisher.messages[0][0] == "evt_123"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("event_id", "event_type"),
    [
        ("", "payment.created"),
        ("   ", "payment.created"),
        ("evt_123", ""),
        ("evt_123", "   "),
    ],
)
async def test_accept_rejects_missing_event_identifiers(
    service: WebhookEventService,
    event_id: str,
    event_type: str,
) -> None:
    """Reject events without valid provider IDs or event types."""
    with pytest.raises(ValueError):
        await service.accept(
            event_id=event_id,
            event_type=event_type,
            payload={},
        )


@pytest.mark.asyncio
async def test_accept_copies_payload(
    service: WebhookEventService,
    repository: InMemoryEventRepository,
) -> None:
    """Prevent later caller mutations from changing stored payload state."""
    payload = {"payment_id": "pay_123", "amount": 100}
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload=payload,
    )

    payload["amount"] = 999

    stored_event = await repository.get("evt_123")

    assert stored_event is not None
    assert stored_event.payload["amount"] == 100


@pytest.mark.asyncio
async def test_mark_processing_transitions_received_event(
    service: WebhookEventService,
    repository: InMemoryEventRepository,
) -> None:
    """Transition a received event into processing and increment attempts."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )

    event = await service.mark_processing("evt_123")

    assert event.status == EventStatus.PROCESSING
    assert event.attempt_count == 1

    stored_event = await repository.get("evt_123")

    assert stored_event is not None
    assert stored_event.status == EventStatus.PROCESSING
    assert stored_event.attempt_count == 1


@pytest.mark.asyncio
async def test_mark_processing_can_retry_failed_event(
    service: WebhookEventService,
    repository: InMemoryEventRepository,
) -> None:
    """Allow failed events to re-enter processing."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )
    await service.mark_processing("evt_123")
    await service.mark_failed("evt_123")

    event = await service.mark_processing("evt_123")

    assert event.status == EventStatus.PROCESSING
    assert event.attempt_count == 2


@pytest.mark.asyncio
async def test_mark_processing_rejects_processed_event(
    service: WebhookEventService,
) -> None:
    """Prevent an already completed event from being processed again."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )
    await service.mark_processing("evt_123")
    await service.mark_processed("evt_123")

    with pytest.raises(
        EventServiceError,
        match="cannot enter processing",
    ):
        await service.mark_processing("evt_123")


@pytest.mark.asyncio
async def test_mark_processed_updates_event_status(
    service: WebhookEventService,
    repository: InMemoryEventRepository,
) -> None:
    """Mark an event as processed after successful business handling."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )
    await service.mark_processing("evt_123")

    event = await service.mark_processed("evt_123")

    assert event.status == EventStatus.PROCESSED
    assert event.attempt_count == 1

    stored_event = await repository.get("evt_123")

    assert stored_event is not None
    assert stored_event.status == EventStatus.PROCESSED


@pytest.mark.asyncio
async def test_mark_processed_rejects_received_event(
    service: WebhookEventService,
) -> None:
    """Require an event to enter processing before completion."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )

    with pytest.raises(
        EventServiceError,
        match="cannot be marked processed",
    ):
        await service.mark_processed("evt_123")


@pytest.mark.asyncio
async def test_mark_failed_updates_event_status(
    service: WebhookEventService,
    repository: InMemoryEventRepository,
) -> None:
    """Mark a processing event as failed for a future retry."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )
    await service.mark_processing("evt_123")

    event = await service.mark_failed("evt_123")

    assert event.status == EventStatus.FAILED
    assert event.attempt_count == 1

    stored_event = await repository.get("evt_123")

    assert stored_event is not None
    assert stored_event.status == EventStatus.FAILED


@pytest.mark.asyncio
async def test_mark_failed_can_dead_letter_event(
    service: WebhookEventService,
    repository: InMemoryEventRepository,
) -> None:
    """Transition a failed processing attempt into the dead-letter state."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )
    await service.mark_processing("evt_123")

    event = await service.mark_failed(
        "evt_123",
        dead_letter=True,
    )

    assert event.status == EventStatus.DEAD_LETTERED

    stored_event = await repository.get("evt_123")

    assert stored_event is not None
    assert stored_event.status == EventStatus.DEAD_LETTERED


@pytest.mark.asyncio
async def test_mark_failed_rejects_non_processing_event(
    service: WebhookEventService,
) -> None:
    """Prevent failure transitions from invalid lifecycle states."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )

    with pytest.raises(
        EventServiceError,
        match="cannot be marked failed",
    ):
        await service.mark_failed("evt_123")


@pytest.mark.asyncio
async def test_lifecycle_preserves_event_identity_and_payload(
    service: WebhookEventService,
) -> None:
    """Preserve immutable event data across lifecycle transitions."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )

    processing_event = await service.mark_processing("evt_123")
    processed_event = await service.mark_processed("evt_123")

    assert processed_event.id == processing_event.id
    assert processed_event.event_id == processing_event.event_id
    assert processed_event.event_type == processing_event.event_type
    assert processed_event.payload == processing_event.payload
    assert processed_event.received_at == processing_event.received_at


@pytest.mark.asyncio
async def test_mark_processing_rejects_missing_event(
    service: WebhookEventService,
) -> None:
    """Raise a service error when the requested event does not exist."""
    with pytest.raises(
        EventServiceError,
        match="evt_missing",
    ):
        await service.mark_processing("evt_missing")


@pytest.mark.asyncio
async def test_mark_processed_rejects_missing_event(
    service: WebhookEventService,
) -> None:
    """Raise a service error when processing a missing event."""
    with pytest.raises(
        EventServiceError,
        match="evt_missing",
    ):
        await service.mark_processed("evt_missing")


@pytest.mark.asyncio
async def test_mark_failed_rejects_missing_event(
    service: WebhookEventService,
) -> None:
    """Raise a service error when failing a missing event."""
    with pytest.raises(
        EventServiceError,
        match="evt_missing",
    ):
        await service.mark_failed("evt_missing")


@pytest.mark.asyncio
async def test_accept_wraps_publisher_failure(
    repository: InMemoryEventRepository,
) -> None:
    """Expose queue failures as service-level errors."""

    class FailingPublisher:
        """Simulate a queue backend failure."""

        async def publish(
            self,
            message: dict[str, Any],
            *,
            message_id: str,
        ) -> None:
            """Raise a simulated infrastructure failure."""
            raise RuntimeError("queue unavailable")

    service = WebhookEventService(
        repository=repository,
        publisher=FailingPublisher(),
    )

    with pytest.raises(
        EventServiceError,
        match="Failed to accept webhook event",
    ):
        await service.accept(
            event_id="evt_123",
            event_type="payment.created",
            payload={"payment_id": "pay_123"},
        )


@pytest.mark.asyncio
async def test_duplicate_accept_returns_existing_event_status(
    service: WebhookEventService,
    repository: InMemoryEventRepository,
) -> None:
    """Return the stored lifecycle status for duplicate deliveries."""
    await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "pay_123"},
    )
    await service.mark_processing("evt_123")
    await service.mark_processed("evt_123")

    result = await service.accept(
        event_id="evt_123",
        event_type="payment.created",
        payload={"payment_id": "different-payload"},
    )

    assert result.duplicate is True
    assert result.status == EventStatus.PROCESSED

    stored_event = await repository.get("evt_123")

    assert stored_event is not None
    assert stored_event.payload == {"payment_id": "pay_123"}


@pytest.mark.asyncio
async def test_repository_create_if_absent_is_atomic() -> None:
    """Return one winner when the same event is concurrently inserted."""
    import asyncio
    from datetime import datetime, timezone

    repository = InMemoryEventRepository.create()

    def build_event() -> WebhookEvent:
        """Create an event with the same provider identifier."""
        return WebhookEvent(
            event_id="evt_123",
            event_type="payment.created",
            payload={"payment_id": "pay_123"},
            received_at=datetime.now(timezone.utc),
        )

    results = await asyncio.gather(
        repository.create_if_absent(build_event()),
        repository.create_if_absent(build_event()),
    )

    assert sum(created for _, created in results) == 1
    assert sum(not created for _, created in results) == 1