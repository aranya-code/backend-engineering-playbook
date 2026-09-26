"""Application configuration for the MongoDB background worker integration."""

from __future__ import annotations

import os


def _get_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    """Read an integer environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    return int(value)


# MongoDB connection
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017",
)
MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "mongodb_background_worker",
)

# MongoDB client timeouts
MONGODB_SERVER_SELECTION_TIMEOUT_MS = _get_int(
    "MONGODB_SERVER_SELECTION_TIMEOUT_MS",
    5000,
)
MONGODB_CONNECT_TIMEOUT_MS = _get_int(
    "MONGODB_CONNECT_TIMEOUT_MS",
    5000,
)
MONGODB_SOCKET_TIMEOUT_MS = _get_int(
    "MONGODB_SOCKET_TIMEOUT_MS",
    30000,
)

# MongoDB connection pool
MONGODB_MAX_POOL_SIZE = _get_int(
    "MONGODB_MAX_POOL_SIZE",
    100,
)
MONGODB_MIN_POOL_SIZE = _get_int(
    "MONGODB_MIN_POOL_SIZE",
    5,
)

# Retryable operations
MONGODB_RETRY_READS = _get_bool(
    "MONGODB_RETRY_READS",
    True,
)
MONGODB_RETRY_WRITES = _get_bool(
    "MONGODB_RETRY_WRITES",
    True,
)

# Background worker
WORKER_NAME = os.getenv(
    "WORKER_NAME",
    "mongodb-background-worker",
)
WORKER_POLL_INTERVAL_SECONDS = _get_int(
    "WORKER_POLL_INTERVAL_SECONDS",
    5,
)
WORKER_BATCH_SIZE = _get_int(
    "WORKER_BATCH_SIZE",
    100,
)
WORKER_MAX_RETRIES = _get_int(
    "WORKER_MAX_RETRIES",
    3,
)
WORKER_RETRY_DELAY_SECONDS = _get_int(
    "WORKER_RETRY_DELAY_SECONDS",
    5,
)

# MongoDB collections
MONGODB_JOBS_COLLECTION = os.getenv(
    "MONGODB_JOBS_COLLECTION",
    "jobs",
)
MONGODB_RESULTS_COLLECTION = os.getenv(
    "MONGODB_RESULTS_COLLECTION",
    "job_results",
)

# Application logging
LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO",
)

"""Application configuration for the MongoDB background worker integration."""

from __future__ import annotations

import os


def _get_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    """Read an integer environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    return int(value)


# MongoDB connection
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017",
)
MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "mongodb_background_worker",
)

# MongoDB client timeouts
MONGODB_SERVER_SELECTION_TIMEOUT_MS = _get_int(
    "MONGODB_SERVER_SELECTION_TIMEOUT_MS",
    5000,
)
MONGODB_CONNECT_TIMEOUT_MS = _get_int(
    "MONGODB_CONNECT_TIMEOUT_MS",
    5000,
)
MONGODB_SOCKET_TIMEOUT_MS = _get_int(
    "MONGODB_SOCKET_TIMEOUT_MS",
    30000,
)

# MongoDB connection pool
MONGODB_MAX_POOL_SIZE = _get_int(
    "MONGODB_MAX_POOL_SIZE",
    100,
)
MONGODB_MIN_POOL_SIZE = _get_int(
    "MONGODB_MIN_POOL_SIZE",
    5,
)

# Retryable operations
MONGODB_RETRY_READS = _get_bool(
    "MONGODB_RETRY_READS",
    True,
)
MONGODB_RETRY_WRITES = _get_bool(
    "MONGODB_RETRY_WRITES",
    True,
)

# Background worker
WORKER_NAME = os.getenv(
    "WORKER_NAME",
    "mongodb-background-worker",
)
WORKER_POLL_INTERVAL_SECONDS = _get_int(
    "WORKER_POLL_INTERVAL_SECONDS",
    5,
)
WORKER_BATCH_SIZE = _get_int(
    "WORKER_BATCH_SIZE",
    100,
)
WORKER_MAX_RETRIES = _get_int(
    "WORKER_MAX_RETRIES",
    3,
)
WORKER_RETRY_DELAY_SECONDS = _get_int(
    "WORKER_RETRY_DELAY_SECONDS",
    5,
)

# MongoDB collections
MONGODB_JOBS_COLLECTION = os.getenv(
    "MONGODB_JOBS_COLLECTION",
    "jobs",
)
MONGODB_RESULTS_COLLECTION = os.getenv(
    "MONGODB_RESULTS_COLLECTION",
    "job_results",
)

# Application logging
LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO",
)