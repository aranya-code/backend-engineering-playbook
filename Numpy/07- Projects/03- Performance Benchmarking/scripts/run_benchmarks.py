"""Run the project's NumPy performance benchmark suite."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"
RESULTS_DIR = PROJECT_ROOT / "results"

DEFAULT_ITERATIONS = 10
DEFAULT_WARMUP_ITERATIONS = 2
DEFAULT_SIZE = 100_000
DEFAULT_ROWS = 10_000
DEFAULT_COLUMNS = 128
DEFAULT_SEED = 42

BENCHMARK_FILES = (
    "benchmark_loops.py",
    "benchmark_vectorization.py",
    "benchmark_dtypes.py",
    "benchmark_views.py",
    "benchmark_broadcasting.py",
)


def parse_args() -> argparse.Namespace:
    """Parse command-line options for the benchmark suite."""
    parser = argparse.ArgumentParser(
        description="Run the NumPy performance benchmarking suite.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help="Number of timed iterations for each benchmark.",
    )
    parser.add_argument(
        "--warmup-iterations",
        type=int,
        default=DEFAULT_WARMUP_ITERATIONS,
        help="Number of warmup executions for each benchmark.",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=DEFAULT_SIZE,
        help="Dataset size for one-dimensional benchmarks.",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=DEFAULT_ROWS,
        help="Number of rows for the broadcasting benchmark.",
    )
    parser.add_argument(
        "--columns",
        type=int,
        default=DEFAULT_COLUMNS,
        help="Number of columns for the broadcasting benchmark.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Seed used by reproducible benchmark datasets.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Run remaining benchmarks when one benchmark fails.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    """Validate benchmark suite configuration."""
    if args.iterations <= 0:
        raise ValueError("iterations must be positive.")
    if args.warmup_iterations < 0:
        raise ValueError("warmup-iterations must be non-negative.")
    if args.size <= 0:
        raise ValueError("size must be positive.")
    if args.rows <= 0:
        raise ValueError("rows must be positive.")
    if args.columns <= 0:
        raise ValueError("columns must be positive.")
    if args.seed < 0:
        raise ValueError("seed must be non-negative.")


def benchmark_command(
    benchmark_file: Path,
    *,
    args: argparse.Namespace,
) -> list[str]:
    """Build the command appropriate for a benchmark script."""
    command = [
        sys.executable,
        str(benchmark_file),
        "--iterations",
        str(args.iterations),
        "--warmup-iterations",
        str(args.warmup_iterations),
        "--seed",
        str(args.seed),
    ]

    if benchmark_file.name in {
        "benchmark_loops.py",
        "benchmark_vectorization.py",
        "benchmark_dtypes.py",
        "benchmark_views.py",
    }:
        command.extend(
            [
                "--size",
                str(args.size),
            ]
        )

    if benchmark_file.name == "benchmark_broadcasting.py":
        command.extend(
            [
                "--rows",
                str(args.rows),
                "--columns",
                str(args.columns),
            ]
        )

    return command


def run_benchmark(
    benchmark_file: Path,
    *,
    args: argparse.Namespace,
) -> tuple[int, str]:
    """Execute one benchmark and return its exit code and output."""
    command = benchmark_command(
        benchmark_file,
        args=args,
    )

    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    output = completed.stdout

    if completed.stderr:
        if output and not output.endswith("\n"):
            output += "\n"
        output += "[stderr]\n"
        output += completed.stderr

    return completed.returncode, output


def write_report(
    sections: list[str],
    *,
    successful: int,
    failed: int,
) -> Path:
    """Write the complete benchmark-suite output to a timestamped report."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    report_path = RESULTS_DIR / f"benchmark-suite-{timestamp}.txt"

    header = "\n".join(
        [
            "NumPy Performance Benchmark Suite",
            "=================================",
            f"Generated at: {timestamp}",
            f"Successful benchmarks: {successful}",
            f"Failed benchmarks: {failed}",
            "",
        ]
    )

    report_path.write_text(
        header + "\n\n".join(sections),
        encoding="utf-8",
    )
    return report_path


