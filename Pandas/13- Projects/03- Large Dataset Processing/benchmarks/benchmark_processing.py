from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

from src.chunk_processor import process_chunk
from src.config import PipelineConfig
from src.transformation import transform_chunk


@dataclass(frozen=True, slots=True)
class ProcessingBenchmarkResult:
    """Represent timing and throughput measurements for one benchmark."""

    operation: str
    rows: int
    columns: int
    elapsed_seconds: float
    rows_per_second: float
    output_rows: int

    @property
    def elapsed_milliseconds(self) -> float:
        """Return elapsed processing time in milliseconds."""
        return self.elapsed_seconds * 1000.0


def _build_dataset(
    rows: int,
) -> pd.DataFrame:
    """Build a representative transactional DataFrame."""
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
            "amount": [
                float((index % 500) + 50)
                for index in range(rows)
            ],
            "quantity": [
                (index % 10) + 1
                for index in range(rows)
            ],
            "created_at": [
                pd.Timestamp(
                    "2026-01-01"
                )
                + pd.Timedelta(
                    minutes=index
                )
                for index in range(rows)
            ],
        }
    )


def _build_config() -> PipelineConfig:
    """Build a benchmark configuration with representative transformations."""
    return PipelineConfig(
        timestamp_columns=("created_at",),
        numeric_columns=(
            "amount",
            "quantity",
        ),
        identifier_columns=("order_id",),
        required_columns=("order_id",),
        categorical_columns=(
            "region",
            "status",
            "product",
        ),
        timestamp_timezone="UTC",
        drop_invalid_records=True,
        drop_duplicates=True,
        target_memory_mb=1024,
        fail_on_validation=False,
    )


def _measure(
    operation: str,
    frame: pd.DataFrame,
    function: Callable[
        [pd.DataFrame],
        pd.DataFrame,
    ],
    *,
    repetitions: int,
) -> ProcessingBenchmarkResult:
    """Measure median elapsed time across repeated processing runs."""
    if repetitions <= 0:
        raise ValueError(
            "repetitions must be greater than zero."
        )

    elapsed_times: list[float] = []
    output_rows = 0

    for _ in range(repetitions):
        started_at = time.perf_counter()

        result = function(
            frame
        )

        elapsed_times.append(
            time.perf_counter()
            - started_at
        )

        if not isinstance(
            result,
            pd.DataFrame,
        ):
            raise TypeError(
                "Benchmark operation must return a pandas DataFrame."
            )

        output_rows = len(
            result
        )

    elapsed_seconds = float(
        pd.Series(
            elapsed_times
        ).median()
    )

    rows_per_second = (
        len(frame) / elapsed_seconds
        if elapsed_seconds > 0
        else 0.0
    )

    return ProcessingBenchmarkResult(
        operation=operation,
        rows=len(frame),
        columns=len(frame.columns),
        elapsed_seconds=elapsed_seconds,
        rows_per_second=rows_per_second,
        output_rows=output_rows,
    )


