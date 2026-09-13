"""Benchmark utilities for comparing numerical processing implementations."""

from __future__ import annotations

import gc
import time
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Timing statistics for a single benchmark execution."""

    name: str
    iterations: int
    warmup_iterations: int
    minimum_seconds: float
    maximum_seconds: float
    mean_seconds: float
    median_seconds: float
    standard_deviation_seconds: float
    total_seconds: float

    @property
    def operations_per_second(self) -> float:
        """Return the average number of benchmark runs per second."""
        if self.mean_seconds <= 0.0:
            return float("inf")

        return 1.0 / self.mean_seconds


@dataclass(frozen=True, slots=True)
class BenchmarkComparison:
    """Comparison between two benchmark implementations."""

    baseline: BenchmarkResult
    candidate: BenchmarkResult

    @property
    def speedup(self) -> float:
        """Return baseline mean runtime divided by candidate mean runtime."""
        if self.candidate.mean_seconds <= 0.0:
            return float("inf")

        return (
            self.baseline.mean_seconds
            / self.candidate.mean_seconds
        )

    @property
    def relative_runtime(self) -> float:
        """Return candidate runtime as a fraction of baseline runtime."""
        if self.baseline.mean_seconds <= 0.0:
            return float("inf")

        return (
            self.candidate.mean_seconds
            / self.baseline.mean_seconds
        )


def benchmark(
    function: Callable[..., Any],
    *args: Any,
    name: str | None = None,
    iterations: int = 10,
    warmup_iterations: int = 2,
    disable_gc: bool = True,
    **kwargs: Any,
) -> BenchmarkResult:
    """Measure repeated execution time using a monotonic high-resolution clock."""
    if iterations <= 0:
        raise ValueError("iterations must be positive.")

    if warmup_iterations < 0:
        raise ValueError(
            "warmup_iterations must be non-negative."
        )

    resolved_name = name or getattr(
        function,
        "__name__",
        "benchmark",
    )

    for _ in range(warmup_iterations):
        function(
            *args,
            **kwargs,
        )

    garbage_collection_enabled = gc.isenabled()

    if disable_gc and garbage_collection_enabled:
        gc.disable()

    timings: list[float] = []

    try:
        for _ in range(iterations):
            start = time.perf_counter()

            function(
                *args,
                **kwargs,
            )

            elapsed = time.perf_counter() - start
            timings.append(elapsed)
    finally:
        if (
            disable_gc
            and garbage_collection_enabled
        ):
            gc.enable()

    timing_array = np.asarray(
        timings,
        dtype=np.float64,
    )

    return BenchmarkResult(
        name=resolved_name,
        iterations=iterations,
        warmup_iterations=warmup_iterations,
        minimum_seconds=float(np.min(timing_array)),
        maximum_seconds=float(np.max(timing_array)),
        mean_seconds=float(np.mean(timing_array)),
        median_seconds=float(np.median(timing_array)),
        standard_deviation_seconds=float(
            np.std(
                timing_array,
                ddof=0,
            )
        ),
        total_seconds=float(np.sum(timing_array)),
    )


def compare(
    baseline_function: Callable[..., Any],
    candidate_function: Callable[..., Any],
    *args: Any,
    baseline_name: str = "baseline",
    candidate_name: str = "candidate",
    iterations: int = 10,
    warmup_iterations: int = 2,
    disable_gc: bool = True,
    **kwargs: Any,
) -> BenchmarkComparison:
    """Benchmark two implementations with identical inputs."""
    baseline = benchmark(
        baseline_function,
        *args,
        name=baseline_name,
        iterations=iterations,
        warmup_iterations=warmup_iterations,
        disable_gc=disable_gc,
        **kwargs,
    )

    candidate = benchmark(
        candidate_function,
        *args,
        name=candidate_name,
        iterations=iterations,
        warmup_iterations=warmup_iterations,
        disable_gc=disable_gc,
        **kwargs,
    )

    return BenchmarkComparison(
        baseline=baseline,
        candidate=candidate,
    )


def benchmark_sizes(
    function: Callable[..., Any],
    sizes: list[int] | tuple[int, ...],
    *,
    factory: Callable[[int], Any],
    iterations: int = 10,
    warmup_iterations: int = 2,
    disable_gc: bool = True,
    name: str | None = None,
    **kwargs: Any,
) -> list[BenchmarkResult]:
    """Benchmark one function across multiple dataset sizes."""
    if not sizes:
        raise ValueError("sizes must not be empty.")

    results: list[BenchmarkResult] = []

    for size in sizes:
        if size <= 0:
            raise ValueError("benchmark sizes must be positive.")

        values = factory(size)

        result = benchmark(
            function,
            values,
            name=f"{name or function.__name__}[{size:,}]",
            iterations=iterations,
            warmup_iterations=warmup_iterations,
            disable_gc=disable_gc,
            **kwargs,
        )

        results.append(result)

    return results


def validate_result(
    result: Any,
) -> None:
    """Validate that a benchmarked function produced a non-null result."""
    if result is None:
        raise ValueError(
            "Benchmarked function returned None."
        )


def benchmark_metadata(
    result: BenchmarkResult,
) -> dict[str, float | int | str]:
    """Convert benchmark statistics into a serializable metadata mapping."""
    return {
        "name": result.name,
        "iterations": result.iterations,
        "warmup_iterations": result.warmup_iterations,
        "minimum_seconds": result.minimum_seconds,
        "maximum_seconds": result.maximum_seconds,
        "mean_seconds": result.mean_seconds,
        "median_seconds": result.median_seconds,
        "standard_deviation_seconds": (
            result.standard_deviation_seconds
        ),
        "total_seconds": result.total_seconds,
        "operations_per_second": result.operations_per_second,
    }

"""Benchmark utilities for comparing numerical processing implementations."""

from __future__ import annotations

import gc
import time
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Timing statistics for a single benchmark execution."""

    name: str
    iterations: int
    warmup_iterations: int
    minimum_seconds: float
    maximum_seconds: float
    mean_seconds: float
    median_seconds: float
    standard_deviation_seconds: float
    total_seconds: float

    @property
    def operations_per_second(self) -> float:
        """Return the average number of benchmark runs per second."""
        if self.mean_seconds <= 0.0:
            return float("inf")

        return 1.0 / self.mean_seconds


