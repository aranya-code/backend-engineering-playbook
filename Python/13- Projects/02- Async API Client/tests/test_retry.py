"""Tests for asynchronous retry utilities."""

from __future__ import annotations

import asyncio

import pytest

from src.exceptions import APIClientError
from src.retry import calculate_backoff, retry_async


def test_calculate_backoff_uses_exponential_delay() -> None:
    """Backoff should double from the configured base delay per attempt."""
    assert calculate_backoff(
        0,
        base_delay=0.5,
        max_delay=30.0,
        jitter=0.0,
    ) == 0.5
    assert calculate_backoff(
        1,
        base_delay=0.5,
        max_delay=30.0,
        jitter=0.0,
    ) == 1.0
    assert calculate_backoff(
        2,
        base_delay=0.5,
        max_delay=30.0,
        jitter=0.0,
    ) == 2.0


def test_calculate_backoff_respects_maximum_delay() -> None:
    """Backoff should never exceed the configured maximum."""
    assert calculate_backoff(
        10,
        base_delay=1.0,
        max_delay=5.0,
        jitter=0.0,
    ) == 5.0


def test_calculate_backoff_applies_jitter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Jitter should increase the base delay within its configured bound."""
    monkeypatch.setattr("src.retry.random.uniform", lambda start, end: end)

    delay = calculate_backoff(
        1,
        base_delay=1.0,
        max_delay=30.0,
        jitter=0.2,
    )

    assert delay == 2.4


@pytest.mark.parametrize(
    ("attempt", "base_delay", "max_delay", "jitter"),
    [
        (-1, 0.5, 30.0, 0.2),
        (0, 0.0, 30.0, 0.2),
        (0, 0.5, 0.0, 0.2),
        (0, 0.5, 30.0, -0.1),
    ],
)
def test_calculate_backoff_rejects_invalid_configuration(
    attempt: int,
    base_delay: float,
    max_delay: float,
    jitter: float,
) -> None:
    """Invalid backoff parameters should fail before execution."""
    with pytest.raises(ValueError):
        calculate_backoff(
            attempt,
            base_delay=base_delay,
            max_delay=max_delay,
            jitter=jitter,
        )


def test_retry_async_rejects_negative_retry_count() -> None:
    """Retry configuration must not permit a negative retry count."""
    with pytest.raises(ValueError, match="must not be negative"):
        retry_async(max_retries=-1)


@pytest.mark.asyncio
async def test_retry_async_returns_success_without_retry() -> None:
    """A successful operation should execute exactly once."""
    call_count = 0

    @retry_async(max_retries=3, jitter=0.0)
    async def operation() -> str:
        nonlocal call_count
        call_count += 1
        return "success"

    result = await operation()

    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_async_retries_transient_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Retryable failures should be retried until the operation succeeds."""
    call_count = 0
    delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    @retry_async(
        max_retries=2,
        base_delay=0.5,
        max_delay=30.0,
        jitter=0.0,
    )
    async def operation() -> str:
        nonlocal call_count
        call_count += 1

        if call_count < 3:
            raise TimeoutError("temporary timeout")

        return "success"

    result = await operation()

    assert result == "success"
    assert call_count == 3
    assert delays == [0.5, 1.0]


@pytest.mark.asyncio
async def test_retry_async_raises_after_retries_are_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The final retryable exception should be propagated."""
    call_count = 0

    async def fake_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    @retry_async(
        max_retries=2,
        base_delay=0.5,
        jitter=0.0,
    )
    async def operation() -> None:
        nonlocal call_count
        call_count += 1
        raise ConnectionError("connection failed")

    with pytest.raises(ConnectionError, match="connection failed"):
        await operation()

    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_async_does_not_retry_non_retryable_exception() -> None:
    """Non-retryable exceptions should propagate immediately."""
    call_count = 0

    @retry_async(max_retries=3, jitter=0.0)
    async def operation() -> None:
        nonlocal call_count
        call_count += 1
        raise ValueError("invalid request")

    with pytest.raises(ValueError, match="invalid request"):
        await operation()

    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_async_retries_api_client_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """API client failures should use the retry policy by default."""
    call_count = 0

    async def fake_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    @retry_async(max_retries=1, jitter=0.0)
    async def operation() -> str:
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            raise APIClientError("transient client failure")

        return "success"

    assert await operation() == "success"
    assert call_count == 2


@pytest.mark.asyncio
async def test_retry_async_preserves_function_metadata() -> None:
    """The retry decorator should preserve the wrapped function metadata."""

    @retry_async(max_retries=1)
    async def operation() -> str:
        """Return a successful operation result."""
        return "success"

    assert operation.__name__ == "operation"
    assert operation.__doc__ == "Return a successful operation result."


@pytest.mark.asyncio
async def test_retry_async_propagates_cancellation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Task cancellation must not be swallowed by the retry mechanism."""
    sleep_called = False

    async def fake_sleep(_: float) -> None:
        nonlocal sleep_called
        sleep_called = True

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    @retry_async(max_retries=3)
    async def operation() -> None:
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await operation()

    assert sleep_called is False


