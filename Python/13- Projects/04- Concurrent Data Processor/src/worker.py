"""Worker strategies for concurrent record processing."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from multiprocessing import Pool
from typing import Any, TypeAlias

from src.processor import Processor, ProcessingError, Record, process_record


Worker: TypeAlias = Callable[[Record], Record]


@dataclass(frozen=True, slots=True)
class WorkerResult:
    """Represent the outcome of processing records with a worker pool."""

    records: list[Record]
    failures: list[Exception]

    @property
    def processed_count(self) -> int:
        """Return the number of successfully processed records."""
        return len(self.records)

    @property
    def failed_count(self) -> int:
        """Return the number of failed records."""
        return len(self.failures)


def process_with_threads(
    records: Iterable[Record],
    transform: Processor,
    *,
    max_workers: int,
) -> WorkerResult:
    """Process I/O-bound records concurrently using a thread pool."""
    if max_workers <= 0:
        raise ValueError("max_workers must be greater than zero.")

    successful: list[Record] = []
    failures: list[Exception] = []

    with ThreadPoolExecutor(
        max_workers=max_workers,
        thread_name_prefix="data-worker",
    ) as executor:
        futures: list[Future[Record]] = [
            executor.submit(process_record, record, transform)
            for record in records
        ]

        for future in futures:
            try:
                successful.append(future.result())
            except (ProcessingError, Exception) as exc:
                failures.append(exc)

    return WorkerResult(
        records=successful,
        failures=failures,
    )


def process_with_processes(
    records: Iterable[Record],
    transform: Processor,
    *,
    max_workers: int,
) -> WorkerResult:
    """Process CPU-bound records using a process pool."""
    if max_workers <= 0:
        raise ValueError("max_workers must be greater than zero.")

    successful: list[Record] = []
    failures: list[Exception] = []

    with Pool(processes=max_workers) as pool:
        jobs = [
            pool.apply_async(process_record, (record, transform))
            for record in records
        ]

        for job in jobs:
            try:
                successful.append(job.get())
            except (ProcessingError, Exception) as exc:
                failures.append(exc)

    return WorkerResult(
        records=successful,
        failures=failures,
    )


def process_in_worker(
    record: Record,
    transform: Worker,
) -> Record:
    """Process one record through a worker-compatible callable."""
    return process_record(record, transform)

"""Worker strategies for concurrent record processing."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from multiprocessing import Pool
from typing import Any, TypeAlias

from src.processor import Processor, ProcessingError, Record, process_record


Worker: TypeAlias = Callable[[Record], Record]


@dataclass(frozen=True, slots=True)
class WorkerResult:
    """Represent the outcome of processing records with a worker pool."""

    records: list[Record]
    failures: list[Exception]

    @property
    def processed_count(self) -> int:
        """Return the number of successfully processed records."""
        return len(self.records)

    @property
    def failed_count(self) -> int:
        """Return the number of failed records."""
        return len(self.failures)


def process_with_threads(
    records: Iterable[Record],
    transform: Processor,
    *,
    max_workers: int,
) -> WorkerResult:
    """Process I/O-bound records concurrently using a thread pool."""
    if max_workers <= 0:
        raise ValueError("max_workers must be greater than zero.")

    successful: list[Record] = []
    failures: list[Exception] = []

    with ThreadPoolExecutor(
        max_workers=max_workers,
        thread_name_prefix="data-worker",
    ) as executor:
        futures: list[Future[Record]] = [
            executor.submit(process_record, record, transform)
            for record in records
        ]

        for future in futures:
            try:
                successful.append(future.result())
            except (ProcessingError, Exception) as exc:
                failures.append(exc)

    return WorkerResult(
        records=successful,
        failures=failures,
    )


def process_with_processes(
    records: Iterable[Record],
    transform: Processor,
    *,
    max_workers: int,
) -> WorkerResult:
    """Process CPU-bound records using a process pool."""
    if max_workers <= 0:
        raise ValueError("max_workers must be greater than zero.")

    successful: list[Record] = []
    failures: list[Exception] = []

    with Pool(processes=max_workers) as pool:
        jobs = [
            pool.apply_async(process_record, (record, transform))
            for record in records
        ]

        for job in jobs:
            try:
                successful.append(job.get())
            except (ProcessingError, Exception) as exc:
                failures.append(exc)

    return WorkerResult(
        records=successful,
        failures=failures,
    )


def process_in_worker(
    record: Record,
    transform: Worker,
) -> Record:
    """Process one record through a worker-compatible callable."""
    return process_record(record, transform)