"""Application configuration for the FastAPI MongoDB REST API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _get_int(name: str, default: int) -> int:
    """Read an integer environment variable with validation."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid integer") from exc

    if parsed < 0:
        raise ValueError(f"{name} must be greater than or equal to zero")

    return parsed


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable application settings loaded from environment variables."""

    mongodb_uri: str
    mongodb_database: str
    mongodb_server_selection_timeout_ms: int
    mongodb_connect_timeout_ms: int
    mongodb_socket_timeout_ms: int
    mongodb_max_pool_size: int
    mongodb_min_pool_size: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application configuration."""
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_database = os.getenv("MONGODB_DATABASE", "fastapi_mongodb")

    if not mongodb_uri.strip():
        raise ValueError("MONGODB_URI must not be empty")

    if not mongodb_database.strip():
        raise ValueError("MONGODB_DATABASE must not be empty")

    max_pool_size = _get_int("MONGODB_MAX_POOL_SIZE", 100)
    min_pool_size = _get_int("MONGODB_MIN_POOL_SIZE", 0)

    if min_pool_size > max_pool_size:
        raise ValueError(
            "MONGODB_MIN_POOL_SIZE must not exceed MONGODB_MAX_POOL_SIZE"
        )

    return Settings(
        mongodb_uri=mongodb_uri,
        mongodb_database=mongodb_database,
        mongodb_server_selection_timeout_ms=_get_int(
            "MONGODB_SERVER_SELECTION_TIMEOUT_MS",
            5_000,
        ),
        mongodb_connect_timeout_ms=_get_int(
            "MONGODB_CONNECT_TIMEOUT_MS",
            5_000,
        ),
        mongodb_socket_timeout_ms=_get_int(
            "MONGODB_SOCKET_TIMEOUT_MS",
            10_000,
        ),
        mongodb_max_pool_size=max_pool_size,
        mongodb_min_pool_size=min_pool_size,
    )

"""Application configuration for the FastAPI MongoDB REST API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _get_int(name: str, default: int) -> int:
    """Read an integer environment variable with validation."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid integer") from exc

    if parsed < 0:
        raise ValueError(f"{name} must be greater than or equal to zero")

    return parsed


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable application settings loaded from environment variables."""

    mongodb_uri: str
    mongodb_database: str
    mongodb_server_selection_timeout_ms: int
    mongodb_connect_timeout_ms: int
    mongodb_socket_timeout_ms: int
    mongodb_max_pool_size: int
    mongodb_min_pool_size: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application configuration."""
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_database = os.getenv("MONGODB_DATABASE", "fastapi_mongodb")

    if not mongodb_uri.strip():
        raise ValueError("MONGODB_URI must not be empty")

    if not mongodb_database.strip():
        raise ValueError("MONGODB_DATABASE must not be empty")

    max_pool_size = _get_int("MONGODB_MAX_POOL_SIZE", 100)
    min_pool_size = _get_int("MONGODB_MIN_POOL_SIZE", 0)

    if min_pool_size > max_pool_size:
        raise ValueError(
            "MONGODB_MIN_POOL_SIZE must not exceed MONGODB_MAX_POOL_SIZE"
        )

    return Settings(
        mongodb_uri=mongodb_uri,
        mongodb_database=mongodb_database,
        mongodb_server_selection_timeout_ms=_get_int(
            "MONGODB_SERVER_SELECTION_TIMEOUT_MS",
            5_000,
        ),
        mongodb_connect_timeout_ms=_get_int(
            "MONGODB_CONNECT_TIMEOUT_MS",
            5_000,
        ),
        mongodb_socket_timeout_ms=_get_int(
            "MONGODB_SOCKET_TIMEOUT_MS",
            10_000,
        ),
        mongodb_max_pool_size=max_pool_size,
        mongodb_min_pool_size=min_pool_size,
    )