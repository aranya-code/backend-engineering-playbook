"""Application configuration for MongoDB schema validation."""

from __future__ import annotations

import os


MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017",
)

MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "mongodb_schema_validation",
)

MONGODB_COLLECTION = os.getenv(
    "MONGODB_COLLECTION",
    "users",
)

MONGODB_SERVER_SELECTION_TIMEOUT_MS = int(
    os.getenv(
        "MONGODB_SERVER_SELECTION_TIMEOUT_MS",
        "5000",
    )
)

MONGODB_CONNECT_TIMEOUT_MS = int(
    os.getenv(
        "MONGODB_CONNECT_TIMEOUT_MS",
        "5000",
    )
)

MONGODB_SOCKET_TIMEOUT_MS = int(
    os.getenv(
        "MONGODB_SOCKET_TIMEOUT_MS",
        "30000",
    )
)

MONGODB_MAX_POOL_SIZE = int(
    os.getenv(
        "MONGODB_MAX_POOL_SIZE",
        "100",
    )
)

MONGODB_MIN_POOL_SIZE = int(
    os.getenv(
        "MONGODB_MIN_POOL_SIZE",
        "5",
    )
)

MONGODB_RETRY_READS = (
    os.getenv("MONGODB_RETRY_READS", "true").lower() == "true"
)

MONGODB_RETRY_WRITES = (
    os.getenv("MONGODB_RETRY_WRITES", "true").lower() == "true"
)

MONGODB_VALIDATION_LEVEL = os.getenv(
    "MONGODB_VALIDATION_LEVEL",
    "strict",
)

MONGODB_VALIDATION_ACTION = os.getenv(
    "MONGODB_VALIDATION_ACTION",
    "error",
)

"""Application configuration for MongoDB schema validation."""

from __future__ import annotations

import os


MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017",
)

MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "mongodb_schema_validation",
)

MONGODB_COLLECTION = os.getenv(
    "MONGODB_COLLECTION",
    "users",
)

MONGODB_SERVER_SELECTION_TIMEOUT_MS = int(
    os.getenv(
        "MONGODB_SERVER_SELECTION_TIMEOUT_MS",
        "5000",
    )
)

MONGODB_CONNECT_TIMEOUT_MS = int(
    os.getenv(
        "MONGODB_CONNECT_TIMEOUT_MS",
        "5000",
    )
)

MONGODB_SOCKET_TIMEOUT_MS = int(
    os.getenv(
        "MONGODB_SOCKET_TIMEOUT_MS",
        "30000",
    )
)

MONGODB_MAX_POOL_SIZE = int(
    os.getenv(
        "MONGODB_MAX_POOL_SIZE",
        "100",
    )
)

MONGODB_MIN_POOL_SIZE = int(
    os.getenv(
        "MONGODB_MIN_POOL_SIZE",
        "5",
    )
)

MONGODB_RETRY_READS = (
    os.getenv("MONGODB_RETRY_READS", "true").lower() == "true"
)

MONGODB_RETRY_WRITES = (
    os.getenv("MONGODB_RETRY_WRITES", "true").lower() == "true"
)

MONGODB_VALIDATION_LEVEL = os.getenv(
    "MONGODB_VALIDATION_LEVEL",
    "strict",
)

MONGODB_VALIDATION_ACTION = os.getenv(
    "MONGODB_VALIDATION_ACTION",
    "error",
)