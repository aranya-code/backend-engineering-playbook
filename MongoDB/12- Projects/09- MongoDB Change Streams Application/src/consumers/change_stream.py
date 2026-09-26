"""MongoDB change stream consumer implementation."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping
from typing import Any

from bson import Timestamp
from pymongo import MongoClient
from pymongo.change_stream import CollectionChangeStream
from pymongo.errors import (
    AutoReconnect,
    ConnectionFailure,
    OperationFailure,
    PyMongoError,
)


logger = logging.getLogger(__name__)

ChangeEvent = Mapping[str, Any]
ChangeEventHandler = Callable[[ChangeEvent], None]


class ChangeStreamConsumer:
    """Consume MongoDB change stream events with resumable processing.

    The consumer uses MongoDB resume tokens to continue from the last
    successfully processed event after transient failures or process
    restarts. Event handlers should be idempotent because an event may be
    delivered more than once when processing succeeds but the resume token
    is not durably persisted before a failure occurs.
    """

    def __init__(
        self,
        client: MongoClient,
        *,
        database_name: str,
        collection_name: str,
        handler: ChangeEventHandler,
        full_document: str = "default",
        max_await_time_ms: int = 1_000,
        batch_size: int = 100,
        resume_token: Mapping[str, Any] | None = None,
        max_retries: int | None = None,
        retry_delay_seconds: float = 2.0,
    ) -> None:
        """Initialize the change stream consumer.

        Args:
            client: Shared MongoDB client.
            database_name: Database containing the watched collection.
            collection_name: Collection to monitor.
            handler: Callable invoked for each change event.
            full_document: Full-document lookup mode for update events.
            max_await_time_ms: Maximum time MongoDB waits for new events.
            batch_size: Maximum number of events requested in each batch.
            resume_token: Previously persisted token used to resume consumption.
            max_retries: Maximum consecutive transient retries. ``None`` means
                retry indefinitely.
            retry_delay_seconds: Delay between transient retry attempts.

        Raises:
            ValueError: If configuration values are invalid.
        """
        if not database_name.strip():
            raise ValueError("database_name must not be empty")

        if not collection_name.strip():
            raise ValueError("collection_name must not be empty")

        if not callable(handler):
            raise ValueError("handler must be callable")

        if max_await_time_ms <= 0:
            raise ValueError("max_await_time_ms must be greater than zero")

        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")

        if max_retries is not None and max_retries < 0:
            raise ValueError("max_retries must be zero or greater")

        if retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must not be negative")

        self._client = client
        self._collection = client[database_name][collection_name]
        self._handler = handler
        self._full_document = full_document
        self._max_await_time_ms = max_await_time_ms
        self._batch_size = batch_size
        self._resume_token = resume_token
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds

        self._running = True
        self._last_event_token: Mapping[str, Any] | None = resume_token

    @property
    def resume_token(self) -> Mapping[str, Any] | None:
        """Return the latest successfully processed resume token."""
        return self._last_event_token

    def stop(self) -> None:
        """Request graceful shutdown of the consumer."""
        self._running = False

    def run(self) -> None:
        """Consume change events until stopped or a fatal error occurs.

        The stream is recreated after transient connection failures. When a
        resume token is available, the next stream starts from that token.
        MongoDB and network failures are retried according to the configured
        retry policy.
        """
        retries = 0

        while self._running:
            try:
                self._consume_stream()
                retries = 0
            except (AutoReconnect, ConnectionFailure) as exc:
                if not self._running:
                    break

                retries += 1

                if (
                    self._max_retries is not None
                    and retries > self._max_retries
                ):
                    logger.exception(
                        "Change stream retry limit exceeded"
                    )
                    raise

                logger.warning(
                    "Change stream connection failed; retry=%d error=%s",
                    retries,
                    exc,
                )

                self._sleep_before_retry(retries)

            except OperationFailure:
                logger.exception(
                    "MongoDB rejected the change stream operation"
                )
                raise

            except PyMongoError:
                logger.exception(
                    "Unexpected MongoDB error in change stream consumer"
                )
                raise

    def _consume_stream(self) -> None:
        """Open and consume one change stream instance."""
        options: dict[str, Any] = {
            "full_document": self._full_document,
            "max_await_time_ms": self._max_await_time_ms,
            "batch_size": self._batch_size,
        }

        if self._resume_token is not None:
            options["resume_after"] = self._resume_token

        logger.info(
            "Starting MongoDB change stream: collection=%s",
            self._collection.full_name,
        )

        with self._collection.watch(**options) as stream:
            self._consume_events(stream)

    def _consume_events(
        self,
        stream: CollectionChangeStream,
    ) -> None:
        """Process events from an active change stream."""
        for event in stream:
            if not self._running:
                break

            try:
                self._handler(event)
            except Exception:
                logger.exception(
                    "Change event handler failed; event will not be acknowledged"
                )
                raise

            token = event.get("_id")

            if token is not None:
                self._last_event_token = token
                self._resume_token = token

                logger.debug(
                    "Change event processed successfully: operation=%s",
                    event.get("operationType"),
                )

    def _sleep_before_retry(self, retry_number: int) -> None:
        """Sleep using bounded exponential backoff before reconnecting."""
        delay = min(
            self._retry_delay_seconds * (2 ** (retry_number - 1)),
            30.0,
        )

        time.sleep(delay)


def create_change_stream(
    client: MongoClient,
    *,
    database_name: str,
    collection_name: str,
    full_document: str = "default",
    max_await_time_ms: int = 1_000,
    batch_size: int = 100,
    resume_token: Mapping[str, Any] | None = None,
) -> CollectionChangeStream:
    """Create a configured MongoDB collection change stream.

    This lower-level helper is useful when the application needs direct
    control over stream iteration rather than the managed retry loop provided
    by :class:`ChangeStreamConsumer`.
    """
    collection = client[database_name][collection_name]

    options: dict[str, Any] = {
        "full_document": full_document,
        "max_await_time_ms": max_await_time_ms,
        "batch_size": batch_size,
    }

    if resume_token is not None:
        options["resume_after"] = resume_token

    return collection.watch(**options)


def log_change_event(event: ChangeEvent) -> None:
    """Example event handler that records the operation type.

    Replace this handler with application-specific processing such as
    publishing to Kafka, updating Redis, invalidating a cache, or invoking
    another service. External side effects must be idempotent.
    """
    operation_type = event.get("operationType", "unknown")

    logger.info(
        "MongoDB change event received: operation=%s",
        operation_type,
    )

    cluster_time = event.get("clusterTime")

    if isinstance(cluster_time, Timestamp):
        logger.debug(
            "MongoDB change event cluster time: timestamp=%s",
            cluster_time,
        )

"""MongoDB change stream consumer implementation."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping
from typing import Any

