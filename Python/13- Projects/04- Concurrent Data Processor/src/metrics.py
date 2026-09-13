"""Metrics collection for the concurrent data processor."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Final


NANOSECONDS_PER_SECOND: Final[int] = 1_000_000_000


@dataclass(frozen=True, slots=True)
class MetricsSnapshot:
    """Represent an immutable point-in-time view of processor metrics."""

    records_processed: int
    records_succeeded: int
    records_failed: int
    batches_processed: int
    processing_seconds: float

    @property
    def success_rate(self) -> float:
        """Return the percentage of processed records completed successfully."""
        if self.records_processed == 0:
            return 0.0

        return self.records_succeeded / self.records_processed


class ProcessingMetrics:
    """Provide thread-safe counters and timing metrics for processing work."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records_processed = 0
        self._records_succeeded = 0
        self._records_failed = 0
        self._batches_processed = 0
        self._processing_seconds = 0.0

    def record_success(self, *, count: int = 1) -> None:
        """Record successfully processed records."""
        self._validate_count(count)

        with self._lock:
            self._records_processed += count
            self._records_succeeded += count

    def record_failure(self, *, count: int = 1) -> None:
        """Record records that failed processing."""
        self._validate_count(count)

        with self._lock:
            self._records_processed += count
            self._records_failed += count

    def record_batch(self) -> None:
        """Record completion of one processing batch."""
        with self._lock:
            self._batches_processed += 1

    def record_processing_time(self, elapsed_seconds: float) -> None:
        """Add elapsed processing time to the aggregate metric."""
        if elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must not be negative.")

        with self._lock:
            self._processing_seconds += elapsed_seconds

    def snapshot(self) -> MetricsSnapshot:
        """Return a consistent snapshot of all current metrics."""
        with self._lock:
            return MetricsSnapshot(
                records_processed=self._records_processed,
                records_succeeded=self._records_succeeded,
                records_failed=self._records_failed,
                batches_processed=self._batches_processed,
                processing_seconds=self._processing_seconds,
            )

    def reset(self) -> None:
        """Reset all metrics to zero."""
        with self._lock:
            self._records_processed = 0
            self._records_succeeded = 0
            self._records_failed = 0
            self._batches_processed = 0
            self._processing_seconds = 0.0

    def timer(self) -> ProcessingTimer:
        """Create a context manager for measuring processing duration."""
        return ProcessingTimer(self)

    @staticmethod
    def _validate_count(count: int) -> None:
        """Validate a record count before updating counters."""
        if count <= 0:
            raise ValueError("count must be greater than zero.")


class ProcessingTimer:
    """Measure elapsed monotonic time and record it in processing metrics."""

    def __init__(self, metrics: ProcessingMetrics) -> None:
        self._metrics = metrics
        self._started_at: int | None = None

    def __enter__(self) -> ProcessingTimer:
        """Start the monotonic timer."""
        self._started_at = time.perf_counter_ns()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Record elapsed time when the context exits."""
        if self._started_at is None:
            raise RuntimeError("ProcessingTimer was not started.")

        elapsed_ns = time.perf_counter_ns() - self._started_at
        self._metrics.record_processing_time(
            elapsed_ns / NANOSECONDS_PER_SECOND
        )

"""Metrics collection for the concurrent data processor."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Final


NANOSECONDS_PER_SECOND: Final[int] = 1_000_000_000


@dataclass(frozen=True, slots=True)
class MetricsSnapshot:
    """Represent an immutable point-in-time view of processor metrics."""

    records_processed: int
    records_succeeded: int
    records_failed: int
    batches_processed: int
    processing_seconds: float

    @property
    def success_rate(self) -> float:
        """Return the percentage of processed records completed successfully."""
        if self.records_processed == 0:
            return 0.0

        return self.records_succeeded / self.records_processed


class ProcessingMetrics:
    """Provide thread-safe counters and timing metrics for processing work."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records_processed = 0
        self._records_succeeded = 0
        self._records_failed = 0
        self._batches_processed = 0
        self._processing_seconds = 0.0

    def record_success(self, *, count: int = 1) -> None:
        """Record successfully processed records."""
        self._validate_count(count)

        with self._lock:
            self._records_processed += count
            self._records_succeeded += count

    def record_failure(self, *, count: int = 1) -> None:
        """Record records that failed processing."""
        self._validate_count(count)

        with self._lock:
            self._records_processed += count
            self._records_failed += count

    def record_batch(self) -> None:
        """Record completion of one processing batch."""
        with self._lock:
            self._batches_processed += 1

    def record_processing_time(self, elapsed_seconds: float) -> None:
        """Add elapsed processing time to the aggregate metric."""
        if elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must not be negative.")

        with self._lock:
            self._processing_seconds += elapsed_seconds

    def snapshot(self) -> MetricsSnapshot:
        """Return a consistent snapshot of all current metrics."""
        with self._lock:
            return MetricsSnapshot(
                records_processed=self._records_processed,
                records_succeeded=self._records_succeeded,
                records_failed=self._records_failed,
                batches_processed=self._batches_processed,
                processing_seconds=self._processing_seconds,
            )

    def reset(self) -> None:
        """Reset all metrics to zero."""
        with self._lock:
            self._records_processed = 0
            self._records_succeeded = 0
            self._records_failed = 0
            self._batches_processed = 0
            self._processing_seconds = 0.0

    def timer(self) -> ProcessingTimer:
        """Create a context manager for measuring processing duration."""
        return ProcessingTimer(self)

    @staticmethod
    def _validate_count(count: int) -> None:
        """Validate a record count before updating counters."""
        if count <= 0:
            raise ValueError("count must be greater than zero.")


class ProcessingTimer:
    """Measure elapsed monotonic time and record it in processing metrics."""

    def __init__(self, metrics: ProcessingMetrics) -> None:
        self._metrics = metrics
        self._started_at: int | None = None

    def __enter__(self) -> ProcessingTimer:
        """Start the monotonic timer."""
        self._started_at = time.perf_counter_ns()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Record elapsed time when the context exits."""
        if self._started_at is None:
            raise RuntimeError("ProcessingTimer was not started.")

        elapsed_ns = time.perf_counter_ns() - self._started_at
        self._metrics.record_processing_time(
            elapsed_ns / NANOSECONDS_PER_SECOND
        )