@dataclass(frozen=True, slots=True)
class BenchmarkComparison:
    """Comparison between two benchmark implementations."""

    baseline: BenchmarkResult
    candidate: BenchmarkResult

    @property
    def speedup(self) -> float:
        """Return baseline mean runtime divided by candidate mean runtime."""
        if self.candidate.mean_seconds <= 0.0:
            return float("inf")

        return (
            self.baseline.mean_seconds
            / self.candidate.mean_seconds
        )

    @property
    def relative_runtime(self) -> float:
        """Return candidate runtime as a fraction of baseline runtime."""
        if self.baseline.mean_seconds <= 0.0:
            return float("inf")

        return (
            self.candidate.mean_seconds
            / self.baseline.mean_seconds
        )


def benchmark(
    function: Callable[..., Any],
    *args: Any,
    name: str | None = None,
    iterations: int = 10,
    warmup_iterations: int = 2,
    disable_gc: bool = True,
    **kwargs: Any,
) -> BenchmarkResult:
    """Measure repeated execution time using a monotonic high-resolution clock."""
    if iterations <= 0:
        raise ValueError("iterations must be positive.")

    if warmup_iterations < 0:
        raise ValueError(
            "warmup_iterations must be non-negative."
        )

    resolved_name = name or getattr(
        function,
        "__name__",
        "benchmark",
    )

    for _ in range(warmup_iterations):
        function(
            *args,
            **kwargs,
        )

    garbage_collection_enabled = gc.isenabled()

    if disable_gc and garbage_collection_enabled:
        gc.disable()

    timings: list[float] = []

    try:
        for _ in range(iterations):
            start = time.perf_counter()

            function(
                *args,
                **kwargs,
            )

            elapsed = time.perf_counter() - start
            timings.append(elapsed)
    finally:
        if (
            disable_gc
            and garbage_collection_enabled
        ):
            gc.enable()

    timing_array = np.asarray(
        timings,
        dtype=np.float64,
    )

    return BenchmarkResult(
        name=resolved_name,
        iterations=iterations,
        warmup_iterations=warmup_iterations,
        minimum_seconds=float(np.min(timing_array)),
        maximum_seconds=float(np.max(timing_array)),
        mean_seconds=float(np.mean(timing_array)),
        median_seconds=float(np.median(timing_array)),
        standard_deviation_seconds=float(
            np.std(
                timing_array,
                ddof=0,
            )
        ),
        total_seconds=float(np.sum(timing_array)),
    )


def compare(
    baseline_function: Callable[..., Any],
    candidate_function: Callable[..., Any],
    *args: Any,
    baseline_name: str = "baseline",
    candidate_name: str = "candidate",
    iterations: int = 10,
    warmup_iterations: int = 2,
    disable_gc: bool = True,
    **kwargs: Any,
) -> BenchmarkComparison:
    """Benchmark two implementations with identical inputs."""
    baseline = benchmark(
        baseline_function,
        *args,
        name=baseline_name,
        iterations=iterations,
        warmup_iterations=warmup_iterations,
        disable_gc=disable_gc,
        **kwargs,
    )

    candidate = benchmark(
        candidate_function,
        *args,
        name=candidate_name,
        iterations=iterations,
        warmup_iterations=warmup_iterations,
        disable_gc=disable_gc,
        **kwargs,
    )

    return BenchmarkComparison(
        baseline=baseline,
        candidate=candidate,
    )


def benchmark_sizes(
    function: Callable[..., Any],
    sizes: list[int] | tuple[int, ...],
    *,
    factory: Callable[[int], Any],
    iterations: int = 10,
    warmup_iterations: int = 2,
    disable_gc: bool = True,
    name: str | None = None,
    **kwargs: Any,
) -> list[BenchmarkResult]:
    """Benchmark one function across multiple dataset sizes."""
    if not sizes:
        raise ValueError("sizes must not be empty.")

    results: list[BenchmarkResult] = []

    for size in sizes:
        if size <= 0:
            raise ValueError("benchmark sizes must be positive.")

        values = factory(size)

        result = benchmark(
            function,
            values,
            name=f"{name or function.__name__}[{size:,}]",
            iterations=iterations,
            warmup_iterations=warmup_iterations,
            disable_gc=disable_gc,
            **kwargs,
        )

        results.append(result)

    return results


def validate_result(
    result: Any,
) -> None:
    """Validate that a benchmarked function produced a non-null result."""
    if result is None:
        raise ValueError(
            "Benchmarked function returned None."
        )


def benchmark_metadata(
    result: BenchmarkResult,
) -> dict[str, float | int | str]:
    """Convert benchmark statistics into a serializable metadata mapping."""
    return {
        "name": result.name,
        "iterations": result.iterations,
        "warmup_iterations": result.warmup_iterations,
        "minimum_seconds": result.minimum_seconds,
        "maximum_seconds": result.maximum_seconds,
        "mean_seconds": result.mean_seconds,
        "median_seconds": result.median_seconds,
        "standard_deviation_seconds": (
            result.standard_deviation_seconds
        ),
        "total_seconds": result.total_seconds,
        "operations_per_second": result.operations_per_second,
    }