"""Benchmark vectorized NumPy transformation strategies."""

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


DEFAULT_SIZE = 100_000
DEFAULT_ITERATIONS = 10
DEFAULT_WARMUP_ITERATIONS = 2
DEFAULT_FACTOR = 1.25
DEFAULT_OFFSET = 10.0
DEFAULT_MINIMUM = 0.0
DEFAULT_MAXIMUM = 1_000_000.0
DEFAULT_SEED = 42


def vectorized_pipeline(
    values: np.ndarray,
    *,
    factor: float,
    offset: float,
    minimum: float,
    maximum: float,
) -> np.ndarray:
    """Apply the transformation through separate vectorized operations."""
    scaled = values * factor
    shifted = scaled + offset
    return np.clip(shifted, minimum, maximum)


def fused_pipeline(
    values: np.ndarray,
    *,
    factor: float,
    offset: float,
    minimum: float,
    maximum: float,
) -> np.ndarray:
    """Apply the project's composite NumPy transformation."""
    return scale_offset_and_clip(
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
    )


def benchmark_strategies(
    values: np.ndarray,
    *,
    factor: float,
    offset: float,
    minimum: float,
    maximum: float,
    iterations: int,
    warmup_iterations: int,
) -> tuple[BenchmarkResult, BenchmarkResult]:
    """Benchmark separate vectorized stages against the composite implementation."""
    vectorized_result = benchmark(
        vectorized_pipeline,
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
        name="separate-vectorized-operations",
        iterations=iterations,
        warmup_iterations=warmup_iterations,
    )

    fused_result = benchmark(
        fused_pipeline,
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
        name="composite-vectorized-operation",
        iterations=iterations,
        warmup_iterations=warmup_iterations,
    )

    return vectorized_result, fused_result


def validate_equivalence(
    values: np.ndarray,
    *,
    factor: float,
    offset: float,
    minimum: float,
    maximum: float,
) -> None:
    """Verify that both vectorized strategies return equivalent arrays."""
    vectorized_result = vectorized_pipeline(
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
    )
    fused_result = fused_pipeline(
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
    )

    np.testing.assert_allclose(
        vectorized_result,
        fused_result,
        rtol=1e-12,
        atol=1e-12,
    )


