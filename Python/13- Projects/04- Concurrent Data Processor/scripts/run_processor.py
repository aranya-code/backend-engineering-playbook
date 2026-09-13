"""Run the concurrent data processor and report processing metrics."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import ProcessorConfig
from src.input import InputReader
from src.metrics import ProcessingMetrics
from src.output import OutputWriter
from src.processor import DataProcessor


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse optional runtime overrides for the processing pipeline."""
    parser = argparse.ArgumentParser(
        description="Run the concurrent data processor.",
    )
    parser.add_argument(
        "--input",
        dest="input_path",
        type=Path,
        help="Override the configured input file.",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        help="Override the configured output file.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        help="Override the configured worker count.",
    )
    parser.add_argument(
        "--mode",
        choices=("thread", "process", "asyncio"),
        help="Override the configured concurrency mode.",
    )

    return parser.parse_args()


def build_config(args: argparse.Namespace) -> ProcessorConfig:
    """Build processor configuration and apply explicit CLI overrides."""
    config = ProcessorConfig.from_environment()

    overrides = {
        "input_path": args.input_path,
        "output_path": args.output_path,
        "max_workers": args.workers,
        "concurrency_mode": args.mode,
    }

    values = {
        field_name: value
        for field_name, value in overrides.items()
        if value is not None
    }

    if not values:
        return config

    return ProcessorConfig(
        input_path=values.get("input_path", config.input_path),
        output_path=values.get("output_path", config.output_path),
        max_workers=values.get("max_workers", config.max_workers),
        concurrency_mode=values.get(
            "concurrency_mode",
            config.concurrency_mode,
        ),
    )


def run() -> int:
    """Execute one complete processing run."""
    args = parse_args()
    config = build_config(args)
    metrics = ProcessingMetrics()

    logger.info(
        "Starting processor: input=%s output=%s mode=%s workers=%d",
        config.input_path,
        config.output_path,
        config.concurrency_mode,
        config.max_workers,
    )

    reader = InputReader(config.input_path)
    processor = DataProcessor(
        max_workers=config.max_workers,
        concurrency_mode=config.concurrency_mode,
        metrics=metrics,
    )
    writer = OutputWriter(config.output_path)

    try:
        with metrics.timer():
            records = reader.read()
            processed_records = processor.process(records)
            output_count = writer.write_jsonl(processed_records)

        snapshot = metrics.snapshot()

        logger.info(
            "Processing completed: processed=%d succeeded=%d "
            "failed=%d output=%d batches=%d duration=%.3fs throughput=%.2f records/s",
            snapshot.records_processed,
            snapshot.records_succeeded,
            snapshot.records_failed,
            output_count,
            snapshot.batches_processed,
            snapshot.processing_seconds,
            (
                snapshot.records_processed / snapshot.processing_seconds
                if snapshot.processing_seconds > 0
                else 0.0
            ),
        )

        if snapshot.records_failed:
            logger.warning(
                "Processing completed with %d failed records.",
                snapshot.records_failed,
            )

        if output_count != snapshot.records_succeeded:
            logger.error(
                "Output count mismatch: output=%d succeeded=%d",
                output_count,
                snapshot.records_succeeded,
            )
            return 1

        return 0

    except KeyboardInterrupt:
        logger.info("Processing interrupted by user.")
        return 130
    except (OSError, ValueError, RuntimeError) as exc:
        logger.exception("Processing failed: %s", exc)
        return 1


def main() -> int:
    """Configure logging and execute the processor CLI."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    return run()


if __name__ == "__main__":
    raise SystemExit(main())

"""Run the concurrent data processor and report processing metrics."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import ProcessorConfig
from src.input import InputReader
from src.metrics import ProcessingMetrics
from src.output import OutputWriter
from src.processor import DataProcessor


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse optional runtime overrides for the processing pipeline."""
    parser = argparse.ArgumentParser(
        description="Run the concurrent data processor.",
    )
    parser.add_argument(
        "--input",
        dest="input_path",
        type=Path,
        help="Override the configured input file.",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        help="Override the configured output file.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        help="Override the configured worker count.",
    )
    parser.add_argument(
        "--mode",
        choices=("thread", "process", "asyncio"),
        help="Override the configured concurrency mode.",
    )

    return parser.parse_args()


def build_config(args: argparse.Namespace) -> ProcessorConfig:
    """Build processor configuration and apply explicit CLI overrides."""
    config = ProcessorConfig.from_environment()

    overrides = {
        "input_path": args.input_path,
        "output_path": args.output_path,
        "max_workers": args.workers,
        "concurrency_mode": args.mode,
    }

    values = {
        field_name: value
        for field_name, value in overrides.items()
        if value is not None
    }

    if not values:
        return config

    return ProcessorConfig(
        input_path=values.get("input_path", config.input_path),
        output_path=values.get("output_path", config.output_path),
        max_workers=values.get("max_workers", config.max_workers),
        concurrency_mode=values.get(
            "concurrency_mode",
            config.concurrency_mode,
        ),
    )


def run() -> int:
    """Execute one complete processing run."""
    args = parse_args()
    config = build_config(args)
    metrics = ProcessingMetrics()

    logger.info(
        "Starting processor: input=%s output=%s mode=%s workers=%d",
        config.input_path,
        config.output_path,
        config.concurrency_mode,
        config.max_workers,
    )

    reader = InputReader(config.input_path)
    processor = DataProcessor(
        max_workers=config.max_workers,
        concurrency_mode=config.concurrency_mode,
        metrics=metrics,
    )
    writer = OutputWriter(config.output_path)

    try:
        with metrics.timer():
            records = reader.read()
            processed_records = processor.process(records)
            output_count = writer.write_jsonl(processed_records)

        snapshot = metrics.snapshot()

        logger.info(
            "Processing completed: processed=%d succeeded=%d "
            "failed=%d output=%d batches=%d duration=%.3fs throughput=%.2f records/s",
            snapshot.records_processed,
            snapshot.records_succeeded,
            snapshot.records_failed,
            output_count,
            snapshot.batches_processed,
            snapshot.processing_seconds,
            (
                snapshot.records_processed / snapshot.processing_seconds
                if snapshot.processing_seconds > 0
                else 0.0
            ),
        )

        if snapshot.records_failed:
            logger.warning(
                "Processing completed with %d failed records.",
                snapshot.records_failed,
            )

        if output_count != snapshot.records_succeeded:
            logger.error(
                "Output count mismatch: output=%d succeeded=%d",
                output_count,
                snapshot.records_succeeded,
            )
            return 1

        return 0

    except KeyboardInterrupt:
        logger.info("Processing interrupted by user.")
        return 130
    except (OSError, ValueError, RuntimeError) as exc:
        logger.exception("Processing failed: %s", exc)
        return 1


def main() -> int:
    """Configure logging and execute the processor CLI."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    return run()


if __name__ == "__main__":
    raise SystemExit(main())