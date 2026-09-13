"""Unit tests for concurrent worker execution."""

from __future__ import annotations

import threading
import time

import pytest

from src.worker import Worker


class TestWorker:
    """Verify worker lifecycle, concurrency limits, and failure handling."""

    def test_worker_processes_items(self) -> None:
        """Worker should process every submitted item."""
        worker = Worker(max_workers=2)

        results = worker.run(
            [1, 2, 3, 4],
            lambda value: value * 2,
        )

        assert results == [2, 4, 6, 8]

    def test_worker_preserves_result_order(self) -> None:
        """Completion order should not change the input/result relationship."""
        worker = Worker(max_workers=4)

        def process(value: int) -> int:
            if value == 1:
                time.sleep(0.02)
            return value

        assert worker.run([1, 2, 3, 4], process) == [1, 2, 3, 4]

    def test_worker_enforces_max_workers(self) -> None:
        """No more than the configured number of tasks should run concurrently."""
        worker = Worker(max_workers=2)
        lock = threading.Lock()
        active = 0
        peak_active = 0

        def process(value: int) -> int:
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

        results = worker.run(range(8), process)

        assert results == list(range(8))
        assert peak_active <= 2

    def test_worker_propagates_task_exception(self) -> None:
        """A failed task should be surfaced to the caller."""

        def process(value: int) -> int:
            if value == 3:
                raise ValueError("invalid input")

            return value

        worker = Worker(max_workers=2)

        with pytest.raises(ValueError, match="invalid input"):
            worker.run([1, 2, 3, 4], process)

    def test_worker_handles_empty_input(self) -> None:
        """An empty workload should return immediately."""
        worker = Worker(max_workers=4)

        assert worker.run([], lambda value: value) == []

    @pytest.mark.parametrize("max_workers", [0, -1])
    def test_worker_rejects_invalid_concurrency(self, max_workers: int) -> None:
        """Worker concurrency must be positive."""
        with pytest.raises(ValueError, match="max_workers"):
            Worker(max_workers=max_workers)

    def test_worker_does_not_mutate_input(self) -> None:
        """Worker execution should not mutate the input collection itself."""
        items = [{"value": 1}, {"value": 2}]
        original = [item.copy() for item in items]
        worker = Worker(max_workers=2)

        worker.run(
            items,
            lambda item: {"value": item["value"] * 2},
        )

        assert items == original

"""Unit tests for concurrent worker execution."""

from __future__ import annotations

import threading
import time

import pytest

from src.worker import Worker


class TestWorker:
    """Verify worker lifecycle, concurrency limits, and failure handling."""

    def test_worker_processes_items(self) -> None:
        """Worker should process every submitted item."""
        worker = Worker(max_workers=2)

        results = worker.run(
            [1, 2, 3, 4],
            lambda value: value * 2,
        )

        assert results == [2, 4, 6, 8]

    def test_worker_preserves_result_order(self) -> None:
        """Completion order should not change the input/result relationship."""
        worker = Worker(max_workers=4)

        def process(value: int) -> int:
            if value == 1:
                time.sleep(0.02)
            return value

        assert worker.run([1, 2, 3, 4], process) == [1, 2, 3, 4]

    def test_worker_enforces_max_workers(self) -> None:
        """No more than the configured number of tasks should run concurrently."""
        worker = Worker(max_workers=2)
        lock = threading.Lock()
        active = 0
        peak_active = 0

        def process(value: int) -> int:
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

        results = worker.run(range(8), process)

        assert results == list(range(8))
        assert peak_active <= 2

    def test_worker_propagates_task_exception(self) -> None:
        """A failed task should be surfaced to the caller."""

        def process(value: int) -> int:
            if value == 3:
                raise ValueError("invalid input")

            return value

        worker = Worker(max_workers=2)

        with pytest.raises(ValueError, match="invalid input"):
            worker.run([1, 2, 3, 4], process)

    def test_worker_handles_empty_input(self) -> None:
        """An empty workload should return immediately."""
        worker = Worker(max_workers=4)

        assert worker.run([], lambda value: value) == []

    @pytest.mark.parametrize("max_workers", [0, -1])
    def test_worker_rejects_invalid_concurrency(self, max_workers: int) -> None:
        """Worker concurrency must be positive."""
        with pytest.raises(ValueError, match="max_workers"):
            Worker(max_workers=max_workers)

    def test_worker_does_not_mutate_input(self) -> None:
        """Worker execution should not mutate the input collection itself."""
        items = [{"value": 1}, {"value": 2}]
        original = [item.copy() for item in items]
        worker = Worker(max_workers=2)

        worker.run(
            items,
            lambda item: {"value": item["value"] * 2},
        )

        assert items == original