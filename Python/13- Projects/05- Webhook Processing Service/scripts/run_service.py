"""CLI entry point for running the webhook processing service."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import WebhookServiceConfig


def configure_logging(level: str) -> None:
    """Configure process-wide logging for the service."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Run the webhook processing service.",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Bind address. Defaults to WEBHOOK_HOST or configuration.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Bind port. Defaults to WEBHOOK_PORT or configuration.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of Uvicorn worker processes.",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable automatic reload for local development.",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="Logging level, such as INFO, WARNING, or DEBUG.",
    )
    return parser


def run_service(
    *,
    host: str | None = None,
    port: int | None = None,
    workers: int | None = None,
    reload: bool = False,
    log_level: str | None = None,
) -> None:
    """Load configuration and start the ASGI application."""
    config = WebhookServiceConfig.from_environment()

    resolved_host = host or config.host
    resolved_port = port or config.port
    resolved_log_level = (log_level or config.log_level).lower()

    if resolved_port < 1 or resolved_port > 65535:
        raise ValueError("port must be between 1 and 65535.")

    if workers is not None and workers <= 0:
        raise ValueError("workers must be greater than zero.")

    if reload and workers not in (None, 1):
        raise ValueError(
            "Automatic reload cannot be combined with multiple workers."
        )

    configure_logging(resolved_log_level)

    uvicorn.run(
        "src.main:app",
        host=resolved_host,
        port=resolved_port,
        workers=workers,
        reload=reload,
        log_level=resolved_log_level,
    )


def main() -> None:
    """Parse command-line arguments and start the service."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        run_service(
            host=args.host,
            port=args.port,
            workers=args.workers,
            reload=args.reload,
            log_level=args.log_level,
        )
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()

"""CLI entry point for running the webhook processing service."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import WebhookServiceConfig


def configure_logging(level: str) -> None:
    """Configure process-wide logging for the service."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Run the webhook processing service.",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Bind address. Defaults to WEBHOOK_HOST or configuration.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Bind port. Defaults to WEBHOOK_PORT or configuration.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of Uvicorn worker processes.",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable automatic reload for local development.",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="Logging level, such as INFO, WARNING, or DEBUG.",
    )
    return parser


def run_service(
    *,
    host: str | None = None,
    port: int | None = None,
    workers: int | None = None,
    reload: bool = False,
    log_level: str | None = None,
) -> None:
    """Load configuration and start the ASGI application."""
    config = WebhookServiceConfig.from_environment()

    resolved_host = host or config.host
    resolved_port = port or config.port
    resolved_log_level = (log_level or config.log_level).lower()

    if resolved_port < 1 or resolved_port > 65535:
        raise ValueError("port must be between 1 and 65535.")

    if workers is not None and workers <= 0:
        raise ValueError("workers must be greater than zero.")

    if reload and workers not in (None, 1):
        raise ValueError(
            "Automatic reload cannot be combined with multiple workers."
        )

    configure_logging(resolved_log_level)

    uvicorn.run(
        "src.main:app",
        host=resolved_host,
        port=resolved_port,
        workers=workers,
        reload=reload,
        log_level=resolved_log_level,
    )


def main() -> None:
    """Parse command-line arguments and start the service."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        run_service(
            host=args.host,
            port=args.port,
            workers=args.workers,
            reload=args.reload,
            log_level=args.log_level,
        )
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()