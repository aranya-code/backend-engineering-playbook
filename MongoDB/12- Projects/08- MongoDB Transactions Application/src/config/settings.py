"""Application configuration for the MongoDB transactions example."""

from __future__ import annotations

import os


def _get_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable with a safe default."""
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    """Read an integer environment variable with validation."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid integer") from exc


MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017",
)

MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "mongodb_transactions",
)

MONGODB_SERVER_SELECTION_TIMEOUT_MS = _get_int(
    "MONGODB_SERVER_SELECTION_TIMEOUT_MS",
    5_000,
)

MONGODB_CONNECT_TIMEOUT_MS = _get_int(
    "MONGODB_CONNECT_TIMEOUT_MS",
    5_000,
)

MONGODB_SOCKET_TIMEOUT_MS = _get_int(
    "MONGODB_SOCKET_TIMEOUT_MS",
    30_000,
)

MONGODB_MAX_POOL_SIZE = _get_int(
    "MONGODB_MAX_POOL_SIZE",
    100,
)

MONGODB_MIN_POOL_SIZE = _get_int(
    "MONGODB_MIN_POOL_SIZE",
    5,
)

MONGODB_RETRY_READS = _get_bool(
    "MONGODB_RETRY_READS",
    True,
)

MONGODB_RETRY_WRITES = _get_bool(
    "MONGODB_RETRY_WRITES",
    True,
)

MONGODB_TRANSACTION_TIMEOUT_MS = _get_int(
    "MONGODB_TRANSACTION_TIMEOUT_MS",
    30_000,
)

"""Application configuration for the MongoDB transactions example."""

from __future__ import annotations

import os


def _get_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable with a safe default."""
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    """Read an integer environment variable with validation."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid integer") from exc


MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017",
)

MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "mongodb_transactions",
)

MONGODB_SERVER_SELECTION_TIMEOUT_MS = _get_int(
    "MONGODB_SERVER_SELECTION_TIMEOUT_MS",
    5_000,
)

MONGODB_CONNECT_TIMEOUT_MS = _get_int(
    "MONGODB_CONNECT_TIMEOUT_MS",
    5_000,
)

MONGODB_SOCKET_TIMEOUT_MS = _get_int(
    "MONGODB_SOCKET_TIMEOUT_MS",
    30_000,
)

MONGODB_MAX_POOL_SIZE = _get_int(
    "MONGODB_MAX_POOL_SIZE",
    100,
)

MONGODB_MIN_POOL_SIZE = _get_int(
    "MONGODB_MIN_POOL_SIZE",
    5,
)

MONGODB_RETRY_READS = _get_bool(
    "MONGODB_RETRY_READS",
    True,
)

MONGODB_RETRY_WRITES = _get_bool(
    "MONGODB_RETRY_WRITES",
    True,
)

MONGODB_TRANSACTION_TIMEOUT_MS = _get_int(
    "MONGODB_TRANSACTION_TIMEOUT_MS",
    30_000,
)