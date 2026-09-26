"""MongoDB connection management utilities."""

from __future__ import annotations

from functools import lru_cache

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


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    """Return the process-wide MongoDB client.

    MongoClient is thread-safe and internally manages connection pooling, so a
    single client should normally be reused for the lifetime of the process.
    """
    return MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=MONGODB_SERVER_SELECTION_TIMEOUT_MS,
        connectTimeoutMS=MONGODB_CONNECT_TIMEOUT_MS,
        socketTimeoutMS=MONGODB_SOCKET_TIMEOUT_MS,
        maxPoolSize=MONGODB_MAX_POOL_SIZE,
        minPoolSize=MONGODB_MIN_POOL_SIZE,
        retryReads=MONGODB_RETRY_READS,
        retryWrites=MONGODB_RETRY_WRITES,
    )


def get_database() -> Database:
    """Return the configured MongoDB database."""
    return get_client()[MONGODB_DATABASE]


def ping_database() -> None:
    """Verify that MongoDB is reachable."""
    get_client().admin.command("ping")


def close_connection() -> None:
    """Close the shared MongoDB client and clear its cached instance."""
    client = get_client()
    client.close()
    get_client.cache_clear()

"""MongoDB connection management utilities."""

from __future__ import annotations

from functools import lru_cache

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


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    """Return the process-wide MongoDB client.

    MongoClient is thread-safe and internally manages connection pooling, so a
    single client should normally be reused for the lifetime of the process.
    """
    return MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=MONGODB_SERVER_SELECTION_TIMEOUT_MS,
        connectTimeoutMS=MONGODB_CONNECT_TIMEOUT_MS,
        socketTimeoutMS=MONGODB_SOCKET_TIMEOUT_MS,
        maxPoolSize=MONGODB_MAX_POOL_SIZE,
        minPoolSize=MONGODB_MIN_POOL_SIZE,
        retryReads=MONGODB_RETRY_READS,
        retryWrites=MONGODB_RETRY_WRITES,
    )


def get_database() -> Database:
    """Return the configured MongoDB database."""
    return get_client()[MONGODB_DATABASE]


def ping_database() -> None:
    """Verify that MongoDB is reachable."""
    get_client().admin.command("ping")


def close_connection() -> None:
    """Close the shared MongoDB client and clear its cached instance."""
    client = get_client()
    client.close()
    get_client.cache_clear()