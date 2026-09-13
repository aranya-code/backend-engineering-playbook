"""Storage lifecycle helpers for the webhook processing service."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any


class StorageError(RuntimeError):
    """Base exception for storage infrastructure failures."""


class StorageUnavailableError(StorageError):
    """Raised when the backing storage cannot be reached."""


@dataclass(slots=True)
class StorageManager:
    """Manage initialization and shutdown of the service storage layer.

    The manager owns the lifecycle of a storage resource without embedding
    application-specific persistence logic. A production implementation can
    wrap a PostgreSQL connection pool, SQLAlchemy session factory, or another
    durable storage backend.
    """

    initialize: Callable[[], Any]
    close: Callable[[], Any]
    _initialized: bool = False

    async def startup(self) -> None:
        """Initialize the storage backend exactly once."""
        if self._initialized:
            return

        try:
            result = self.initialize()

            if hasattr(result, "__await__"):
                await result
        except Exception as exc:
            raise StorageUnavailableError(
                "Failed to initialize webhook storage."
            ) from exc

        self._initialized = True

    async def shutdown(self) -> None:
        """Close the storage backend and release owned resources."""
        if not self._initialized:
            return

        try:
            result = self.close()

            if hasattr(result, "__await__"):
                await result
        except Exception as exc:
            raise StorageError(
                "Failed to close webhook storage cleanly."
            ) from exc
        finally:
            self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Return whether the storage backend is currently initialized."""
        return self._initialized


@asynccontextmanager
async def storage_lifespan(
    storage: StorageManager,
) -> AsyncIterator[StorageManager]:
    """Manage storage initialization for an application lifespan."""
    await storage.startup()

    try:
        yield storage
    finally:
        await storage.shutdown()

"""Storage lifecycle helpers for the webhook processing service."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any


class StorageError(RuntimeError):
    """Base exception for storage infrastructure failures."""


class StorageUnavailableError(StorageError):
    """Raised when the backing storage cannot be reached."""


@dataclass(slots=True)
class StorageManager:
    """Manage initialization and shutdown of the service storage layer.

    The manager owns the lifecycle of a storage resource without embedding
    application-specific persistence logic. A production implementation can
    wrap a PostgreSQL connection pool, SQLAlchemy session factory, or another
    durable storage backend.
    """

    initialize: Callable[[], Any]
    close: Callable[[], Any]
    _initialized: bool = False

    async def startup(self) -> None:
        """Initialize the storage backend exactly once."""
        if self._initialized:
            return

        try:
            result = self.initialize()

            if hasattr(result, "__await__"):
                await result
        except Exception as exc:
            raise StorageUnavailableError(
                "Failed to initialize webhook storage."
            ) from exc

        self._initialized = True

    async def shutdown(self) -> None:
        """Close the storage backend and release owned resources."""
        if not self._initialized:
            return

        try:
            result = self.close()

            if hasattr(result, "__await__"):
                await result
        except Exception as exc:
            raise StorageError(
                "Failed to close webhook storage cleanly."
            ) from exc
        finally:
            self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Return whether the storage backend is currently initialized."""
        return self._initialized


@asynccontextmanager
async def storage_lifespan(
    storage: StorageManager,
) -> AsyncIterator[StorageManager]:
    """Manage storage initialization for an application lifespan."""
    await storage.startup()

    try:
        yield storage
    finally:
        await storage.shutdown()