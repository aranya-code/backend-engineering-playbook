"""Benchmark numerical processing performance across NumPy dtypes."""

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
from src.numpy_processor import scale_offset_and_clip


DEFAULT_SIZE = 1_000_000
DEFAULT_ITERATIONS = 10
DEFAULT_WARMUP_ITERATIONS = 2
DEFAULT_FACTOR = 1.25
DEFAULT_OFFSET = 10.0
DEFAULT_MINIMUM = 0.0
DEFAULT_MAXIMUM = 1_000_000.0
DEFAULT_SEED = 42

BENCHMARK_DTYPES = (
    np.dtype(np.float32),
    np.dtype(np.float64),
)


def process_dtype(
    values: np.ndarray,
    *,
    factor: float,
    offset: float,
    minimum: float,
    maximum: float,
) -> np.ndarray:
    """Apply the same vectorized transformation to a dtype-specific array."""
    return scale_offset_and_clip(
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
    )


def benchmark_dtype(
    values: np.ndarray,
    *,
    factor: float,
    offset: float,
    minimum: float,
    maximum: float,
    iterations: int,
    warmup_iterations: int,
) -> BenchmarkResult:
    """Measure transformation performance for one NumPy dtype."""
    return benchmark(
        process_dtype,
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
        name=f"dtype-{values.dtype}",
        iterations=iterations,
        warmup_iterations=warmup_iterations,
    )


def validate_results(
    baseline_values: np.ndarray,
    candidate_values: np.ndarray,
    *,
    rtol: float = 1e-5,
    atol: float = 1e-6,
) -> None:
    """Verify that dtype variants produce numerically compatible results."""
    baseline = process_dtype(
        baseline_values,
        factor=DEFAULT_FACTOR,
        offset=DEFAULT_OFFSET,
        minimum=DEFAULT_MINIMUM,
        maximum=DEFAULT_MAXIMUM,
    )
    candidate = process_dtype(
        candidate_values,
        factor=DEFAULT_FACTOR,
        offset=DEFAULT_OFFSET,
        minimum=DEFAULT_MINIMUM,
        maximum=DEFAULT_MAXIMUM,
    )

    np.testing.assert_allclose(
        baseline,
        candidate,
        rtol=rtol,
        atol=atol,
    )


