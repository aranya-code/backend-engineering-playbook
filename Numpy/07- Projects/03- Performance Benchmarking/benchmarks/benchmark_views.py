"""Benchmark NumPy view-based operations against copy-producing operations."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.benchmarks import BenchmarkResult, benchmark, benchmark_metadata
from src.datasets import generate_uniform


DEFAULT_SIZE = 1_000_000
DEFAULT_ITERATIONS = 10
DEFAULT_WARMUP_ITERATIONS = 2
DEFAULT_SLICE_START = 100_000
DEFAULT_SLICE_STOP = 900_000
DEFAULT_STRIDE = 2
DEFAULT_SEED = 42


def slice_view(values: np.ndarray) -> np.ndarray:
    """Return a basic slice that normally shares memory with the input."""
    return values[
        DEFAULT_SLICE_START:DEFAULT_SLICE_STOP:DEFAULT_STRIDE
    ]


def fancy_index_copy(values: np.ndarray) -> np.ndarray:
    """Return a selection produced through integer-array indexing."""
    indices = np.arange(
        DEFAULT_SLICE_START,
        DEFAULT_SLICE_STOP,
        DEFAULT_STRIDE,
        dtype=np.intp,
    )
    return values[indices]


def ravel_view(values: np.ndarray) -> np.ndarray:
    """Flatten a contiguous array while allowing a view when possible."""
    return values.ravel()


def flatten_copy(values: np.ndarray) -> np.ndarray:
    """Flatten an array using an operation that always allocates a copy."""
    return values.flatten()


def benchmark_operations(
    values: np.ndarray,
    *,
    iterations: int,
    warmup_iterations: int,
) -> dict[str, BenchmarkResult]:
    """Benchmark representative view and copy-producing operations."""
    operations = {
        "slice-view": slice_view,
        "fancy-index-copy": fancy_index_copy,
        "ravel-view": ravel_view,
        "flatten-copy": flatten_copy,
    }

    results: dict[str, BenchmarkResult] = {}

    for name, function in operations.items():
        results[name] = benchmark(
            function,
            values,
            name=name,
            iterations=iterations,
            warmup_iterations=warmup_iterations,
        )

    return results


def validate_memory_behavior(values: np.ndarray) -> None:
    """Validate the expected sharing behavior of representative operations."""
    view_result = slice_view(values)
    copy_result = fancy_index_copy(values)
    ravel_result = ravel_view(values)
    flatten_result = flatten_copy(values)

    assert np.shares_memory(values, view_result)
    assert not np.shares_memory(values, copy_result)
    assert np.shares_memory(values, ravel_result)
    assert not np.shares_memory(values, flatten_result)


def format_result(
    name: str,
    result: BenchmarkResult,
) -> str:
    """Format benchmark statistics for terminal output."""
    metrics = benchmark_metadata(result)
    return "\n".join(
        [
            f"{name}:",
            f"  mean: {metrics['mean_seconds']:.6f} s",
            f"  median: {metrics['median_seconds']:.6f} s",
            f"  minimum: {metrics['minimum_seconds']:.6f} s",
            f"  operations/sec: {metrics['operations_per_second']:.2f}",
        ]
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the view and copy benchmark."""
    parser = argparse.ArgumentParser(
        description="Benchmark NumPy views against copy-producing operations.",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=DEFAULT_SIZE,
        help="Number of input elements.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help="Number of timed iterations.",
    )
    parser.add_argument(
        "--warmup-iterations",
        type=int,
        default=DEFAULT_WARMUP_ITERATIONS,
        help="Number of warmup executions.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Seed for reproducible input generation.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    """Validate benchmark parameters before allocating the dataset."""
    if args.size <= 0:
        raise ValueError("size must be positive.")
    if args.iterations <= 0:
        raise ValueError("iterations must be positive.")
    if args.warmup_iterations < 0:
        raise ValueError("warmup-iterations must be non-negative.")
    if args.seed < 0:
        raise ValueError("seed must be non-negative.")
    if args.size <= DEFAULT_SLICE_STOP:
        raise ValueError(
            f"size must be greater than {DEFAULT_SLICE_STOP} "
            "for the configured benchmark slice."
        )


def main() -> int:
    """Generate input, validate memory semantics, and run benchmarks."""
    args = parse_args()

    try:
        validate_args(args)

        values = generate_uniform(
            args.size,
            low=0.0,
            high=1_000.0,
            dtype=np.float64,
            seed=args.seed,
        )

        validate_memory_behavior(values)

        results = benchmark_operations(
            values,
            iterations=args.iterations,
            warmup_iterations=args.warmup_iterations,
        )

    except (AssertionError, TypeError, ValueError) as exc:
        print(f"Benchmark failed: {exc}", file=sys.stderr)
        return 1

    print("NumPy View vs Copy Benchmark")
    print("============================")
    print(f"Dataset size: {values.size:,}")
    print(f"Dtype: {values.dtype}")
    print(f"Input bytes: {values.nbytes:,}")
    print()

    for name, result in results.items():
        print(format_result(name, result))
        print()

    print("Memory semantics")
    print("----------------")
    print(
        "slice-view shares memory:",
        np.shares_memory(values, slice_view(values)),
    )
    print(
        "fancy-index-copy shares memory:",
        np.shares_memory(values, fancy_index_copy(values)),
    )
    print(
        "ravel-view shares memory:",
        np.shares_memory(values, ravel_view(values)),
    )
    print(
        "flatten-copy shares memory:",
        np.shares_memory(values, flatten_copy(values)),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Benchmark NumPy view-based operations against copy-producing operations."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.benchmarks import BenchmarkResult, benchmark, benchmark_metadata
from src.datasets import generate_uniform


DEFAULT_SIZE = 1_000_000
DEFAULT_ITERATIONS = 10
DEFAULT_WARMUP_ITERATIONS = 2
DEFAULT_SLICE_START = 100_000
DEFAULT_SLICE_STOP = 900_000
DEFAULT_STRIDE = 2
DEFAULT_SEED = 42


def slice_view(values: np.ndarray) -> np.ndarray:
    """Return a basic slice that normally shares memory with the input."""
    return values[
        DEFAULT_SLICE_START:DEFAULT_SLICE_STOP:DEFAULT_STRIDE
    ]


def fancy_index_copy(values: np.ndarray) -> np.ndarray:
    """Return a selection produced through integer-array indexing."""
    indices = np.arange(
        DEFAULT_SLICE_START,
        DEFAULT_SLICE_STOP,
        DEFAULT_STRIDE,
        dtype=np.intp,
    )
    return values[indices]


def ravel_view(values: np.ndarray) -> np.ndarray:
    """Flatten a contiguous array while allowing a view when possible."""
    return values.ravel()


def flatten_copy(values: np.ndarray) -> np.ndarray:
    """Flatten an array using an operation that always allocates a copy."""
    return values.flatten()


def benchmark_operations(
    values: np.ndarray,
    *,
    iterations: int,
    warmup_iterations: int,
) -> dict[str, BenchmarkResult]:
    """Benchmark representative view and copy-producing operations."""
    operations = {
        "slice-view": slice_view,
        "fancy-index-copy": fancy_index_copy,
        "ravel-view": ravel_view,
        "flatten-copy": flatten_copy,
    }

    results: dict[str, BenchmarkResult] = {}

    for name, function in operations.items():
        results[name] = benchmark(
            function,
            values,
            name=name,
            iterations=iterations,
            warmup_iterations=warmup_iterations,
        )

    return results


def validate_memory_behavior(values: np.ndarray) -> None:
    """Validate the expected sharing behavior of representative operations."""
    view_result = slice_view(values)
    copy_result = fancy_index_copy(values)
    ravel_result = ravel_view(values)
    flatten_result = flatten_copy(values)

    assert np.shares_memory(values, view_result)
    assert not np.shares_memory(values, copy_result)
    assert np.shares_memory(values, ravel_result)
    assert not np.shares_memory(values, flatten_result)


def format_result(
    name: str,
    result: BenchmarkResult,
) -> str:
    """Format benchmark statistics for terminal output."""
    metrics = benchmark_metadata(result)
    return "\n".join(
        [
            f"{name}:",
            f"  mean: {metrics['mean_seconds']:.6f} s",
            f"  median: {metrics['median_seconds']:.6f} s",
            f"  minimum: {metrics['minimum_seconds']:.6f} s",
            f"  operations/sec: {metrics['operations_per_second']:.2f}",
        ]
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the view and copy benchmark."""
    parser = argparse.ArgumentParser(
        description="Benchmark NumPy views against copy-producing operations.",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=DEFAULT_SIZE,
        help="Number of input elements.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help="Number of timed iterations.",
    )
    parser.add_argument(
        "--warmup-iterations",
        type=int,
        default=DEFAULT_WARMUP_ITERATIONS,
        help="Number of warmup executions.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Seed for reproducible input generation.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    """Validate benchmark parameters before allocating the dataset."""
    if args.size <= 0:
        raise ValueError("size must be positive.")
    if args.iterations <= 0:
        raise ValueError("iterations must be positive.")
    if args.warmup_iterations < 0:
        raise ValueError("warmup-iterations must be non-negative.")
    if args.seed < 0:
        raise ValueError("seed must be non-negative.")
    if args.size <= DEFAULT_SLICE_STOP:
        raise ValueError(
            f"size must be greater than {DEFAULT_SLICE_STOP} "
            "for the configured benchmark slice."
        )


def main() -> int:
    """Generate input, validate memory semantics, and run benchmarks."""
    args = parse_args()

    try:
        validate_args(args)

        values = generate_uniform(
            args.size,
            low=0.0,
            high=1_000.0,
            dtype=np.float64,
            seed=args.seed,
        )

        validate_memory_behavior(values)

        results = benchmark_operations(
            values,
            iterations=args.iterations,
            warmup_iterations=args.warmup_iterations,
        )

    except (AssertionError, TypeError, ValueError) as exc:
        print(f"Benchmark failed: {exc}", file=sys.stderr)
        return 1

    print("NumPy View vs Copy Benchmark")
    print("============================")
    print(f"Dataset size: {values.size:,}")
    print(f"Dtype: {values.dtype}")
    print(f"Input bytes: {values.nbytes:,}")
    print()

    for name, result in results.items():
        print(format_result(name, result))
        print()

    print("Memory semantics")
    print("----------------")
    print(
        "slice-view shares memory:",
        np.shares_memory(values, slice_view(values)),
    )
    print(
        "fancy-index-copy shares memory:",
        np.shares_memory(values, fancy_index_copy(values)),
    )
    print(
        "ravel-view shares memory:",
        np.shares_memory(values, ravel_view(values)),
    )
    print(
        "flatten-copy shares memory:",
        np.shares_memory(values, flatten_copy(values)),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())