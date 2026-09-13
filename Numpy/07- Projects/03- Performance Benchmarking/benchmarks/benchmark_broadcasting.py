"""Benchmark NumPy broadcasting patterns and their memory implications."""

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


DEFAULT_ROWS = 10_000
DEFAULT_COLUMNS = 128
DEFAULT_ITERATIONS = 10
DEFAULT_WARMUP_ITERATIONS = 2
DEFAULT_SEED = 42


def add_scalar(values: np.ndarray, scalar: float) -> np.ndarray:
    """Broadcast a scalar across every array element."""
    return values + scalar


def add_row_vector(
    values: np.ndarray,
    offsets: np.ndarray,
) -> np.ndarray:
    """Broadcast a one-dimensional vector across matrix rows."""
    return values + offsets


def add_column_vector(
    values: np.ndarray,
    offsets: np.ndarray,
) -> np.ndarray:
    """Broadcast a column vector across matrix columns."""
    return values + offsets


def add_same_shape(
    values: np.ndarray,
    offsets: np.ndarray,
) -> np.ndarray:
    """Add two arrays with identical shapes without broadcasting."""
    return values + offsets


def validate_broadcasting() -> None:
    """Validate broadcasting semantics before running timed benchmarks."""
    values = np.ones((4, 3), dtype=np.float64)
    scalar_result = add_scalar(values, 2.0)
    row_offsets = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    row_result = add_row_vector(values, row_offsets)
    column_offsets = np.array(
        [[1.0], [2.0], [3.0], [4.0]],
        dtype=np.float64,
    )
    column_result = add_column_vector(values, column_offsets)

    np.testing.assert_allclose(
        scalar_result,
        np.full((4, 3), 3.0),
    )
    np.testing.assert_allclose(
        row_result,
        np.array(
            [
                [2.0, 3.0, 4.0],
                [2.0, 3.0, 4.0],
                [2.0, 3.0, 4.0],
                [2.0, 3.0, 4.0],
            ]
        ),
    )
    np.testing.assert_allclose(
        column_result,
        np.array(
            [
                [2.0, 2.0, 2.0],
                [3.0, 3.0, 3.0],
                [4.0, 4.0, 4.0],
                [5.0, 5.0, 5.0],
            ]
        ),
    )


def benchmark_broadcasting(
    values: np.ndarray,
    row_offsets: np.ndarray,
    column_offsets: np.ndarray,
    same_shape_offsets: np.ndarray,
    *,
    iterations: int,
    warmup_iterations: int,
) -> dict[str, BenchmarkResult]:
    """Benchmark representative broadcasting and same-shape operations."""
    operations = {
        "scalar-broadcast": (
            add_scalar,
            (values, 2.0),
        ),
        "row-vector-broadcast": (
            add_row_vector,
            (values, row_offsets),
        ),
        "column-vector-broadcast": (
            add_column_vector,
            (values, column_offsets),
        ),
        "same-shape-addition": (
            add_same_shape,
            (values, same_shape_offsets),
        ),
    }

    results: dict[str, BenchmarkResult] = {}

    for name, (function, arguments) in operations.items():
        results[name] = benchmark(
            function,
            *arguments,
            name=name,
            iterations=iterations,
            warmup_iterations=warmup_iterations,
        )

    return results


def format_result(
    name: str,
    result: BenchmarkResult,
) -> str:
    """Format timing statistics for terminal output."""
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


