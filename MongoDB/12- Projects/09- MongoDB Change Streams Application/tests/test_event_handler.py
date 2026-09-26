"""Tests for MongoDB change stream event handling."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from handlers.event_handler import EventHandler


@pytest.fixture
def processor() -> MagicMock:
    """Return a mocked downstream event processor."""
    return MagicMock()


@pytest.fixture
def event_handler(processor: MagicMock) -> EventHandler:
    """Create an event handler with a mocked processor."""
    return EventHandler(processor=processor)


def test_handles_insert_event(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Insert events are dispatched to the processor."""
    event = {
        "_id": {"_data": "resume-token-1"},
        "operationType": "insert",
        "fullDocument": {
            "_id": "document-001",
            "name": "Alice",
        },
    }

    event_handler.handle(event)

    processor.process_insert.assert_called_once_with(
        event["fullDocument"]
    )


def test_handles_update_event(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Update events are dispatched with the complete event payload."""
    event = {
        "_id": {"_data": "resume-token-2"},
        "operationType": "update",
        "documentKey": {"_id": "document-001"},
        "updateDescription": {
            "updatedFields": {
                "status": "completed",
            },
            "removedFields": [],
        },
        "fullDocument": {
            "_id": "document-001",
            "status": "completed",
        },
    }

    event_handler.handle(event)

    processor.process_update.assert_called_once_with(event)


def test_handles_replace_event(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Replace events are dispatched with the replacement document."""
    event = {
        "_id": {"_data": "resume-token-3"},
        "operationType": "replace",
        "documentKey": {"_id": "document-001"},
        "fullDocument": {
            "_id": "document-001",
            "name": "Updated Alice",
        },
    }

    event_handler.handle(event)

    processor.process_replace.assert_called_once_with(
        event["fullDocument"]
    )


def test_handles_delete_event(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Delete events are dispatched using their document key."""
    event = {
        "_id": {"_data": "resume-token-4"},
        "operationType": "delete",
        "documentKey": {
            "_id": "document-001",
        },
    }

    event_handler.handle(event)

    processor.process_delete.assert_called_once_with(
        event["documentKey"]
    )


def test_ignores_unsupported_operation_type(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Unsupported MongoDB operation types are ignored."""
    event = {
        "_id": {"_data": "resume-token-5"},
        "operationType": "invalidate",
    }

    event_handler.handle(event)

    processor.process_insert.assert_not_called()
    processor.process_update.assert_not_called()
    processor.process_replace.assert_not_called()
    processor.process_delete.assert_not_called()


@pytest.mark.parametrize(
    "operation_type",
    [
        "insert",
        "update",
        "replace",
        "delete",
    ],
)
def test_accepts_supported_operation_types(
    event_handler: EventHandler,
    processor: MagicMock,
    operation_type: str,
) -> None:
    """All supported MongoDB change stream operations are dispatched."""
    event = {
        "_id": {"_data": f"resume-{operation_type}"},
        "operationType": operation_type,
        "documentKey": {"_id": "document-001"},
        "fullDocument": {
            "_id": "document-001",
        },
        "updateDescription": {
            "updatedFields": {},
            "removedFields": [],
        },
    }

    event_handler.handle(event)

    assert (
        processor.process_insert.called
        or processor.process_update.called
        or processor.process_replace.called
        or processor.process_delete.called
    )


def test_rejects_event_without_operation_type(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Malformed events without operationType are rejected."""
    event = {
        "_id": {"_data": "resume-token-invalid"},
        "fullDocument": {
            "_id": "document-001",
        },
    }

    with pytest.raises(ValueError, match="operationType"):
        event_handler.handle(event)

    processor.process_insert.assert_not_called()
    processor.process_update.assert_not_called()
    processor.process_replace.assert_not_called()
    processor.process_delete.assert_not_called()


def test_rejects_non_mapping_event(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Non-dictionary events are rejected before dispatch."""
    with pytest.raises((TypeError, ValueError)):
        event_handler.handle(None)

    processor.process_insert.assert_not_called()
    processor.process_update.assert_not_called()
    processor.process_replace.assert_not_called()
    processor.process_delete.assert_not_called()


def test_propagates_processor_failure(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Processor failures propagate to the change stream consumer."""
    event = {
        "_id": {"_data": "resume-token-6"},
        "operationType": "insert",
        "fullDocument": {
            "_id": "document-001",
        },
    }

    processor.process_insert.side_effect = RuntimeError(
        "downstream processing failed"
    )

    with pytest.raises(
        RuntimeError,
        match="downstream processing failed",
    ):
        event_handler.handle(event)

    processor.process_insert.assert_called_once_with(
        event["fullDocument"]
    )


def test_does_not_mutate_event(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Event handling does not modify the MongoDB change event."""
    event = {
        "_id": {"_data": "resume-token-7"},
        "operationType": "insert",
        "fullDocument": {
            "_id": "document-001",
            "status": "created",
        },
    }

    original_event = {
        "_id": {"_data": "resume-token-7"},
        "operationType": "insert",
        "fullDocument": {
            "_id": "document-001",
            "status": "created",
        },
    }

    event_handler.handle(event)

    assert event == original_event


def test_update_event_preserves_update_description(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Update events retain changed and removed field information."""
    event = {
        "_id": {"_data": "resume-token-8"},
        "operationType": "update",
        "documentKey": {"_id": "document-001"},
        "updateDescription": {
            "updatedFields": {
                "status": "completed",
                "attempts": 3,
            },
            "removedFields": [
                "temporary_status",
            ],
        },
    }

    event_handler.handle(event)

    processor.process_update.assert_called_once_with(event)
    assert (
        processor.process_update.call_args.args[0]["updateDescription"]
        == event["updateDescription"]
    )


def test_delete_event_does_not_require_full_document(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Delete events are handled without requiring fullDocument."""
    event = {
        "_id": {"_data": "resume-token-9"},
        "operationType": "delete",
        "documentKey": {
            "_id": "document-001",
        },
    }

    event_handler.handle(event)

    processor.process_delete.assert_called_once_with(
        {
            "_id": "document-001",
        }
    )


def test_handler_dispatches_exactly_one_processor_operation(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Each supported event results in exactly one processor call."""
    event = {
        "_id": {"_data": "resume-token-10"},
        "operationType": "insert",
        "fullDocument": {
            "_id": "document-001",
        },
    }

    event_handler.handle(event)

    assert processor.method_calls == [
        processor.process_insert.call_args
    ]

"""Tests for MongoDB change stream event handling."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from handlers.event_handler import EventHandler


@pytest.fixture
def processor() -> MagicMock:
    """Return a mocked downstream event processor."""
    return MagicMock()


@pytest.fixture
def event_handler(processor: MagicMock) -> EventHandler:
    """Create an event handler with a mocked processor."""
    return EventHandler(processor=processor)


def test_handles_insert_event(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Insert events are dispatched to the processor."""
    event = {
        "_id": {"_data": "resume-token-1"},
        "operationType": "insert",
        "fullDocument": {
            "_id": "document-001",
            "name": "Alice",
        },
    }

    event_handler.handle(event)

    processor.process_insert.assert_called_once_with(
        event["fullDocument"]
    )


def test_handles_update_event(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Update events are dispatched with the complete event payload."""
    event = {
        "_id": {"_data": "resume-token-2"},
        "operationType": "update",
        "documentKey": {"_id": "document-001"},
        "updateDescription": {
            "updatedFields": {
                "status": "completed",
            },
            "removedFields": [],
        },
        "fullDocument": {
            "_id": "document-001",
            "status": "completed",
        },
    }

    event_handler.handle(event)

    processor.process_update.assert_called_once_with(event)


def test_handles_replace_event(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Replace events are dispatched with the replacement document."""
    event = {
        "_id": {"_data": "resume-token-3"},
        "operationType": "replace",
        "documentKey": {"_id": "document-001"},
        "fullDocument": {
            "_id": "document-001",
            "name": "Updated Alice",
        },
    }

    event_handler.handle(event)

    processor.process_replace.assert_called_once_with(
        event["fullDocument"]
    )


def test_handles_delete_event(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Delete events are dispatched using their document key."""
    event = {
        "_id": {"_data": "resume-token-4"},
        "operationType": "delete",
        "documentKey": {
            "_id": "document-001",
        },
    }

    event_handler.handle(event)

    processor.process_delete.assert_called_once_with(
        event["documentKey"]
    )


def test_ignores_unsupported_operation_type(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Unsupported MongoDB operation types are ignored."""
    event = {
        "_id": {"_data": "resume-token-5"},
        "operationType": "invalidate",
    }

    event_handler.handle(event)

    processor.process_insert.assert_not_called()
    processor.process_update.assert_not_called()
    processor.process_replace.assert_not_called()
    processor.process_delete.assert_not_called()


@pytest.mark.parametrize(
    "operation_type",
    [
        "insert",
        "update",
        "replace",
        "delete",
    ],
)
def test_accepts_supported_operation_types(
    event_handler: EventHandler,
    processor: MagicMock,
    operation_type: str,
) -> None:
    """All supported MongoDB change stream operations are dispatched."""
    event = {
        "_id": {"_data": f"resume-{operation_type}"},
        "operationType": operation_type,
        "documentKey": {"_id": "document-001"},
        "fullDocument": {
            "_id": "document-001",
        },
        "updateDescription": {
            "updatedFields": {},
            "removedFields": [],
        },
    }

    event_handler.handle(event)

    assert (
        processor.process_insert.called
        or processor.process_update.called
        or processor.process_replace.called
        or processor.process_delete.called
    )


def test_rejects_event_without_operation_type(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Malformed events without operationType are rejected."""
    event = {
        "_id": {"_data": "resume-token-invalid"},
        "fullDocument": {
            "_id": "document-001",
        },
    }

    with pytest.raises(ValueError, match="operationType"):
        event_handler.handle(event)

    processor.process_insert.assert_not_called()
    processor.process_update.assert_not_called()
    processor.process_replace.assert_not_called()
    processor.process_delete.assert_not_called()


def test_rejects_non_mapping_event(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Non-dictionary events are rejected before dispatch."""
    with pytest.raises((TypeError, ValueError)):
        event_handler.handle(None)

    processor.process_insert.assert_not_called()
    processor.process_update.assert_not_called()
    processor.process_replace.assert_not_called()
    processor.process_delete.assert_not_called()


def test_propagates_processor_failure(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Processor failures propagate to the change stream consumer."""
    event = {
        "_id": {"_data": "resume-token-6"},
        "operationType": "insert",
        "fullDocument": {
            "_id": "document-001",
        },
    }

    processor.process_insert.side_effect = RuntimeError(
        "downstream processing failed"
    )

    with pytest.raises(
        RuntimeError,
        match="downstream processing failed",
    ):
        event_handler.handle(event)

    processor.process_insert.assert_called_once_with(
        event["fullDocument"]
    )


def test_does_not_mutate_event(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Event handling does not modify the MongoDB change event."""
    event = {
        "_id": {"_data": "resume-token-7"},
        "operationType": "insert",
        "fullDocument": {
            "_id": "document-001",
            "status": "created",
        },
    }

    original_event = {
        "_id": {"_data": "resume-token-7"},
        "operationType": "insert",
        "fullDocument": {
            "_id": "document-001",
            "status": "created",
        },
    }

    event_handler.handle(event)

    assert event == original_event


def test_update_event_preserves_update_description(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Update events retain changed and removed field information."""
    event = {
        "_id": {"_data": "resume-token-8"},
        "operationType": "update",
        "documentKey": {"_id": "document-001"},
        "updateDescription": {
            "updatedFields": {
                "status": "completed",
                "attempts": 3,
            },
            "removedFields": [
                "temporary_status",
            ],
        },
    }

    event_handler.handle(event)

    processor.process_update.assert_called_once_with(event)
    assert (
        processor.process_update.call_args.args[0]["updateDescription"]
        == event["updateDescription"]
    )


def test_delete_event_does_not_require_full_document(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Delete events are handled without requiring fullDocument."""
    event = {
        "_id": {"_data": "resume-token-9"},
        "operationType": "delete",
        "documentKey": {
            "_id": "document-001",
        },
    }

    event_handler.handle(event)

    processor.process_delete.assert_called_once_with(
        {
            "_id": "document-001",
        }
    )


def test_handler_dispatches_exactly_one_processor_operation(
    event_handler: EventHandler,
    processor: MagicMock,
) -> None:
    """Each supported event results in exactly one processor call."""
    event = {
        "_id": {"_data": "resume-token-10"},
        "operationType": "insert",
        "fullDocument": {
            "_id": "document-001",
        },
    }

    event_handler.handle(event)

    assert processor.method_calls == [
        processor.process_insert.call_args
    ]