def _benchmark_copy(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark a full DataFrame copy."""
    return frame.copy(
        deep=True
    )


def _benchmark_filter(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark vectorized filtering."""
    return frame.loc[
        frame["status"].eq("paid")
        & frame["amount"].ge(250)
    ].copy()


def _benchmark_sort(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark stable sorting by amount."""
    return frame.sort_values(
        "amount",
        ascending=False,
        kind="stable",
    ).reset_index(
        drop=True
    )


def _benchmark_groupby(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark grouped transactional aggregation."""
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


def _benchmark_vectorized_metric(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark a vectorized derived metric."""
    result = frame.copy(
        deep=False
    )
    result["revenue_per_unit"] = (
        result["amount"]
        / result["quantity"]
    )
    return result


def _benchmark_transform(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark the project's production transformation pipeline."""
    configuration = _build_config()

    return transform_chunk(
        frame,
        pipeline_config=configuration,
    )


def _benchmark_process_chunk(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark the chunk-processing orchestration layer."""
    configuration = _build_config()

    metadata_type = None

    try:
        from src.ingestion import ChunkMetadata

        metadata_type = ChunkMetadata
    except ImportError:
        metadata_type = None

    if metadata_type is None:
        return transform_chunk(
            frame,
            pipeline_config=configuration,
        )

    metadata = metadata_type(
        chunk_number=1,
        row_count=len(frame),
        memory_bytes=int(
            frame.memory_usage(
                index=True,
                deep=True,
            ).sum()
        ),
        columns=tuple(
            str(column)
            for column in frame.columns
        ),
    )

    result = process_chunk(
        frame,
        metadata,
        lambda chunk, _: transform_chunk(
            chunk,
            pipeline_config=configuration,
        ),
    )

    return result.data


def run_benchmark(
    *,
    rows: int,
    repetitions: int,
) -> list[ProcessingBenchmarkResult]:
    """Run representative Pandas and pipeline-processing benchmarks."""
    frame = _build_dataset(
        rows
    )

    operations: tuple[
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
            _benchmark_copy,
        ),
        (
            "filter",
            _benchmark_filter,
        ),
        (
            "sort",
            _benchmark_sort,
        ),
        (
            "groupby",
            _benchmark_groupby,
        ),
        (
            "vectorized_metric",
            _benchmark_vectorized_metric,
        ),
        (
            "transform_chunk",
            _benchmark_transform,
        ),
        (
            "process_chunk",
            _benchmark_process_chunk,
        ),
    )

    results: list[ProcessingBenchmarkResult] = []

    for operation, function in operations:
        results.append(
            _measure(
                operation,
                frame,
                function,
                repetitions=repetitions,
            )
        )

    return results


def write_results(
    results: list[ProcessingBenchmarkResult],
    output_path: Path,
) -> Path:
    """Write benchmark results as structured JSON."""
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
                "elapsed_milliseconds": (
                    result.elapsed_milliseconds
                ),
            }
            for result in results
        ]
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
    """Build the benchmark command-line interface."""
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark Pandas processing operations and the "
            "Large Dataset Processing pipeline."
        )
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=100_000,
        help="Number of synthetic rows to process.",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=3,
        help="Number of timed repetitions for each operation.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmarks") / "processing_results.json",
        help="Path for the JSON benchmark report.",
    )

    return parser


def main(
    argv: list[str] | None = None,
) -> int:
    """Execute processing benchmarks and return a process-compatible exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        results = run_benchmark(
            rows=args.rows,
            repetitions=args.repetitions,
        )
        output_path = write_results(
            results,
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
        f"Repetitions: {args.repetitions}"
    )
    print()
    print(
        f"{'Operation':<24}"
        f"{'Rows':>12}"
        f"{'Output Rows':>16}"
        f"{'Elapsed (ms)':>18}"
        f"{'Rows/sec':>18}"
    )
    print(
        "-" * 88
    )

    for result in results:
        print(
            f"{result.operation:<24}"
            f"{result.rows:>12,}"
            f"{result.output_rows:>16,}"
            f"{result.elapsed_milliseconds:>18.3f}"
            f"{result.rows_per_second:>18,.0f}"
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
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

from src.chunk_processor import process_chunk
from src.config import PipelineConfig
from src.transformation import transform_chunk


@dataclass(frozen=True, slots=True)
class ProcessingBenchmarkResult:
    """Represent timing and throughput measurements for one benchmark."""

    operation: str
    rows: int
    columns: int
    elapsed_seconds: float
    rows_per_second: float
    output_rows: int

    @property
    def elapsed_milliseconds(self) -> float:
        """Return elapsed processing time in milliseconds."""
        return self.elapsed_seconds * 1000.0


def _build_dataset(
    rows: int,
) -> pd.DataFrame:
    """Build a representative transactional DataFrame."""
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
            "amount": [
                float((index % 500) + 50)
                for index in range(rows)
            ],
            "quantity": [
                (index % 10) + 1
                for index in range(rows)
            ],
            "created_at": [
                pd.Timestamp(
                    "2026-01-01"
                )
                + pd.Timedelta(
                    minutes=index
                )
                for index in range(rows)
            ],
        }
    )


def _build_config() -> PipelineConfig:
    """Build a benchmark configuration with representative transformations."""
    return PipelineConfig(
        timestamp_columns=("created_at",),
        numeric_columns=(
            "amount",
            "quantity",
        ),
        identifier_columns=("order_id",),
        required_columns=("order_id",),
        categorical_columns=(
            "region",
            "status",
            "product",
        ),
        timestamp_timezone="UTC",
        drop_invalid_records=True,
        drop_duplicates=True,
        target_memory_mb=1024,
        fail_on_validation=False,
    )


def _measure(
    operation: str,
    frame: pd.DataFrame,
    function: Callable[
        [pd.DataFrame],
        pd.DataFrame,
    ],
    *,
    repetitions: int,
) -> ProcessingBenchmarkResult:
    """Measure median elapsed time across repeated processing runs."""
    if repetitions <= 0:
        raise ValueError(
            "repetitions must be greater than zero."
        )

    elapsed_times: list[float] = []
    output_rows = 0

    for _ in range(repetitions):
        started_at = time.perf_counter()

        result = function(
            frame
        )

        elapsed_times.append(
            time.perf_counter()
            - started_at
        )

        if not isinstance(
            result,
            pd.DataFrame,
        ):
            raise TypeError(
                "Benchmark operation must return a pandas DataFrame."
            )

        output_rows = len(
            result
        )

    elapsed_seconds = float(
        pd.Series(
            elapsed_times
        ).median()
    )

    rows_per_second = (
        len(frame) / elapsed_seconds
        if elapsed_seconds > 0
        else 0.0
    )

    return ProcessingBenchmarkResult(
        operation=operation,
        rows=len(frame),
        columns=len(frame.columns),
        elapsed_seconds=elapsed_seconds,
        rows_per_second=rows_per_second,
        output_rows=output_rows,
    )


def _benchmark_copy(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark a full DataFrame copy."""
    return frame.copy(
        deep=True
    )


def _benchmark_filter(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark vectorized filtering."""
    return frame.loc[
        frame["status"].eq("paid")
        & frame["amount"].ge(250)
    ].copy()


def _benchmark_sort(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark stable sorting by amount."""
    return frame.sort_values(
        "amount",
        ascending=False,
        kind="stable",
    ).reset_index(
        drop=True
    )


def _benchmark_groupby(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark grouped transactional aggregation."""
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


def _benchmark_vectorized_metric(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark a vectorized derived metric."""
    result = frame.copy(
        deep=False
    )
    result["revenue_per_unit"] = (
        result["amount"]
        / result["quantity"]
    )
    return result


def _benchmark_transform(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark the project's production transformation pipeline."""
    configuration = _build_config()

    return transform_chunk(
        frame,
        pipeline_config=configuration,
    )


def _benchmark_process_chunk(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Benchmark the chunk-processing orchestration layer."""
    configuration = _build_config()

    metadata_type = None

    try:
        from src.ingestion import ChunkMetadata

        metadata_type = ChunkMetadata
    except ImportError:
        metadata_type = None

    if metadata_type is None:
        return transform_chunk(
            frame,
            pipeline_config=configuration,
        )

    metadata = metadata_type(
        chunk_number=1,
        row_count=len(frame),
        memory_bytes=int(
            frame.memory_usage(
                index=True,
                deep=True,
            ).sum()
        ),
        columns=tuple(
            str(column)
            for column in frame.columns
        ),
    )

    result = process_chunk(
        frame,
        metadata,
        lambda chunk, _: transform_chunk(
            chunk,
            pipeline_config=configuration,
        ),
    )

    return result.data


def run_benchmark(
    *,
    rows: int,
    repetitions: int,
) -> list[ProcessingBenchmarkResult]:
    """Run representative Pandas and pipeline-processing benchmarks."""
    frame = _build_dataset(
        rows
    )

    operations: tuple[
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
            _benchmark_copy,
        ),
        (
            "filter",
            _benchmark_filter,
        ),
        (
            "sort",
            _benchmark_sort,
        ),
        (
            "groupby",
            _benchmark_groupby,
        ),
        (
            "vectorized_metric",
            _benchmark_vectorized_metric,
        ),
        (
            "transform_chunk",
            _benchmark_transform,
        ),
        (
            "process_chunk",
            _benchmark_process_chunk,
        ),
    )

    results: list[ProcessingBenchmarkResult] = []

    for operation, function in operations:
        results.append(
            _measure(
                operation,
                frame,
                function,
                repetitions=repetitions,
            )
        )

    return results


def write_results(
    results: list[ProcessingBenchmarkResult],
    output_path: Path,
) -> Path:
    """Write benchmark results as structured JSON."""
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
                "elapsed_milliseconds": (
                    result.elapsed_milliseconds
                ),
            }
            for result in results
        ]
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
    """Build the benchmark command-line interface."""
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark Pandas processing operations and the "
            "Large Dataset Processing pipeline."
        )
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=100_000,
        help="Number of synthetic rows to process.",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=3,
        help="Number of timed repetitions for each operation.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmarks") / "processing_results.json",
        help="Path for the JSON benchmark report.",
    )

    return parser


def main(
    argv: list[str] | None = None,
) -> int:
    """Execute processing benchmarks and return a process-compatible exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        results = run_benchmark(
            rows=args.rows,
            repetitions=args.repetitions,
        )
        output_path = write_results(
            results,
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
        f"Repetitions: {args.repetitions}"
    )
    print()
    print(
        f"{'Operation':<24}"
        f"{'Rows':>12}"
        f"{'Output Rows':>16}"
        f"{'Elapsed (ms)':>18}"
        f"{'Rows/sec':>18}"
    )
    print(
        "-" * 88
    )

    for result in results:
        print(
            f"{result.operation:<24}"
            f"{result.rows:>12,}"
            f"{result.output_rows:>16,}"
            f"{result.elapsed_milliseconds:>18.3f}"
            f"{result.rows_per_second:>18,.0f}"
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