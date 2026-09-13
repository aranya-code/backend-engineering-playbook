from __future__ import annotations

import argparse
import json
import sys
import time
import tracemalloc
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import pandas as pd


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Represent memory and runtime measurements for one benchmark run."""

    operation: str
    rows: int
    columns: int
    elapsed_seconds: float
    peak_memory_bytes: int
    current_memory_bytes: int

    @property
    def peak_memory_mb(self) -> float:
        """Return peak traced memory usage in mebibytes."""
        return self.peak_memory_bytes / (1024 * 1024)

    @property
    def current_memory_mb(self) -> float:
        """Return current traced memory usage in mebibytes."""
        return self.current_memory_bytes / (1024 * 1024)


def _build_dataset(
    rows: int,
) -> pd.DataFrame:
    """Build a representative transaction dataset for benchmarking."""
    if rows <= 0:
        raise ValueError(
            "rows must be greater than zero."
        )

    regions = (
        "north",
        "south",
        "east",
        "west",
    )
    statuses = (
        "paid",
        "pending",
        "cancelled",
    )
    products = (
        "laptop",
        "phone",
        "tablet",
        "monitor",
    )

    return pd.DataFrame(
        {
            "order_id": [
                f"ORD-{index:010d}"
                for index in range(rows)
            ],
            "customer_id": [
                f"CUST-{index % 100_000:08d}"
                for index in range(rows)
            ],
            "region": [
                regions[index % len(regions)]
                for index in range(rows)
            ],
            "status": [
                statuses[index % len(statuses)]
                for index in range(rows)
            ],
            "product": [
                products[index % len(products)]
                for index in range(rows)
            ],
            "quantity": [
                (index % 10) + 1
                for index in range(rows)
            ],
            "amount": [
                float((index % 500) + 50)
                for index in range(rows)
            ],
        }
    )


def _measure(
    operation: str,
    frame: pd.DataFrame,
    function: Callable[
        [pd.DataFrame],
        pd.DataFrame,
    ],
) -> BenchmarkResult:
    """Measure runtime and Python-level peak allocations for an operation."""
    tracemalloc.start()
    started_at = time.perf_counter()

    result = function(
        frame
    )

    elapsed_seconds = (
        time.perf_counter()
        - started_at
    )

    current_memory, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if not isinstance(
        result,
        pd.DataFrame,
    ):
        raise TypeError(
            "Benchmark operation must return a pandas DataFrame."
        )

    return BenchmarkResult(
        operation=operation,
        rows=len(result),
        columns=len(result.columns),
        elapsed_seconds=elapsed_seconds,
        peak_memory_bytes=peak_memory,
        current_memory_bytes=current_memory,
    )


def benchmark_copy(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark the cost of making a deep DataFrame copy."""
    return frame.copy(
        deep=True
    )


