"""MongoDB connection management.

Provides a single MongoClient instance per application process and exposes
helpers for accessing the configured database and performing health checks.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pymongo import MongoClient
from pymongo.database import Database

from src.config.settings import Settings, get_settings


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    """Create and cache the MongoDB client for the current process.

    MongoClient is thread-safe and manages its own connection pool. Reusing
    one client per process avoids unnecessary connection creation and pool
    churn.
    """
    settings = get_settings()

    return MongoClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout_ms,
        connectTimeoutMS=settings.mongodb_connect_timeout_ms,
        socketTimeoutMS=settings.mongodb_socket_timeout_ms,
        maxPoolSize=settings.mongodb_max_pool_size,
        minPoolSize=settings.mongodb_min_pool_size,
        retryWrites=True,
    )


def get_database(
    settings: Settings | None = None,
) -> Database[Any]:
    """Return the configured MongoDB database."""
    settings = settings or get_settings()
    return get_client()[settings.mongodb_database]


def check_connection() -> bool:
    """Verify that MongoDB is reachable and responding."""
    try:
        get_client().admin.command("ping")
        return True
    except Exception:
        return False


def close_connection() -> None:
    """Close the cached MongoDB client and release its connection pool."""
    client = get_client()
    client.close()
    get_client.cache_clear()

"""MongoDB connection management.

Provides a single MongoClient instance per application process and exposes
helpers for accessing the configured database and performing health checks.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pymongo import MongoClient
from pymongo.database import Database

from src.config.settings import Settings, get_settings


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    """Create and cache the MongoDB client for the current process.

    MongoClient is thread-safe and manages its own connection pool. Reusing
    one client per process avoids unnecessary connection creation and pool
    churn.
    """
    settings = get_settings()

    return MongoClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout_ms,
        connectTimeoutMS=settings.mongodb_connect_timeout_ms,
        socketTimeoutMS=settings.mongodb_socket_timeout_ms,
        maxPoolSize=settings.mongodb_max_pool_size,
        minPoolSize=settings.mongodb_min_pool_size,
        retryWrites=True,
    )


def get_database(
    settings: Settings | None = None,
) -> Database[Any]:
    """Return the configured MongoDB database."""
    settings = settings or get_settings()
    return get_client()[settings.mongodb_database]


def check_connection() -> bool:
    """Verify that MongoDB is reachable and responding."""
    try:
        get_client().admin.command("ping")
        return True
    except Exception:
        return False


def close_connection() -> None:
    """Close the cached MongoDB client and release its connection pool."""
    client = get_client()
    client.close()
    get_client.cache_clear()