def main() -> int:
    """Run the configured benchmark suite and persist its output."""
    args = parse_args()

    try:
        validate_args(args)
    except ValueError as exc:
        print(f"Invalid configuration: {exc}", file=sys.stderr)
        return 2

    sections: list[str] = []
    successful = 0
    failed = 0

    for benchmark_name in BENCHMARK_FILES:
        benchmark_file = BENCHMARKS_DIR / benchmark_name

        if not benchmark_file.is_file():
            message = (
                f"=== {benchmark_name} ===\n"
                f"Benchmark file does not exist: {benchmark_file}"
            )
            sections.append(message)
            failed += 1

            if not args.continue_on_error:
                break

            continue

        print(f"Running {benchmark_name}...", flush=True)

        exit_code, output = run_benchmark(
            benchmark_file,
            args=args,
        )

        status = "PASS" if exit_code == 0 else "FAIL"
        sections.append(
            f"=== {benchmark_name} [{status}] ===\n{output.rstrip()}"
        )

        if exit_code == 0:
            successful += 1
        else:
            failed += 1
            print(
                f"{benchmark_name} failed with exit code {exit_code}.",
                file=sys.stderr,
            )

            if not args.continue_on_error:
                break

    report_path = write_report(
        sections,
        successful=successful,
        failed=failed,
    )

    print()
    print(f"Successful benchmarks: {successful}")
    print(f"Failed benchmarks: {failed}")
    print(f"Report: {report_path}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Run the project's NumPy performance benchmark suite."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"
RESULTS_DIR = PROJECT_ROOT / "results"

DEFAULT_ITERATIONS = 10
DEFAULT_WARMUP_ITERATIONS = 2
DEFAULT_SIZE = 100_000
DEFAULT_ROWS = 10_000
DEFAULT_COLUMNS = 128
DEFAULT_SEED = 42

BENCHMARK_FILES = (
    "benchmark_loops.py",
    "benchmark_vectorization.py",
    "benchmark_dtypes.py",
    "benchmark_views.py",
    "benchmark_broadcasting.py",
)


def parse_args() -> argparse.Namespace:
    """Parse command-line options for the benchmark suite."""
    parser = argparse.ArgumentParser(
        description="Run the NumPy performance benchmarking suite.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help="Number of timed iterations for each benchmark.",
    )
    parser.add_argument(
        "--warmup-iterations",
        type=int,
        default=DEFAULT_WARMUP_ITERATIONS,
        help="Number of warmup executions for each benchmark.",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=DEFAULT_SIZE,
        help="Dataset size for one-dimensional benchmarks.",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=DEFAULT_ROWS,
        help="Number of rows for the broadcasting benchmark.",
    )
    parser.add_argument(
        "--columns",
        type=int,
        default=DEFAULT_COLUMNS,
        help="Number of columns for the broadcasting benchmark.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Seed used by reproducible benchmark datasets.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Run remaining benchmarks when one benchmark fails.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    """Validate benchmark suite configuration."""
    if args.iterations <= 0:
        raise ValueError("iterations must be positive.")
    if args.warmup_iterations < 0:
        raise ValueError("warmup-iterations must be non-negative.")
    if args.size <= 0:
        raise ValueError("size must be positive.")
    if args.rows <= 0:
        raise ValueError("rows must be positive.")
    if args.columns <= 0:
        raise ValueError("columns must be positive.")
    if args.seed < 0:
        raise ValueError("seed must be non-negative.")


def benchmark_command(
    benchmark_file: Path,
    *,
    args: argparse.Namespace,
) -> list[str]:
    """Build the command appropriate for a benchmark script."""
    command = [
        sys.executable,
        str(benchmark_file),
        "--iterations",
        str(args.iterations),
        "--warmup-iterations",
        str(args.warmup_iterations),
        "--seed",
        str(args.seed),
    ]

    if benchmark_file.name in {
        "benchmark_loops.py",
        "benchmark_vectorization.py",
        "benchmark_dtypes.py",
        "benchmark_views.py",
    }:
        command.extend(
            [
                "--size",
                str(args.size),
            ]
        )

    if benchmark_file.name == "benchmark_broadcasting.py":
        command.extend(
            [
                "--rows",
                str(args.rows),
                "--columns",
                str(args.columns),
            ]
        )

    return command


def run_benchmark(
    benchmark_file: Path,
    *,
    args: argparse.Namespace,
) -> tuple[int, str]:
    """Execute one benchmark and return its exit code and output."""
    command = benchmark_command(
        benchmark_file,
        args=args,
    )

    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    output = completed.stdout

    if completed.stderr:
        if output and not output.endswith("\n"):
            output += "\n"
        output += "[stderr]\n"
        output += completed.stderr

    return completed.returncode, output


def write_report(
    sections: list[str],
    *,
    successful: int,
    failed: int,
) -> Path:
    """Write the complete benchmark-suite output to a timestamped report."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    report_path = RESULTS_DIR / f"benchmark-suite-{timestamp}.txt"

    header = "\n".join(
        [
            "NumPy Performance Benchmark Suite",
            "=================================",
            f"Generated at: {timestamp}",
            f"Successful benchmarks: {successful}",
            f"Failed benchmarks: {failed}",
            "",
        ]
    )

    report_path.write_text(
        header + "\n\n".join(sections),
        encoding="utf-8",
    )
    return report_path


def main() -> int:
    """Run the configured benchmark suite and persist its output."""
    args = parse_args()

    try:
        validate_args(args)
    except ValueError as exc:
        print(f"Invalid configuration: {exc}", file=sys.stderr)
        return 2

    sections: list[str] = []
    successful = 0
    failed = 0

    for benchmark_name in BENCHMARK_FILES:
        benchmark_file = BENCHMARKS_DIR / benchmark_name

        if not benchmark_file.is_file():
            message = (
                f"=== {benchmark_name} ===\n"
                f"Benchmark file does not exist: {benchmark_file}"
            )
            sections.append(message)
            failed += 1

            if not args.continue_on_error:
                break

            continue

        print(f"Running {benchmark_name}...", flush=True)

        exit_code, output = run_benchmark(
            benchmark_file,
            args=args,
        )

        status = "PASS" if exit_code == 0 else "FAIL"
        sections.append(
            f"=== {benchmark_name} [{status}] ===\n{output.rstrip()}"
        )

        if exit_code == 0:
            successful += 1
        else:
            failed += 1
            print(
                f"{benchmark_name} failed with exit code {exit_code}.",
                file=sys.stderr,
            )

            if not args.continue_on_error:
                break

    report_path = write_report(
        sections,
        successful=successful,
        failed=failed,
    )

    print()
    print(f"Successful benchmarks: {successful}")
    print(f"Failed benchmarks: {failed}")
    print(f"Report: {report_path}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())