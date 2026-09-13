"""Metrics and observability primitives for the background job system."""

from __future__ import annotations

import threading
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class JobMetricsSnapshot:
    """Represent an immutable point-in-time view of worker metrics."""

    jobs_submitted: int
    jobs_started: int
    jobs_succeeded: int
    jobs_failed: int
    jobs_dead_lettered: int
    jobs_retried: int
    active_jobs: int
    total_execution_time_seconds: float
    average_execution_time_seconds: float


class JobMetrics:
    """Collect thread-safe in-process metrics for background job execution.

    The collector is intentionally independent of a metrics backend. It can
    feed Prometheus, CloudWatch, OpenTelemetry, or another observability
    system without coupling job execution code to a particular vendor.
    """

    _COUNTER_FIELDS: Final[tuple[str, ...]] = (
        "jobs_submitted",
        "jobs_started",
        "jobs_succeeded",
        "jobs_failed",
        "jobs_dead_lettered",
        "jobs_retried",
    )

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: Counter[str] = Counter()
        self._active_jobs = 0
        self._total_execution_time = 0.0
        self._started_at: dict[str, float] = {}
        self._job_durations: defaultdict[str, list[float]] = defaultdict(list)

    def record_submitted(self) -> None:
        """Record a job entering the queueing pipeline."""
        with self._lock:
            self._counters["jobs_submitted"] += 1

    def record_started(self, job_id: str) -> None:
        """Record the start of a job execution."""
        if not job_id:
            raise ValueError("job_id must not be empty.")

        with self._lock:
            self._counters["jobs_started"] += 1
            self._active_jobs += 1
            self._started_at[job_id] = time.monotonic()

    def record_succeeded(self, job_id: str) -> None:
        """Record successful completion and its execution duration."""
        self._record_completion(
            job_id,
            counter="jobs_succeeded",
        )

    def record_failed(self, job_id: str) -> None:
        """Record failed completion and its execution duration."""
        self._record_completion(
            job_id,
            counter="jobs_failed",
        )

    def record_dead_lettered(self, job_id: str) -> None:
        """Record a job permanently moved to a dead-letter state."""
        with self._lock:
            self._counters["jobs_dead_lettered"] += 1

        self._record_duration(job_id)

    def record_retried(self) -> None:
        """Record a job execution that will be retried."""
        with self._lock:
            self._counters["jobs_retried"] += 1

    def snapshot(self) -> JobMetricsSnapshot:
        """Return a consistent point-in-time metrics snapshot."""
        with self._lock:
            jobs_started = self._counters["jobs_started"]
            total_execution_time = self._total_execution_time

            average_execution_time = (
                total_execution_time / jobs_started
                if jobs_started
                else 0.0
            )

            return JobMetricsSnapshot(
                jobs_submitted=self._counters["jobs_submitted"],
                jobs_started=jobs_started,
                jobs_succeeded=self._counters["jobs_succeeded"],
                jobs_failed=self._counters["jobs_failed"],
                jobs_dead_lettered=self._counters["jobs_dead_lettered"],
                jobs_retried=self._counters["jobs_retried"],
                active_jobs=self._active_jobs,
                total_execution_time_seconds=total_execution_time,
                average_execution_time_seconds=average_execution_time,
            )

    def reset(self) -> None:
        """Reset collected metrics.

        Useful for isolated tests. Production systems should generally export
        cumulative metrics rather than periodically resetting process state.
        """
        with self._lock:
            self._counters.clear()
            self._active_jobs = 0
            self._total_execution_time = 0.0
            self._started_at.clear()
            self._job_durations.clear()

    def _record_completion(self, job_id: str, *, counter: str) -> None:
        """Record a terminal execution outcome and its duration."""
        with self._lock:
            self._counters[counter] += 1

            started_at = self._started_at.pop(job_id, None)

            if started_at is None:
                return

            self._active_jobs = max(0, self._active_jobs - 1)

            duration = max(0.0, time.monotonic() - started_at)
            self._total_execution_time += duration
            self._job_durations[job_id].append(duration)

    def _record_duration(self, job_id: str) -> None:
        """Record duration for a terminal job without changing success/failure."""
        with self._lock:
            started_at = self._started_at.pop(job_id, None)

            if started_at is None:
                return

            self._active_jobs = max(0, self._active_jobs - 1)

            duration = max(0.0, time.monotonic() - started_at)
            self._total_execution_time += duration
            self._job_durations[job_id].append(duration)