from bson import Timestamp
from pymongo import MongoClient
from pymongo.change_stream import CollectionChangeStream
from pymongo.errors import (
    AutoReconnect,
    ConnectionFailure,
    OperationFailure,
    PyMongoError,
)


logger = logging.getLogger(__name__)

ChangeEvent = Mapping[str, Any]
ChangeEventHandler = Callable[[ChangeEvent], None]


class ChangeStreamConsumer:
    """Consume MongoDB change stream events with resumable processing.

    The consumer uses MongoDB resume tokens to continue from the last
    successfully processed event after transient failures or process
    restarts. Event handlers should be idempotent because an event may be
    delivered more than once when processing succeeds but the resume token
    is not durably persisted before a failure occurs.
    """

    def __init__(
        self,
        client: MongoClient,
        *,
        database_name: str,
        collection_name: str,
        handler: ChangeEventHandler,
        full_document: str = "default",
        max_await_time_ms: int = 1_000,
        batch_size: int = 100,
        resume_token: Mapping[str, Any] | None = None,
        max_retries: int | None = None,
        retry_delay_seconds: float = 2.0,
    ) -> None:
        """Initialize the change stream consumer.

        Args:
            client: Shared MongoDB client.
            database_name: Database containing the watched collection.
            collection_name: Collection to monitor.
            handler: Callable invoked for each change event.
            full_document: Full-document lookup mode for update events.
            max_await_time_ms: Maximum time MongoDB waits for new events.
            batch_size: Maximum number of events requested in each batch.
            resume_token: Previously persisted token used to resume consumption.
            max_retries: Maximum consecutive transient retries. ``None`` means
                retry indefinitely.
            retry_delay_seconds: Delay between transient retry attempts.

        Raises:
            ValueError: If configuration values are invalid.
        """
        if not database_name.strip():
            raise ValueError("database_name must not be empty")

        if not collection_name.strip():
            raise ValueError("collection_name must not be empty")

        if not callable(handler):
            raise ValueError("handler must be callable")

        if max_await_time_ms <= 0:
            raise ValueError("max_await_time_ms must be greater than zero")

        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")

        if max_retries is not None and max_retries < 0:
            raise ValueError("max_retries must be zero or greater")

        if retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must not be negative")

        self._client = client
        self._collection = client[database_name][collection_name]
        self._handler = handler
        self._full_document = full_document
        self._max_await_time_ms = max_await_time_ms
        self._batch_size = batch_size
        self._resume_token = resume_token
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds

        self._running = True
        self._last_event_token: Mapping[str, Any] | None = resume_token

    @property
    def resume_token(self) -> Mapping[str, Any] | None:
        """Return the latest successfully processed resume token."""
        return self._last_event_token

    def stop(self) -> None:
        """Request graceful shutdown of the consumer."""
        self._running = False

    def run(self) -> None:
        """Consume change events until stopped or a fatal error occurs.

        The stream is recreated after transient connection failures. When a
        resume token is available, the next stream starts from that token.
        MongoDB and network failures are retried according to the configured
        retry policy.
        """
        retries = 0

        while self._running:
            try:
                self._consume_stream()
                retries = 0
            except (AutoReconnect, ConnectionFailure) as exc:
                if not self._running:
                    break

                retries += 1

                if (
                    self._max_retries is not None
                    and retries > self._max_retries
                ):
                    logger.exception(
                        "Change stream retry limit exceeded"
                    )
                    raise

                logger.warning(
                    "Change stream connection failed; retry=%d error=%s",
                    retries,
                    exc,
                )

                self._sleep_before_retry(retries)

            except OperationFailure:
                logger.exception(
                    "MongoDB rejected the change stream operation"
                )
                raise

            except PyMongoError:
                logger.exception(
                    "Unexpected MongoDB error in change stream consumer"
                )
                raise

    def _consume_stream(self) -> None:
        """Open and consume one change stream instance."""
        options: dict[str, Any] = {
            "full_document": self._full_document,
            "max_await_time_ms": self._max_await_time_ms,
            "batch_size": self._batch_size,
        }

        if self._resume_token is not None:
            options["resume_after"] = self._resume_token

        logger.info(
            "Starting MongoDB change stream: collection=%s",
            self._collection.full_name,
        )

        with self._collection.watch(**options) as stream:
            self._consume_events(stream)

    def _consume_events(
        self,
        stream: CollectionChangeStream,
    ) -> None:
        """Process events from an active change stream."""
        for event in stream:
            if not self._running:
                break

            try:
                self._handler(event)
            except Exception:
                logger.exception(
                    "Change event handler failed; event will not be acknowledged"
                )
                raise

            token = event.get("_id")

            if token is not None:
                self._last_event_token = token
                self._resume_token = token

                logger.debug(
                    "Change event processed successfully: operation=%s",
                    event.get("operationType"),
                )

    def _sleep_before_retry(self, retry_number: int) -> None:
        """Sleep using bounded exponential backoff before reconnecting."""
        delay = min(
            self._retry_delay_seconds * (2 ** (retry_number - 1)),
            30.0,
        )

        time.sleep(delay)


