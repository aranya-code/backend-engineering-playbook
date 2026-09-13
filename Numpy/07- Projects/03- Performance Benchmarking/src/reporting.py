"""Benchmark report generation and serialization utilities."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .benchmarks import BenchmarkComparison, BenchmarkResult


def benchmark_result_to_dict(
    result: BenchmarkResult,
) -> dict[str, Any]:
    """Convert a benchmark result into a serializable mapping."""
    data = asdict(result)
    data["operations_per_second"] = result.operations_per_second
    return data


def comparison_to_dict(
    comparison: BenchmarkComparison,
) -> dict[str, Any]:
    """Convert a benchmark comparison into a serializable mapping."""
    return {
        "baseline": benchmark_result_to_dict(
            comparison.baseline
        ),
        "candidate": benchmark_result_to_dict(
            comparison.candidate
        ),
        "speedup": comparison.speedup,
        "relative_runtime": comparison.relative_runtime,
    }


def write_json_report(
    data: dict[str, Any] | list[dict[str, Any]],
    path: str | Path,
    *,
    indent: int = 2,
    allow_overwrite: bool = True,
) -> Path:
    """Write benchmark results as structured JSON."""
    output_path = Path(path)

    if output_path.suffix.lower() != ".json":
        raise ValueError(
            f"Expected a .json output path, got {output_path.suffix}."
        )

    if output_path.exists() and not allow_overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=indent,
            sort_keys=True,
        )
        file.write("\n")

    return output_path


def write_csv_report(
    results: list[BenchmarkResult],
    path: str | Path,
    *,
    allow_overwrite: bool = True,
) -> Path:
    """Write benchmark results as a flat CSV report."""
    if not results:
        raise ValueError(
            "results must contain at least one benchmark result."
        )

    output_path = Path(path)

    if output_path.suffix.lower() != ".csv":
        raise ValueError(
            f"Expected a .csv output path, got {output_path.suffix}."
        )

    if output_path.exists() and not allow_overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "name",
        "iterations",
        "warmup_iterations",
        "minimum_seconds",
        "maximum_seconds",
        "mean_seconds",
        "median_seconds",
        "standard_deviation_seconds",
        "total_seconds",
        "operations_per_second",
    ]

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for result in results:
            writer.writerow(
                benchmark_result_to_dict(result)
            )

    return output_path


def format_result(
    result: BenchmarkResult,
) -> str:
    """Format one benchmark result for terminal output."""
    return (
        f"{result.name}: "
        f"mean={result.mean_seconds:.6f}s, "
        f"median={result.median_seconds:.6f}s, "
        f"min={result.minimum_seconds:.6f}s, "
        f"max={result.maximum_seconds:.6f}s, "
        f"stddev={result.standard_deviation_seconds:.6f}s, "
        f"ops/s={result.operations_per_second:.2f}"
    )


def format_comparison(
    comparison: BenchmarkComparison,
) -> str:
    """Format a baseline-versus-candidate comparison."""
    return (
        f"{comparison.baseline.name} vs "
        f"{comparison.candidate.name}: "
        f"speedup={comparison.speedup:.2f}x, "
        f"relative_runtime={comparison.relative_runtime:.2%}"
    )


def format_results_table(
    results: list[BenchmarkResult],
) -> str:
    """Render benchmark results as a simple Markdown table."""
    if not results:
        return (
            "| Benchmark | Mean | Median | Min | Max | Ops/s |\n"
            "|---|---:|---:|---:|---:|---:|"
        )

    lines = [
        "| Benchmark | Mean | Median | Min | Max | Ops/s |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for result in results:
        lines.append(
            f"| {result.name} "
            f"| {result.mean_seconds:.6f}s "
            f"| {result.median_seconds:.6f}s "
            f"| {result.minimum_seconds:.6f}s "
            f"| {result.maximum_seconds:.6f}s "
            f"| {result.operations_per_second:.2f} |"
        )

    return "\n".join(lines)


def write_markdown_report(
    results: list[BenchmarkResult],
    path: str | Path,
    *,
    title: str = "Performance Benchmark Report",
    allow_overwrite: bool = True,
) -> Path:
    """Write benchmark results as a Markdown report."""
    if not results:
        raise ValueError(
            "results must contain at least one benchmark result."
        )

    output_path = Path(path)

    if output_path.suffix.lower() != ".md":
        raise ValueError(
            f"Expected a .md output path, got {output_path.suffix}."
        )

    if output_path.exists() and not allow_overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    content = (
        f"# {title}\n\n"
        "## Results\n\n"
        f"{format_results_table(results)}\n"
    )

    output_path.write_text(
        content,
        encoding="utf-8",
    )

    return output_path

"""Benchmark report generation and serialization utilities."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .benchmarks import BenchmarkComparison, BenchmarkResult


