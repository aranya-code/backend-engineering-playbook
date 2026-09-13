from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import config
from src.pipeline import main as pipeline_main


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface for the pipeline runner."""
    parser = argparse.ArgumentParser(
        description=(
            "Run the API Data Processing Pipeline against a configured "
            "or explicitly supplied API endpoint."
        )
    )
    parser.add_argument(
        "endpoint",
        nargs="?",
        default=config.api_base_url,
        help=(
            "API endpoint to process. Defaults to API_BASE_URL "
            "from the active environment configuration."
        ),
    )
    return parser


def run(
    argv: list[str] | None = None,
) -> int:
    """Parse CLI arguments and execute the pipeline."""
    args = build_parser().parse_args(argv)

    return pipeline_main(
        args.endpoint,
        pipeline_config=config,
    )


if __name__ == "__main__":
    raise SystemExit(run())

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import config
from src.pipeline import main as pipeline_main


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface for the pipeline runner."""
    parser = argparse.ArgumentParser(
        description=(
            "Run the API Data Processing Pipeline against a configured "
            "or explicitly supplied API endpoint."
        )
    )
    parser.add_argument(
        "endpoint",
        nargs="?",
        default=config.api_base_url,
        help=(
            "API endpoint to process. Defaults to API_BASE_URL "
            "from the active environment configuration."
        ),
    )
    return parser


def run(
    argv: list[str] | None = None,
) -> int:
    """Parse CLI arguments and execute the pipeline."""
    args = build_parser().parse_args(argv)

    return pipeline_main(
        args.endpoint,
        pipeline_config=config,
    )


if __name__ == "__main__":
    raise SystemExit(run())