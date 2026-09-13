"""Tests for concurrency strategies used by the concurrent data processor."""

from __future__ import annotations

import asyncio
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial

import pytest

from src.concurrency import (
    run_async,
    run_processes,
    run_threads,
)


def _square(value: int) -> int:
    """Return the square of an integer."""
    return value * value


def _slow_square(value: int, delay: float = 0.01) -> int:
    """Return the square after a small delay."""
    time.sleep(delay)
    return value * value


def _async_square(value: int) -> int:
    """Return a deterministic result for async execution tests."""
    return value * value


class TestThreadConcurrency:
    """Verify thread-based execution for I/O-oriented workloads."""

    def test_run_threads_processes_all_items(self) -> None:
        """Thread execution should return one result for every input."""
        results = run_threads(
            range(5),
            _square,
            max_workers=2,
        )

        assert results == [0, 1, 4, 9, 16]

    def test_run_threads_preserves_input_order(self) -> None:
        """Result ordering should remain aligned with input ordering."""
        worker = partial(_slow_square, delay=0.02)

        results = run_threads(
            [3, 1, 4, 2],
            worker,
            max_workers=4,
        )

        assert results == [9, 1, 16, 4]

    def test_run_threads_supports_bounded_concurrency(self) -> None:
        """Thread execution should not exceed the configured worker limit."""
        lock = threading.Lock()
        active = 0
        peak_active = 0

        def worker(value: int) -> int:
            nonlocal active, peak_active

            with lock:
                active += 1
                peak_active = max(peak_active, active)

            try:
                time.sleep(0.01)
                return value
            finally:
                with lock:
                    active -= 1

        results = run_threads(
            range(8),
            worker,
            max_workers=2,
        )

        assert results == list(range(8))
        assert peak_active <= 2

    def test_run_threads_propagates_worker_exception(self) -> None:
        """Exceptions raised by worker functions should reach the caller."""

        def worker(value: int) -> int:
            if value == 2:
                raise ValueError("invalid item")

            return value

        with pytest.raises(ValueError, match="invalid item"):
            run_threads(
                [1, 2, 3],
                worker,
                max_workers=2,
            )

    @pytest.mark.parametrize("max_workers", [0, -1])
    def test_run_threads_rejects_invalid_worker_count(
        self,
        max_workers: int,
    ) -> None:
        """Thread concurrency must use a positive worker count."""
        with pytest.raises(ValueError, match="max_workers"):
            run_threads(
                [1, 2],
                _square,
                max_workers=max_workers,
            )


class TestProcessConcurrency:
    """Verify process-based execution for CPU-oriented workloads."""

    def test_run_processes_processes_all_items(self) -> None:
        """Process execution should return one result for every input."""
        results = run_processes(
            range(5),
            _square,
            max_workers=2,
        )

        assert results == [0, 1, 4, 9, 16]

    def test_run_processes_preserves_input_order(self) -> None:
        """Process results should remain associated with their inputs."""
        results = run_processes(
            [3, 1, 4, 2],
            _square,
            max_workers=2,
        )

        assert results == [9, 1, 16, 4]

    def test_run_processes_handles_empty_input(self) -> None:
        """Empty workloads should produce no process work."""
        assert run_processes(
            [],
            _square,
            max_workers=2,
        ) == []

    def test_run_processes_propagates_worker_exception(self) -> None:
        """Worker exceptions should not be silently discarded."""

        def worker(value: int) -> int:
            if value == 2:
                raise ValueError("invalid item")

            return value

        with pytest.raises(ValueError, match="invalid item"):
            run_processes(
                [1, 2, 3],
                worker,
                max_workers=2,
            )

    @pytest.mark.parametrize("max_workers", [0, -1])
    def test_run_processes_rejects_invalid_worker_count(
        self,
        max_workers: int,
    ) -> None:
        """Process concurrency must use a positive worker count."""
        with pytest.raises(ValueError, match="max_workers"):
            run_processes(
                [1, 2],
                _square,
                max_workers=max_workers,
            )