def estimate_output_bytes(shape: tuple[int, ...], dtype: np.dtype) -> int:
    """Estimate the raw data-buffer size of an output array."""
    return int(np.prod(shape, dtype=np.int64)) * dtype.itemsize


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the broadcasting benchmark."""
    parser = argparse.ArgumentParser(
        description="Benchmark NumPy broadcasting patterns.",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=DEFAULT_ROWS,
        help="Number of rows in the benchmark matrix.",
    )
    parser.add_argument(
        "--columns",
        type=int,
        default=DEFAULT_COLUMNS,
        help="Number of columns in the benchmark matrix.",
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
    """Validate benchmark dimensions and execution parameters."""
    if args.rows <= 0:
        raise ValueError("rows must be positive.")
    if args.columns <= 0:
        raise ValueError("columns must be positive.")
    if args.iterations <= 0:
        raise ValueError("iterations must be positive.")
    if args.warmup_iterations < 0:
        raise ValueError("warmup-iterations must be non-negative.")
    if args.seed < 0:
        raise ValueError("seed must be non-negative.")


def main() -> int:
    """Generate input, validate broadcasting, and run benchmarks."""
    args = parse_args()

    try:
        validate_args(args)
        validate_broadcasting()

        values = generate_uniform(
            args.rows * args.columns,
            low=0.0,
            high=1_000.0,
            dtype=np.float64,
            seed=args.seed,
        ).reshape(args.rows, args.columns)

        row_offsets = generate_uniform(
            args.columns,
            low=0.0,
            high=10.0,
            dtype=np.float64,
            seed=args.seed + 1,
        )

        column_offsets = generate_uniform(
            args.rows,
            low=0.0,
            high=10.0,
            dtype=np.float64,
            seed=args.seed + 2,
        ).reshape(args.rows, 1)

        same_shape_offsets = generate_uniform(
            args.rows * args.columns,
            low=0.0,
            high=10.0,
            dtype=np.float64,
            seed=args.seed + 3,
        ).reshape(args.rows, args.columns)

        results = benchmark_broadcasting(
            values,
            row_offsets,
            column_offsets,
            same_shape_offsets,
            iterations=args.iterations,
            warmup_iterations=args.warmup_iterations,
        )

        expected_output_bytes = estimate_output_bytes(
            values.shape,
            values.dtype,
        )

    except (AssertionError, TypeError, ValueError) as exc:
        print(f"Benchmark failed: {exc}", file=sys.stderr)
        return 1

    print("NumPy Broadcasting Benchmark")
    print("============================")
    print(f"Input shape: {values.shape}")
    print(f"Dtype: {values.dtype}")
    print(f"Input bytes: {values.nbytes:,}")
    print(f"Output bytes per operation: {expected_output_bytes:,}")
    print()

    for name, result in results.items():
        print(format_result(name, result))
        print()

    print("Broadcasted operand shapes")
    print("--------------------------")
    print(f"Input:              {values.shape}")
    print(f"Scalar:             scalar")
    print(f"Row vector:         {row_offsets.shape}")
    print(f"Column vector:      {column_offsets.shape}")
    print(f"Same-shape operand:  {same_shape_offsets.shape}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Benchmark NumPy broadcasting patterns and their memory implications."""

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


DEFAULT_ROWS = 10_000
DEFAULT_COLUMNS = 128
DEFAULT_ITERATIONS = 10
DEFAULT_WARMUP_ITERATIONS = 2
DEFAULT_SEED = 42


def add_scalar(values: np.ndarray, scalar: float) -> np.ndarray:
    """Broadcast a scalar across every array element."""
    return values + scalar


def add_row_vector(
    values: np.ndarray,
    offsets: np.ndarray,
) -> np.ndarray:
    """Broadcast a one-dimensional vector across matrix rows."""
    return values + offsets


def add_column_vector(
    values: np.ndarray,
    offsets: np.ndarray,
) -> np.ndarray:
    """Broadcast a column vector across matrix columns."""
    return values + offsets


def add_same_shape(
    values: np.ndarray,
    offsets: np.ndarray,
) -> np.ndarray:
    """Add two arrays with identical shapes without broadcasting."""
    return values + offsets


def validate_broadcasting() -> None:
    """Validate broadcasting semantics before running timed benchmarks."""
    values = np.ones((4, 3), dtype=np.float64)
    scalar_result = add_scalar(values, 2.0)
    row_offsets = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    row_result = add_row_vector(values, row_offsets)
    column_offsets = np.array(
        [[1.0], [2.0], [3.0], [4.0]],
        dtype=np.float64,
    )
    column_result = add_column_vector(values, column_offsets)

    np.testing.assert_allclose(
        scalar_result,
        np.full((4, 3), 3.0),
    )
    np.testing.assert_allclose(
        row_result,
        np.array(
            [
                [2.0, 3.0, 4.0],
                [2.0, 3.0, 4.0],
                [2.0, 3.0, 4.0],
                [2.0, 3.0, 4.0],
            ]
        ),
    )
    np.testing.assert_allclose(
        column_result,
        np.array(
            [
                [2.0, 2.0, 2.0],
                [3.0, 3.0, 3.0],
                [4.0, 4.0, 4.0],
                [5.0, 5.0, 5.0],
            ]
        ),
    )


