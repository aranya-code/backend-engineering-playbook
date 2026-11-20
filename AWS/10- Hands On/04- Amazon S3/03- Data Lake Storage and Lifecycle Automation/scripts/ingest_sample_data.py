#!/usr/bin/env python3
"""Run read-only preflight validation for the sample data lake dataset.

This utility validates the local event dataset and can optionally verify that
the configured S3 bucket is accessible. It does not upload, modify, or delete
AWS resources or objects.

Actual dataset ingestion is handled separately by the project's ingestion
implementation.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "samples" / "sample_events.json"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.validate_dataset import (  # noqa: E402
    DatasetValidationError,
    EventValidationError,
    validate_dataset_file,
)

LOGGER = logging.getLogger("data_lake.ingestion_preflight")


class S3PreflightError(RuntimeError):
    """Raised when the configured S3 bucket cannot be verified."""


def configure_logging(verbose: bool = False) -> None:
    """Configure application logging without writing diagnostics to stdout."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stderr,
    )


def validate_s3_bucket(
    bucket_name: str,
    region: str | None = None,
    profile: str | None = None,
) -> dict[str, Any]:
    """Verify S3 bucket accessibility using a read-only HEAD request."""
    if not bucket_name or not bucket_name.strip():
        raise ValueError("S3 bucket name must not be empty.")

    session = boto3.Session(
        profile_name=profile,
        region_name=region,
    )
    s3_client = session.client("s3")

    try:
        response = s3_client.head_bucket(Bucket=bucket_name)
    except ClientError as exc:
        error = exc.response.get("Error", {})
        error_code = error.get("Code", "Unknown")
        error_message = error.get("Message", "S3 bucket verification failed.")

        raise S3PreflightError(
            f"Unable to verify bucket {bucket_name!r}: "
            f"{error_code}: {error_message}"
        ) from exc
    except BotoCoreError as exc:
        raise S3PreflightError(
            f"AWS SDK error while verifying bucket {bucket_name!r}: {exc}"
        ) from exc

    status_code = response.get("ResponseMetadata", {}).get(
        "HTTPStatusCode"
    )

    if status_code != 200:
        raise S3PreflightError(
            f"Unexpected response while verifying bucket "
            f"{bucket_name!r}: HTTP {status_code!r}."
        )

    return {
        "bucket": bucket_name,
        "status": "accessible",
        "region": region,
        "http_status": status_code,
        "operation": "HeadBucket",
    }


def build_report(
    dataset_report: dict[str, Any],
    bucket_report: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build a machine-readable preflight report."""
    return {
        "status": "valid",
        "mode": "read_only_preflight",
        "dataset": dataset_report,
        "s3_bucket": bucket_report,
        "aws_mutations_performed": False,
        "upload_performed": False,
    }


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate the sample event dataset and optionally verify "
            "read-only access to an S3 bucket. No data is uploaded."
        )
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Input JSON dataset. Default: {DEFAULT_SOURCE}",
    )
    parser.add_argument(
        "--bucket",
        help=(
            "Optional S3 bucket to verify using HeadBucket. "
            "No objects are uploaded or modified."
        ),
    )
    parser.add_argument(
        "--region",
        help="AWS Region used for the optional S3 bucket check.",
    )
    parser.add_argument(
        "--profile",
        help="Optional AWS CLI profile for the S3 bucket check.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging.",
    )

    return parser.parse_args()


def main() -> int:
    """Run dataset validation and optional read-only S3 preflight checks."""
    arguments = parse_arguments()
    configure_logging(arguments.verbose)

    try:
        dataset_report = validate_dataset_file(arguments.file)

        bucket_report = None
        if arguments.bucket:
            bucket_report = validate_s3_bucket(
                bucket_name=arguments.bucket,
                region=arguments.region,
                profile=arguments.profile,
            )

        report = build_report(
            dataset_report=dataset_report,
            bucket_report=bucket_report,
        )

    except (
        DatasetValidationError,
        EventValidationError,
        FileNotFoundError,
        ValueError,
        S3PreflightError,
    ) as exc:
        LOGGER.error("Preflight validation failed: %s", exc)

        error_report = {
            "status": "invalid",
            "mode": "read_only_preflight",
            "source": str(arguments.file),
            "error": str(exc),
            "aws_mutations_performed": False,
            "upload_performed": False,
        }

        print(json.dumps(error_report, indent=2))
        return 1

    except OSError as exc:
        LOGGER.exception("Unable to access the dataset: %s", exc)
        return 1
    except BotoCoreError as exc:
        LOGGER.exception("AWS preflight operation failed: %s", exc)
        return 1

    LOGGER.info(
        "Dataset validation succeeded: %d records across %d date partitions.",
        dataset_report["record_count"],
        dataset_report["partition_count"],
    )

    if bucket_report:
        LOGGER.info(
            "S3 bucket preflight succeeded: %s",
            bucket_report["bucket"],
        )

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())