def benchmark_result_to_dict(
    result: BenchmarkResult,
) -> dict[str, Any]:
    """Convert a benchmark result into a serializable mapping."""
    data = asdict(result)
    data["operations_per_second"] = result.operations_per_second
    return data


def comparison_to_dict(
    comparison: BenchmarkComparison,
) -> dict[str, Any]:
    """Convert a benchmark comparison into a serializable mapping."""
    return {
        "baseline": benchmark_result_to_dict(
            comparison.baseline
        ),
        "candidate": benchmark_result_to_dict(
            comparison.candidate
        ),
        "speedup": comparison.speedup,
        "relative_runtime": comparison.relative_runtime,
    }


def write_json_report(
    data: dict[str, Any] | list[dict[str, Any]],
    path: str | Path,
    *,
    indent: int = 2,
    allow_overwrite: bool = True,
) -> Path:
    """Write benchmark results as structured JSON."""
    output_path = Path(path)

    if output_path.suffix.lower() != ".json":
        raise ValueError(
            f"Expected a .json output path, got {output_path.suffix}."
        )

    if output_path.exists() and not allow_overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=indent,
            sort_keys=True,
        )
        file.write("\n")

    return output_path


def write_csv_report(
    results: list[BenchmarkResult],
    path: str | Path,
    *,
    allow_overwrite: bool = True,
) -> Path:
    """Write benchmark results as a flat CSV report."""
    if not results:
        raise ValueError(
            "results must contain at least one benchmark result."
        )

    output_path = Path(path)

    if output_path.suffix.lower() != ".csv":
        raise ValueError(
            f"Expected a .csv output path, got {output_path.suffix}."
        )

    if output_path.exists() and not allow_overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "name",
        "iterations",
        "warmup_iterations",
        "minimum_seconds",
        "maximum_seconds",
        "mean_seconds",
        "median_seconds",
        "standard_deviation_seconds",
        "total_seconds",
        "operations_per_second",
    ]

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for result in results:
            writer.writerow(
                benchmark_result_to_dict(result)
            )

    return output_path


def format_result(
    result: BenchmarkResult,
) -> str:
    """Format one benchmark result for terminal output."""
    return (
        f"{result.name}: "
        f"mean={result.mean_seconds:.6f}s, "
        f"median={result.median_seconds:.6f}s, "
        f"min={result.minimum_seconds:.6f}s, "
        f"max={result.maximum_seconds:.6f}s, "
        f"stddev={result.standard_deviation_seconds:.6f}s, "
        f"ops/s={result.operations_per_second:.2f}"
    )


def format_comparison(
    comparison: BenchmarkComparison,
) -> str:
    """Format a baseline-versus-candidate comparison."""
    return (
        f"{comparison.baseline.name} vs "
        f"{comparison.candidate.name}: "
        f"speedup={comparison.speedup:.2f}x, "
        f"relative_runtime={comparison.relative_runtime:.2%}"
    )


def format_results_table(
    results: list[BenchmarkResult],
) -> str:
    """Render benchmark results as a simple Markdown table."""
    if not results:
        return (
            "| Benchmark | Mean | Median | Min | Max | Ops/s |\n"
            "|---|---:|---:|---:|---:|---:|"
        )

    lines = [
        "| Benchmark | Mean | Median | Min | Max | Ops/s |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for result in results:
        lines.append(
            f"| {result.name} "
            f"| {result.mean_seconds:.6f}s "
            f"| {result.median_seconds:.6f}s "
            f"| {result.minimum_seconds:.6f}s "
            f"| {result.maximum_seconds:.6f}s "
            f"| {result.operations_per_second:.2f} |"
        )

    return "\n".join(lines)


def write_markdown_report(
    results: list[BenchmarkResult],
    path: str | Path,
    *,
    title: str = "Performance Benchmark Report",
    allow_overwrite: bool = True,
) -> Path:
    """Write benchmark results as a Markdown report."""
    if not results:
        raise ValueError(
            "results must contain at least one benchmark result."
        )

    output_path = Path(path)

    if output_path.suffix.lower() != ".md":
        raise ValueError(
            f"Expected a .md output path, got {output_path.suffix}."
        )

    if output_path.exists() and not allow_overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    content = (
        f"# {title}\n\n"
        "## Results\n\n"
        f"{format_results_table(results)}\n"
    )

    output_path.write_text(
        content,
        encoding="utf-8",
    )

    return output_path