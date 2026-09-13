"""Benchmark thread-based concurrency for the concurrent data processor."""

from __future__ import annotations

import argparse
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Represent timing measurements for one benchmark configuration."""

    workers: int
    iterations: int
    total_seconds: float

    @property
    def items_per_second(self) -> float:
        """Return the completed workload throughput."""
        return self.iterations / self.total_seconds


def io_bound_work(value: int, delay: float) -> int:
    """Simulate blocking I/O without performing external network calls."""
    time.sleep(delay)
    return value * 2


def benchmark_threads(
    *,
    items: int,
    workers: int,
    delay: float,
    repetitions: int,
) -> BenchmarkResult:
    """Measure throughput for a bounded thread pool."""
    if items <= 0:
        raise ValueError("items must be greater than zero.")
    if workers <= 0:
        raise ValueError("workers must be greater than zero.")
    if delay < 0:
        raise ValueError("delay must not be negative.")
    if repetitions <= 0:
        raise ValueError("repetitions must be greater than zero.")

    workload = list(range(items))
    elapsed_samples: list[float] = []

    for _ in range(repetitions):
        start = time.perf_counter()

        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(
                executor.map(
                    lambda value: io_bound_work(value, delay),
                    workload,
                )
            )

        elapsed_samples.append(time.perf_counter() - start)

        if len(results) != items:
            raise RuntimeError("Benchmark produced an unexpected result count.")

    return BenchmarkResult(
        workers=workers,
        iterations=items,
        total_seconds=statistics.median(elapsed_samples),
    )


def print_results(results: list[BenchmarkResult]) -> None:
    """Print benchmark measurements in a compact tabular format."""
    print(
        f"{'Workers':>8} {'Seconds':>12} "
        f"{'Items/sec':>14}"
    )
    print("-" * 38)

    for result in results:
        print(
            f"{result.workers:>8} "
            f"{result.total_seconds:>12.4f} "
            f"{result.items_per_second:>14.2f}"
        )


def parse_args() -> argparse.Namespace:
    """Parse benchmark configuration from the command line."""
    parser = argparse.ArgumentParser(
        description="Benchmark Python thread concurrency for an I/O-bound workload.",
    )
    parser.add_argument(
        "--items",
        type=int,
        default=100,
        help="Number of work items per benchmark run.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        nargs="+",
        default=[1, 2, 4, 8, 16],
        help="Thread counts to benchmark.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.01,
        help="Simulated blocking I/O delay in seconds.",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=3,
        help="Number of measurements per worker configuration.",
    )

    return parser.parse_args()


def main() -> None:
    """Run the thread-concurrency benchmark."""
    args = parse_args()

    results = [
        benchmark_threads(
            items=args.items,
            workers=workers,
            delay=args.delay,
            repetitions=args.repetitions,
        )
        for workers in args.workers
    ]

    print_results(results)


if __name__ == "__main__":
    main()

"""Benchmark thread-based concurrency for the concurrent data processor."""

from __future__ import annotations

import argparse
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Represent timing measurements for one benchmark configuration."""

    workers: int
    iterations: int
    total_seconds: float

    @property
    def items_per_second(self) -> float:
        """Return the completed workload throughput."""
        return self.iterations / self.total_seconds


def io_bound_work(value: int, delay: float) -> int:
    """Simulate blocking I/O without performing external network calls."""
    time.sleep(delay)
    return value * 2


def benchmark_threads(
    *,
    items: int,
    workers: int,
    delay: float,
    repetitions: int,
) -> BenchmarkResult:
    """Measure throughput for a bounded thread pool."""
    if items <= 0:
        raise ValueError("items must be greater than zero.")
    if workers <= 0:
        raise ValueError("workers must be greater than zero.")
    if delay < 0:
        raise ValueError("delay must not be negative.")
    if repetitions <= 0:
        raise ValueError("repetitions must be greater than zero.")

    workload = list(range(items))
    elapsed_samples: list[float] = []

    for _ in range(repetitions):
        start = time.perf_counter()

        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(
                executor.map(
                    lambda value: io_bound_work(value, delay),
                    workload,
                )
            )

        elapsed_samples.append(time.perf_counter() - start)

        if len(results) != items:
            raise RuntimeError("Benchmark produced an unexpected result count.")

    return BenchmarkResult(
        workers=workers,
        iterations=items,
        total_seconds=statistics.median(elapsed_samples),
    )


def print_results(results: list[BenchmarkResult]) -> None:
    """Print benchmark measurements in a compact tabular format."""
    print(
        f"{'Workers':>8} {'Seconds':>12} "
        f"{'Items/sec':>14}"
    )
    print("-" * 38)

    for result in results:
        print(
            f"{result.workers:>8} "
            f"{result.total_seconds:>12.4f} "
            f"{result.items_per_second:>14.2f}"
        )


def parse_args() -> argparse.Namespace:
    """Parse benchmark configuration from the command line."""
    parser = argparse.ArgumentParser(
        description="Benchmark Python thread concurrency for an I/O-bound workload.",
    )
    parser.add_argument(
        "--items",
        type=int,
        default=100,
        help="Number of work items per benchmark run.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        nargs="+",
        default=[1, 2, 4, 8, 16],
        help="Thread counts to benchmark.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.01,
        help="Simulated blocking I/O delay in seconds.",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=3,
        help="Number of measurements per worker configuration.",
    )

    return parser.parse_args()


def main() -> None:
    """Run the thread-concurrency benchmark."""
    args = parse_args()

    results = [
        benchmark_threads(
            items=args.items,
            workers=workers,
            delay=args.delay,
            repetitions=args.repetitions,
        )
        for workers in args.workers
    ]

    print_results(results)


if __name__ == "__main__":
    main()