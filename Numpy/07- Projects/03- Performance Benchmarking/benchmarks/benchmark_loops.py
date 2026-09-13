"""Benchmark Python loops against NumPy vectorized operations."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.benchmarks import BenchmarkComparison, benchmark, benchmark_metadata, compare
from src.datasets import generate_uniform
from src.numpy_processor import scale_offset_and_clip as numpy_transform
from src.python_processor import scale_offset_and_clip as python_transform


DEFAULT_SIZE = 100_000
DEFAULT_ITERATIONS = 10
DEFAULT_WARMUP_ITERATIONS = 2
DEFAULT_FACTOR = 1.25
DEFAULT_OFFSET = 10.0
DEFAULT_MINIMUM = 0.0
DEFAULT_MAXIMUM = 1_000_000.0
DEFAULT_SEED = 42


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the benchmark."""
    parser = argparse.ArgumentParser(
        description="Benchmark Python-loop and NumPy numerical transformations.",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=DEFAULT_SIZE,
        help="Number of numeric values to benchmark.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help="Number of timed benchmark iterations.",
    )
    parser.add_argument(
        "--warmup-iterations",
        type=int,
        default=DEFAULT_WARMUP_ITERATIONS,
        help="Number of warmup executions before timing.",
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
        help="Inclusive minimum value.",
    )
    parser.add_argument(
        "--maximum",
        type=float,
        default=DEFAULT_MAXIMUM,
        help="Inclusive maximum value.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Seed used to generate reproducible benchmark input.",
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


def run_benchmark(
    values: np.ndarray,
    *,
    factor: float,
    offset: float,
    minimum: float,
    maximum: float,
    iterations: int,
    warmup_iterations: int,
) -> BenchmarkComparison:
    """Benchmark equivalent Python and NumPy transformations."""
    return compare(
        python_transform,
        numpy_transform,
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
        iterations=iterations,
        warmup_iterations=warmup_iterations,
        name="python-vs-numpy",
    )


def validate_equivalence(
    values: np.ndarray,
    *,
    factor: float,
    offset: float,
    minimum: float,
    maximum: float,
) -> None:
    """Verify that benchmark implementations produce equivalent results."""
    python_result = np.asarray(
        python_transform(
            values.tolist(),
            factor=factor,
            offset=offset,
            minimum=minimum,
            maximum=maximum,
        ),
        dtype=np.float64,
    )
    numpy_result = numpy_transform(
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
    )

    np.testing.assert_allclose(
        python_result,
        numpy_result,
        rtol=1e-12,
        atol=1e-12,
    )


def format_comparison(comparison: BenchmarkComparison) -> str:
    """Format benchmark comparison metrics for terminal output."""
    baseline = benchmark_metadata(comparison.baseline)
    candidate = benchmark_metadata(comparison.candidate)

    return "\n".join(
        [
            "Benchmark Results",
            "-----------------",
            f"Baseline: {comparison.baseline.name}",
            f"  Mean:   {baseline['mean_seconds']:.6f} s",
            f"  Median: {baseline['median_seconds']:.6f} s",
            f"  Min:    {baseline['minimum_seconds']:.6f} s",
            f"Candidate: {comparison.candidate.name}",
            f"  Mean:   {candidate['mean_seconds']:.6f} s",
            f"  Median: {candidate['median_seconds']:.6f} s",
            f"  Min:    {candidate['minimum_seconds']:.6f} s",
            f"Speedup: {comparison.speedup:.2f}x",
            f"Relative runtime: {comparison.relative_runtime:.2%}",
        ]
    )


def main() -> int:
    """Generate reproducible input, validate equivalence, and run benchmarks."""
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

        comparison = run_benchmark(
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
    print(format_comparison(comparison))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Benchmark Python loops against NumPy vectorized operations."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.benchmarks import BenchmarkComparison, benchmark, benchmark_metadata, compare
from src.datasets import generate_uniform
from src.numpy_processor import scale_offset_and_clip as numpy_transform
from src.python_processor import scale_offset_and_clip as python_transform


DEFAULT_SIZE = 100_000
DEFAULT_ITERATIONS = 10
DEFAULT_WARMUP_ITERATIONS = 2
DEFAULT_FACTOR = 1.25
DEFAULT_OFFSET = 10.0
DEFAULT_MINIMUM = 0.0
DEFAULT_MAXIMUM = 1_000_000.0
DEFAULT_SEED = 42


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the benchmark."""
    parser = argparse.ArgumentParser(
        description="Benchmark Python-loop and NumPy numerical transformations.",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=DEFAULT_SIZE,
        help="Number of numeric values to benchmark.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help="Number of timed benchmark iterations.",
    )
    parser.add_argument(
        "--warmup-iterations",
        type=int,
        default=DEFAULT_WARMUP_ITERATIONS,
        help="Number of warmup executions before timing.",
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
        help="Inclusive minimum value.",
    )
    parser.add_argument(
        "--maximum",
        type=float,
        default=DEFAULT_MAXIMUM,
        help="Inclusive maximum value.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Seed used to generate reproducible benchmark input.",
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


def run_benchmark(
    values: np.ndarray,
    *,
    factor: float,
    offset: float,
    minimum: float,
    maximum: float,
    iterations: int,
    warmup_iterations: int,
) -> BenchmarkComparison:
    """Benchmark equivalent Python and NumPy transformations."""
    return compare(
        python_transform,
        numpy_transform,
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
        iterations=iterations,
        warmup_iterations=warmup_iterations,
        name="python-vs-numpy",
    )


def validate_equivalence(
    values: np.ndarray,
    *,
    factor: float,
    offset: float,
    minimum: float,
    maximum: float,
) -> None:
    """Verify that benchmark implementations produce equivalent results."""
    python_result = np.asarray(
        python_transform(
            values.tolist(),
            factor=factor,
            offset=offset,
            minimum=minimum,
            maximum=maximum,
        ),
        dtype=np.float64,
    )
    numpy_result = numpy_transform(
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
    )

    np.testing.assert_allclose(
        python_result,
        numpy_result,
        rtol=1e-12,
        atol=1e-12,
    )


def format_comparison(comparison: BenchmarkComparison) -> str:
    """Format benchmark comparison metrics for terminal output."""
    baseline = benchmark_metadata(comparison.baseline)
    candidate = benchmark_metadata(comparison.candidate)

    return "\n".join(
        [
            "Benchmark Results",
            "-----------------",
            f"Baseline: {comparison.baseline.name}",
            f"  Mean:   {baseline['mean_seconds']:.6f} s",
            f"  Median: {baseline['median_seconds']:.6f} s",
            f"  Min:    {baseline['minimum_seconds']:.6f} s",
            f"Candidate: {comparison.candidate.name}",
            f"  Mean:   {candidate['mean_seconds']:.6f} s",
            f"  Median: {candidate['median_seconds']:.6f} s",
            f"  Min:    {candidate['minimum_seconds']:.6f} s",
            f"Speedup: {comparison.speedup:.2f}x",
            f"Relative runtime: {comparison.relative_runtime:.2%}",
        ]
    )


def main() -> int:
    """Generate reproducible input, validate equivalence, and run benchmarks."""
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

        comparison = run_benchmark(
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
    print(format_comparison(comparison))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())