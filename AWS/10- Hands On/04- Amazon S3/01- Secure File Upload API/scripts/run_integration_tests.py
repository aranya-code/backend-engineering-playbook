
from __future__ import annotations

import argparse
import logging
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


LOGGER = logging.getLogger("run_integration_tests")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEST_PATH = PROJECT_ROOT / "tests" / "integration"
DEFAULT_API_URL = "http://127.0.0.1:8000"
DEFAULT_HEALTH_PATH = "/health"
DEFAULT_HEALTH_TIMEOUT = 5.0


def parse_args() -> argparse.Namespace:
    """Parse integration test runner arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Run Secure File Upload API integration tests against "
            "a running API and its configured S3 environment."
        )
    )

    parser.add_argument(
        "--api-url",
        default=os.getenv("API_BASE_URL", DEFAULT_API_URL),
        help=(
            "Base URL of the running API. "
            "Defaults to API_BASE_URL or http://127.0.0.1:8000."
        ),
    )

    parser.add_argument(
        "--health-path",
        default=DEFAULT_HEALTH_PATH,
        help="API health endpoint path. Defaults to /health.",
    )

    parser.add_argument(
        "--health-timeout",
        type=float,
        default=DEFAULT_HEALTH_TIMEOUT,
        help="Timeout in seconds for each health check request.",
    )

    parser.add_argument(
        "--skip-health-check",
        action="store_true",
        help="Run pytest without checking API availability first.",
    )

    parser.add_argument(
        "--pytest-path",
        type=Path,
        default=DEFAULT_TEST_PATH,
        help="Integration test directory or file to execute.",
    )

    parser.add_argument(
        "--pytest-arg",
        action="append",
        default=[],
        help=(
            "Additional argument passed to pytest. "
            "May be supplied multiple times."
        ),
    )

    parser.add_argument(
        "--env",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help=(
            "Environment variable passed to the integration test process. "
            "May be supplied multiple times."
        ),
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose runner logging and pytest output.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Display the pytest command without executing tests.",
    )

    return parser.parse_args()


def configure_logging(verbose: bool) -> None:
    """Configure runner logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def validate_url(url: str, argument_name: str) -> str:
    """Validate an HTTP or HTTPS URL and return its normalized form."""
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(
            f"{argument_name} must be a valid HTTP or HTTPS URL."
        )

    if parsed.username or parsed.password:
        raise ValueError(
            f"{argument_name} must not contain embedded credentials."
        )

    return url.rstrip("/")


def validate_health_path(path: str) -> str:
    """Validate the configured health endpoint path."""
    if not path.startswith("/"):
        raise ValueError("--health-path must start with '/'.")

    if "?" in path or "#" in path:
        raise ValueError(
            "--health-path must contain only a URL path, not a query or fragment."
        )

    return path


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate runner arguments before accessing external services."""
    args.api_url = validate_url(args.api_url, "--api-url")
    args.health_path = validate_health_path(args.health_path)

    if args.health_timeout <= 0:
        raise ValueError("--health-timeout must be greater than zero.")

    if not args.pytest_path.exists():
        raise FileNotFoundError(
            f"Integration test path does not exist: {args.pytest_path}"
        )

    if not args.pytest_path.is_dir() and not args.pytest_path.is_file():
        raise ValueError(
            f"Integration test path is not a file or directory: "
            f"{args.pytest_path}"
        )

    for item in args.env:
        if "=" not in item:
            raise ValueError(
                f"Invalid --env value {item!r}. Expected KEY=VALUE."
            )

        key, _ = item.split("=", 1)

        if not key or not key.replace("_", "").isalnum():
            raise ValueError(
                f"Invalid environment variable name: {key!r}"
            )


def check_api_health(
    api_url: str,
    health_path: str,
    timeout: float,
) -> None:
    """
    Verify that the API health endpoint responds successfully.

    The API must already be running. This runner does not start or stop
    application containers or processes.
    """
    health_url = urljoin(
        f"{api_url}/",
        health_path.lstrip("/"),
    )

    request = Request(
        health_url,
        headers={
            "Accept": "application/json",
            "User-Agent": "secure-file-upload-integration-runner/1.0",
        },
        method="GET",
    )

    LOGGER.info("Checking API health at %s", health_url)

    try:
        with urlopen(request, timeout=timeout) as response:
            if not 200 <= response.status < 300:
                raise RuntimeError(
                    f"API health check returned HTTP {response.status}."
                )

            LOGGER.info(
                "API health check passed with HTTP %d.",
                response.status,
            )

    except HTTPError as exc:
        raise RuntimeError(
            f"API health check failed with HTTP {exc.code}."
        ) from exc

    except URLError as exc:
        raise RuntimeError(
            f"API health endpoint is unavailable: {exc.reason}"
        ) from exc

    except TimeoutError as exc:
        raise RuntimeError(
            f"API health check timed out after {timeout} seconds."
        ) from exc


def build_test_environment(
    api_url: str,
    environment_overrides: Sequence[str],
) -> dict[str, str]:
    """Build the environment inherited by the pytest subprocess."""
    environment = os.environ.copy()

    environment["API_BASE_URL"] = api_url

    for item in environment_overrides:
        key, value = item.split("=", 1)
        environment[key] = value

    return environment


def build_pytest_command(
    pytest_path: Path,
    verbose: bool,
    additional_arguments: Sequence[str],
) -> list[str]:
    """Build the pytest command for the integration test suite."""
    command = [
        sys.executable,
        "-m",
        "pytest",
        str(pytest_path),
        "-m",
        "integration",
        "-ra",
    ]

    if verbose:
        command.append("-v")

    command.extend(additional_arguments)

    return command


def run_pytest(
    command: Sequence[str],
    environment: dict[str, str],
    dry_run: bool,
) -> int:
    """Execute pytest and return its process exit code."""
    LOGGER.info("Integration test command: %s", shlex.join(command))

    if dry_run:
        LOGGER.info("Dry run enabled. Pytest was not executed.")
        return 0

    LOGGER.info("Starting integration tests.")

    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            env=environment,
            check=False,
        )

    except OSError as exc:
        LOGGER.error("Unable to start pytest: %s", exc)
        return 2

    if result.returncode == 0:
        LOGGER.info("Integration test suite completed successfully.")
    else:
        LOGGER.error(
            "Integration tests failed with exit code %d.",
            result.returncode,
        )

    return result.returncode


def main() -> int:
    """Execute API preflight checks and the integration test suite."""
    args = parse_args()
    configure_logging(args.verbose)

    try:
        validate_arguments(args)

        if not args.skip_health_check and not args.dry_run:
            check_api_health(
                api_url=args.api_url,
                health_path=args.health_path,
                timeout=args.health_timeout,
            )
        elif args.skip_health_check:
            LOGGER.warning(
                "API health check skipped. Test failures may be caused "
                "by an unavailable API."
            )

        environment = build_test_environment(
            api_url=args.api_url,
            environment_overrides=args.env,
        )

        command = build_pytest_command(
            pytest_path=args.pytest_path,
            verbose=args.verbose,
            additional_arguments=args.pytest_arg,
        )

        return run_pytest(
            command=command,
            environment=environment,
            dry_run=args.dry_run,
        )

    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        LOGGER.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
