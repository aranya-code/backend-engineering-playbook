"""Asynchronous rate limiting for outbound API requests."""

from __future__ import annotations

import asyncio
import time


class AsyncRateLimiter:
    """Enforce a minimum interval between asynchronous requests."""

    def __init__(self, requests_per_second: float) -> None:
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be greater than zero.")

        self._interval = 1.0 / requests_per_second
        self._lock = asyncio.Lock()
        self._next_allowed_at = 0.0

    async def acquire(self) -> None:
        """Wait until the next request is permitted."""
        async with self._lock:
            now = time.monotonic()
            wait_time = self._next_allowed_at - now

            if wait_time > 0:
                await asyncio.sleep(wait_time)

            self._next_allowed_at = max(
                self._next_allowed_at,
                time.monotonic(),
            ) + self._interval

    async def __aenter__(self) -> AsyncRateLimiter:
        """Acquire permission before entering the context."""
        await self.acquire()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Release the context without additional rate-limiter state."""
        return None

"""Asynchronous rate limiting for outbound API requests."""

from __future__ import annotations

import asyncio
import time


class AsyncRateLimiter:
    """Enforce a minimum interval between asynchronous requests."""

    def __init__(self, requests_per_second: float) -> None:
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be greater than zero.")

        self._interval = 1.0 / requests_per_second
        self._lock = asyncio.Lock()
        self._next_allowed_at = 0.0

    async def acquire(self) -> None:
        """Wait until the next request is permitted."""
        async with self._lock:
            now = time.monotonic()
            wait_time = self._next_allowed_at - now

            if wait_time > 0:
                await asyncio.sleep(wait_time)

            self._next_allowed_at = max(
                self._next_allowed_at,
                time.monotonic(),
            ) + self._interval

    async def __aenter__(self) -> AsyncRateLimiter:
        """Acquire permission before entering the context."""
        await self.acquire()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Release the context without additional rate-limiter state."""
        return None