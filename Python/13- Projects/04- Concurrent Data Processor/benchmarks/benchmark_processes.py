"""Benchmark process-based concurrency for the concurrent data processor."""

from __future__ import annotations

import argparse
import statistics
import time
from dataclasses import dataclass
from typing import Callable

from src.concurrency import ConcurrencyExecutor


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Represent timing measurements for one process-pool configuration."""

    workers: int
    items: int
    total_seconds: float

    @property
    def items_per_second(self) -> float:
        """Return workload throughput for the measured execution."""
        return self.items / self.total_seconds


def cpu_bound_work(value: int, iterations: int) -> int:
    """Perform deterministic CPU-bound work suitable for process execution."""
    result = value

    for _ in range(iterations):
        result = (result * 31 + 17) % 1_000_000_007

    return result


def benchmark_processes(
    *,
    items: int,
    workers: int,
    iterations: int,
    repetitions: int,
) -> BenchmarkResult:
    """Measure throughput for a bounded process pool."""
    if items <= 0:
        raise ValueError("items must be greater than zero.")
    if workers <= 0:
        raise ValueError("workers must be greater than zero.")
    if iterations <= 0:
        raise ValueError("iterations must be greater than zero.")
    if repetitions <= 0:
        raise ValueError("repetitions must be greater than zero.")

    workload = list(range(items))
    worker = lambda value: cpu_bound_work(value, iterations)
    elapsed_samples: list[float] = []

    for _ in range(repetitions):
        start = time.perf_counter()

        with ConcurrencyExecutor(
            mode="process",
            max_workers=workers,
        ) as executor:
            results = executor.map(worker, workload)

        elapsed_samples.append(time.perf_counter() - start)

        if len(results) != items:
            raise RuntimeError("Benchmark produced an unexpected result count.")

    return BenchmarkResult(
        workers=workers,
        items=items,
        total_seconds=statistics.median(elapsed_samples),
    )


def print_results(results: list[BenchmarkResult]) -> None:
    """Print process benchmark measurements in a compact table."""
    print(f"{'Workers':>8} {'Seconds':>12} {'Items/sec':>14}")
    print("-" * 38)

    for result in results:
        print(
            f"{result.workers:>8} "
            f"{result.total_seconds:>12.4f} "
            f"{result.items_per_second:>14.2f}"
        )


def parse_args() -> argparse.Namespace:
    """Parse benchmark parameters from the command line."""
    parser = argparse.ArgumentParser(
        description="Benchmark Python process-based concurrency.",
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
        default=[1, 2, 4, 8],
        help="Process counts to benchmark.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=100_000,
        help="CPU iterations performed for each item.",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=3,
        help="Number of measurements per worker configuration.",
    )

    return parser.parse_args()


def main() -> None:
    """Run the process-concurrency benchmark."""
    args = parse_args()

    results = [
        benchmark_processes(
            items=args.items,
            workers=workers,
            iterations=args.iterations,
            repetitions=args.repetitions,
        )
        for workers in args.workers
    ]

    print_results(results)


if __name__ == "__main__":
    main()

"""Benchmark process-based concurrency for the concurrent data processor."""

from __future__ import annotations

import argparse
import statistics
import time
from dataclasses import dataclass
from typing import Callable

from src.concurrency import ConcurrencyExecutor


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Represent timing measurements for one process-pool configuration."""

    workers: int
    items: int
    total_seconds: float

    @property
    def items_per_second(self) -> float:
        """Return workload throughput for the measured execution."""
        return self.items / self.total_seconds


def cpu_bound_work(value: int, iterations: int) -> int:
    """Perform deterministic CPU-bound work suitable for process execution."""
    result = value

    for _ in range(iterations):
        result = (result * 31 + 17) % 1_000_000_007

    return result


def benchmark_processes(
    *,
    items: int,
    workers: int,
    iterations: int,
    repetitions: int,
) -> BenchmarkResult:
    """Measure throughput for a bounded process pool."""
    if items <= 0:
        raise ValueError("items must be greater than zero.")
    if workers <= 0:
        raise ValueError("workers must be greater than zero.")
    if iterations <= 0:
        raise ValueError("iterations must be greater than zero.")
    if repetitions <= 0:
        raise ValueError("repetitions must be greater than zero.")

    workload = list(range(items))
    worker = lambda value: cpu_bound_work(value, iterations)
    elapsed_samples: list[float] = []

    for _ in range(repetitions):
        start = time.perf_counter()

        with ConcurrencyExecutor(
            mode="process",
            max_workers=workers,
        ) as executor:
            results = executor.map(worker, workload)

        elapsed_samples.append(time.perf_counter() - start)

        if len(results) != items:
            raise RuntimeError("Benchmark produced an unexpected result count.")

    return BenchmarkResult(
        workers=workers,
        items=items,
        total_seconds=statistics.median(elapsed_samples),
    )


def print_results(results: list[BenchmarkResult]) -> None:
    """Print process benchmark measurements in a compact table."""
    print(f"{'Workers':>8} {'Seconds':>12} {'Items/sec':>14}")
    print("-" * 38)

    for result in results:
        print(
            f"{result.workers:>8} "
            f"{result.total_seconds:>12.4f} "
            f"{result.items_per_second:>14.2f}"
        )


def parse_args() -> argparse.Namespace:
    """Parse benchmark parameters from the command line."""
    parser = argparse.ArgumentParser(
        description="Benchmark Python process-based concurrency.",
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
        default=[1, 2, 4, 8],
        help="Process counts to benchmark.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=100_000,
        help="CPU iterations performed for each item.",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=3,
        help="Number of measurements per worker configuration.",
    )

    return parser.parse_args()


def main() -> None:
    """Run the process-concurrency benchmark."""
    args = parse_args()

    results = [
        benchmark_processes(
            items=args.items,
            workers=workers,
            iterations=args.iterations,
            repetitions=args.repetitions,
        )
        for workers in args.workers
    ]

    print_results(results)


if __name__ == "__main__":
    main()