"""Benchmark asyncio-based concurrency for the concurrent data processor."""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time
from dataclasses import dataclass

from src.concurrency import gather_bounded


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Represent timing measurements for one asyncio configuration."""

    concurrency: int
    items: int
    total_seconds: float

    @property
    def items_per_second(self) -> float:
        """Return workload throughput for the measured execution."""
        return self.items / self.total_seconds


async def io_bound_work(value: int, delay: float) -> int:
    """Simulate non-blocking I/O suitable for asyncio concurrency."""
    await asyncio.sleep(delay)
    return value * 2


async def benchmark_asyncio(
    *,
    items: int,
    concurrency: int,
    delay: float,
    repetitions: int,
) -> BenchmarkResult:
    """Measure throughput for bounded asyncio concurrency."""
    if items <= 0:
        raise ValueError("items must be greater than zero.")
    if concurrency <= 0:
        raise ValueError("concurrency must be greater than zero.")
    if delay < 0:
        raise ValueError("delay must not be negative.")
    if repetitions <= 0:
        raise ValueError("repetitions must be greater than zero.")

    workload = range(items)
    elapsed_samples: list[float] = []

    async def worker(value: int) -> int:
        """Process one workload item without blocking the event loop."""
        return await io_bound_work(value, delay)

    for _ in range(repetitions):
        start = time.perf_counter()

        results = await gather_bounded(
            (
                lambda value=value: worker(value)
                for value in workload
            ),
            max_concurrency=concurrency,
        )

        elapsed_samples.append(time.perf_counter() - start)

        if len(results) != items:
            raise RuntimeError("Benchmark produced an unexpected result count.")

    return BenchmarkResult(
        concurrency=concurrency,
        items=items,
        total_seconds=statistics.median(elapsed_samples),
    )


def print_results(results: list[BenchmarkResult]) -> None:
    """Print asyncio benchmark measurements in a compact table."""
    print(f"{'Concurrency':>12} {'Seconds':>12} {'Items/sec':>14}")
    print("-" * 42)

    for result in results:
        print(
            f"{result.concurrency:>12} "
            f"{result.total_seconds:>12.4f} "
            f"{result.items_per_second:>14.2f}"
        )


def parse_args() -> argparse.Namespace:
    """Parse benchmark parameters from the command line."""
    parser = argparse.ArgumentParser(
        description="Benchmark asyncio concurrency for an I/O-bound workload.",
    )
    parser.add_argument(
        "--items",
        type=int,
        default=100,
        help="Number of work items per benchmark run.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        nargs="+",
        default=[1, 2, 4, 8, 16, 32],
        help="Async concurrency limits to benchmark.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.01,
        help="Simulated non-blocking I/O delay in seconds.",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=3,
        help="Number of measurements per concurrency configuration.",
    )

    return parser.parse_args()


async def run(args: argparse.Namespace) -> list[BenchmarkResult]:
    """Run all asyncio benchmark configurations."""
    return [
        await benchmark_asyncio(
            items=args.items,
            concurrency=concurrency,
            delay=args.delay,
            repetitions=args.repetitions,
        )
        for concurrency in args.concurrency
    ]


def main() -> None:
    """Run the asyncio concurrency benchmark."""
    args = parse_args()
    results = asyncio.run(run(args))
    print_results(results)


if __name__ == "__main__":
    main()

"""Benchmark asyncio-based concurrency for the concurrent data processor."""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time
from dataclasses import dataclass

from src.concurrency import gather_bounded


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Represent timing measurements for one asyncio configuration."""

    concurrency: int
    items: int
    total_seconds: float

    @property
    def items_per_second(self) -> float:
        """Return workload throughput for the measured execution."""
        return self.items / self.total_seconds


async def io_bound_work(value: int, delay: float) -> int:
    """Simulate non-blocking I/O suitable for asyncio concurrency."""
    await asyncio.sleep(delay)
    return value * 2


async def benchmark_asyncio(
    *,
    items: int,
    concurrency: int,
    delay: float,
    repetitions: int,
) -> BenchmarkResult:
    """Measure throughput for bounded asyncio concurrency."""
    if items <= 0:
        raise ValueError("items must be greater than zero.")
    if concurrency <= 0:
        raise ValueError("concurrency must be greater than zero.")
    if delay < 0:
        raise ValueError("delay must not be negative.")
    if repetitions <= 0:
        raise ValueError("repetitions must be greater than zero.")

    workload = range(items)
    elapsed_samples: list[float] = []

    async def worker(value: int) -> int:
        """Process one workload item without blocking the event loop."""
        return await io_bound_work(value, delay)

    for _ in range(repetitions):
        start = time.perf_counter()

        results = await gather_bounded(
            (
                lambda value=value: worker(value)
                for value in workload
            ),
            max_concurrency=concurrency,
        )

        elapsed_samples.append(time.perf_counter() - start)

        if len(results) != items:
            raise RuntimeError("Benchmark produced an unexpected result count.")

    return BenchmarkResult(
        concurrency=concurrency,
        items=items,
        total_seconds=statistics.median(elapsed_samples),
    )


def print_results(results: list[BenchmarkResult]) -> None:
    """Print asyncio benchmark measurements in a compact table."""
    print(f"{'Concurrency':>12} {'Seconds':>12} {'Items/sec':>14}")
    print("-" * 42)

    for result in results:
        print(
            f"{result.concurrency:>12} "
            f"{result.total_seconds:>12.4f} "
            f"{result.items_per_second:>14.2f}"
        )


def parse_args() -> argparse.Namespace:
    """Parse benchmark parameters from the command line."""
    parser = argparse.ArgumentParser(
        description="Benchmark asyncio concurrency for an I/O-bound workload.",
    )
    parser.add_argument(
        "--items",
        type=int,
        default=100,
        help="Number of work items per benchmark run.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        nargs="+",
        default=[1, 2, 4, 8, 16, 32],
        help="Async concurrency limits to benchmark.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.01,
        help="Simulated non-blocking I/O delay in seconds.",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=3,
        help="Number of measurements per concurrency configuration.",
    )

    return parser.parse_args()


async def run(args: argparse.Namespace) -> list[BenchmarkResult]:
    """Run all asyncio benchmark configurations."""
    return [
        await benchmark_asyncio(
            items=args.items,
            concurrency=concurrency,
            delay=args.delay,
            repetitions=args.repetitions,
        )
        for concurrency in args.concurrency
    ]


def main() -> None:
    """Run the asyncio concurrency benchmark."""
    args = parse_args()
    results = asyncio.run(run(args))
    print_results(results)


if __name__ == "__main__":
    main()