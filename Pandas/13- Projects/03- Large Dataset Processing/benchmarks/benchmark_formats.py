from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import pandas as pd


@dataclass(frozen=True, slots=True)
class FormatBenchmarkResult:
    """Represent read/write performance for one storage format."""

    format: str
    rows: int
    columns: int
    write_seconds: float
    read_seconds: float
    file_size_bytes: int
    round_trip_rows: int

    @property
    def write_rows_per_second(self) -> float:
        """Return write throughput in rows per second."""
        if self.write_seconds <= 0:
            return 0.0

        return self.rows / self.write_seconds

    @property
    def read_rows_per_second(self) -> float:
        """Return read throughput in rows per second."""
        if self.read_seconds <= 0:
            return 0.0

        return self.rows / self.read_seconds

    @property
    def file_size_mb(self) -> float:
        """Return output size in mebibytes."""
        return self.file_size_bytes / (1024 * 1024)


@dataclass(frozen=True, slots=True)
class FormatBenchmark:
    """Define one benchmarkable dataframe storage format."""

    name: str
    suffix: str
    writer: Callable[[pd.DataFrame, Path], None]
    reader: Callable[[Path], pd.DataFrame]


def _build_dataset(
    rows: int,
) -> pd.DataFrame:
    """Build a representative transaction dataset."""
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
            "created_at": [
                pd.Timestamp("2026-01-01")
                + pd.Timedelta(minutes=index)
                for index in range(rows)
            ],
        }
    )