"""Metrics and observability primitives for the background job system."""

from __future__ import annotations

import threading
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class JobMetricsSnapshot:
    """Represent an immutable point-in-time view of worker metrics."""

    jobs_submitted: int
    jobs_started: int
    jobs_succeeded: int
    jobs_failed: int
    jobs_dead_lettered: int
    jobs_retried: int
    active_jobs: int
    total_execution_time_seconds: float
    average_execution_time_seconds: float


class JobMetrics:
    """Collect thread-safe in-process metrics for background job execution.

    The collector is intentionally independent of a metrics backend. It can
    feed Prometheus, CloudWatch, OpenTelemetry, or another observability
    system without coupling job execution code to a particular vendor.
    """

    _COUNTER_FIELDS: Final[tuple[str, ...]] = (
        "jobs_submitted",
        "jobs_started",
        "jobs_succeeded",
        "jobs_failed",
        "jobs_dead_lettered",
        "jobs_retried",
    )

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: Counter[str] = Counter()
        self._active_jobs = 0
        self._total_execution_time = 0.0
        self._started_at: dict[str, float] = {}
        self._job_durations: defaultdict[str, list[float]] = defaultdict(list)

    def record_submitted(self) -> None:
        """Record a job entering the queueing pipeline."""
        with self._lock:
            self._counters["jobs_submitted"] += 1

    def record_started(self, job_id: str) -> None:
        """Record the start of a job execution."""
        if not job_id:
            raise ValueError("job_id must not be empty.")

        with self._lock:
            self._counters["jobs_started"] += 1
            self._active_jobs += 1
            self._started_at[job_id] = time.monotonic()

    def record_succeeded(self, job_id: str) -> None:
        """Record successful completion and its execution duration."""
        self._record_completion(
            job_id,
            counter="jobs_succeeded",
        )

    def record_failed(self, job_id: str) -> None:
        """Record failed completion and its execution duration."""
        self._record_completion(
            job_id,
            counter="jobs_failed",
        )

    def record_dead_lettered(self, job_id: str) -> None:
        """Record a job permanently moved to a dead-letter state."""
        with self._lock:
            self._counters["jobs_dead_lettered"] += 1

        self._record_duration(job_id)

    def record_retried(self) -> None:
        """Record a job execution that will be retried."""
        with self._lock:
            self._counters["jobs_retried"] += 1

    def snapshot(self) -> JobMetricsSnapshot:
        """Return a consistent point-in-time metrics snapshot."""
        with self._lock:
            jobs_started = self._counters["jobs_started"]
            total_execution_time = self._total_execution_time

            average_execution_time = (
                total_execution_time / jobs_started
                if jobs_started
                else 0.0
            )

            return JobMetricsSnapshot(
                jobs_submitted=self._counters["jobs_submitted"],
                jobs_started=jobs_started,
                jobs_succeeded=self._counters["jobs_succeeded"],
                jobs_failed=self._counters["jobs_failed"],
                jobs_dead_lettered=self._counters["jobs_dead_lettered"],
                jobs_retried=self._counters["jobs_retried"],
                active_jobs=self._active_jobs,
                total_execution_time_seconds=total_execution_time,
                average_execution_time_seconds=average_execution_time,
            )

    def reset(self) -> None:
        """Reset collected metrics.

        Useful for isolated tests. Production systems should generally export
        cumulative metrics rather than periodically resetting process state.
        """
        with self._lock:
            self._counters.clear()
            self._active_jobs = 0
            self._total_execution_time = 0.0
            self._started_at.clear()
            self._job_durations.clear()

    def _record_completion(self, job_id: str, *, counter: str) -> None:
        """Record a terminal execution outcome and its duration."""
        with self._lock:
            self._counters[counter] += 1

            started_at = self._started_at.pop(job_id, None)

            if started_at is None:
                return

            self._active_jobs = max(0, self._active_jobs - 1)

            duration = max(0.0, time.monotonic() - started_at)
            self._total_execution_time += duration
            self._job_durations[job_id].append(duration)

    def _record_duration(self, job_id: str) -> None:
        """Record duration for a terminal job without changing success/failure."""
        with self._lock:
            started_at = self._started_at.pop(job_id, None)

            if started_at is None:
                return

            self._active_jobs = max(0, self._active_jobs - 1)

            duration = max(0.0, time.monotonic() - started_at)
            self._total_execution_time += duration
            self._job_durations[job_id].append(duration)