class TestAsyncConcurrency:
    """Verify asyncio-based execution for non-blocking I/O workloads."""

    def test_run_async_processes_all_items(self) -> None:
        """Async execution should process every input item."""

        async def worker(value: int) -> int:
            await asyncio.sleep(0)
            return _async_square(value)

        results = asyncio.run(
            run_async(
                range(5),
                worker,
                max_concurrency=2,
            )
        )

        assert results == [0, 1, 4, 9, 16]

    def test_run_async_preserves_input_order(self) -> None:
        """Async completion order should not alter result ordering."""

        async def worker(value: int) -> int:
            await asyncio.sleep(0.01 * (4 - value))
            return value * 2

        results = asyncio.run(
            run_async(
                [0, 1, 2, 3, 4],
                worker,
                max_concurrency=5,
            )
        )

        assert results == [0, 2, 4, 6, 8]

    def test_run_async_enforces_concurrency_limit(self) -> None:
        """Async execution should respect its concurrency bound."""
        active = 0
        peak_active = 0

        async def worker(value: int) -> int:
            nonlocal active, peak_active

            active += 1
            peak_active = max(peak_active, active)

            try:
                await asyncio.sleep(0.01)
                return value
            finally:
                active -= 1

        results = asyncio.run(
            run_async(
                range(10),
                worker,
                max_concurrency=3,
            )
        )

        assert results == list(range(10))
        assert peak_active <= 3

    def test_run_async_propagates_worker_exception(self) -> None:
        """Async worker failures should be propagated to the caller."""

        async def worker(value: int) -> int:
            if value == 2:
                raise ValueError("invalid item")

            await asyncio.sleep(0)
            return value

        with pytest.raises(ValueError, match="invalid item"):
            asyncio.run(
                run_async(
                    [1, 2, 3],
                    worker,
                    max_concurrency=2,
                )
            )

    def test_run_async_handles_empty_input(self) -> None:
        """An empty async workload should return without creating tasks."""

        async def worker(value: int) -> int:
            return value

        assert asyncio.run(
            run_async(
                [],
                worker,
                max_concurrency=2,
            )
        ) == []

    @pytest.mark.parametrize("max_concurrency", [0, -1])
    def test_run_async_rejects_invalid_concurrency(
        self,
        max_concurrency: int,
    ) -> None:
        """Async concurrency must use a positive limit."""

        async def worker(value: int) -> int:
            return value

        with pytest.raises(ValueError, match="max_concurrency"):
            asyncio.run(
                run_async(
                    [1, 2],
                    worker,
                    max_concurrency=max_concurrency,
                )
            )


def test_thread_pool_executor_supports_picklable_style_worker() -> None:
    """Thread execution should remain compatible with ordinary callables."""
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(_square, [1, 2, 3]))

    assert results == [1, 4, 9]


def test_process_pool_executor_can_execute_module_level_worker() -> None:
    """Module-level workers should be suitable for process execution."""
    with ProcessPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(_square, [1, 2, 3]))

    assert results == [1, 4, 9]

"""Tests for concurrency strategies used by the concurrent data processor."""

from __future__ import annotations

import asyncio
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial

import pytest

from src.concurrency import (
    run_async,
    run_processes,
    run_threads,
)


def _square(value: int) -> int:
    """Return the square of an integer."""
    return value * value


def _slow_square(value: int, delay: float = 0.01) -> int:
    """Return the square after a small delay."""
    time.sleep(delay)
    return value * value


def _async_square(value: int) -> int:
    """Return a deterministic result for async execution tests."""
    return value * value


class TestThreadConcurrency:
    """Verify thread-based execution for I/O-oriented workloads."""

    def test_run_threads_processes_all_items(self) -> None:
        """Thread execution should return one result for every input."""
        results = run_threads(
            range(5),
            _square,
            max_workers=2,
        )

        assert results == [0, 1, 4, 9, 16]

    def test_run_threads_preserves_input_order(self) -> None:
        """Result ordering should remain aligned with input ordering."""
        worker = partial(_slow_square, delay=0.02)

        results = run_threads(
            [3, 1, 4, 2],
            worker,
            max_workers=4,
        )

        assert results == [9, 1, 16, 4]

    def test_run_threads_supports_bounded_concurrency(self) -> None:
        """Thread execution should not exceed the configured worker limit."""
        lock = threading.Lock()
        active = 0
        peak_active = 0

        def worker(value: int) -> int:
            nonlocal active, peak_active

            with lock:
                active += 1
                peak_active = max(peak_active, active)

            try:
                time.sleep(0.01)
                return value
            finally:
                with lock:
                    active -= 1

        results = run_threads(
            range(8),
            worker,
            max_workers=2,
        )

        assert results == list(range(8))
        assert peak_active <= 2

    def test_run_threads_propagates_worker_exception(self) -> None:
        """Exceptions raised by worker functions should reach the caller."""

        def worker(value: int) -> int:
            if value == 2:
                raise ValueError("invalid item")

            return value

        with pytest.raises(ValueError, match="invalid item"):
            run_threads(
                [1, 2, 3],
                worker,
                max_workers=2,
            )

    @pytest.mark.parametrize("max_workers", [0, -1])
    def test_run_threads_rejects_invalid_worker_count(
        self,
        max_workers: int,
    ) -> None:
        """Thread concurrency must use a positive worker count."""
        with pytest.raises(ValueError, match="max_workers"):
            run_threads(
                [1, 2],
                _square,
                max_workers=max_workers,
            )