def benchmark_numeric_conversion(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark vectorized numeric conversion across value columns."""
    result = frame.copy(
        deep=False
    )

    result["quantity"] = pd.to_numeric(
        result["quantity"],
        errors="coerce",
    )
    result["amount"] = pd.to_numeric(
        result["amount"],
        errors="coerce",
    )

    return result


def benchmark_categorical_conversion(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark categorical encoding for low-cardinality string columns."""
    result = frame.copy(
        deep=False
    )

    for column in (
        "region",
        "status",
        "product",
    ):
        result[column] = result[column].astype(
            "category"
        )

    return result


def benchmark_filter(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark a vectorized boolean filter."""
    return frame.loc[
        frame["amount"].ge(250)
        & frame["status"].eq("paid")
    ].copy()


def benchmark_groupby(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark a production-style grouped revenue aggregation."""
    return (
        frame.groupby(
            ["region", "product"],
            observed=True,
            sort=False,
        )
        .agg(
            order_count=(
                "order_id",
                "count",
            ),
            revenue=(
                "amount",
                "sum",
            ),
            quantity=(
                "quantity",
                "sum",
            ),
        )
        .reset_index()
    )


def benchmark_sort(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark sorting by revenue in descending order."""
    return frame.sort_values(
        "amount",
        ascending=False,
        kind="stable",
    ).reset_index(
        drop=True
    )


def benchmark_memory_optimization(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark common dtype optimizations for memory efficiency."""
    result = frame.copy(
        deep=True
    )

    for column in (
        "region",
        "status",
        "product",
    ):
        result[column] = result[column].astype(
            "category"
        )

    result["quantity"] = pd.to_numeric(
        result["quantity"],
        downcast="integer",
    )
    result["amount"] = pd.to_numeric(
        result["amount"],
        downcast="float",
    )

    return result


def _deep_memory_bytes(
    frame: pd.DataFrame,
) -> int:
    """Return the deep DataFrame memory footprint."""
    return int(
        frame.memory_usage(
            index=True,
            deep=True,
        ).sum()
    )


def _memory_comparison(
    original: pd.DataFrame,
    optimized: pd.DataFrame,
) -> dict[str, int | float]:
    """Compare deep memory usage before and after dtype optimization."""
    original_bytes = _deep_memory_bytes(
        original
    )
    optimized_bytes = _deep_memory_bytes(
        optimized
    )

    saved_bytes = (
        original_bytes
        - optimized_bytes
    )

    reduction_percent = (
        saved_bytes / original_bytes * 100
        if original_bytes
        else 0.0
    )

    return {
        "original_memory_bytes": original_bytes,
        "optimized_memory_bytes": optimized_bytes,
        "saved_memory_bytes": saved_bytes,
        "reduction_percent": reduction_percent,
    }


def run_benchmark(
    *,
    rows: int,
) -> tuple[
    list[BenchmarkResult],
    dict[str, int | float],
]:
    """Build benchmark data and execute the configured memory scenarios."""
    frame = _build_dataset(
        rows
    )

    memory_results = {
        "rows": rows,
        "columns": len(frame.columns),
        "raw_memory_bytes": _deep_memory_bytes(
            frame
        ),
        "raw_memory_mb": (
            _deep_memory_bytes(frame)
            / (1024 * 1024)
        ),
    }

    benchmark_operations: tuple[
        tuple[
            str,
            Callable[
                [pd.DataFrame],
                pd.DataFrame,
            ],
        ],
        ...,
    ] = (
        (
            "copy",
            benchmark_copy,
        ),
        (
            "numeric_conversion",
            benchmark_numeric_conversion,
        ),
        (
            "categorical_conversion",
            benchmark_categorical_conversion,
        ),
        (
            "filter",
            benchmark_filter,
        ),
        (
            "groupby",
            benchmark_groupby,
        ),
        (
            "sort",
            benchmark_sort,
        ),
        (
            "memory_optimization",
            benchmark_memory_optimization,
        ),
    )

    results: list[BenchmarkResult] = []

    for operation, function in benchmark_operations:
        results.append(
            _measure(
                operation,
                frame,
                function,
            )
        )

    optimized = benchmark_memory_optimization(
        frame
    )

    memory_results.update(
        _memory_comparison(
            frame,
            optimized,
        )
    )

    return (
        results,
        memory_results,
    )


def write_results(
    results: list[BenchmarkResult],
    memory_comparison: dict[str, int | float],
    output_path: Path,
) -> Path:
    """Write benchmark measurements as structured JSON."""
    output_path = (
        Path(output_path)
        .expanduser()
        .resolve()
    )
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "benchmarks": [
            {
                **asdict(result),
                "peak_memory_mb": result.peak_memory_mb,
                "current_memory_mb": result.current_memory_mb,
            }
            for result in results
        ],
        "memory_comparison": memory_comparison,
    }

    temporary_path = output_path.with_suffix(
        ".tmp"
    )

    try:
        temporary_path.write_text(
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        temporary_path.replace(
            output_path
        )
    except OSError as exc:
        try:
            temporary_path.unlink(
                missing_ok=True
            )
        except OSError:
            pass

        raise RuntimeError(
            f"Failed to write benchmark results: {output_path}"
        ) from exc

    return output_path


def _build_parser() -> argparse.ArgumentParser:
    """Build the benchmark CLI."""
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark Pandas memory behavior and common large-dataset "
            "operations."
        )
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=100_000,
        help="Number of synthetic rows to generate.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmarks") / "memory_results.json",
        help="Path for the JSON benchmark report.",
    )

    return parser


