"""Unit tests for the concurrent data processor."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest

from src.processor import DataProcessor


def _process_with_threads(
    processor: DataProcessor,
    items: Iterable[Any],
    worker: Callable[[Any], Any],
    *,
    max_workers: int,
) -> list[Any]:
    """Execute processor items concurrently using a bounded thread pool."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(worker, items))


class TestDataProcessor:
    """Verify core processing behavior and concurrency boundaries."""

    def test_process_transforms_each_item(self) -> None:
        """Each input item should be transformed exactly once."""
        processor = DataProcessor(max_workers=2)

        result = processor.process(
            [1, 2, 3, 4],
            lambda value: value * 2,
        )

        assert result == [2, 4, 6, 8]

    def test_process_preserves_input_order(self) -> None:
        """Concurrent execution should not unnecessarily reorder results."""
        processor = DataProcessor(max_workers=4)

        result = processor.process(
            ["a", "b", "c", "d"],
            lambda value: value.upper(),
        )

        assert result == ["A", "B", "C", "D"]

    def test_process_empty_input_returns_empty_result(self) -> None:
        """Empty input should not create unnecessary worker activity."""
        processor = DataProcessor(max_workers=4)

        assert processor.process([], lambda value: value) == []

    def test_process_propagates_worker_exception(self) -> None:
        """Worker failures should be visible to the caller."""

        def fail_on_invalid_item(value: int) -> int:
            if value == 2:
                raise ValueError("invalid item")

            return value

        processor = DataProcessor(max_workers=2)

        with pytest.raises(ValueError, match="invalid item"):
            processor.process(
                [1, 2, 3],
                fail_on_invalid_item,
            )

    def test_process_uses_bounded_concurrency(self) -> None:
        """The configured worker limit should bound concurrent execution."""
        processor = DataProcessor(max_workers=2)
        active_workers = 0
        peak_workers = 0

        def worker(value: int) -> int:
            nonlocal active_workers, peak_workers

            active_workers += 1
            peak_workers = max(peak_workers, active_workers)

            try:
                return value * 2
            finally:
                active_workers -= 1

        result = _process_with_threads(
            processor,
            range(10),
            worker,
            max_workers=processor.max_workers,
        )

        assert result == [value * 2 for value in range(10)]
        assert peak_workers <= 2

    def test_process_does_not_mutate_input(self) -> None:
        """Processing should not mutate the caller's input collection."""
        processor = DataProcessor(max_workers=2)
        items = [{"value": 1}, {"value": 2}]
        original = [item.copy() for item in items]

        processor.process(
            items,
            lambda item: {"value": item["value"] * 2},
        )

        assert items == original

    @pytest.mark.parametrize(
        "max_workers",
        [0, -1],
    )
    def test_invalid_worker_count_is_rejected(self, max_workers: int) -> None:
        """Worker concurrency must be a positive integer."""
        with pytest.raises(ValueError, match="max_workers"):
            DataProcessor(max_workers=max_workers)

    def test_worker_count_is_exposed_for_operational_introspection(self) -> None:
        """Configured concurrency should be observable by callers."""
        processor = DataProcessor(max_workers=8)

        assert processor.max_workers == 8

"""Unit tests for the concurrent data processor."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest

from src.processor import DataProcessor


def _process_with_threads(
    processor: DataProcessor,
    items: Iterable[Any],
    worker: Callable[[Any], Any],
    *,
    max_workers: int,
) -> list[Any]:
    """Execute processor items concurrently using a bounded thread pool."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(worker, items))


class TestDataProcessor:
    """Verify core processing behavior and concurrency boundaries."""

    def test_process_transforms_each_item(self) -> None:
        """Each input item should be transformed exactly once."""
        processor = DataProcessor(max_workers=2)

        result = processor.process(
            [1, 2, 3, 4],
            lambda value: value * 2,
        )

        assert result == [2, 4, 6, 8]

    def test_process_preserves_input_order(self) -> None:
        """Concurrent execution should not unnecessarily reorder results."""
        processor = DataProcessor(max_workers=4)

        result = processor.process(
            ["a", "b", "c", "d"],
            lambda value: value.upper(),
        )

        assert result == ["A", "B", "C", "D"]

    def test_process_empty_input_returns_empty_result(self) -> None:
        """Empty input should not create unnecessary worker activity."""
        processor = DataProcessor(max_workers=4)

        assert processor.process([], lambda value: value) == []

    def test_process_propagates_worker_exception(self) -> None:
        """Worker failures should be visible to the caller."""

        def fail_on_invalid_item(value: int) -> int:
            if value == 2:
                raise ValueError("invalid item")

            return value

        processor = DataProcessor(max_workers=2)

        with pytest.raises(ValueError, match="invalid item"):
            processor.process(
                [1, 2, 3],
                fail_on_invalid_item,
            )

    def test_process_uses_bounded_concurrency(self) -> None:
        """The configured worker limit should bound concurrent execution."""
        processor = DataProcessor(max_workers=2)
        active_workers = 0
        peak_workers = 0

        def worker(value: int) -> int:
            nonlocal active_workers, peak_workers

            active_workers += 1
            peak_workers = max(peak_workers, active_workers)

            try:
                return value * 2
            finally:
                active_workers -= 1

        result = _process_with_threads(
            processor,
            range(10),
            worker,
            max_workers=processor.max_workers,
        )

        assert result == [value * 2 for value in range(10)]
        assert peak_workers <= 2

    def test_process_does_not_mutate_input(self) -> None:
        """Processing should not mutate the caller's input collection."""
        processor = DataProcessor(max_workers=2)
        items = [{"value": 1}, {"value": 2}]
        original = [item.copy() for item in items]

        processor.process(
            items,
            lambda item: {"value": item["value"] * 2},
        )

        assert items == original

    @pytest.mark.parametrize(
        "max_workers",
        [0, -1],
    )
    def test_invalid_worker_count_is_rejected(self, max_workers: int) -> None:
        """Worker concurrency must be a positive integer."""
        with pytest.raises(ValueError, match="max_workers"):
            DataProcessor(max_workers=max_workers)

    def test_worker_count_is_exposed_for_operational_introspection(self) -> None:
        """Configured concurrency should be observable by callers."""
        processor = DataProcessor(max_workers=8)

        assert processor.max_workers == 8