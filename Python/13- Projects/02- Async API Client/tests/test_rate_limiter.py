"""Tests for asynchronous API rate limiting."""

from __future__ import annotations

import asyncio

import pytest

from src.rate_limiter import AsyncRateLimiter


def test_rate_limiter_rejects_non_positive_rate() -> None:
    """The configured request rate must be greater than zero."""
    with pytest.raises(ValueError, match="greater than zero"):
        AsyncRateLimiter(0)

    with pytest.raises(ValueError, match="greater than zero"):
        AsyncRateLimiter(-1)


@pytest.mark.asyncio
async def test_first_acquire_does_not_wait(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The first request should be permitted immediately."""
    limiter = AsyncRateLimiter(requests_per_second=10)

    current_time = 100.0
    sleeps: list[float] = []

    monkeypatch.setattr(
        "src.rate_limiter.time.monotonic",
        lambda: current_time,
    )

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    await limiter.acquire()

    assert sleeps == []


@pytest.mark.asyncio
async def test_acquire_enforces_request_interval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Subsequent requests should wait for the configured interval."""
    limiter = AsyncRateLimiter(requests_per_second=2)

    current_time = 100.0
    sleeps: list[float] = []

    monkeypatch.setattr(
        "src.rate_limiter.time.monotonic",
        lambda: current_time,
    )

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    await limiter.acquire()
    current_time = 100.1
    await limiter.acquire()

    assert sleeps == pytest.approx([0.4])


@pytest.mark.asyncio
async def test_acquire_allows_request_after_interval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A request arriving after the interval should not be delayed."""
    limiter = AsyncRateLimiter(requests_per_second=2)

    current_time = 100.0
    sleeps: list[float] = []

    monkeypatch.setattr(
        "src.rate_limiter.time.monotonic",
        lambda: current_time,
    )

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    await limiter.acquire()
    current_time = 100.5
    await limiter.acquire()

    assert sleeps == []


@pytest.mark.asyncio
async def test_acquire_serializes_concurrent_callers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Concurrent callers should share one rate-limiting schedule."""
    limiter = AsyncRateLimiter(requests_per_second=10)

    current_time = 100.0
    sleeps: list[float] = []

    monkeypatch.setattr(
        "src.rate_limiter.time.monotonic",
        lambda: current_time,
    )

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    await asyncio.gather(
        limiter.acquire(),
        limiter.acquire(),
        limiter.acquire(),
    )

    assert len(sleeps) == 2
    assert sleeps == pytest.approx([0.1, 0.1])


@pytest.mark.asyncio
async def test_rate_limiter_uses_monotonic_clock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rate limiting should use a monotonic clock rather than wall time."""
    limiter = AsyncRateLimiter(requests_per_second=5)

    monotonic_calls = 0
    current_time = 50.0

    def fake_monotonic() -> float:
        nonlocal monotonic_calls
        monotonic_calls += 1
        return current_time

    monkeypatch.setattr(
        "src.rate_limiter.time.monotonic",
        fake_monotonic,
    )

    async def fake_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    await limiter.acquire()

    assert monotonic_calls >= 1


@pytest.mark.asyncio
async def test_context_manager_acquires_rate_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Using the limiter as a context manager should acquire permission."""
    limiter = AsyncRateLimiter(requests_per_second=2)

    current_time = 100.0
    sleeps: list[float] = []

    monkeypatch.setattr(
        "src.rate_limiter.time.monotonic",
        lambda: current_time,
    )

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    async with limiter:
        pass

    current_time = 100.1

    async with limiter:
        pass

    assert sleeps == pytest.approx([0.4])


@pytest.mark.asyncio
async def test_context_manager_does_not_release_extra_capacity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exiting the context must not reset the limiter's request schedule."""
    limiter = AsyncRateLimiter(requests_per_second=2)

    current_time = 100.0
    sleeps: list[float] = []

    monkeypatch.setattr(
        "src.rate_limiter.time.monotonic",
        lambda: current_time,
    )

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    async with limiter:
        pass

    current_time = 100.1

    async with limiter:
        pass

    assert sleeps == pytest.approx([0.4])


@pytest.mark.asyncio
async def test_rate_limiter_preserves_schedule_when_clock_does_not_advance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stalled monotonic clock should not permit requests to bypass spacing."""
    limiter = AsyncRateLimiter(requests_per_second=10)

    current_time = 100.0
    sleeps: list[float] = []

    monkeypatch.setattr(
        "src.rate_limiter.time.monotonic",
        lambda: current_time,
    )

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    await limiter.acquire()
    await limiter.acquire()

    assert sleeps == pytest.approx([0.1])

"""Tests for asynchronous API rate limiting."""

from __future__ import annotations

import asyncio

import pytest

from src.rate_limiter import AsyncRateLimiter


def test_rate_limiter_rejects_non_positive_rate() -> None:
    """The configured request rate must be greater than zero."""
    with pytest.raises(ValueError, match="greater than zero"):
        AsyncRateLimiter(0)

    with pytest.raises(ValueError, match="greater than zero"):
        AsyncRateLimiter(-1)


@pytest.mark.asyncio
async def test_first_acquire_does_not_wait(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The first request should be permitted immediately."""
    limiter = AsyncRateLimiter(requests_per_second=10)

    current_time = 100.0
    sleeps: list[float] = []

    monkeypatch.setattr(
        "src.rate_limiter.time.monotonic",
        lambda: current_time,
    )

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    await limiter.acquire()

    assert sleeps == []


@pytest.mark.asyncio
async def test_acquire_enforces_request_interval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Subsequent requests should wait for the configured interval."""
    limiter = AsyncRateLimiter(requests_per_second=2)

    current_time = 100.0
    sleeps: list[float] = []

    monkeypatch.setattr(
        "src.rate_limiter.time.monotonic",
        lambda: current_time,
    )

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    await limiter.acquire()
    current_time = 100.1
    await limiter.acquire()

    assert sleeps == pytest.approx([0.4])


@pytest.mark.asyncio
async def test_acquire_allows_request_after_interval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A request arriving after the interval should not be delayed."""
    limiter = AsyncRateLimiter(requests_per_second=2)

    current_time = 100.0
    sleeps: list[float] = []

    monkeypatch.setattr(
        "src.rate_limiter.time.monotonic",
        lambda: current_time,
    )

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    await limiter.acquire()
    current_time = 100.5
    await limiter.acquire()

    assert sleeps == []


@pytest.mark.asyncio
async def test_acquire_serializes_concurrent_callers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Concurrent callers should share one rate-limiting schedule."""
    limiter = AsyncRateLimiter(requests_per_second=10)

    current_time = 100.0
    sleeps: list[float] = []

    monkeypatch.setattr(
        "src.rate_limiter.time.monotonic",
        lambda: current_time,
    )

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    await asyncio.gather(
        limiter.acquire(),
        limiter.acquire(),
        limiter.acquire(),
    )

    assert len(sleeps) == 2
    assert sleeps == pytest.approx([0.1, 0.1])


@pytest.mark.asyncio
async def test_rate_limiter_uses_monotonic_clock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rate limiting should use a monotonic clock rather than wall time."""
    limiter = AsyncRateLimiter(requests_per_second=5)

    monotonic_calls = 0
    current_time = 50.0

    def fake_monotonic() -> float:
        nonlocal monotonic_calls
        monotonic_calls += 1
        return current_time

    monkeypatch.setattr(
        "src.rate_limiter.time.monotonic",
        fake_monotonic,
    )

    async def fake_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    await limiter.acquire()

    assert monotonic_calls >= 1


@pytest.mark.asyncio
async def test_context_manager_acquires_rate_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Using the limiter as a context manager should acquire permission."""
    limiter = AsyncRateLimiter(requests_per_second=2)

    current_time = 100.0
    sleeps: list[float] = []

    monkeypatch.setattr(
        "src.rate_limiter.time.monotonic",
        lambda: current_time,
    )

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    async with limiter:
        pass

    current_time = 100.1

    async with limiter:
        pass

    assert sleeps == pytest.approx([0.4])


@pytest.mark.asyncio
async def test_context_manager_does_not_release_extra_capacity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exiting the context must not reset the limiter's request schedule."""
    limiter = AsyncRateLimiter(requests_per_second=2)

    current_time = 100.0
    sleeps: list[float] = []

    monkeypatch.setattr(
        "src.rate_limiter.time.monotonic",
        lambda: current_time,
    )

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    async with limiter:
        pass

    current_time = 100.1

    async with limiter:
        pass

    assert sleeps == pytest.approx([0.4])


@pytest.mark.asyncio
async def test_rate_limiter_preserves_schedule_when_clock_does_not_advance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stalled monotonic clock should not permit requests to bypass spacing."""
    limiter = AsyncRateLimiter(requests_per_second=10)

    current_time = 100.0
    sleeps: list[float] = []

    monkeypatch.setattr(
        "src.rate_limiter.time.monotonic",
        lambda: current_time,
    )

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    await limiter.acquire()
    await limiter.acquire()

    assert sleeps == pytest.approx([0.1])