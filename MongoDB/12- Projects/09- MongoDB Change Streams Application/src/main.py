"""MongoDB change streams application entry point."""

from __future__ import annotations

import logging
import os
import signal
from typing import Any

from pymongo import MongoClient
from pymongo.errors import PyMongoError


MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017/?replicaSet=rs0",
)
MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "mongodb_change_streams",
)
MONGODB_COLLECTION = os.getenv(
    "MONGODB_COLLECTION",
    "events",
)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


logger = logging.getLogger(__name__)


class ChangeStreamApplication:
    """Consume MongoDB change events until shutdown is requested."""

    def __init__(
        self,
        client: MongoClient,
        *,
        database_name: str,
        collection_name: str,
    ) -> None:
        self._client = client
        self._collection = client[database_name][collection_name]
        self._shutdown_requested = False

    def request_shutdown(self, signum: int, _frame: Any) -> None:
        """Request a graceful application shutdown."""
        logger.info(
            "Shutdown signal received: signal=%s",
            signum,
        )
        self._shutdown_requested = True

    def run(self) -> None:
        """Consume and process MongoDB change events."""
        logger.info(
            "Starting change stream: database=%s collection=%s",
            self._collection.database.name,
            self._collection.name,
        )

        with self._collection.watch(
            full_document="updateLookup",
        ) as stream:
            for change in stream:
                if self._shutdown_requested:
                    logger.info("Stopping change stream consumer")
                    break

                self.process_change(change)

    @staticmethod
    def process_change(change: dict[str, Any]) -> None:
        """Process a single MongoDB change event.

        Production consumers should make this operation idempotent. If the
        process fails after receiving an event, MongoDB can resume the stream
        from a resume token and the event may be observed again.
        """
        operation_type = change.get("operationType")
        document_key = change.get("documentKey")

        logger.info(
            "Received MongoDB change event: operation=%s document_key=%s",
            operation_type,
            document_key,
        )

        if operation_type == "insert":
            logger.info("Inserted document: %s", change.get("fullDocument"))

        elif operation_type == "update":
            logger.info(
                "Updated document: %s",
                change.get("fullDocument"),
            )

        elif operation_type == "replace":
            logger.info(
                "Replaced document: %s",
                change.get("fullDocument"),
            )

        elif operation_type == "delete":
            logger.info("Deleted document: %s", document_key)

        else:
            logger.info(
                "Unhandled MongoDB operation type: %s",
                operation_type,
            )


def configure_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def create_client() -> MongoClient:
    """Create the application MongoDB client."""
    return MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5_000,
        connectTimeoutMS=5_000,
        socketTimeoutMS=30_000,
        maxPoolSize=20,
        retryReads=True,
        retryWrites=True,
    )


def main() -> int:
    """Run the MongoDB change stream application."""
    configure_logging()

    client = create_client()

    try:
        client.admin.command("ping")

        application = ChangeStreamApplication(
            client,
            database_name=MONGODB_DATABASE,
            collection_name=MONGODB_COLLECTION,
        )

        signal.signal(signal.SIGINT, application.request_shutdown)
        signal.signal(signal.SIGTERM, application.request_shutdown)

        application.run()
        return 0

    except PyMongoError:
        logger.exception("MongoDB change stream application failed")
        return 1

    finally:
        client.close()
        logger.info("MongoDB client closed")


if __name__ == "__main__":
    raise SystemExit(main())

"""MongoDB change streams application entry point."""

from __future__ import annotations

import logging
import os
import signal
from typing import Any

from pymongo import MongoClient
from pymongo.errors import PyMongoError


MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017/?replicaSet=rs0",
)
MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "mongodb_change_streams",
)
MONGODB_COLLECTION = os.getenv(
    "MONGODB_COLLECTION",
    "events",
)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


logger = logging.getLogger(__name__)


class ChangeStreamApplication:
    """Consume MongoDB change events until shutdown is requested."""

    def __init__(
        self,
        client: MongoClient,
        *,
        database_name: str,
        collection_name: str,
    ) -> None:
        self._client = client
        self._collection = client[database_name][collection_name]
        self._shutdown_requested = False

    def request_shutdown(self, signum: int, _frame: Any) -> None:
        """Request a graceful application shutdown."""
        logger.info(
            "Shutdown signal received: signal=%s",
            signum,
        )
        self._shutdown_requested = True

    def run(self) -> None:
        """Consume and process MongoDB change events."""
        logger.info(
            "Starting change stream: database=%s collection=%s",
            self._collection.database.name,
            self._collection.name,
        )

        with self._collection.watch(
            full_document="updateLookup",
        ) as stream:
            for change in stream:
                if self._shutdown_requested:
                    logger.info("Stopping change stream consumer")
                    break

                self.process_change(change)

    @staticmethod
    def process_change(change: dict[str, Any]) -> None:
        """Process a single MongoDB change event.

        Production consumers should make this operation idempotent. If the
        process fails after receiving an event, MongoDB can resume the stream
        from a resume token and the event may be observed again.
        """
        operation_type = change.get("operationType")
        document_key = change.get("documentKey")

        logger.info(
            "Received MongoDB change event: operation=%s document_key=%s",
            operation_type,
            document_key,
        )

        if operation_type == "insert":
            logger.info("Inserted document: %s", change.get("fullDocument"))

        elif operation_type == "update":
            logger.info(
                "Updated document: %s",
                change.get("fullDocument"),
            )

        elif operation_type == "replace":
            logger.info(
                "Replaced document: %s",
                change.get("fullDocument"),
            )

        elif operation_type == "delete":
            logger.info("Deleted document: %s", document_key)

        else:
            logger.info(
                "Unhandled MongoDB operation type: %s",
                operation_type,
            )


def configure_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def create_client() -> MongoClient:
    """Create the application MongoDB client."""
    return MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5_000,
        connectTimeoutMS=5_000,
        socketTimeoutMS=30_000,
        maxPoolSize=20,
        retryReads=True,
        retryWrites=True,
    )


def main() -> int:
    """Run the MongoDB change stream application."""
    configure_logging()

    client = create_client()

    try:
        client.admin.command("ping")

        application = ChangeStreamApplication(
            client,
            database_name=MONGODB_DATABASE,
            collection_name=MONGODB_COLLECTION,
        )

        signal.signal(signal.SIGINT, application.request_shutdown)
        signal.signal(signal.SIGTERM, application.request_shutdown)

        application.run()
        return 0

    except PyMongoError:
        logger.exception("MongoDB change stream application failed")
        return 1

    finally:
        client.close()
        logger.info("MongoDB client closed")


if __name__ == "__main__":
    raise SystemExit(main())