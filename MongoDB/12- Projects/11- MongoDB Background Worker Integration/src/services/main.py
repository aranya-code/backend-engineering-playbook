"""Service-layer entry point for the MongoDB background worker."""

from __future__ import annotations

import logging

from database.connection import (
    check_connection,
    create_mongodb_client,
    get_database,
)
from services.processing_service import ProcessingService

logger = logging.getLogger(__name__)


def create_processing_service() -> tuple[object, ProcessingService]:
    """Create the MongoDB client, database, and processing service."""
    client = create_mongodb_client()
    check_connection(client)

    database = get_database(client)
    service = ProcessingService(database)

    return client, service


def main() -> None:
    """Initialize the processing service and verify MongoDB connectivity."""
    client, _service = create_processing_service()

    try:
        logger.info("MongoDB processing service initialized successfully")
    finally:
        client.close()


if __name__ == "__main__":
    main()

"""Service-layer entry point for the MongoDB background worker."""

from __future__ import annotations

import logging

from database.connection import (
    check_connection,
    create_mongodb_client,
    get_database,
)
from services.processing_service import ProcessingService

logger = logging.getLogger(__name__)


def create_processing_service() -> tuple[object, ProcessingService]:
    """Create the MongoDB client, database, and processing service."""
    client = create_mongodb_client()
    check_connection(client)

    database = get_database(client)
    service = ProcessingService(database)

    return client, service


def main() -> None:
    """Initialize the processing service and verify MongoDB connectivity."""
    client, _service = create_processing_service()

    try:
        logger.info("MongoDB processing service initialized successfully")
    finally:
        client.close()


if __name__ == "__main__":
    main()