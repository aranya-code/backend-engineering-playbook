"""Application settings for the MongoDB query performance optimization project."""

from __future__ import annotations

import os


MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017",
)

MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "mongodb_query_performance",
)

MONGODB_SERVER_SELECTION_TIMEOUT_MS = int(
    os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000"),
)

MONGODB_CONNECT_TIMEOUT_MS = int(
    os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "5000"),
)

MONGODB_SOCKET_TIMEOUT_MS = int(
    os.getenv("MONGODB_SOCKET_TIMEOUT_MS", "10000"),
)

MONGODB_MAX_POOL_SIZE = int(
    os.getenv("MONGODB_MAX_POOL_SIZE", "100"),
)

MONGODB_MIN_POOL_SIZE = int(
    os.getenv("MONGODB_MIN_POOL_SIZE", "0"),
)

MONGODB_RETRY_READS = os.getenv(
    "MONGODB_RETRY_READS",
    "true",
).lower() in {"1", "true", "yes"}

MONGODB_RETRY_WRITES = os.getenv(
    "MONGODB_RETRY_WRITES",
    "true",
).lower() in {"1", "true", "yes"}

"""Application settings for the MongoDB query performance optimization project."""

from __future__ import annotations

import os


MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017",
)

MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "mongodb_query_performance",
)

MONGODB_SERVER_SELECTION_TIMEOUT_MS = int(
    os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000"),
)

MONGODB_CONNECT_TIMEOUT_MS = int(
    os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "5000"),
)

MONGODB_SOCKET_TIMEOUT_MS = int(
    os.getenv("MONGODB_SOCKET_TIMEOUT_MS", "10000"),
)

MONGODB_MAX_POOL_SIZE = int(
    os.getenv("MONGODB_MAX_POOL_SIZE", "100"),
)

MONGODB_MIN_POOL_SIZE = int(
    os.getenv("MONGODB_MIN_POOL_SIZE", "0"),
)

MONGODB_RETRY_READS = os.getenv(
    "MONGODB_RETRY_READS",
    "true",
).lower() in {"1", "true", "yes"}

MONGODB_RETRY_WRITES = os.getenv(
    "MONGODB_RETRY_WRITES",
    "true",
).lower() in {"1", "true", "yes"}