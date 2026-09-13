from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from src.config import config
from src.pipeline import PipelineError, run_pipeline


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface for the pipeline runner."""
    parser = argparse.ArgumentParser(
        description=(
            "Run the Large Dataset Processing pipeline with optional "
            "runtime configuration overrides."
        )
    )

    parser.add_argument(
        "--input",
        dest="input_path",
        type=Path,
        default=None,
        help=(
            "Input dataset path. Overrides the configured input_path "
            "for this process."
        ),
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        default=None,
        help=(
            "Final processed dataset path. Overrides the configured "
            "output_path for this process."
        ),
    )
    parser.add_argument(
        "--report",
        dest="report_path",
        type=Path,
        default=None,
        help=(
            "Processing report path. Overrides the configured "
            "report_path for this process."
        ),
    )
    parser.add_argument(
        "--chunk-size",
        dest="chunk_size",
        type=int,
        default=None,
        help=(
            "Number of rows processed per chunk. "
            "Overrides the configured chunk size."
        ),
    )
    parser.add_argument(
        "--max-rows",
        dest="max_rows",
        type=int,
        default=None,
        help=(
            "Optional maximum number of input rows to process."
        ),
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Resume from existing processing state instead of "
            "cleaning previous outputs."
        ),
    )
    parser.add_argument(
        "--enable-checkpoints",
        action="store_true",
        help="Enable durable chunk checkpoints.",
    )
    parser.add_argument(
        "--no-validation-fail",
        action="store_true",
        help=(
            "Record validation failures without stopping the pipeline."
        ),
    )
    parser.add_argument(
        "--log-level",
        choices=(
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ),
        default=None,
        help="Override the configured log level.",
    )

    return parser


def _apply_overrides(
    args: argparse.Namespace,
) -> None:
    """Apply explicitly supplied CLI options to the shared configuration."""
    if args.input_path is not None:
        config.input_path = (
            args.input_path
            .expanduser()
            .resolve()
        )

    if args.output_path is not None:
        config.output_path = (
            args.output_path
            .expanduser()
            .resolve()
        )

    if args.report_path is not None:
        config.report_path = (
            args.report_path
            .expanduser()
            .resolve()
        )

    if args.chunk_size is not None:
        if args.chunk_size <= 0:
            raise ValueError(
                "--chunk-size must be greater than zero."
            )

        config.chunk_size = args.chunk_size

    if args.max_rows is not None:
        if args.max_rows <= 0:
            raise ValueError(
                "--max-rows must be greater than zero."
            )

        config.max_rows = args.max_rows

    if args.resume:
        config.resume_enabled = True

    if args.enable_checkpoints:
        config.checkpointing_enabled = True

    if args.no_validation_fail:
        config.fail_on_validation = False

    if args.log_level is not None:
        config.log_level = args.log_level


def _configure_logging() -> None:
    """Configure process-level logging for the CLI entrypoint."""
    level_name = str(
        config.log_level
    ).upper()

    level = getattr(
        logging,
        level_name,
        logging.INFO,
    )

    logging.basicConfig(
        level=level,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )


def _validate_cli_configuration() -> None:
    """Validate runtime configuration after command-line overrides."""
    config.validate()

    input_path = Path(
        config.input_path
    ).expanduser()

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input dataset does not exist: {input_path}"
        )

    if not input_path.is_file():
        raise ValueError(
            f"Input dataset is not a regular file: {input_path}"
        )


def _print_result(
    result: object,
) -> None:
    """Print a concise operational summary of the completed pipeline run."""
    metrics = result.metrics

    print(
        "Pipeline completed successfully."
    )
    print(
        f"Rows read: {metrics.rows_read:,}"
    )
    print(
        f"Rows written: {metrics.rows_written:,}"
    )
    print(
        f"Rows rejected: {metrics.rows_rejected:,}"
    )
    print(
        f"Chunks processed: {metrics.chunks_processed:,}"
    )
    print(
        f"Chunks failed: {metrics.chunks_failed:,}"
    )
    print(
        f"Elapsed: {metrics.elapsed_seconds:.3f}s"
    )
    print(
        f"Throughput: {metrics.throughput_rows_per_second:,.0f} rows/s"
    )
    print(
        f"Output: {result.output_path}"
    )
    print(
        f"Report: {result.report_path}"
    )

    if result.checkpoint_paths:
        print(
            f"Checkpoints: {len(result.checkpoint_paths):,}"
        )


def run(
    argv: list[str] | None = None,
) -> int:
    """Parse CLI arguments, execute the pipeline, and return an exit code."""
    parser = _build_parser()
    args = parser.parse_args(
        argv
    )

    try:
        _apply_overrides(
            args
        )
        _configure_logging()
        _validate_cli_configuration()

        result = run_pipeline(
            pipeline_config=config
        )

    except (
        PipelineError,
        FileNotFoundError,
        OSError,
        ValueError,
        TypeError,
    ) as exc:
        print(
            f"Pipeline failed: {exc}",
            file=sys.stderr,
        )
        return 1

    _print_result(
        result
    )

    if (
        config.fail_on_validation
        and not result.validation.is_valid
    ):
        print(
            "Pipeline completed with validation issues.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(
        run(
            sys.argv[1:]
        )
    )

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from src.config import config
from src.pipeline import PipelineError, run_pipeline


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface for the pipeline runner."""
    parser = argparse.ArgumentParser(
        description=(
            "Run the Large Dataset Processing pipeline with optional "
            "runtime configuration overrides."
        )
    )

    parser.add_argument(
        "--input",
        dest="input_path",
        type=Path,
        default=None,
        help=(
            "Input dataset path. Overrides the configured input_path "
            "for this process."
        ),
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        default=None,
        help=(
            "Final processed dataset path. Overrides the configured "
            "output_path for this process."
        ),
    )
    parser.add_argument(
        "--report",
        dest="report_path",
        type=Path,
        default=None,
        help=(
            "Processing report path. Overrides the configured "
            "report_path for this process."
        ),
    )
    parser.add_argument(
        "--chunk-size",
        dest="chunk_size",
        type=int,
        default=None,
        help=(
            "Number of rows processed per chunk. "
            "Overrides the configured chunk size."
        ),
    )
    parser.add_argument(
        "--max-rows",
        dest="max_rows",
        type=int,
        default=None,
        help=(
            "Optional maximum number of input rows to process."
        ),
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Resume from existing processing state instead of "
            "cleaning previous outputs."
        ),
    )
    parser.add_argument(
        "--enable-checkpoints",
        action="store_true",
        help="Enable durable chunk checkpoints.",
    )
    parser.add_argument(
        "--no-validation-fail",
        action="store_true",
        help=(
            "Record validation failures without stopping the pipeline."
        ),
    )
    parser.add_argument(
        "--log-level",
        choices=(
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ),
        default=None,
        help="Override the configured log level.",
    )

    return parser


