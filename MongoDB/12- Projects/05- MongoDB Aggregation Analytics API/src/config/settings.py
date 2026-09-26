"""Application settings for the MongoDB aggregation analytics API."""

from __future__ import annotations

import os


MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017",
)

MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "mongodb_aggregation_analytics",
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

MONGODB_RETRY_WRITES = os.getenv(
    "MONGODB_RETRY_WRITES",
    "true",
).lower() in {"1", "true", "yes"}

MONGODB_RETRY_READS = os.getenv(
    "MONGODB_RETRY_READS",
    "true",
).lower() in {"1", "true", "yes"}

API_TITLE = os.getenv(
    "API_TITLE",
    "MongoDB Aggregation Analytics API",
)

API_VERSION = os.getenv(
    "API_VERSION",
    "1.0.0",
)

API_HOST = os.getenv(
    "API_HOST",
    "0.0.0.0",
)

API_PORT = int(
    os.getenv("API_PORT", "8000"),
)

"""Application settings for the MongoDB aggregation analytics API."""

from __future__ import annotations

import os


MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017",
)

MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "mongodb_aggregation_analytics",
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

MONGODB_RETRY_WRITES = os.getenv(
    "MONGODB_RETRY_WRITES",
    "true",
).lower() in {"1", "true", "yes"}

MONGODB_RETRY_READS = os.getenv(
    "MONGODB_RETRY_READS",
    "true",
).lower() in {"1", "true", "yes"}

API_TITLE = os.getenv(
    "API_TITLE",
    "MongoDB Aggregation Analytics API",
)

API_VERSION = os.getenv(
    "API_VERSION",
    "1.0.0",
)

API_HOST = os.getenv(
    "API_HOST",
    "0.0.0.0",
)

API_PORT = int(
    os.getenv("API_PORT", "8000"),
)