def format_results(
    vectorized_result: BenchmarkResult,
    fused_result: BenchmarkResult,
) -> str:
    """Format benchmark metrics for terminal output."""
    vectorized_metrics = benchmark_metadata(vectorized_result)
    fused_metrics = benchmark_metadata(fused_result)

    baseline_mean = vectorized_result.mean_seconds
    candidate_mean = fused_result.mean_seconds
    speedup = (
        baseline_mean / candidate_mean
        if candidate_mean > 0.0
        else float("inf")
    )
    relative_runtime = (
        candidate_mean / baseline_mean
        if baseline_mean > 0.0
        else float("inf")
    )

    return "\n".join(
        [
            "Vectorization Benchmark",
            "-----------------------",
            f"Separate operations: {vectorized_result.name}",
            f"  Mean:   {vectorized_metrics['mean_seconds']:.6f} s",
            f"  Median: {vectorized_metrics['median_seconds']:.6f} s",
            f"  Min:    {vectorized_metrics['minimum_seconds']:.6f} s",
            f"Composite operation: {fused_result.name}",
            f"  Mean:   {fused_metrics['mean_seconds']:.6f} s",
            f"  Median: {fused_metrics['median_seconds']:.6f} s",
            f"  Min:    {fused_metrics['minimum_seconds']:.6f} s",
            f"Composite speedup: {speedup:.2f}x",
            f"Composite relative runtime: {relative_runtime:.2%}",
        ]
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the benchmark."""
    parser = argparse.ArgumentParser(
        description="Benchmark alternative vectorized NumPy transformation strategies.",
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
    """Validate benchmark parameters before dataset allocation."""
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
    """Generate input, validate equivalent behavior, and run the benchmark."""
    args = parse_args()

    try:
        validate_args(args)

        values = generate_uniform(
            args.size,
            low=0.0,
            high=min(args.maximum, 1_000.0),
            dtype=np.float64,
            seed=args.seed,
        )

        validate_equivalence(
            values,
            factor=args.factor,
            offset=args.offset,
            minimum=args.minimum,
            maximum=args.maximum,
        )

        vectorized_result, fused_result = benchmark_strategies(
            values,
            factor=args.factor,
            offset=args.offset,
            minimum=args.minimum,
            maximum=args.maximum,
            iterations=args.iterations,
            warmup_iterations=args.warmup_iterations,
        )

    except (AssertionError, TypeError, ValueError) as exc:
        print(f"Benchmark failed: {exc}", file=sys.stderr)
        return 1

    print(f"Dataset size: {args.size:,}")
    print(f"Dtype: {values.dtype}")
    print(f"Input bytes: {values.nbytes:,}")
    print(format_results(vectorized_result, fused_result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Benchmark vectorized NumPy transformation strategies."""

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


DEFAULT_SIZE = 100_000
DEFAULT_ITERATIONS = 10
DEFAULT_WARMUP_ITERATIONS = 2
DEFAULT_FACTOR = 1.25
DEFAULT_OFFSET = 10.0
DEFAULT_MINIMUM = 0.0
DEFAULT_MAXIMUM = 1_000_000.0
DEFAULT_SEED = 42


def vectorized_pipeline(
    values: np.ndarray,
    *,
    factor: float,
    offset: float,
    minimum: float,
    maximum: float,
) -> np.ndarray:
    """Apply the transformation through separate vectorized operations."""
    scaled = values * factor
    shifted = scaled + offset
    return np.clip(shifted, minimum, maximum)


def fused_pipeline(
    values: np.ndarray,
    *,
    factor: float,
    offset: float,
    minimum: float,
    maximum: float,
) -> np.ndarray:
    """Apply the project's composite NumPy transformation."""
    return scale_offset_and_clip(
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
    )


def benchmark_strategies(
    values: np.ndarray,
    *,
    factor: float,
    offset: float,
    minimum: float,
    maximum: float,
    iterations: int,
    warmup_iterations: int,
) -> tuple[BenchmarkResult, BenchmarkResult]:
    """Benchmark separate vectorized stages against the composite implementation."""
    vectorized_result = benchmark(
        vectorized_pipeline,
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
        name="separate-vectorized-operations",
        iterations=iterations,
        warmup_iterations=warmup_iterations,
    )

    fused_result = benchmark(
        fused_pipeline,
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
        name="composite-vectorized-operation",
        iterations=iterations,
        warmup_iterations=warmup_iterations,
    )

    return vectorized_result, fused_result


def validate_equivalence(
    values: np.ndarray,
    *,
    factor: float,
    offset: float,
    minimum: float,
    maximum: float,
) -> None:
    """Verify that both vectorized strategies return equivalent arrays."""
    vectorized_result = vectorized_pipeline(
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
    )
    fused_result = fused_pipeline(
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
    )

    np.testing.assert_allclose(
        vectorized_result,
        fused_result,
        rtol=1e-12,
        atol=1e-12,
    )


def format_results(
    vectorized_result: BenchmarkResult,
    fused_result: BenchmarkResult,
) -> str:
    """Format benchmark metrics for terminal output."""
    vectorized_metrics = benchmark_metadata(vectorized_result)
    fused_metrics = benchmark_metadata(fused_result)

    baseline_mean = vectorized_result.mean_seconds
    candidate_mean = fused_result.mean_seconds
    speedup = (
        baseline_mean / candidate_mean
        if candidate_mean > 0.0
        else float("inf")
    )
    relative_runtime = (
        candidate_mean / baseline_mean
        if baseline_mean > 0.0
        else float("inf")
    )

    return "\n".join(
        [
            "Vectorization Benchmark",
            "-----------------------",
            f"Separate operations: {vectorized_result.name}",
            f"  Mean:   {vectorized_metrics['mean_seconds']:.6f} s",
            f"  Median: {vectorized_metrics['median_seconds']:.6f} s",
            f"  Min:    {vectorized_metrics['minimum_seconds']:.6f} s",
            f"Composite operation: {fused_result.name}",
            f"  Mean:   {fused_metrics['mean_seconds']:.6f} s",
            f"  Median: {fused_metrics['median_seconds']:.6f} s",
            f"  Min:    {fused_metrics['minimum_seconds']:.6f} s",
            f"Composite speedup: {speedup:.2f}x",
            f"Composite relative runtime: {relative_runtime:.2%}",
        ]
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the benchmark."""
    parser = argparse.ArgumentParser(
        description="Benchmark alternative vectorized NumPy transformation strategies.",
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
    """Validate benchmark parameters before dataset allocation."""
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
    """Generate input, validate equivalent behavior, and run the benchmark."""
    args = parse_args()

    try:
        validate_args(args)

        values = generate_uniform(
            args.size,
            low=0.0,
            high=min(args.maximum, 1_000.0),
            dtype=np.float64,
            seed=args.seed,
        )

        validate_equivalence(
            values,
            factor=args.factor,
            offset=args.offset,
            minimum=args.minimum,
            maximum=args.maximum,
        )

        vectorized_result, fused_result = benchmark_strategies(
            values,
            factor=args.factor,
            offset=args.offset,
            minimum=args.minimum,
            maximum=args.maximum,
            iterations=args.iterations,
            warmup_iterations=args.warmup_iterations,
        )

    except (AssertionError, TypeError, ValueError) as exc:
        print(f"Benchmark failed: {exc}", file=sys.stderr)
        return 1

    print(f"Dataset size: {args.size:,}")
    print(f"Dtype: {values.dtype}")
    print(f"Input bytes: {values.nbytes:,}")
    print(format_results(vectorized_result, fused_result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())