def main(
    argv: list[str] | None = None,
) -> int:
    """Run the benchmark CLI and return a process-compatible exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        results, memory_comparison = run_benchmark(
            rows=args.rows
        )
        output_path = write_results(
            results,
            memory_comparison,
            args.output,
        )
    except (
        OSError,
        TypeError,
        ValueError,
        RuntimeError,
    ) as exc:
        parser.error(
            str(exc)
        )
        return 2

    print(
        f"Benchmark rows: {args.rows:,}"
    )
    print(
        f"Raw DataFrame memory: "
        f"{memory_comparison['raw_memory_mb']:.2f} MiB"
    )
    print(
        f"Optimized DataFrame memory: "
        f"{memory_comparison['optimized_memory_bytes'] / (1024 * 1024):.2f} MiB"
    )
    print(
        f"Memory reduction: "
        f"{memory_comparison['reduction_percent']:.2f}%"
    )
    print()
    print(
        f"{'Operation':<24}"
        f"{'Rows':>12}"
        f"{'Elapsed (s)':>16}"
        f"{'Peak (MiB)':>16}"
    )
    print(
        "-" * 68
    )

    for result in results:
        print(
            f"{result.operation:<24}"
            f"{result.rows:>12,}"
            f"{result.elapsed_seconds:>16.4f}"
            f"{result.peak_memory_mb:>16.2f}"
        )

    print()
    print(
        f"Results written to: {output_path}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main(
            sys.argv[1:]
        )
    )

from __future__ import annotations

import argparse
import json
import sys
import time
import tracemalloc
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import pandas as pd


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Represent memory and runtime measurements for one benchmark run."""

    operation: str
    rows: int
    columns: int
    elapsed_seconds: float
    peak_memory_bytes: int
    current_memory_bytes: int

    @property
    def peak_memory_mb(self) -> float:
        """Return peak traced memory usage in mebibytes."""
        return self.peak_memory_bytes / (1024 * 1024)

    @property
    def current_memory_mb(self) -> float:
        """Return current traced memory usage in mebibytes."""
        return self.current_memory_bytes / (1024 * 1024)


def _build_dataset(
    rows: int,
) -> pd.DataFrame:
    """Build a representative transaction dataset for benchmarking."""
    if rows <= 0:
        raise ValueError(
            "rows must be greater than zero."
        )

    regions = (
        "north",
        "south",
        "east",
        "west",
    )
    statuses = (
        "paid",
        "pending",
        "cancelled",
    )
    products = (
        "laptop",
        "phone",
        "tablet",
        "monitor",
    )

    return pd.DataFrame(
        {
            "order_id": [
                f"ORD-{index:010d}"
                for index in range(rows)
            ],
            "customer_id": [
                f"CUST-{index % 100_000:08d}"
                for index in range(rows)
            ],
            "region": [
                regions[index % len(regions)]
                for index in range(rows)
            ],
            "status": [
                statuses[index % len(statuses)]
                for index in range(rows)
            ],
            "product": [
                products[index % len(products)]
                for index in range(rows)
            ],
            "quantity": [
                (index % 10) + 1
                for index in range(rows)
            ],
            "amount": [
                float((index % 500) + 50)
                for index in range(rows)
            ],
        }
    )


