"""Retry utilities for transient asynchronous API failures."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from src.exceptions import APIClientError

P = ParamSpec("P")
T = TypeVar("T")


def calculate_backoff(
    attempt: int,
    *,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    jitter: float = 0.2,
) -> float:
    """Calculate exponential backoff with bounded random jitter."""
    if attempt < 0:
        raise ValueError("attempt must not be negative.")
    if base_delay <= 0:
        raise ValueError("base_delay must be greater than zero.")
    if max_delay <= 0:
        raise ValueError("max_delay must be greater than zero.")
    if jitter < 0:
        raise ValueError("jitter must not be negative.")

    exponential_delay = min(base_delay * (2**attempt), max_delay)
    jitter_range = exponential_delay * jitter

    return min(
        exponential_delay + random.uniform(0, jitter_range),
        max_delay,
    )


def retry_async(
    *,
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    jitter: float = 0.2,
    retryable_exceptions: tuple[type[Exception], ...] = (
        TimeoutError,
        ConnectionError,
        APIClientError,
    ),
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Retry an asynchronous operation after configured transient failures."""
    if max_retries < 0:
        raise ValueError("max_retries must not be negative.")

    def decorator(
        function: Callable[P, Awaitable[T]],
    ) -> Callable[P, Awaitable[T]]:
        @wraps(function)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            attempts = max_retries + 1

            for attempt in range(attempts):
                try:
                    return await function(*args, **kwargs)
                except asyncio.CancelledError:
                    raise
                except retryable_exceptions:
                    if attempt >= max_retries:
                        raise

                    delay = calculate_backoff(
                        attempt,
                        base_delay=base_delay,
                        max_delay=max_delay,
                        jitter=jitter,
                    )
                    await asyncio.sleep(delay)

            raise RuntimeError("Retry loop exited unexpectedly.")

        return wrapper

    return decorator

"""Retry utilities for transient asynchronous API failures."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from src.exceptions import APIClientError

P = ParamSpec("P")
T = TypeVar("T")


def calculate_backoff(
    attempt: int,
    *,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    jitter: float = 0.2,
) -> float:
    """Calculate exponential backoff with bounded random jitter."""
    if attempt < 0:
        raise ValueError("attempt must not be negative.")
    if base_delay <= 0:
        raise ValueError("base_delay must be greater than zero.")
    if max_delay <= 0:
        raise ValueError("max_delay must be greater than zero.")
    if jitter < 0:
        raise ValueError("jitter must not be negative.")

    exponential_delay = min(base_delay * (2**attempt), max_delay)
    jitter_range = exponential_delay * jitter

    return min(
        exponential_delay + random.uniform(0, jitter_range),
        max_delay,
    )


def retry_async(
    *,
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    jitter: float = 0.2,
    retryable_exceptions: tuple[type[Exception], ...] = (
        TimeoutError,
        ConnectionError,
        APIClientError,
    ),
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Retry an asynchronous operation after configured transient failures."""
    if max_retries < 0:
        raise ValueError("max_retries must not be negative.")

    def decorator(
        function: Callable[P, Awaitable[T]],
    ) -> Callable[P, Awaitable[T]]:
        @wraps(function)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            attempts = max_retries + 1

            for attempt in range(attempts):
                try:
                    return await function(*args, **kwargs)
                except asyncio.CancelledError:
                    raise
                except retryable_exceptions:
                    if attempt >= max_retries:
                        raise

                    delay = calculate_backoff(
                        attempt,
                        base_delay=base_delay,
                        max_delay=max_delay,
                        jitter=jitter,
                    )
                    await asyncio.sleep(delay)

            raise RuntimeError("Retry loop exited unexpectedly.")

        return wrapper

    return decorator