@pytest.mark.asyncio
async def test_custom_retryable_exceptions_limit_retry_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Custom exception configuration should restrict what gets retried."""
    call_count = 0

    async def fake_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    @retry_async(
        max_retries=2,
        retryable_exceptions=(TimeoutError,),
        jitter=0.0,
    )
    async def operation() -> None:
        nonlocal call_count
        call_count += 1
        raise ConnectionError("not configured for retry")

    with pytest.raises(ConnectionError, match="not configured for retry"):
        await operation()

    assert call_count == 1

"""Tests for asynchronous retry utilities."""

from __future__ import annotations

import asyncio

import pytest

from src.exceptions import APIClientError
from src.retry import calculate_backoff, retry_async


def test_calculate_backoff_uses_exponential_delay() -> None:
    """Backoff should double from the configured base delay per attempt."""
    assert calculate_backoff(
        0,
        base_delay=0.5,
        max_delay=30.0,
        jitter=0.0,
    ) == 0.5
    assert calculate_backoff(
        1,
        base_delay=0.5,
        max_delay=30.0,
        jitter=0.0,
    ) == 1.0
    assert calculate_backoff(
        2,
        base_delay=0.5,
        max_delay=30.0,
        jitter=0.0,
    ) == 2.0


def test_calculate_backoff_respects_maximum_delay() -> None:
    """Backoff should never exceed the configured maximum."""
    assert calculate_backoff(
        10,
        base_delay=1.0,
        max_delay=5.0,
        jitter=0.0,
    ) == 5.0


def test_calculate_backoff_applies_jitter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Jitter should increase the base delay within its configured bound."""
    monkeypatch.setattr("src.retry.random.uniform", lambda start, end: end)

    delay = calculate_backoff(
        1,
        base_delay=1.0,
        max_delay=30.0,
        jitter=0.2,
    )

    assert delay == 2.4


@pytest.mark.parametrize(
    ("attempt", "base_delay", "max_delay", "jitter"),
    [
        (-1, 0.5, 30.0, 0.2),
        (0, 0.0, 30.0, 0.2),
        (0, 0.5, 0.0, 0.2),
        (0, 0.5, 30.0, -0.1),
    ],
)
def test_calculate_backoff_rejects_invalid_configuration(
    attempt: int,
    base_delay: float,
    max_delay: float,
    jitter: float,
) -> None:
    """Invalid backoff parameters should fail before execution."""
    with pytest.raises(ValueError):
        calculate_backoff(
            attempt,
            base_delay=base_delay,
            max_delay=max_delay,
            jitter=jitter,
        )


def test_retry_async_rejects_negative_retry_count() -> None:
    """Retry configuration must not permit a negative retry count."""
    with pytest.raises(ValueError, match="must not be negative"):
        retry_async(max_retries=-1)


@pytest.mark.asyncio
async def test_retry_async_returns_success_without_retry() -> None:
    """A successful operation should execute exactly once."""
    call_count = 0

    @retry_async(max_retries=3, jitter=0.0)
    async def operation() -> str:
        nonlocal call_count
        call_count += 1
        return "success"

    result = await operation()

    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_async_retries_transient_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Retryable failures should be retried until the operation succeeds."""
    call_count = 0
    delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    @retry_async(
        max_retries=2,
        base_delay=0.5,
        max_delay=30.0,
        jitter=0.0,
    )
    async def operation() -> str:
        nonlocal call_count
        call_count += 1

        if call_count < 3:
            raise TimeoutError("temporary timeout")

        return "success"

    result = await operation()

    assert result == "success"
    assert call_count == 3
    assert delays == [0.5, 1.0]


@pytest.mark.asyncio
async def test_retry_async_raises_after_retries_are_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The final retryable exception should be propagated."""
    call_count = 0

    async def fake_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    @retry_async(
        max_retries=2,
        base_delay=0.5,
        jitter=0.0,
    )
    async def operation() -> None:
        nonlocal call_count
        call_count += 1
        raise ConnectionError("connection failed")

    with pytest.raises(ConnectionError, match="connection failed"):
        await operation()

    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_async_does_not_retry_non_retryable_exception() -> None:
    """Non-retryable exceptions should propagate immediately."""
    call_count = 0

    @retry_async(max_retries=3, jitter=0.0)
    async def operation() -> None:
        nonlocal call_count
        call_count += 1
        raise ValueError("invalid request")

    with pytest.raises(ValueError, match="invalid request"):
        await operation()

    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_async_retries_api_client_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """API client failures should use the retry policy by default."""
    call_count = 0

    async def fake_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    @retry_async(max_retries=1, jitter=0.0)
    async def operation() -> str:
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            raise APIClientError("transient client failure")

        return "success"

    assert await operation() == "success"
    assert call_count == 2


@pytest.mark.asyncio
async def test_retry_async_preserves_function_metadata() -> None:
    """The retry decorator should preserve the wrapped function metadata."""

    @retry_async(max_retries=1)
    async def operation() -> str:
        """Return a successful operation result."""
        return "success"

    assert operation.__name__ == "operation"
    assert operation.__doc__ == "Return a successful operation result."


@pytest.mark.asyncio
async def test_retry_async_propagates_cancellation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Task cancellation must not be swallowed by the retry mechanism."""
    sleep_called = False

    async def fake_sleep(_: float) -> None:
        nonlocal sleep_called
        sleep_called = True

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    @retry_async(max_retries=3)
    async def operation() -> None:
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await operation()

    assert sleep_called is False


@pytest.mark.asyncio
async def test_custom_retryable_exceptions_limit_retry_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Custom exception configuration should restrict what gets retried."""
    call_count = 0

    async def fake_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    @retry_async(
        max_retries=2,
        retryable_exceptions=(TimeoutError,),
        jitter=0.0,
    )
    async def operation() -> None:
        nonlocal call_count
        call_count += 1
        raise ConnectionError("not configured for retry")

    with pytest.raises(ConnectionError, match="not configured for retry"):
        await operation()

    assert call_count == 1