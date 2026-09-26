"""Tests for the MongoDB change stream consumer."""

from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest
from pymongo.errors import PyMongoError

from consumers.change_stream import ChangeStreamConsumer


@pytest.fixture
def collection() -> MagicMock:
    """Return a mocked MongoDB collection."""
    return MagicMock()


@pytest.fixture
def handler() -> MagicMock:
    """Return a mocked change event handler."""
    return MagicMock()


@pytest.fixture
def consumer(
    collection: MagicMock,
    handler: MagicMock,
) -> ChangeStreamConsumer:
    """Create a change stream consumer using mocked dependencies."""
    return ChangeStreamConsumer(
        collection=collection,
        event_handler=handler,
    )


def test_consumer_initializes_with_collection_and_handler(
    collection: MagicMock,
    handler: MagicMock,
) -> None:
    """The consumer stores its MongoDB collection and event handler."""
    consumer = ChangeStreamConsumer(
        collection=collection,
        event_handler=handler,
    )

    assert consumer.collection is collection
    assert consumer.event_handler is handler


def test_start_watches_collection_for_supported_events(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
) -> None:
    """The consumer creates a MongoDB change stream with event filtering."""
    change_stream = MagicMock()
    collection.watch.return_value = change_stream

    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.return_value = iter(())

    consumer.start()

    collection.watch.assert_called_once()

    pipeline = collection.watch.call_args.args[0]
    options = collection.watch.call_args.kwargs

    assert pipeline == [
        {
            "$match": {
                "operationType": {
                    "$in": [
                        "insert",
                        "update",
                        "replace",
                        "delete",
                    ]
                }
            }
        }
    ]
    assert options["full_document"] == "updateLookup"


def test_start_processes_insert_event(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
    handler: MagicMock,
) -> None:
    """Insert events are forwarded to the event handler."""
    change_stream = MagicMock()
    collection.watch.return_value = change_stream

    event = {
        "_id": {"_data": "resume-token-1"},
        "operationType": "insert",
        "fullDocument": {
            "_id": "document-001",
            "name": "Alice",
        },
    }

    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.return_value = iter([event])

    consumer.start()

    handler.handle.assert_called_once_with(event)


def test_start_processes_update_event(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
    handler: MagicMock,
) -> None:
    """Update events are forwarded to the event handler."""
    change_stream = MagicMock()
    collection.watch.return_value = change_stream

    event = {
        "_id": {"_data": "resume-token-2"},
        "operationType": "update",
        "documentKey": {"_id": "document-001"},
        "updateDescription": {
            "updatedFields": {"status": "completed"},
            "removedFields": [],
        },
        "fullDocument": {
            "_id": "document-001",
            "status": "completed",
        },
    }

    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.return_value = iter([event])

    consumer.start()

    handler.handle.assert_called_once_with(event)


def test_start_processes_replace_event(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
    handler: MagicMock,
) -> None:
    """Replace events are forwarded to the event handler."""
    change_stream = MagicMock()
    collection.watch.return_value = change_stream

    event = {
        "_id": {"_data": "resume-token-3"},
        "operationType": "replace",
        "documentKey": {"_id": "document-001"},
        "fullDocument": {
            "_id": "document-001",
            "status": "replaced",
        },
    }

    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.return_value = iter([event])

    consumer.start()

    handler.handle.assert_called_once_with(event)


def test_start_processes_delete_event(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
    handler: MagicMock,
) -> None:
    """Delete events are forwarded to the event handler."""
    change_stream = MagicMock()
    collection.watch.return_value = change_stream

    event = {
        "_id": {"_data": "resume-token-4"},
        "operationType": "delete",
        "documentKey": {"_id": "document-001"},
    }

    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.return_value = iter([event])

    consumer.start()

    handler.handle.assert_called_once_with(event)


def test_events_are_processed_in_order(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
    handler: MagicMock,
) -> None:
    """Events are handed to the handler in MongoDB stream order."""
    change_stream = MagicMock()
    collection.watch.return_value = change_stream

    events = [
        {
            "_id": {"_data": "token-1"},
            "operationType": "insert",
            "fullDocument": {"_id": "document-001"},
        },
        {
            "_id": {"_data": "token-2"},
            "operationType": "update",
            "documentKey": {"_id": "document-001"},
        },
        {
            "_id": {"_data": "token-3"},
            "operationType": "delete",
            "documentKey": {"_id": "document-001"},
        },
    ]

    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.return_value = iter(events)

    consumer.start()

    assert handler.handle.call_args_list == [
        call(events[0]),
        call(events[1]),
        call(events[2]),
    ]


def test_handler_failure_does_not_mark_event_as_successfully_processed(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
    handler: MagicMock,
) -> None:
    """Handler failures propagate so the event can be retried or recovered."""
    change_stream = MagicMock()
    collection.watch.return_value = change_stream

    event = {
        "_id": {"_data": "resume-token-5"},
        "operationType": "insert",
        "fullDocument": {"_id": "document-001"},
    }

    handler.handle.side_effect = RuntimeError("processing failed")

    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.return_value = iter([event])

    with pytest.raises(RuntimeError, match="processing failed"):
        consumer.start()

    handler.handle.assert_called_once_with(event)


