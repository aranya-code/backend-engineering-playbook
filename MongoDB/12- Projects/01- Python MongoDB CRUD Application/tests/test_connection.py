"""Tests for MongoDB connection management."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pymongo import MongoClient

from src.database.connection import (
    check_connection,
    close_connection,
    get_client,
    get_database,
)


@pytest.fixture(autouse=True)
def clear_client_cache() -> None:
    """Ensure connection state does not leak between tests."""
    get_client.cache_clear()
    yield
    get_client.cache_clear()


def test_get_client_returns_cached_client() -> None:
    """The application should reuse one MongoClient per process."""
    with patch("src.database.connection.MongoClient") as mock_client:
        first_client = get_client()
        second_client = get_client()

        assert first_client is second_client
        mock_client.assert_called_once()


def test_get_client_uses_configured_settings() -> None:
    """MongoClient should receive the configured connection parameters."""
    with patch("src.database.connection.MongoClient") as mock_client:
        get_client()

        mock_client.assert_called_once_with(
            "mongodb://localhost:27017",
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            maxPoolSize=100,
            minPoolSize=0,
            retryWrites=True,
        )


def test_get_database_returns_configured_database() -> None:
    """The configured database should be selected from the cached client."""
    mock_database = MagicMock()

    with patch("src.database.connection.get_client") as mock_get_client:
        mock_get_client.return_value.__getitem__.return_value = mock_database

        database = get_database()

        assert database is mock_database


def test_check_connection_returns_true_when_ping_succeeds() -> None:
    """A successful MongoDB ping should report a healthy connection."""
    mock_client = MagicMock(spec=MongoClient)
    mock_client.admin.command.return_value = {"ok": 1}

    with patch("src.database.connection.get_client", return_value=mock_client):
        assert check_connection() is True

    mock_client.admin.command.assert_called_once_with("ping")


def test_check_connection_returns_false_when_ping_fails() -> None:
    """Connection health checks should return false when MongoDB is unreachable."""
    mock_client = MagicMock(spec=MongoClient)
    mock_client.admin.command.side_effect = RuntimeError("MongoDB unavailable")

    with patch("src.database.connection.get_client", return_value=mock_client):
        assert check_connection() is False


def test_close_connection_closes_client_and_clears_cache() -> None:
    """Closing the connection should release the client and clear its cache."""
    mock_client = MagicMock(spec=MongoClient)

    with patch("src.database.connection.get_client", return_value=mock_client):
        close_connection()

    mock_client.close.assert_called_once()
    get_client.cache_clear()

"""Tests for MongoDB connection management."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pymongo import MongoClient

from src.database.connection import (
    check_connection,
    close_connection,
    get_client,
    get_database,
)


@pytest.fixture(autouse=True)
def clear_client_cache() -> None:
    """Ensure connection state does not leak between tests."""
    get_client.cache_clear()
    yield
    get_client.cache_clear()


def test_get_client_returns_cached_client() -> None:
    """The application should reuse one MongoClient per process."""
    with patch("src.database.connection.MongoClient") as mock_client:
        first_client = get_client()
        second_client = get_client()

        assert first_client is second_client
        mock_client.assert_called_once()


def test_get_client_uses_configured_settings() -> None:
    """MongoClient should receive the configured connection parameters."""
    with patch("src.database.connection.MongoClient") as mock_client:
        get_client()

        mock_client.assert_called_once_with(
            "mongodb://localhost:27017",
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            maxPoolSize=100,
            minPoolSize=0,
            retryWrites=True,
        )


def test_get_database_returns_configured_database() -> None:
    """The configured database should be selected from the cached client."""
    mock_database = MagicMock()

    with patch("src.database.connection.get_client") as mock_get_client:
        mock_get_client.return_value.__getitem__.return_value = mock_database

        database = get_database()

        assert database is mock_database


def test_check_connection_returns_true_when_ping_succeeds() -> None:
    """A successful MongoDB ping should report a healthy connection."""
    mock_client = MagicMock(spec=MongoClient)
    mock_client.admin.command.return_value = {"ok": 1}

    with patch("src.database.connection.get_client", return_value=mock_client):
        assert check_connection() is True

    mock_client.admin.command.assert_called_once_with("ping")


def test_check_connection_returns_false_when_ping_fails() -> None:
    """Connection health checks should return false when MongoDB is unreachable."""
    mock_client = MagicMock(spec=MongoClient)
    mock_client.admin.command.side_effect = RuntimeError("MongoDB unavailable")

    with patch("src.database.connection.get_client", return_value=mock_client):
        assert check_connection() is False


def test_close_connection_closes_client_and_clears_cache() -> None:
    """Closing the connection should release the client and clear its cache."""
    mock_client = MagicMock(spec=MongoClient)

    with patch("src.database.connection.get_client", return_value=mock_client):
        close_connection()

    mock_client.close.assert_called_once()
    get_client.cache_clear()