def benchmark_broadcasting(
    values: np.ndarray,
    row_offsets: np.ndarray,
    column_offsets: np.ndarray,
    same_shape_offsets: np.ndarray,
    *,
    iterations: int,
    warmup_iterations: int,
) -> dict[str, BenchmarkResult]:
    """Benchmark representative broadcasting and same-shape operations."""
    operations = {
        "scalar-broadcast": (
            add_scalar,
            (values, 2.0),
        ),
        "row-vector-broadcast": (
            add_row_vector,
            (values, row_offsets),
        ),
        "column-vector-broadcast": (
            add_column_vector,
            (values, column_offsets),
        ),
        "same-shape-addition": (
            add_same_shape,
            (values, same_shape_offsets),
        ),
    }

    results: dict[str, BenchmarkResult] = {}

    for name, (function, arguments) in operations.items():
        results[name] = benchmark(
            function,
            *arguments,
            name=name,
            iterations=iterations,
            warmup_iterations=warmup_iterations,
        )

    return results


def format_result(
    name: str,
    result: BenchmarkResult,
) -> str:
    """Format timing statistics for terminal output."""
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


def estimate_output_bytes(shape: tuple[int, ...], dtype: np.dtype) -> int:
    """Estimate the raw data-buffer size of an output array."""
    return int(np.prod(shape, dtype=np.int64)) * dtype.itemsize


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the broadcasting benchmark."""
    parser = argparse.ArgumentParser(
        description="Benchmark NumPy broadcasting patterns.",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=DEFAULT_ROWS,
        help="Number of rows in the benchmark matrix.",
    )
    parser.add_argument(
        "--columns",
        type=int,
        default=DEFAULT_COLUMNS,
        help="Number of columns in the benchmark matrix.",
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
    """Validate benchmark dimensions and execution parameters."""
    if args.rows <= 0:
        raise ValueError("rows must be positive.")
    if args.columns <= 0:
        raise ValueError("columns must be positive.")
    if args.iterations <= 0:
        raise ValueError("iterations must be positive.")
    if args.warmup_iterations < 0:
        raise ValueError("warmup-iterations must be non-negative.")
    if args.seed < 0:
        raise ValueError("seed must be non-negative.")


def main() -> int:
    """Generate input, validate broadcasting, and run benchmarks."""
    args = parse_args()

    try:
        validate_args(args)
        validate_broadcasting()

        values = generate_uniform(
            args.rows * args.columns,
            low=0.0,
            high=1_000.0,
            dtype=np.float64,
            seed=args.seed,
        ).reshape(args.rows, args.columns)

        row_offsets = generate_uniform(
            args.columns,
            low=0.0,
            high=10.0,
            dtype=np.float64,
            seed=args.seed + 1,
        )

        column_offsets = generate_uniform(
            args.rows,
            low=0.0,
            high=10.0,
            dtype=np.float64,
            seed=args.seed + 2,
        ).reshape(args.rows, 1)

        same_shape_offsets = generate_uniform(
            args.rows * args.columns,
            low=0.0,
            high=10.0,
            dtype=np.float64,
            seed=args.seed + 3,
        ).reshape(args.rows, args.columns)

        results = benchmark_broadcasting(
            values,
            row_offsets,
            column_offsets,
            same_shape_offsets,
            iterations=args.iterations,
            warmup_iterations=args.warmup_iterations,
        )

        expected_output_bytes = estimate_output_bytes(
            values.shape,
            values.dtype,
        )

    except (AssertionError, TypeError, ValueError) as exc:
        print(f"Benchmark failed: {exc}", file=sys.stderr)
        return 1

    print("NumPy Broadcasting Benchmark")
    print("============================")
    print(f"Input shape: {values.shape}")
    print(f"Dtype: {values.dtype}")
    print(f"Input bytes: {values.nbytes:,}")
    print(f"Output bytes per operation: {expected_output_bytes:,}")
    print()

    for name, result in results.items():
        print(format_result(name, result))
        print()

    print("Broadcasted operand shapes")
    print("--------------------------")
    print(f"Input:              {values.shape}")
    print(f"Scalar:             scalar")
    print(f"Row vector:         {row_offsets.shape}")
    print(f"Column vector:      {column_offsets.shape}")
    print(f"Same-shape operand:  {same_shape_offsets.shape}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())