def test_mongodb_error_from_watch_is_propagated(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
) -> None:
    """MongoDB stream creation failures are not silently swallowed."""
    collection.watch.side_effect = PyMongoError(
        "change stream unavailable"
    )

    with pytest.raises(
        PyMongoError,
        match="change stream unavailable",
    ):
        consumer.start()


def test_consumer_can_resume_from_resume_token(
    collection: MagicMock,
    handler: MagicMock,
) -> None:
    """A consumer can start from a previously persisted resume token."""
    resume_token = {
        "_data": "previous-resume-token",
    }

    consumer = ChangeStreamConsumer(
        collection=collection,
        event_handler=handler,
        resume_token=resume_token,
    )

    change_stream = MagicMock()
    collection.watch.return_value = change_stream
    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.return_value = iter(())

    consumer.start()

    options = collection.watch.call_args.kwargs

    assert options["resume_after"] == resume_token


def test_consumer_does_not_process_events_after_handler_failure(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
    handler: MagicMock,
) -> None:
    """A failed event stops sequential processing before later events."""
    change_stream = MagicMock()
    collection.watch.return_value = change_stream

    events = [
        {
            "_id": {"_data": "token-1"},
            "operationType": "insert",
            "fullDocument": {"_id": "document-001"},
        },
        {
            "_id": {"_data": "token-2"},
            "operationType": "insert",
            "fullDocument": {"_id": "document-002"},
        },
    ]

    handler.handle.side_effect = [
        RuntimeError("first event failed"),
        None,
    ]

    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.return_value = iter(events)

    with pytest.raises(RuntimeError, match="first event failed"):
        consumer.start()

    handler.handle.assert_called_once_with(events[0])


def test_stop_requests_consumer_shutdown(
    consumer: ChangeStreamConsumer,
) -> None:
    """Stopping the consumer changes its running state."""
    consumer.stop()

    assert consumer.is_running is False


def test_start_marks_consumer_as_running_until_stream_finishes(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
) -> None:
    """The consumer exposes its running state while processing a stream."""
    change_stream = MagicMock()
    collection.watch.return_value = change_stream

    states: list[bool] = []

    def event_iterator():
        states.append(consumer.is_running)
        yield {
            "_id": {"_data": "token-1"},
            "operationType": "insert",
            "fullDocument": {"_id": "document-001"},
        }

    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.side_effect = event_iterator

    consumer.start()

    assert states == [True]
    assert consumer.is_running is False

"""Tests for the MongoDB change stream consumer."""

from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest
from pymongo.errors import PyMongoError

from consumers.change_stream import ChangeStreamConsumer


@pytest.fixture
def collection() -> MagicMock:
    """Return a mocked MongoDB collection."""
    return MagicMock()


@pytest.fixture
def handler() -> MagicMock:
    """Return a mocked change event handler."""
    return MagicMock()


@pytest.fixture
def consumer(
    collection: MagicMock,
    handler: MagicMock,
) -> ChangeStreamConsumer:
    """Create a change stream consumer using mocked dependencies."""
    return ChangeStreamConsumer(
        collection=collection,
        event_handler=handler,
    )


def test_consumer_initializes_with_collection_and_handler(
    collection: MagicMock,
    handler: MagicMock,
) -> None:
    """The consumer stores its MongoDB collection and event handler."""
    consumer = ChangeStreamConsumer(
        collection=collection,
        event_handler=handler,
    )

    assert consumer.collection is collection
    assert consumer.event_handler is handler


def test_start_watches_collection_for_supported_events(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
) -> None:
    """The consumer creates a MongoDB change stream with event filtering."""
    change_stream = MagicMock()
    collection.watch.return_value = change_stream

    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.return_value = iter(())

    consumer.start()

    collection.watch.assert_called_once()

    pipeline = collection.watch.call_args.args[0]
    options = collection.watch.call_args.kwargs

    assert pipeline == [
        {
            "$match": {
                "operationType": {
                    "$in": [
                        "insert",
                        "update",
                        "replace",
                        "delete",
                    ]
                }
            }
        }
    ]
    assert options["full_document"] == "updateLookup"


def test_start_processes_insert_event(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
    handler: MagicMock,
) -> None:
    """Insert events are forwarded to the event handler."""
    change_stream = MagicMock()
    collection.watch.return_value = change_stream

    event = {
        "_id": {"_data": "resume-token-1"},
        "operationType": "insert",
        "fullDocument": {
            "_id": "document-001",
            "name": "Alice",
        },
    }

    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.return_value = iter([event])

    consumer.start()

    handler.handle.assert_called_once_with(event)


def test_start_processes_update_event(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
    handler: MagicMock,
) -> None:
    """Update events are forwarded to the event handler."""
    change_stream = MagicMock()
    collection.watch.return_value = change_stream

    event = {
        "_id": {"_data": "resume-token-2"},
        "operationType": "update",
        "documentKey": {"_id": "document-001"},
        "updateDescription": {
            "updatedFields": {"status": "completed"},
            "removedFields": [],
        },
        "fullDocument": {
            "_id": "document-001",
            "status": "completed",
        },
    }

    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.return_value = iter([event])

    consumer.start()

    handler.handle.assert_called_once_with(event)


