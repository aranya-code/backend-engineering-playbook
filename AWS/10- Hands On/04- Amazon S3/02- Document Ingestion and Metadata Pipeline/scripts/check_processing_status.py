"""Check document processing status through the document ingestion API.

The API exposes processing status independently of the S3 storage layer.
This script polls that endpoint until the document reaches a terminal state
or the configured timeout expires.

Examples:
    python scripts/check_processing_status.py \
        document-ingestion-tests/incoming/sample-document.pdf

    python scripts/check_processing_status.py \
        document-ingestion-tests/incoming/sample-document.pdf \
        --base-url http://127.0.0.1:8000

    python scripts/check_processing_status.py \
        document-ingestion-tests/incoming/sample-document.pdf \
        --wait \
        --interval 5 \
        --timeout 300

The object identifier must match the API's object_id value returned by
submit_document.py. The script does not query DynamoDB or S3 directly.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote, urlsplit

import httpx


DEFAULT_API_URL = "http://127.0.0.1:8000"
DEFAULT_REQUEST_TIMEOUT_SECONDS = 15.0
DEFAULT_POLL_INTERVAL_SECONDS = 5.0
DEFAULT_WAIT_TIMEOUT_SECONDS = 300.0

PROCESSING_STATUS_ENDPOINT = "/documents/{object_id}/status"

TERMINAL_STATUSES = {
    "COMPLETED",
    "FAILED",
    "SUCCEEDED",
    "ERROR",
}

logger = logging.getLogger("check_processing_status")


class ProcessingStatusError(RuntimeError):
    """Raised when the processing status cannot be retrieved."""


class ProcessingTimeoutError(ProcessingStatusError):
    """Raised when processing does not finish within the requested timeout."""


def configure_logging(verbose: bool = False) -> None:
    """Configure CLI logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def validate_base_url(base_url: str) -> str:
    """Validate and normalize the API base URL."""
    if not base_url or base_url != base_url.strip():
        raise ValueError("API base URL must be a non-empty valid URL.")

    parsed_url = urlsplit(base_url)

    if parsed_url.scheme not in {"http", "https"}:
        raise ValueError("API base URL must use HTTP or HTTPS.")

    if not parsed_url.netloc:
        raise ValueError("API base URL must include a hostname.")

    if parsed_url.username or parsed_url.password:
        raise ValueError(
            "Credentials must not be embedded in the API base URL."
        )

    if parsed_url.query or parsed_url.fragment:
        raise ValueError(
            "API base URL must not contain a query string or fragment."
        )

    return base_url.rstrip("/")


def validate_object_id(object_id: str) -> str:
    """Validate the object identifier returned by the submission API."""
    normalized_object_id = object_id.strip()

    if not normalized_object_id:
        raise ValueError("A document object identifier is required.")

    if normalized_object_id != object_id:
        raise ValueError(
            "Object identifier must not contain leading or trailing spaces."
        )

    if "\x00" in normalized_object_id:
        raise ValueError("Object identifier contains an invalid character.")

    return normalized_object_id


def build_status_url(
    *,
    api_url: str,
    object_id: str,
) -> str:
    """Build the status endpoint URL using a safely encoded object ID."""
    encoded_object_id = quote(
        object_id,
        safe="",
    )

    return (
        f"{api_url}/documents/"
        f"{encoded_object_id}/status"
    )


def fetch_processing_status(
    *,
    client: httpx.Client,
    status_url: str,
) -> dict[str, Any]:
    """Retrieve the current processing status from the API."""
    try:
        response = client.get(status_url)
        response.raise_for_status()

    except httpx.HTTPStatusError as exc:
        response_body = exc.response.text.strip()

        if exc.response.status_code == 404:
            raise ProcessingStatusError(
                "Document processing status was not found. "
                "Verify the object identifier and API status endpoint."
            ) from exc

        if exc.response.status_code in {401, 403}:
            raise ProcessingStatusError(
                "The API rejected the status request. "
                "Check the API authentication and authorization settings."
            ) from exc

        if response_body:
            logger.debug(
                "Status API error response: %s",
                response_body,
            )

        raise ProcessingStatusError(
            f"Status API returned HTTP {exc.response.status_code}."
        ) from exc

    except httpx.RequestError as exc:
        raise ProcessingStatusError(
            f"Unable to communicate with the status API: {exc}"
        ) from exc

    try:
        result = response.json()
    except ValueError as exc:
        raise ProcessingStatusError(
            "Status API returned an invalid JSON response."
        ) from exc

    if not isinstance(result, dict):
        raise ProcessingStatusError(
            "Status API returned an unexpected response structure."
        )

    if "processing_status" not in result:
        raise ProcessingStatusError(
            "Status API response does not contain processing_status."
        )

    processing_status = result["processing_status"]

    if not isinstance(processing_status, str):
        raise ProcessingStatusError(
            "Status API returned an invalid processing_status value."
        )

    result["processing_status"] = processing_status.upper()

    return result