def _write_csv(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    """Write a DataFrame to CSV."""
    frame.to_csv(
        path,
        index=False,
    )


def _read_csv(
    path: Path,
) -> pd.DataFrame:
    """Read a CSV file into a DataFrame."""
    return pd.read_csv(
        path
    )


def _write_parquet(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    """Write a DataFrame to Snappy-compressed Parquet."""
    frame.to_parquet(
        path,
        index=False,
        compression="snappy",
    )


def _read_parquet(
    path: Path,
) -> pd.DataFrame:
    """Read a Parquet file into a DataFrame."""
    return pd.read_parquet(
        path
    )


def _write_json(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    """Write a DataFrame to newline-delimited JSON."""
    frame.to_json(
        path,
        orient="records",
        lines=True,
        date_format="iso",
    )


def _read_json(
    path: Path,
) -> pd.DataFrame:
    """Read newline-delimited JSON into a DataFrame."""
    return pd.read_json(
        path,
        orient="records",
        lines=True,
    )


def _formats() -> tuple[FormatBenchmark, ...]:
    """Return the storage formats covered by the benchmark."""
    return (
        FormatBenchmark(
            name="csv",
            suffix=".csv",
            writer=_write_csv,
            reader=_read_csv,
        ),
        FormatBenchmark(
            name="parquet",
            suffix=".parquet",
            writer=_write_parquet,
            reader=_read_parquet,
        ),
        FormatBenchmark(
            name="json",
            suffix=".jsonl",
            writer=_write_json,
            reader=_read_json,
        ),
    )


def _benchmark_format(
    frame: pd.DataFrame,
    benchmark: FormatBenchmark,
    directory: Path,
) -> FormatBenchmarkResult:
    """Measure write time, read time, and serialized size."""
    output_path = (
        directory
        / f"dataset{benchmark.suffix}"
    )

    started_at = time.perf_counter()

    benchmark.writer(
        frame,
        output_path,
    )

    write_seconds = (
        time.perf_counter()
        - started_at
    )

    if not output_path.exists():
        raise RuntimeError(
            f"Writer did not create expected output: {output_path}"
        )

    started_at = time.perf_counter()

    loaded = benchmark.reader(
        output_path
    )

    read_seconds = (
        time.perf_counter()
        - started_at
    )

    return FormatBenchmarkResult(
        format=benchmark.name,
        rows=len(frame),
        columns=len(frame.columns),
        write_seconds=write_seconds,
        read_seconds=read_seconds,
        file_size_bytes=output_path.stat().st_size,
        round_trip_rows=len(loaded),
    )


def _validate_round_trip(
    expected: pd.DataFrame,
    actual: pd.DataFrame,
    *,
    format_name: str,
) -> None:
    """Validate that serialization preserved the expected dataset shape."""
    if len(expected) != len(actual):
        raise RuntimeError(
            f"{format_name} round-trip changed row count: "
            f"{len(expected)} -> {len(actual)}"
        )

    if len(expected.columns) != len(actual.columns):
        raise RuntimeError(
            f"{format_name} round-trip changed column count: "
            f"{len(expected.columns)} -> {len(actual.columns)}"
        )

    if list(expected.columns) != list(actual.columns):
        raise RuntimeError(
            f"{format_name} round-trip changed column names."
        )


def _benchmark_with_validation(
    frame: pd.DataFrame,
    benchmark: FormatBenchmark,
    directory: Path,
) -> FormatBenchmarkResult:
    """Benchmark a format and validate its basic round-trip integrity."""
    output_path = (
        directory
        / f"dataset{benchmark.suffix}"
    )

    started_at = time.perf_counter()

    benchmark.writer(
        frame,
        output_path,
    )

    write_seconds = (
        time.perf_counter()
        - started_at
    )

    started_at = time.perf_counter()

    loaded = benchmark.reader(
        output_path
    )

    read_seconds = (
        time.perf_counter()
        - started_at
    )

    _validate_round_trip(
        frame,
        loaded,
        format_name=benchmark.name,
    )

    return FormatBenchmarkResult(
        format=benchmark.name,
        rows=len(frame),
        columns=len(frame.columns),
        write_seconds=write_seconds,
        read_seconds=read_seconds,
        file_size_bytes=output_path.stat().st_size,
        round_trip_rows=len(loaded),
    )


def run_benchmark(
    *,
    rows: int,
) -> list[FormatBenchmarkResult]:
    """Benchmark CSV, Parquet, and newline-delimited JSON."""
    frame = _build_dataset(
        rows
    )

    with tempfile.TemporaryDirectory(
        prefix="pandas-format-benchmark-"
    ) as directory:
        directory_path = Path(
            directory
        )

        results = [
            _benchmark_with_validation(
                frame,
                benchmark,
                directory_path,
            )
            for benchmark in _formats()
        ]

    return results


def write_results(
    results: list[FormatBenchmarkResult],
    output_path: Path,
) -> Path:
    """Persist format benchmark results as JSON."""
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
                "write_rows_per_second": (
                    result.write_rows_per_second
                ),
                "read_rows_per_second": (
                    result.read_rows_per_second
                ),
                "file_size_mb": (
                    result.file_size_mb
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
            "Benchmark CSV, Parquet, and JSON serialization "
            "for a representative Pandas dataset."
        )
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=100_000,
        help="Number of synthetic rows to serialize.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmarks") / "format_results.json",
        help="Path for the JSON benchmark report.",
    )

    return parser


def main(
    argv: list[str] | None = None,
) -> int:
    """Run storage-format benchmarks and return a process-compatible exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        results = run_benchmark(
            rows=args.rows
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
        ImportError,
    ) as exc:
        parser.error(
            str(exc)
        )
        return 2

    print(
        f"Benchmark rows: {args.rows:,}"
    )
    print()
    print(
        f"{'Format':<12}"
        f"{'Rows':>12}"
        f"{'Write (ms)':>16}"
        f"{'Read (ms)':>16}"
        f"{'Size (MiB)':>16}"
        f"{'Write rows/s':>18}"
        f"{'Read rows/s':>18}"
    )
    print(
        "-" * 108
    )

    for result in results:
        print(
            f"{result.format:<12}"
            f"{result.rows:>12,}"
            f"{result.write_seconds * 1000:>16.3f}"
            f"{result.read_seconds * 1000:>16.3f}"
            f"{result.file_size_mb:>16.2f}"
            f"{result.write_rows_per_second:>18,.0f}"
            f"{result.read_rows_per_second:>18,.0f}"
        )

    print()
    print(
        "Format selection should consider serialization speed, "
        "storage footprint, schema fidelity, and downstream compatibility."
    )
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
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import pandas as pd


@dataclass(frozen=True, slots=True)
class FormatBenchmarkResult:
    """Represent read/write performance for one storage format."""

    format: str
    rows: int
    columns: int
    write_seconds: float
    read_seconds: float
    file_size_bytes: int
    round_trip_rows: int

    @property
    def write_rows_per_second(self) -> float:
        """Return write throughput in rows per second."""
        if self.write_seconds <= 0:
            return 0.0

        return self.rows / self.write_seconds

    @property
    def read_rows_per_second(self) -> float:
        """Return read throughput in rows per second."""
        if self.read_seconds <= 0:
            return 0.0

        return self.rows / self.read_seconds

    @property
    def file_size_mb(self) -> float:
        """Return output size in mebibytes."""
        return self.file_size_bytes / (1024 * 1024)


@dataclass(frozen=True, slots=True)
class FormatBenchmark:
    """Define one benchmarkable dataframe storage format."""

    name: str
    suffix: str
    writer: Callable[[pd.DataFrame, Path], None]
    reader: Callable[[Path], pd.DataFrame]


def _build_dataset(
    rows: int,
) -> pd.DataFrame:
    """Build a representative transaction dataset."""
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
            "created_at": [
                pd.Timestamp("2026-01-01")
                + pd.Timedelta(minutes=index)
                for index in range(rows)
            ],
        }
    )


def _write_csv(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    """Write a DataFrame to CSV."""
    frame.to_csv(
        path,
        index=False,
    )


def _read_csv(
    path: Path,
) -> pd.DataFrame:
    """Read a CSV file into a DataFrame."""
    return pd.read_csv(
        path
    )


def _write_parquet(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    """Write a DataFrame to Snappy-compressed Parquet."""
    frame.to_parquet(
        path,
        index=False,
        compression="snappy",
    )


def _read_parquet(
    path: Path,
) -> pd.DataFrame:
    """Read a Parquet file into a DataFrame."""
    return pd.read_parquet(
        path
    )


def _write_json(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    """Write a DataFrame to newline-delimited JSON."""
    frame.to_json(
        path,
        orient="records",
        lines=True,
        date_format="iso",
    )


def _read_json(
    path: Path,
) -> pd.DataFrame:
    """Read newline-delimited JSON into a DataFrame."""
    return pd.read_json(
        path,
        orient="records",
        lines=True,
    )


def _formats() -> tuple[FormatBenchmark, ...]:
    """Return the storage formats covered by the benchmark."""
    return (
        FormatBenchmark(
            name="csv",
            suffix=".csv",
            writer=_write_csv,
            reader=_read_csv,
        ),
        FormatBenchmark(
            name="parquet",
            suffix=".parquet",
            writer=_write_parquet,
            reader=_read_parquet,
        ),
        FormatBenchmark(
            name="json",
            suffix=".jsonl",
            writer=_write_json,
            reader=_read_json,
        ),
    )


def _benchmark_format(
    frame: pd.DataFrame,
    benchmark: FormatBenchmark,
    directory: Path,
) -> FormatBenchmarkResult:
    """Measure write time, read time, and serialized size."""
    output_path = (
        directory
        / f"dataset{benchmark.suffix}"
    )

    started_at = time.perf_counter()

    benchmark.writer(
        frame,
        output_path,
    )

    write_seconds = (
        time.perf_counter()
        - started_at
    )

    if not output_path.exists():
        raise RuntimeError(
            f"Writer did not create expected output: {output_path}"
        )

    started_at = time.perf_counter()

    loaded = benchmark.reader(
        output_path
    )

    read_seconds = (
        time.perf_counter()
        - started_at
    )

    return FormatBenchmarkResult(
        format=benchmark.name,
        rows=len(frame),
        columns=len(frame.columns),
        write_seconds=write_seconds,
        read_seconds=read_seconds,
        file_size_bytes=output_path.stat().st_size,
        round_trip_rows=len(loaded),
    )


def _validate_round_trip(
    expected: pd.DataFrame,
    actual: pd.DataFrame,
    *,
    format_name: str,
) -> None:
    """Validate that serialization preserved the expected dataset shape."""
    if len(expected) != len(actual):
        raise RuntimeError(
            f"{format_name} round-trip changed row count: "
            f"{len(expected)} -> {len(actual)}"
        )

    if len(expected.columns) != len(actual.columns):
        raise RuntimeError(
            f"{format_name} round-trip changed column count: "
            f"{len(expected.columns)} -> {len(actual.columns)}"
        )

    if list(expected.columns) != list(actual.columns):
        raise RuntimeError(
            f"{format_name} round-trip changed column names."
        )


def _benchmark_with_validation(
    frame: pd.DataFrame,
    benchmark: FormatBenchmark,
    directory: Path,
) -> FormatBenchmarkResult:
    """Benchmark a format and validate its basic round-trip integrity."""
    output_path = (
        directory
        / f"dataset{benchmark.suffix}"
    )

    started_at = time.perf_counter()

    benchmark.writer(
        frame,
        output_path,
    )

    write_seconds = (
        time.perf_counter()
        - started_at
    )

    started_at = time.perf_counter()

    loaded = benchmark.reader(
        output_path
    )

    read_seconds = (
        time.perf_counter()
        - started_at
    )

    _validate_round_trip(
        frame,
        loaded,
        format_name=benchmark.name,
    )

    return FormatBenchmarkResult(
        format=benchmark.name,
        rows=len(frame),
        columns=len(frame.columns),
        write_seconds=write_seconds,
        read_seconds=read_seconds,
        file_size_bytes=output_path.stat().st_size,
        round_trip_rows=len(loaded),
    )


def run_benchmark(
    *,
    rows: int,
) -> list[FormatBenchmarkResult]:
    """Benchmark CSV, Parquet, and newline-delimited JSON."""
    frame = _build_dataset(
        rows
    )

    with tempfile.TemporaryDirectory(
        prefix="pandas-format-benchmark-"
    ) as directory:
        directory_path = Path(
            directory
        )

        results = [
            _benchmark_with_validation(
                frame,
                benchmark,
                directory_path,
            )
            for benchmark in _formats()
        ]

    return results


def write_results(
    results: list[FormatBenchmarkResult],
    output_path: Path,
) -> Path:
    """Persist format benchmark results as JSON."""
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
                "write_rows_per_second": (
                    result.write_rows_per_second
                ),
                "read_rows_per_second": (
                    result.read_rows_per_second
                ),
                "file_size_mb": (
                    result.file_size_mb
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
            "Benchmark CSV, Parquet, and JSON serialization "
            "for a representative Pandas dataset."
        )
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=100_000,
        help="Number of synthetic rows to serialize.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmarks") / "format_results.json",
        help="Path for the JSON benchmark report.",
    )

    return parser


def main(
    argv: list[str] | None = None,
) -> int:
    """Run storage-format benchmarks and return a process-compatible exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        results = run_benchmark(
            rows=args.rows
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
        ImportError,
    ) as exc:
        parser.error(
            str(exc)
        )
        return 2

    print(
        f"Benchmark rows: {args.rows:,}"
    )
    print()
    print(
        f"{'Format':<12}"
        f"{'Rows':>12}"
        f"{'Write (ms)':>16}"
        f"{'Read (ms)':>16}"
        f"{'Size (MiB)':>16}"
        f"{'Write rows/s':>18}"
        f"{'Read rows/s':>18}"
    )
    print(
        "-" * 108
    )

    for result in results:
        print(
            f"{result.format:<12}"
            f"{result.rows:>12,}"
            f"{result.write_seconds * 1000:>16.3f}"
            f"{result.read_seconds * 1000:>16.3f}"
            f"{result.file_size_mb:>16.2f}"
            f"{result.write_rows_per_second:>18,.0f}"
            f"{result.read_rows_per_second:>18,.0f}"
        )

    print()
    print(
        "Format selection should consider serialization speed, "
        "storage footprint, schema fidelity, and downstream compatibility."
    )
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