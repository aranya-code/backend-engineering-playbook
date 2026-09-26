"""MongoDB connection management for the FastAPI application."""

from __future__ import annotations

from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from src.config.settings import Settings, get_settings


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    """Create and cache one MongoDB client per application process."""
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


def get_database() -> Database:
    """Return the configured MongoDB database."""
    settings = get_settings()
    return get_client()[settings.mongodb_database]


def check_connection() -> bool:
    """Return whether MongoDB is reachable."""
    try:
        get_client().admin.command("ping")
    except Exception:
        return False

    return True


def close_connection() -> None:
    """Close the MongoDB client and release its connection pool."""
    get_client().close()
    get_client.cache_clear()

"""MongoDB connection management for the FastAPI application."""

from __future__ import annotations

from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from src.config.settings import Settings, get_settings


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    """Create and cache one MongoDB client per application process."""
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


def get_database() -> Database:
    """Return the configured MongoDB database."""
    settings = get_settings()
    return get_client()[settings.mongodb_database]


def check_connection() -> bool:
    """Return whether MongoDB is reachable."""
    try:
        get_client().admin.command("ping")
    except Exception:
        return False

    return True


def close_connection() -> None:
    """Close the MongoDB client and release its connection pool."""
    get_client().close()
    get_client.cache_clear()