def display_status(result: dict[str, Any]) -> None:
    """Display a processing status response as readable JSON."""
    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )


def get_status_value(result: dict[str, Any]) -> str:
    """Return the normalized processing status."""
    return result["processing_status"].upper()


def is_terminal_status(processing_status: str) -> bool:
    """Determine whether processing has reached a terminal state."""
    return processing_status.upper() in TERMINAL_STATUSES


def format_timestamp(timestamp: float) -> str:
    """Format a Unix timestamp as an ISO 8601 UTC timestamp."""
    return datetime.fromtimestamp(
        timestamp,
        tz=timezone.utc,
    ).isoformat()


def poll_processing_status(
    *,
    client: httpx.Client,
    status_url: str,
    object_id: str,
    poll_interval_seconds: float,
    wait_timeout_seconds: float,
) -> dict[str, Any]:
    """Poll until processing reaches a terminal state or times out.

    Polling uses a monotonic clock so system clock adjustments do not affect
    timeout calculation. Requests are sequential and are not retried
    automatically; transient failures are surfaced to the operator.
    """
    started_at = time.monotonic()
    deadline = started_at + wait_timeout_seconds
    previous_status: str | None = None

    logger.info(
        "Waiting for document processing. Object ID: %s",
        object_id,
    )

    while True:
        result = fetch_processing_status(
            client=client,
            status_url=status_url,
        )

        current_status = get_status_value(result)

        if current_status != previous_status:
            logger.info(
                "Processing status changed: %s",
                current_status,
            )
            previous_status = current_status

        if is_terminal_status(current_status):
            elapsed_seconds = time.monotonic() - started_at

            logger.info(
                "Processing reached terminal status %s after %.1f seconds.",
                current_status,
                elapsed_seconds,
            )

            return result

        remaining_seconds = deadline - time.monotonic()

        if remaining_seconds <= 0:
            raise ProcessingTimeoutError(
                "Document processing did not reach a terminal status "
                f"within {wait_timeout_seconds:.1f} seconds. "
                f"Last observed status: {current_status}."
            )

        time.sleep(
            min(
                poll_interval_seconds,
                remaining_seconds,
            )
        )


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Retrieve or monitor the processing status of an uploaded document."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "object_id",
        help=(
            "Document object_id returned by submit_document.py. "
            "Use the complete identifier, including the bucket name."
        ),
    )

    parser.add_argument(
        "--base-url",
        default=os.getenv("DOCUMENT_API_URL", DEFAULT_API_URL),
        help=(
            "Base URL of the document ingestion API. "
            "Can also be configured using DOCUMENT_API_URL."
        ),
    )

    parser.add_argument(
        "--wait",
        action="store_true",
        help="Poll until processing reaches a terminal status.",
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help="Polling interval in seconds when --wait is enabled.",
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_WAIT_TIMEOUT_SECONDS,
        help="Maximum polling duration in seconds when --wait is enabled.",
    )

    parser.add_argument(
        "--request-timeout",
        type=float,
        default=DEFAULT_REQUEST_TIMEOUT_SECONDS,
        help="HTTP timeout for each status request in seconds.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging.",
    )

    return parser


def main() -> int:
    """Execute the document processing status workflow."""
    parser = build_argument_parser()
    args = parser.parse_args()

    configure_logging(args.verbose)

    try:
        object_id = validate_object_id(args.object_id)
        api_url = validate_base_url(args.base_url)

        if args.interval <= 0:
            raise ValueError(
                "Polling interval must be greater than zero."
            )

        if args.timeout <= 0:
            raise ValueError(
                "Polling timeout must be greater than zero."
            )

        if args.request_timeout <= 0:
            raise ValueError(
                "Request timeout must be greater than zero."
            )

        status_url = build_status_url(
            api_url=api_url,
            object_id=object_id,
        )

        with httpx.Client(
            timeout=httpx.Timeout(args.request_timeout),
            follow_redirects=False,
        ) as client:
            if args.wait:
                result = poll_processing_status(
                    client=client,
                    status_url=status_url,
                    object_id=object_id,
                    poll_interval_seconds=args.interval,
                    wait_timeout_seconds=args.timeout,
                )
            else:
                result = fetch_processing_status(
                    client=client,
                    status_url=status_url,
                )

        display_status(result)

        processing_status = get_status_value(result)

        if processing_status in {"FAILED", "ERROR"}:
            logger.error(
                "Document processing finished unsuccessfully."
            )
            return 2

        if processing_status in {"COMPLETED", "SUCCEEDED"}:
            logger.info("Document processing completed successfully.")
            return 0

        logger.info(
            "Document processing is not yet complete. "
            "Use --wait to monitor until a terminal status is reached."
        )
        return 0

    except ProcessingTimeoutError as exc:
        logger.error("%s", exc)
        return 3

    except ProcessingStatusError as exc:
        logger.error("%s", exc)
        return 1

    except (ValueError, OSError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())