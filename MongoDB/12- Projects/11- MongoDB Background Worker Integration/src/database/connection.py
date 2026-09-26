"""MongoDB connection management for the background worker integration."""

from __future__ import annotations

from pymongo import MongoClient
from pymongo.database import Database

from config.settings import (
    MONGODB_CONNECT_TIMEOUT_MS,
    MONGODB_DATABASE,
    MONGODB_MAX_POOL_SIZE,
    MONGODB_MIN_POOL_SIZE,
    MONGODB_RETRY_READS,
    MONGODB_RETRY_WRITES,
    MONGODB_SERVER_SELECTION_TIMEOUT_MS,
    MONGODB_SOCKET_TIMEOUT_MS,
    MONGODB_URI,
)


def create_mongodb_client() -> MongoClient:
    """Create a configured MongoDB client."""
    return MongoClient(
        MONGODB_URI,
        connectTimeoutMS=MONGODB_CONNECT_TIMEOUT_MS,
        serverSelectionTimeoutMS=MONGODB_SERVER_SELECTION_TIMEOUT_MS,
        socketTimeoutMS=MONGODB_SOCKET_TIMEOUT_MS,
        maxPoolSize=MONGODB_MAX_POOL_SIZE,
        minPoolSize=MONGODB_MIN_POOL_SIZE,
        retryReads=MONGODB_RETRY_READS,
        retryWrites=MONGODB_RETRY_WRITES,
    )


def get_database(client: MongoClient) -> Database:
    """Return the configured application database."""
    return client[MONGODB_DATABASE]


def check_connection(client: MongoClient) -> None:
    """Verify that MongoDB is reachable."""
    client.admin.command("ping")

"""MongoDB connection management for the background worker integration."""

from __future__ import annotations

from pymongo import MongoClient
from pymongo.database import Database

from config.settings import (
    MONGODB_CONNECT_TIMEOUT_MS,
    MONGODB_DATABASE,
    MONGODB_MAX_POOL_SIZE,
    MONGODB_MIN_POOL_SIZE,
    MONGODB_RETRY_READS,
    MONGODB_RETRY_WRITES,
    MONGODB_SERVER_SELECTION_TIMEOUT_MS,
    MONGODB_SOCKET_TIMEOUT_MS,
    MONGODB_URI,
)


def create_mongodb_client() -> MongoClient:
    """Create a configured MongoDB client."""
    return MongoClient(
        MONGODB_URI,
        connectTimeoutMS=MONGODB_CONNECT_TIMEOUT_MS,
        serverSelectionTimeoutMS=MONGODB_SERVER_SELECTION_TIMEOUT_MS,
        socketTimeoutMS=MONGODB_SOCKET_TIMEOUT_MS,
        maxPoolSize=MONGODB_MAX_POOL_SIZE,
        minPoolSize=MONGODB_MIN_POOL_SIZE,
        retryReads=MONGODB_RETRY_READS,
        retryWrites=MONGODB_RETRY_WRITES,
    )


def get_database(client: MongoClient) -> Database:
    """Return the configured application database."""
    return client[MONGODB_DATABASE]


def check_connection(client: MongoClient) -> None:
    """Verify that MongoDB is reachable."""
    client.admin.command("ping")