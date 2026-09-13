"""Concurrency primitives and execution strategies for data processing."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from multiprocessing import Pool
from typing import TypeVar

from src.processor import Processor, Record, process_record

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ConcurrencyResult:
    """Represent ordered processing results and failures."""

    results: list[Record]
    failures: list[Exception]

    @property
    def processed_count(self) -> int:
        """Return the number of successfully processed records."""
        return len(self.results)

    @property
    def failed_count(self) -> int:
        """Return the number of failed records."""
        return len(self.failures)


def run_threads(
    records: Iterable[Record],
    transform: Processor,
    *,
    max_workers: int,
) -> ConcurrencyResult:
    """Run record processing concurrently using worker threads."""
    if max_workers <= 0:
        raise ValueError("max_workers must be greater than zero.")

    results: list[Record] = []
    failures: list[Exception] = []

    with ThreadPoolExecutor(
        max_workers=max_workers,
        thread_name_prefix="processor",
    ) as executor:
        futures: list[Future[Record]] = [
            executor.submit(process_record, record, transform)
            for record in records
        ]

        for future in futures:
            try:
                results.append(future.result())
            except Exception as exc:
                failures.append(exc)

    return ConcurrencyResult(results=results, failures=failures)


def run_processes(
    records: Iterable[Record],
    transform: Processor,
    *,
    max_workers: int,
) -> ConcurrencyResult:
    """Run CPU-bound record processing using worker processes."""
    if max_workers <= 0:
        raise ValueError("max_workers must be greater than zero.")

    results: list[Record] = []
    failures: list[Exception] = []

    with Pool(processes=max_workers) as pool:
        async_results = [
            pool.apply_async(process_record, (record, transform))
            for record in records
        ]

        for result in async_results:
            try:
                results.append(result.get())
            except Exception as exc:
                failures.append(exc)

    return ConcurrencyResult(results=results, failures=failures)


async def run_async(
    records: Iterable[Record],
    transform: Callable[[Record], Awaitable[Record]],
    *,
    max_concurrency: int,
) -> ConcurrencyResult:
    """Run asynchronous record processing with bounded concurrency."""
    if max_concurrency <= 0:
        raise ValueError("max_concurrency must be greater than zero.")

    semaphore = asyncio.Semaphore(max_concurrency)

    async def process_one(record: Record) -> Record:
        async with semaphore:
            return await transform(record)

    tasks = [
        asyncio.create_task(process_one(record))
        for record in records
    ]

    completed = await asyncio.gather(*tasks, return_exceptions=True)

    results: list[Record] = []
    failures: list[Exception] = []

    for result in completed:
        if isinstance(result, Exception):
            failures.append(result)
        else:
            results.append(result)

    return ConcurrencyResult(results=results, failures=failures)

"""Concurrency primitives and execution strategies for data processing."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from multiprocessing import Pool
from typing import TypeVar

from src.processor import Processor, Record, process_record

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ConcurrencyResult:
    """Represent ordered processing results and failures."""

    results: list[Record]
    failures: list[Exception]

    @property
    def processed_count(self) -> int:
        """Return the number of successfully processed records."""
        return len(self.results)

    @property
    def failed_count(self) -> int:
        """Return the number of failed records."""
        return len(self.failures)


def run_threads(
    records: Iterable[Record],
    transform: Processor,
    *,
    max_workers: int,
) -> ConcurrencyResult:
    """Run record processing concurrently using worker threads."""
    if max_workers <= 0:
        raise ValueError("max_workers must be greater than zero.")

    results: list[Record] = []
    failures: list[Exception] = []

    with ThreadPoolExecutor(
        max_workers=max_workers,
        thread_name_prefix="processor",
    ) as executor:
        futures: list[Future[Record]] = [
            executor.submit(process_record, record, transform)
            for record in records
        ]

        for future in futures:
            try:
                results.append(future.result())
            except Exception as exc:
                failures.append(exc)

    return ConcurrencyResult(results=results, failures=failures)


def run_processes(
    records: Iterable[Record],
    transform: Processor,
    *,
    max_workers: int,
) -> ConcurrencyResult:
    """Run CPU-bound record processing using worker processes."""
    if max_workers <= 0:
        raise ValueError("max_workers must be greater than zero.")

    results: list[Record] = []
    failures: list[Exception] = []

    with Pool(processes=max_workers) as pool:
        async_results = [
            pool.apply_async(process_record, (record, transform))
            for record in records
        ]

        for result in async_results:
            try:
                results.append(result.get())
            except Exception as exc:
                failures.append(exc)

    return ConcurrencyResult(results=results, failures=failures)


async def run_async(
    records: Iterable[Record],
    transform: Callable[[Record], Awaitable[Record]],
    *,
    max_concurrency: int,
) -> ConcurrencyResult:
    """Run asynchronous record processing with bounded concurrency."""
    if max_concurrency <= 0:
        raise ValueError("max_concurrency must be greater than zero.")

    semaphore = asyncio.Semaphore(max_concurrency)

    async def process_one(record: Record) -> Record:
        async with semaphore:
            return await transform(record)

    tasks = [
        asyncio.create_task(process_one(record))
        for record in records
    ]

    completed = await asyncio.gather(*tasks, return_exceptions=True)

    results: list[Record] = []
    failures: list[Exception] = []

    for result in completed:
        if isinstance(result, Exception):
            failures.append(result)
        else:
            results.append(result)

    return ConcurrencyResult(results=results, failures=failures)