def test_start_processes_replace_event(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
    handler: MagicMock,
) -> None:
    """Replace events are forwarded to the event handler."""
    change_stream = MagicMock()
    collection.watch.return_value = change_stream

    event = {
        "_id": {"_data": "resume-token-3"},
        "operationType": "replace",
        "documentKey": {"_id": "document-001"},
        "fullDocument": {
            "_id": "document-001",
            "status": "replaced",
        },
    }

    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.return_value = iter([event])

    consumer.start()

    handler.handle.assert_called_once_with(event)


def test_start_processes_delete_event(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
    handler: MagicMock,
) -> None:
    """Delete events are forwarded to the event handler."""
    change_stream = MagicMock()
    collection.watch.return_value = change_stream

    event = {
        "_id": {"_data": "resume-token-4"},
        "operationType": "delete",
        "documentKey": {"_id": "document-001"},
    }

    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.return_value = iter([event])

    consumer.start()

    handler.handle.assert_called_once_with(event)


def test_events_are_processed_in_order(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
    handler: MagicMock,
) -> None:
    """Events are handed to the handler in MongoDB stream order."""
    change_stream = MagicMock()
    collection.watch.return_value = change_stream

    events = [
        {
            "_id": {"_data": "token-1"},
            "operationType": "insert",
            "fullDocument": {"_id": "document-001"},
        },
        {
            "_id": {"_data": "token-2"},
            "operationType": "update",
            "documentKey": {"_id": "document-001"},
        },
        {
            "_id": {"_data": "token-3"},
            "operationType": "delete",
            "documentKey": {"_id": "document-001"},
        },
    ]

    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.return_value = iter(events)

    consumer.start()

    assert handler.handle.call_args_list == [
        call(events[0]),
        call(events[1]),
        call(events[2]),
    ]


def test_handler_failure_does_not_mark_event_as_successfully_processed(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
    handler: MagicMock,
) -> None:
    """Handler failures propagate so the event can be retried or recovered."""
    change_stream = MagicMock()
    collection.watch.return_value = change_stream

    event = {
        "_id": {"_data": "resume-token-5"},
        "operationType": "insert",
        "fullDocument": {"_id": "document-001"},
    }

    handler.handle.side_effect = RuntimeError("processing failed")

    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.return_value = iter([event])

    with pytest.raises(RuntimeError, match="processing failed"):
        consumer.start()

    handler.handle.assert_called_once_with(event)


def test_mongodb_error_from_watch_is_propagated(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
) -> None:
    """MongoDB stream creation failures are not silently swallowed."""
    collection.watch.side_effect = PyMongoError(
        "change stream unavailable"
    )

    with pytest.raises(
        PyMongoError,
        match="change stream unavailable",
    ):
        consumer.start()


def test_consumer_can_resume_from_resume_token(
    collection: MagicMock,
    handler: MagicMock,
) -> None:
    """A consumer can start from a previously persisted resume token."""
    resume_token = {
        "_data": "previous-resume-token",
    }

    consumer = ChangeStreamConsumer(
        collection=collection,
        event_handler=handler,
        resume_token=resume_token,
    )

    change_stream = MagicMock()
    collection.watch.return_value = change_stream
    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.return_value = iter(())

    consumer.start()

    options = collection.watch.call_args.kwargs

    assert options["resume_after"] == resume_token


def test_consumer_does_not_process_events_after_handler_failure(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
    handler: MagicMock,
) -> None:
    """A failed event stops sequential processing before later events."""
    change_stream = MagicMock()
    collection.watch.return_value = change_stream

    events = [
        {
            "_id": {"_data": "token-1"},
            "operationType": "insert",
            "fullDocument": {"_id": "document-001"},
        },
        {
            "_id": {"_data": "token-2"},
            "operationType": "insert",
            "fullDocument": {"_id": "document-002"},
        },
    ]

    handler.handle.side_effect = [
        RuntimeError("first event failed"),
        None,
    ]

    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.return_value = iter(events)

    with pytest.raises(RuntimeError, match="first event failed"):
        consumer.start()

    handler.handle.assert_called_once_with(events[0])


def test_stop_requests_consumer_shutdown(
    consumer: ChangeStreamConsumer,
) -> None:
    """Stopping the consumer changes its running state."""
    consumer.stop()

    assert consumer.is_running is False


def test_start_marks_consumer_as_running_until_stream_finishes(
    consumer: ChangeStreamConsumer,
    collection: MagicMock,
) -> None:
    """The consumer exposes its running state while processing a stream."""
    change_stream = MagicMock()
    collection.watch.return_value = change_stream

    states: list[bool] = []

    def event_iterator():
        states.append(consumer.is_running)
        yield {
            "_id": {"_data": "token-1"},
            "operationType": "insert",
            "fullDocument": {"_id": "document-001"},
        }

    change_stream.__enter__.return_value = change_stream
    change_stream.__iter__.side_effect = event_iterator

    consumer.start()

    assert states == [True]
    assert consumer.is_running is False