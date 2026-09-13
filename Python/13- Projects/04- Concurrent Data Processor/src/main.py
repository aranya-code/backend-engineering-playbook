"""Application entry point for the concurrent data processor."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from src.config import ProcessorConfig
from src.input import InputReader
from src.metrics import ProcessingMetrics
from src.output import OutputWriter
from src.processor import DataProcessor

logger = logging.getLogger(__name__)


def run() -> int:
    """Execute the configured data-processing pipeline."""
    config = ProcessorConfig.from_environment()
    metrics = ProcessingMetrics()

    input_reader = InputReader(config.input_path)
    processor = DataProcessor(
        max_workers=config.max_workers,
        concurrency_mode=config.concurrency_mode,
        metrics=metrics,
    )
    output_writer = OutputWriter(config.output_path)

    logger.info(
        "Starting data processor: input=%s output=%s mode=%s workers=%d",
        config.input_path,
        config.output_path,
        config.concurrency_mode,
        config.max_workers,
    )

    try:
        records = input_reader.read()
        processed_records = processor.process(records)

        output_count = output_writer.write_jsonl(processed_records)

        snapshot = metrics.snapshot()

        logger.info(
            "Processing completed: records=%d succeeded=%d failed=%d "
            "batches=%d duration=%.3fs success_rate=%.2f%%",
            snapshot.records_processed,
            snapshot.records_succeeded,
            snapshot.records_failed,
            snapshot.batches_processed,
            snapshot.processing_seconds,
            snapshot.success_rate * 100,
        )

        if output_count != snapshot.records_succeeded:
            logger.warning(
                "Output count differs from successful record count: "
                "output=%d succeeded=%d",
                output_count,
                snapshot.records_succeeded,
            )

        return 0

    except KeyboardInterrupt:
        logger.info("Processing interrupted by user.")
        return 130
    except (OSError, ValueError, RuntimeError) as exc:
        logger.exception("Data processing failed: %s", exc)
        return 1


def main() -> int:
    """Configure application logging and execute the processor."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    return run()


if __name__ == "__main__":
    sys.exit(main())

"""Application entry point for the concurrent data processor."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from src.config import ProcessorConfig
from src.input import InputReader
from src.metrics import ProcessingMetrics
from src.output import OutputWriter
from src.processor import DataProcessor

logger = logging.getLogger(__name__)


def run() -> int:
    """Execute the configured data-processing pipeline."""
    config = ProcessorConfig.from_environment()
    metrics = ProcessingMetrics()

    input_reader = InputReader(config.input_path)
    processor = DataProcessor(
        max_workers=config.max_workers,
        concurrency_mode=config.concurrency_mode,
        metrics=metrics,
    )
    output_writer = OutputWriter(config.output_path)

    logger.info(
        "Starting data processor: input=%s output=%s mode=%s workers=%d",
        config.input_path,
        config.output_path,
        config.concurrency_mode,
        config.max_workers,
    )

    try:
        records = input_reader.read()
        processed_records = processor.process(records)

        output_count = output_writer.write_jsonl(processed_records)

        snapshot = metrics.snapshot()

        logger.info(
            "Processing completed: records=%d succeeded=%d failed=%d "
            "batches=%d duration=%.3fs success_rate=%.2f%%",
            snapshot.records_processed,
            snapshot.records_succeeded,
            snapshot.records_failed,
            snapshot.batches_processed,
            snapshot.processing_seconds,
            snapshot.success_rate * 100,
        )

        if output_count != snapshot.records_succeeded:
            logger.warning(
                "Output count differs from successful record count: "
                "output=%d succeeded=%d",
                output_count,
                snapshot.records_succeeded,
            )

        return 0

    except KeyboardInterrupt:
        logger.info("Processing interrupted by user.")
        return 130
    except (OSError, ValueError, RuntimeError) as exc:
        logger.exception("Data processing failed: %s", exc)
        return 1


def main() -> int:
    """Configure application logging and execute the processor."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    return run()


if __name__ == "__main__":
    sys.exit(main())