def _apply_overrides(
    args: argparse.Namespace,
) -> None:
    """Apply explicitly supplied CLI options to the shared configuration."""
    if args.input_path is not None:
        config.input_path = (
            args.input_path
            .expanduser()
            .resolve()
        )

    if args.output_path is not None:
        config.output_path = (
            args.output_path
            .expanduser()
            .resolve()
        )

    if args.report_path is not None:
        config.report_path = (
            args.report_path
            .expanduser()
            .resolve()
        )

    if args.chunk_size is not None:
        if args.chunk_size <= 0:
            raise ValueError(
                "--chunk-size must be greater than zero."
            )

        config.chunk_size = args.chunk_size

    if args.max_rows is not None:
        if args.max_rows <= 0:
            raise ValueError(
                "--max-rows must be greater than zero."
            )

        config.max_rows = args.max_rows

    if args.resume:
        config.resume_enabled = True

    if args.enable_checkpoints:
        config.checkpointing_enabled = True

    if args.no_validation_fail:
        config.fail_on_validation = False

    if args.log_level is not None:
        config.log_level = args.log_level


def _configure_logging() -> None:
    """Configure process-level logging for the CLI entrypoint."""
    level_name = str(
        config.log_level
    ).upper()

    level = getattr(
        logging,
        level_name,
        logging.INFO,
    )

    logging.basicConfig(
        level=level,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )


def _validate_cli_configuration() -> None:
    """Validate runtime configuration after command-line overrides."""
    config.validate()

    input_path = Path(
        config.input_path
    ).expanduser()

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input dataset does not exist: {input_path}"
        )

    if not input_path.is_file():
        raise ValueError(
            f"Input dataset is not a regular file: {input_path}"
        )


def _print_result(
    result: object,
) -> None:
    """Print a concise operational summary of the completed pipeline run."""
    metrics = result.metrics

    print(
        "Pipeline completed successfully."
    )
    print(
        f"Rows read: {metrics.rows_read:,}"
    )
    print(
        f"Rows written: {metrics.rows_written:,}"
    )
    print(
        f"Rows rejected: {metrics.rows_rejected:,}"
    )
    print(
        f"Chunks processed: {metrics.chunks_processed:,}"
    )
    print(
        f"Chunks failed: {metrics.chunks_failed:,}"
    )
    print(
        f"Elapsed: {metrics.elapsed_seconds:.3f}s"
    )
    print(
        f"Throughput: {metrics.throughput_rows_per_second:,.0f} rows/s"
    )
    print(
        f"Output: {result.output_path}"
    )
    print(
        f"Report: {result.report_path}"
    )

    if result.checkpoint_paths:
        print(
            f"Checkpoints: {len(result.checkpoint_paths):,}"
        )


def run(
    argv: list[str] | None = None,
) -> int:
    """Parse CLI arguments, execute the pipeline, and return an exit code."""
    parser = _build_parser()
    args = parser.parse_args(
        argv
    )

    try:
        _apply_overrides(
            args
        )
        _configure_logging()
        _validate_cli_configuration()

        result = run_pipeline(
            pipeline_config=config
        )

    except (
        PipelineError,
        FileNotFoundError,
        OSError,
        ValueError,
        TypeError,
    ) as exc:
        print(
            f"Pipeline failed: {exc}",
            file=sys.stderr,
        )
        return 1

    _print_result(
        result
    )

    if (
        config.fail_on_validation
        and not result.validation.is_valid
    ):
        print(
            "Pipeline completed with validation issues.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(
        run(
            sys.argv[1:]
        )
    )