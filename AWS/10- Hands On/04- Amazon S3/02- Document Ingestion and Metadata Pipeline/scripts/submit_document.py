"""Submit a document to the S3 document ingestion API.

The API validates the uploaded document, stores it in the configured S3
bucket, and returns an identifier for asynchronous ingestion and processing.

Example:
    python scripts/submit_document.py ./sample.pdf

    python scripts/submit_document.py ./sample.pdf \
        --base-url http://127.0.0.1:8000

    python scripts/submit_document.py ./sample.pdf \
        --content-type application/pdf
"""

from __future__ import annotations

import argparse
import json
import logging
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx


DEFAULT_API_URL = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT_SECONDS = 120.0
DOCUMENTS_ENDPOINT = "/documents"

logger = logging.getLogger("submit_document")


def configure_logging(verbose: bool = False) -> None:
    """Configure CLI logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
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


def resolve_content_type(
    file_path: Path,
    content_type: str | None,
) -> str:
    """Resolve the document MIME type from an explicit value or filename."""
    if content_type:
        normalized_content_type = content_type.strip().lower()

        if not normalized_content_type:
            raise ValueError("Content type cannot be empty.")

        return normalized_content_type

    detected_content_type, _ = mimetypes.guess_type(
        file_path.name,
        strict=False,
    )

    if not detected_content_type:
        raise ValueError(
            "Unable to determine the document content type. "
            "Specify it explicitly using --content-type."
        )

    return detected_content_type


def validate_document_path(file_path: Path) -> Path:
    """Validate the local document before making an HTTP request."""
    resolved_path = file_path.expanduser().resolve()

    if not resolved_path.exists():
        raise FileNotFoundError(
            f"Document does not exist: {resolved_path}"
        )

    if not resolved_path.is_file():
        raise ValueError(
            f"Document path is not a regular file: {resolved_path}"
        )

    if not os.access(resolved_path, os.R_OK):
        raise PermissionError(
            f"Document is not readable: {resolved_path}"
        )

    if resolved_path.stat().st_size == 0:
        raise ValueError("Empty documents cannot be submitted.")

    return resolved_path


def submit_document(
    *,
    file_path: Path,
    api_url: str,
    content_type: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    """Upload a document using the API's multipart upload endpoint.

    The API is responsible for authoritative document validation, object-key
    generation, and S3 storage. This client does not access S3 directly.

    Automatic retries are intentionally disabled. The API generates a new
    object key for each successful upload, so blindly retrying a POST after
    an ambiguous network failure could create duplicate documents.
    """
    endpoint = f"{api_url}{DOCUMENTS_ENDPOINT}"

    with file_path.open("rb") as document_file:
        files = {
            "file": (
                file_path.name,
                document_file,
                content_type,
            )
        }

        with httpx.Client(
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=False,
        ) as client:
            response = client.post(
                endpoint,
                files=files,
            )

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        response_body = response.text.strip()

        if response_body:
            logger.error(
                "Document submission failed with HTTP %s: %s",
                response.status_code,
                response_body,
            )
        else:
            logger.error(
                "Document submission failed with HTTP %s.",
                response.status_code,
            )

        raise RuntimeError(
            f"Document API returned HTTP {response.status_code}."
        ) from exc

    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Document API returned an invalid JSON response."
        ) from exc

    if not isinstance(result, dict):
        raise RuntimeError(
            "Document API returned an unexpected response structure."
        )

    required_fields = {
        "object_id",
        "bucket_name",
        "object_key",
        "processing_status",
    }

    missing_fields = required_fields.difference(result)

    if missing_fields:
        raise RuntimeError(
            "Document API response is missing required fields: "
            + ", ".join(sorted(missing_fields))
        )

    return result


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Upload a document to the S3 document ingestion API."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "file",
        type=Path,
        help="Path to the document to upload.",
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
        "--content-type",
        default=None,
        help=(
            "Document MIME type. If omitted, it is inferred from "
            "the filename."
        ),
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="HTTP request timeout in seconds.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level CLI logging.",
    )

    return parser


def main() -> int:
    """Execute the document submission workflow."""
    parser = build_argument_parser()
    args = parser.parse_args()

    configure_logging(args.verbose)

    try:
        if args.timeout <= 0:
            raise ValueError("Request timeout must be greater than zero.")

        file_path = validate_document_path(args.file)
        api_url = validate_base_url(args.base_url)

        content_type = resolve_content_type(
            file_path=file_path,
            content_type=args.content_type,
        )

        file_size_bytes = file_path.stat().st_size

        logger.info("Submitting document: %s", file_path.name)
        logger.info(
            "Document size: %s bytes; content type: %s",
            file_size_bytes,
            content_type,
        )

        result = submit_document(
            file_path=file_path,
            api_url=api_url,
            content_type=content_type,
            timeout_seconds=args.timeout,
        )

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            )
        )

        logger.info(
            "Document accepted for asynchronous ingestion. "
            "Object ID: %s",
            result["object_id"],
        )

        return 0

    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1

    except PermissionError as exc:
        logger.error("%s", exc)
        return 1

    except (ValueError, OSError) as exc:
        logger.error("%s", exc)
        return 1

    except httpx.TimeoutException:
        logger.error(
            "Document submission timed out. The upload outcome may be "
            "unknown. Check the API and S3 bucket before submitting again."
        )
        return 1

    except httpx.RequestError as exc:
        logger.error(
            "Unable to communicate with the document API: %s",
            exc,
        )
        return 1

    except RuntimeError as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())