class TestProcessConcurrency:
    """Verify process-based execution for CPU-oriented workloads."""

    def test_run_processes_processes_all_items(self) -> None:
        """Process execution should return one result for every input."""
        results = run_processes(
            range(5),
            _square,
            max_workers=2,
        )

        assert results == [0, 1, 4, 9, 16]

    def test_run_processes_preserves_input_order(self) -> None:
        """Process results should remain associated with their inputs."""
        results = run_processes(
            [3, 1, 4, 2],
            _square,
            max_workers=2,
        )

        assert results == [9, 1, 16, 4]

    def test_run_processes_handles_empty_input(self) -> None:
        """Empty workloads should produce no process work."""
        assert run_processes(
            [],
            _square,
            max_workers=2,
        ) == []

    def test_run_processes_propagates_worker_exception(self) -> None:
        """Worker exceptions should not be silently discarded."""

        def worker(value: int) -> int:
            if value == 2:
                raise ValueError("invalid item")

            return value

        with pytest.raises(ValueError, match="invalid item"):
            run_processes(
                [1, 2, 3],
                worker,
                max_workers=2,
            )

    @pytest.mark.parametrize("max_workers", [0, -1])
    def test_run_processes_rejects_invalid_worker_count(
        self,
        max_workers: int,
    ) -> None:
        """Process concurrency must use a positive worker count."""
        with pytest.raises(ValueError, match="max_workers"):
            run_processes(
                [1, 2],
                _square,
                max_workers=max_workers,
            )


class TestAsyncConcurrency:
    """Verify asyncio-based execution for non-blocking I/O workloads."""

    def test_run_async_processes_all_items(self) -> None:
        """Async execution should process every input item."""

        async def worker(value: int) -> int:
            await asyncio.sleep(0)
            return _async_square(value)

        results = asyncio.run(
            run_async(
                range(5),
                worker,
                max_concurrency=2,
            )
        )

        assert results == [0, 1, 4, 9, 16]

    def test_run_async_preserves_input_order(self) -> None:
        """Async completion order should not alter result ordering."""

        async def worker(value: int) -> int:
            await asyncio.sleep(0.01 * (4 - value))
            return value * 2

        results = asyncio.run(
            run_async(
                [0, 1, 2, 3, 4],
                worker,
                max_concurrency=5,
            )
        )

        assert results == [0, 2, 4, 6, 8]

    def test_run_async_enforces_concurrency_limit(self) -> None:
        """Async execution should respect its concurrency bound."""
        active = 0
        peak_active = 0

        async def worker(value: int) -> int:
            nonlocal active, peak_active

            active += 1
            peak_active = max(peak_active, active)

            try:
                await asyncio.sleep(0.01)
                return value
            finally:
                active -= 1

        results = asyncio.run(
            run_async(
                range(10),
                worker,
                max_concurrency=3,
            )
        )

        assert results == list(range(10))
        assert peak_active <= 3

    def test_run_async_propagates_worker_exception(self) -> None:
        """Async worker failures should be propagated to the caller."""

        async def worker(value: int) -> int:
            if value == 2:
                raise ValueError("invalid item")

            await asyncio.sleep(0)
            return value

        with pytest.raises(ValueError, match="invalid item"):
            asyncio.run(
                run_async(
                    [1, 2, 3],
                    worker,
                    max_concurrency=2,
                )
            )

    def test_run_async_handles_empty_input(self) -> None:
        """An empty async workload should return without creating tasks."""

        async def worker(value: int) -> int:
            return value

        assert asyncio.run(
            run_async(
                [],
                worker,
                max_concurrency=2,
            )
        ) == []

    @pytest.mark.parametrize("max_concurrency", [0, -1])
    def test_run_async_rejects_invalid_concurrency(
        self,
        max_concurrency: int,
    ) -> None:
        """Async concurrency must use a positive limit."""

        async def worker(value: int) -> int:
            return value

        with pytest.raises(ValueError, match="max_concurrency"):
            asyncio.run(
                run_async(
                    [1, 2],
                    worker,
                    max_concurrency=max_concurrency,
                )
            )


def test_thread_pool_executor_supports_picklable_style_worker() -> None:
    """Thread execution should remain compatible with ordinary callables."""
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(_square, [1, 2, 3]))

    assert results == [1, 4, 9]


def test_process_pool_executor_can_execute_module_level_worker() -> None:
    """Module-level workers should be suitable for process execution."""
    with ProcessPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(_square, [1, 2, 3]))

    assert results == [1, 4, 9]