def format_result(result: BenchmarkResult, values: np.ndarray) -> str:
    """Format timing and memory characteristics for terminal output."""
    metrics = benchmark_metadata(result)
    return "\n".join(
        [
            f"{result.name}:",
            f"  dtype: {values.dtype}",
            f"  itemsize: {values.itemsize} bytes",
            f"  nbytes: {values.nbytes:,} bytes",
            f"  mean: {metrics['mean_seconds']:.6f} s",
            f"  median: {metrics['median_seconds']:.6f} s",
            f"  minimum: {metrics['minimum_seconds']:.6f} s",
            f"  operations/sec: {metrics['operations_per_second']:.2f}",
        ]
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the dtype benchmark."""
    parser = argparse.ArgumentParser(
        description="Benchmark NumPy numerical processing across dtypes.",
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
        "--factor",
        type=float,
        default=DEFAULT_FACTOR,
        help="Multiplication factor.",
    )
    parser.add_argument(
        "--offset",
        type=float,
        default=DEFAULT_OFFSET,
        help="Additive offset.",
    )
    parser.add_argument(
        "--minimum",
        type=float,
        default=DEFAULT_MINIMUM,
        help="Inclusive minimum output value.",
    )
    parser.add_argument(
        "--maximum",
        type=float,
        default=DEFAULT_MAXIMUM,
        help="Inclusive maximum output value.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Seed for reproducible input generation.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    """Validate benchmark configuration before allocating data."""
    if args.size <= 0:
        raise ValueError("size must be positive.")
    if args.iterations <= 0:
        raise ValueError("iterations must be positive.")
    if args.warmup_iterations < 0:
        raise ValueError("warmup-iterations must be non-negative.")
    if not np.isfinite(args.factor):
        raise ValueError("factor must be finite.")
    if not np.isfinite(args.offset):
        raise ValueError("offset must be finite.")
    if not np.isfinite(args.minimum):
        raise ValueError("minimum must be finite.")
    if not np.isfinite(args.maximum):
        raise ValueError("maximum must be finite.")
    if args.minimum > args.maximum:
        raise ValueError("minimum must not exceed maximum.")


def main() -> int:
    """Generate equivalent datasets and benchmark each supported dtype."""
    args = parse_args()

    try:
        validate_args(args)

        base_values = generate_uniform(
            args.size,
            low=0.0,
            high=min(args.maximum, 1_000.0),
            dtype=np.float64,
            seed=args.seed,
        )

        dtype_values = {
            dtype: base_values.astype(dtype, copy=False)
            for dtype in BENCHMARK_DTYPES
        }

        reference_values = dtype_values[np.dtype(np.float64)]

        for dtype, values in dtype_values.items():
            if dtype != np.dtype(np.float64):
                validate_results(reference_values, values)

        print("NumPy Dtype Benchmark")
        print("=====================")
        print(f"Dataset size: {args.size:,}")
        print(f"Iterations: {args.iterations}")
        print(f"Warmup iterations: {args.warmup_iterations}")
        print()

        results: list[BenchmarkResult] = []

        for dtype, values in dtype_values.items():
            result = benchmark_dtype(
                values,
                factor=args.factor,
                offset=args.offset,
                minimum=args.minimum,
                maximum=args.maximum,
                iterations=args.iterations,
                warmup_iterations=args.warmup_iterations,
            )
            results.append(result)
            print(format_result(result, values))
            print()

        if len(results) >= 2:
            baseline = results[0]
            candidate = results[1]

            speedup = (
                baseline.mean_seconds / candidate.mean_seconds
                if candidate.mean_seconds > 0.0
                else float("inf")
            )
            memory_ratio = (
                dtype_values[benchmark_dtypes[0]].nbytes
                / dtype_values[benchmark_dtypes[1]].nbytes
            )

            print(
                f"Second dtype relative runtime: "
                f"{candidate.mean_seconds / baseline.mean_seconds:.2%}"
            )
            print(f"First/second dtype memory ratio: {memory_ratio:.2f}x")
            print(f"Second dtype speedup vs first: {speedup:.2f}x")

    except (AssertionError, TypeError, ValueError) as exc:
        print(f"Benchmark failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Benchmark numerical processing performance across NumPy dtypes."""

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
from src.numpy_processor import scale_offset_and_clip


DEFAULT_SIZE = 1_000_000
DEFAULT_ITERATIONS = 10
DEFAULT_WARMUP_ITERATIONS = 2
DEFAULT_FACTOR = 1.25
DEFAULT_OFFSET = 10.0
DEFAULT_MINIMUM = 0.0
DEFAULT_MAXIMUM = 1_000_000.0
DEFAULT_SEED = 42

BENCHMARK_DTYPES = (
    np.dtype(np.float32),
    np.dtype(np.float64),
)


def process_dtype(
    values: np.ndarray,
    *,
    factor: float,
    offset: float,
    minimum: float,
    maximum: float,
) -> np.ndarray:
    """Apply the same vectorized transformation to a dtype-specific array."""
    return scale_offset_and_clip(
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
    )


def benchmark_dtype(
    values: np.ndarray,
    *,
    factor: float,
    offset: float,
    minimum: float,
    maximum: float,
    iterations: int,
    warmup_iterations: int,
) -> BenchmarkResult:
    """Measure transformation performance for one NumPy dtype."""
    return benchmark(
        process_dtype,
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
        name=f"dtype-{values.dtype}",
        iterations=iterations,
        warmup_iterations=warmup_iterations,
    )


def validate_results(
    baseline_values: np.ndarray,
    candidate_values: np.ndarray,
    *,
    rtol: float = 1e-5,
    atol: float = 1e-6,
) -> None:
    """Verify that dtype variants produce numerically compatible results."""
    baseline = process_dtype(
        baseline_values,
        factor=DEFAULT_FACTOR,
        offset=DEFAULT_OFFSET,
        minimum=DEFAULT_MINIMUM,
        maximum=DEFAULT_MAXIMUM,
    )
    candidate = process_dtype(
        candidate_values,
        factor=DEFAULT_FACTOR,
        offset=DEFAULT_OFFSET,
        minimum=DEFAULT_MINIMUM,
        maximum=DEFAULT_MAXIMUM,
    )

    np.testing.assert_allclose(
        baseline,
        candidate,
        rtol=rtol,
        atol=atol,
    )


def format_result(result: BenchmarkResult, values: np.ndarray) -> str:
    """Format timing and memory characteristics for terminal output."""
    metrics = benchmark_metadata(result)
    return "\n".join(
        [
            f"{result.name}:",
            f"  dtype: {values.dtype}",
            f"  itemsize: {values.itemsize} bytes",
            f"  nbytes: {values.nbytes:,} bytes",
            f"  mean: {metrics['mean_seconds']:.6f} s",
            f"  median: {metrics['median_seconds']:.6f} s",
            f"  minimum: {metrics['minimum_seconds']:.6f} s",
            f"  operations/sec: {metrics['operations_per_second']:.2f}",
        ]
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the dtype benchmark."""
    parser = argparse.ArgumentParser(
        description="Benchmark NumPy numerical processing across dtypes.",
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
        "--factor",
        type=float,
        default=DEFAULT_FACTOR,
        help="Multiplication factor.",
    )
    parser.add_argument(
        "--offset",
        type=float,
        default=DEFAULT_OFFSET,
        help="Additive offset.",
    )
    parser.add_argument(
        "--minimum",
        type=float,
        default=DEFAULT_MINIMUM,
        help="Inclusive minimum output value.",
    )
    parser.add_argument(
        "--maximum",
        type=float,
        default=DEFAULT_MAXIMUM,
        help="Inclusive maximum output value.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Seed for reproducible input generation.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    """Validate benchmark configuration before allocating data."""
    if args.size <= 0:
        raise ValueError("size must be positive.")
    if args.iterations <= 0:
        raise ValueError("iterations must be positive.")
    if args.warmup_iterations < 0:
        raise ValueError("warmup-iterations must be non-negative.")
    if not np.isfinite(args.factor):
        raise ValueError("factor must be finite.")
    if not np.isfinite(args.offset):
        raise ValueError("offset must be finite.")
    if not np.isfinite(args.minimum):
        raise ValueError("minimum must be finite.")
    if not np.isfinite(args.maximum):
        raise ValueError("maximum must be finite.")
    if args.minimum > args.maximum:
        raise ValueError("minimum must not exceed maximum.")


def main() -> int:
    """Generate equivalent datasets and benchmark each supported dtype."""
    args = parse_args()

    try:
        validate_args(args)

        base_values = generate_uniform(
            args.size,
            low=0.0,
            high=min(args.maximum, 1_000.0),
            dtype=np.float64,
            seed=args.seed,
        )

        dtype_values = {
            dtype: base_values.astype(dtype, copy=False)
            for dtype in BENCHMARK_DTYPES
        }

        reference_values = dtype_values[np.dtype(np.float64)]

        for dtype, values in dtype_values.items():
            if dtype != np.dtype(np.float64):
                validate_results(reference_values, values)

        print("NumPy Dtype Benchmark")
        print("=====================")
        print(f"Dataset size: {args.size:,}")
        print(f"Iterations: {args.iterations}")
        print(f"Warmup iterations: {args.warmup_iterations}")
        print()

        results: list[BenchmarkResult] = []

        for dtype, values in dtype_values.items():
            result = benchmark_dtype(
                values,
                factor=args.factor,
                offset=args.offset,
                minimum=args.minimum,
                maximum=args.maximum,
                iterations=args.iterations,
                warmup_iterations=args.warmup_iterations,
            )
            results.append(result)
            print(format_result(result, values))
            print()

        if len(results) >= 2:
            baseline = results[0]
            candidate = results[1]

            speedup = (
                baseline.mean_seconds / candidate.mean_seconds
                if candidate.mean_seconds > 0.0
                else float("inf")
            )
            memory_ratio = (
                dtype_values[benchmark_dtypes[0]].nbytes
                / dtype_values[benchmark_dtypes[1]].nbytes
            )

            print(
                f"Second dtype relative runtime: "
                f"{candidate.mean_seconds / baseline.mean_seconds:.2%}"
            )
            print(f"First/second dtype memory ratio: {memory_ratio:.2f}x")
            print(f"Second dtype speedup vs first: {speedup:.2f}x")

    except (AssertionError, TypeError, ValueError) as exc:
        print(f"Benchmark failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())