def _measure(
    operation: str,
    frame: pd.DataFrame,
    function: Callable[
        [pd.DataFrame],
        pd.DataFrame,
    ],
) -> BenchmarkResult:
    """Measure runtime and Python-level peak allocations for an operation."""
    tracemalloc.start()
    started_at = time.perf_counter()

    result = function(
        frame
    )

    elapsed_seconds = (
        time.perf_counter()
        - started_at
    )

    current_memory, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if not isinstance(
        result,
        pd.DataFrame,
    ):
        raise TypeError(
            "Benchmark operation must return a pandas DataFrame."
        )

    return BenchmarkResult(
        operation=operation,
        rows=len(result),
        columns=len(result.columns),
        elapsed_seconds=elapsed_seconds,
        peak_memory_bytes=peak_memory,
        current_memory_bytes=current_memory,
    )


def benchmark_copy(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark the cost of making a deep DataFrame copy."""
    return frame.copy(
        deep=True
    )


def benchmark_numeric_conversion(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark vectorized numeric conversion across value columns."""
    result = frame.copy(
        deep=False
    )

    result["quantity"] = pd.to_numeric(
        result["quantity"],
        errors="coerce",
    )
    result["amount"] = pd.to_numeric(
        result["amount"],
        errors="coerce",
    )

    return result


def benchmark_categorical_conversion(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark categorical encoding for low-cardinality string columns."""
    result = frame.copy(
        deep=False
    )

    for column in (
        "region",
        "status",
        "product",
    ):
        result[column] = result[column].astype(
            "category"
        )

    return result


def benchmark_filter(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark a vectorized boolean filter."""
    return frame.loc[
        frame["amount"].ge(250)
        & frame["status"].eq("paid")
    ].copy()


def benchmark_groupby(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark a production-style grouped revenue aggregation."""
    return (
        frame.groupby(
            ["region", "product"],
            observed=True,
            sort=False,
        )
        .agg(
            order_count=(
                "order_id",
                "count",
            ),
            revenue=(
                "amount",
                "sum",
            ),
            quantity=(
                "quantity",
                "sum",
            ),
        )
        .reset_index()
    )


def benchmark_sort(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark sorting by revenue in descending order."""
    return frame.sort_values(
        "amount",
        ascending=False,
        kind="stable",
    ).reset_index(
        drop=True
    )


def benchmark_memory_optimization(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark common dtype optimizations for memory efficiency."""
    result = frame.copy(
        deep=True
    )

    for column in (
        "region",
        "status",
        "product",
    ):
        result[column] = result[column].astype(
            "category"
        )

    result["quantity"] = pd.to_numeric(
        result["quantity"],
        downcast="integer",
    )
    result["amount"] = pd.to_numeric(
        result["amount"],
        downcast="float",
    )

    return result


def _deep_memory_bytes(
    frame: pd.DataFrame,
) -> int:
    """Return the deep DataFrame memory footprint."""
    return int(
        frame.memory_usage(
            index=True,
            deep=True,
        ).sum()
    )


def _memory_comparison(
    original: pd.DataFrame,
    optimized: pd.DataFrame,
) -> dict[str, int | float]:
    """Compare deep memory usage before and after dtype optimization."""
    original_bytes = _deep_memory_bytes(
        original
    )
    optimized_bytes = _deep_memory_bytes(
        optimized
    )

    saved_bytes = (
        original_bytes
        - optimized_bytes
    )

    reduction_percent = (
        saved_bytes / original_bytes * 100
        if original_bytes
        else 0.0
    )

    return {
        "original_memory_bytes": original_bytes,
        "optimized_memory_bytes": optimized_bytes,
        "saved_memory_bytes": saved_bytes,
        "reduction_percent": reduction_percent,
    }


def run_benchmark(
    *,
    rows: int,
) -> tuple[
    list[BenchmarkResult],
    dict[str, int | float],
]:
    """Build benchmark data and execute the configured memory scenarios."""
    frame = _build_dataset(
        rows
    )

    memory_results = {
        "rows": rows,
        "columns": len(frame.columns),
        "raw_memory_bytes": _deep_memory_bytes(
            frame
        ),
        "raw_memory_mb": (
            _deep_memory_bytes(frame)
            / (1024 * 1024)
        ),
    }

    benchmark_operations: tuple[
        tuple[
            str,
            Callable[
                [pd.DataFrame],
                pd.DataFrame,
            ],
        ],
        ...,
    ] = (
        (
            "copy",
            benchmark_copy,
        ),
        (
            "numeric_conversion",
            benchmark_numeric_conversion,
        ),
        (
            "categorical_conversion",
            benchmark_categorical_conversion,
        ),
        (
            "filter",
            benchmark_filter,
        ),
        (
            "groupby",
            benchmark_groupby,
        ),
        (
            "sort",
            benchmark_sort,
        ),
        (
            "memory_optimization",
            benchmark_memory_optimization,
        ),
    )

    results: list[BenchmarkResult] = []

    for operation, function in benchmark_operations:
        results.append(
            _measure(
                operation,
                frame,
                function,
            )
        )

    optimized = benchmark_memory_optimization(
        frame
    )

    memory_results.update(
        _memory_comparison(
            frame,
            optimized,
        )
    )

    return (
        results,
        memory_results,
    )


def write_results(
    results: list[BenchmarkResult],
    memory_comparison: dict[str, int | float],
    output_path: Path,
) -> Path:
    """Write benchmark measurements as structured JSON."""
    output_path = (
        Path(output_path)
        .expanduser()
        .resolve()
    )
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "benchmarks": [
            {
                **asdict(result),
                "peak_memory_mb": result.peak_memory_mb,
                "current_memory_mb": result.current_memory_mb,
            }
            for result in results
        ],
        "memory_comparison": memory_comparison,
    }

    temporary_path = output_path.with_suffix(
        ".tmp"
    )

    try:
        temporary_path.write_text(
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        temporary_path.replace(
            output_path
        )
    except OSError as exc:
        try:
            temporary_path.unlink(
                missing_ok=True
            )
        except OSError:
            pass

        raise RuntimeError(
            f"Failed to write benchmark results: {output_path}"
        ) from exc

    return output_path


def _build_parser() -> argparse.ArgumentParser:
    """Build the benchmark CLI."""
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark Pandas memory behavior and common large-dataset "
            "operations."
        )
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=100_000,
        help="Number of synthetic rows to generate.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmarks") / "memory_results.json",
        help="Path for the JSON benchmark report.",
    )

    return parser


def main(
    argv: list[str] | None = None,
) -> int:
    """Run the benchmark CLI and return a process-compatible exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        results, memory_comparison = run_benchmark(
            rows=args.rows
        )
        output_path = write_results(
            results,
            memory_comparison,
            args.output,
        )
    except (
        OSError,
        TypeError,
        ValueError,
        RuntimeError,
    ) as exc:
        parser.error(
            str(exc)
        )
        return 2

    print(
        f"Benchmark rows: {args.rows:,}"
    )
    print(
        f"Raw DataFrame memory: "
        f"{memory_comparison['raw_memory_mb']:.2f} MiB"
    )
    print(
        f"Optimized DataFrame memory: "
        f"{memory_comparison['optimized_memory_bytes'] / (1024 * 1024):.2f} MiB"
    )
    print(
        f"Memory reduction: "
        f"{memory_comparison['reduction_percent']:.2f}%"
    )
    print()
    print(
        f"{'Operation':<24}"
        f"{'Rows':>12}"
        f"{'Elapsed (s)':>16}"
        f"{'Peak (MiB)':>16}"
    )
    print(
        "-" * 68
    )

    for result in results:
        print(
            f"{result.operation:<24}"
            f"{result.rows:>12,}"
            f"{result.elapsed_seconds:>16.4f}"
            f"{result.peak_memory_mb:>16.2f}"
        )

    print()
    print(
        f"Results written to: {output_path}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main(
            sys.argv[1:]
        )
    )