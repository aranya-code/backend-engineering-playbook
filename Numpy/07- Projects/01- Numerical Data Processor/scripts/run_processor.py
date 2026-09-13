from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.pipeline import run_pipeline

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Numerical Data Processor pipeline.",
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Path to the input .npy file.",
    )

    parser.add_argument(
        "--output-array",
        type=Path,
        default=None,
        help="Path for the processed .npy output.",
    )

    parser.add_argument(
        "--output-statistics",
        type=Path,
        default=None,
        help="Path for the statistics JSON output.",
    )

    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO",
        help="Logging level.",
    )

    return parser.parse_args()


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    args = parse_args()
    configure_logging(args.log_level)

    try:
        array_path, statistics_path = run_pipeline(
            args.input,
            output_array_path=args.output_array,
            output_statistics_path=args.output_statistics,
        )
    except (OSError, TypeError, ValueError) as exc:
        LOGGER.error("Processing failed: %s", exc)
        return 1

    LOGGER.info(
        "Processed array written to %s",
        array_path,
    )
    LOGGER.info(
        "Statistics written to %s",
        statistics_path,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.pipeline import run_pipeline

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Numerical Data Processor pipeline.",
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Path to the input .npy file.",
    )

    parser.add_argument(
        "--output-array",
        type=Path,
        default=None,
        help="Path for the processed .npy output.",
    )

    parser.add_argument(
        "--output-statistics",
        type=Path,
        default=None,
        help="Path for the statistics JSON output.",
    )

    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO",
        help="Logging level.",
    )

    return parser.parse_args()


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    args = parse_args()
    configure_logging(args.log_level)

    try:
        array_path, statistics_path = run_pipeline(
            args.input,
            output_array_path=args.output_array,
            output_statistics_path=args.output_statistics,
        )
    except (OSError, TypeError, ValueError) as exc:
        LOGGER.error("Processing failed: %s", exc)
        return 1

    LOGGER.info(
        "Processed array written to %s",
        array_path,
    )
    LOGGER.info(
        "Statistics written to %s",
        statistics_path,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())