def create_change_stream(
    client: MongoClient,
    *,
    database_name: str,
    collection_name: str,
    full_document: str = "default",
    max_await_time_ms: int = 1_000,
    batch_size: int = 100,
    resume_token: Mapping[str, Any] | None = None,
) -> CollectionChangeStream:
    """Create a configured MongoDB collection change stream.

    This lower-level helper is useful when the application needs direct
    control over stream iteration rather than the managed retry loop provided
    by :class:`ChangeStreamConsumer`.
    """
    collection = client[database_name][collection_name]

    options: dict[str, Any] = {
        "full_document": full_document,
        "max_await_time_ms": max_await_time_ms,
        "batch_size": batch_size,
    }

    if resume_token is not None:
        options["resume_after"] = resume_token

    return collection.watch(**options)


def log_change_event(event: ChangeEvent) -> None:
    """Example event handler that records the operation type.

    Replace this handler with application-specific processing such as
    publishing to Kafka, updating Redis, invalidating a cache, or invoking
    another service. External side effects must be idempotent.
    """
    operation_type = event.get("operationType", "unknown")

    logger.info(
        "MongoDB change event received: operation=%s",
        operation_type,
    )

    cluster_time = event.get("clusterTime")

    if isinstance(cluster_time, Timestamp):
        logger.debug(
            "MongoDB change event cluster time: timestamp=%s",
            cluster_time,
        )