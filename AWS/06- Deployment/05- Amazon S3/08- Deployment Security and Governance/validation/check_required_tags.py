import argparse
import json
import logging
import sys
from dataclasses import dataclass
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError


LOGGER = logging.getLogger("s3_security.required_tags")

DEFAULT_REQUIRED_TAGS = {
    "Environment",
    "Owner",
    "Project",
    "CostCenter",
}


@dataclass(frozen=True)
class SecurityFinding:
    """Represent an S3 bucket tagging compliance finding."""

    bucket_name: str
    check: str
    passed: bool
    message: str
    severity: str = "MEDIUM"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "bucket": self.bucket_name,
            "check": self.check,
            "passed": self.passed,
            "severity": self.severity,
            "message": self.message,
        }


class RequiredTagsCheckError(Exception):
    """Represent an error during S3 bucket tag validation."""


class S3RequiredTagsChecker:
    """Validate required tags on S3 buckets."""

    def __init__(
        self,
        s3_client: Any | None = None,
        required_tags: set[str] | None = None,
    ) -> None:
        self.s3_client = s3_client or boto3.client("s3")
        self.required_tags = required_tags or DEFAULT_REQUIRED_TAGS

        if not self.required_tags:
            raise ValueError("At least one required tag must be configured.")

    def check_bucket(self, bucket_name: str) -> list[SecurityFinding]:
        """Check whether a bucket contains all required tag keys."""
        try:
            response = self.s3_client.get_bucket_tagging(
                Bucket=bucket_name
            )
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")

            if error_code == "NoSuchTagSet":
                return [
                    SecurityFinding(
                        bucket_name=bucket_name,
                        check="required_tags",
                        passed=False,
                        message=(
                            "Bucket has no tag set. Required tags are "
                            f"missing: {', '.join(sorted(self.required_tags))}."
                        ),
                    )
                ]

            raise RequiredTagsCheckError(
                f"Unable to inspect tags for {bucket_name}: {error_code}"
            ) from exc

        except BotoCoreError as exc:
            raise RequiredTagsCheckError(
                f"Unable to inspect tags for {bucket_name}: {exc}"
            ) from exc

        tag_set = response.get("TagSet", [])
        actual_tags = {
            tag.get("Key")
            for tag in tag_set
            if tag.get("Key")
        }

        missing_tags = self.required_tags - actual_tags

        if missing_tags:
            return [
                SecurityFinding(
                    bucket_name=bucket_name,
                    check="required_tags",
                    passed=False,
                    message=(
                        "Missing required tag keys: "
                        f"{', '.join(sorted(missing_tags))}."
                    ),
                )
            ]

        return [
            SecurityFinding(
                bucket_name=bucket_name,
                check="required_tags",
                passed=True,
                message=(
                    "All required tag keys are present: "
                    f"{', '.join(sorted(self.required_tags))}."
                ),
                severity="INFO",
            )
        ]


def get_bucket_names(
    s3_client: Any,
    configured_buckets: list[str] | None = None,
) -> list[str]:
    """Return explicitly configured buckets or all accessible buckets."""
    if configured_buckets:
        return sorted(set(configured_buckets))

    try:
        response = s3_client.list_buckets()
    except (ClientError, BotoCoreError) as exc:
        raise RequiredTagsCheckError(
            f"Unable to list S3 buckets: {exc}"
        ) from exc

    return sorted(
        bucket["Name"]
        for bucket in response.get("Buckets", [])
        if bucket.get("Name")
    )


def parse_required_tags(values: list[str] | None) -> set[str]:
    """Parse comma-separated required tag keys."""
    if not values:
        return set(DEFAULT_REQUIRED_TAGS)

    required_tags = {
        tag.strip()
        for value in values
        for tag in value.split(",")
        if tag.strip()
    }

    if not required_tags:
        raise ValueError("At least one non-empty tag key is required.")

    return required_tags


def configure_logging(verbose: bool = False) -> None:
    """Configure command-line logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate required tags on S3 buckets."
    )

    parser.add_argument(
        "--bucket",
        action="append",
        dest="buckets",
        help=(
            "Bucket to inspect. Repeat the option to inspect multiple "
            "buckets. If omitted, all accessible buckets are inspected."
        ),
    )
    parser.add_argument(
        "--region",
        help="AWS Region used to configure the S3 client.",
    )
    parser.add_argument(
        "--required-tags",
        action="append",
        help=(
            "Comma-separated required tag keys. Repeat the option to add "
            "more keys. Defaults to Environment, Owner, Project, CostCenter."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Print findings as JSON.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )

    return parser.parse_args()


def main() -> int:
    """Run required-tag checks and return an appropriate exit code."""
    arguments = parse_arguments()
    configure_logging(arguments.verbose)

    try:
        required_tags = parse_required_tags(arguments.required_tags)
        session = boto3.Session(region_name=arguments.region)
        s3_client = session.client("s3")

        checker = S3RequiredTagsChecker(
            s3_client=s3_client,
            required_tags=required_tags,
        )

        bucket_names = get_bucket_names(
            s3_client,
            configured_buckets=arguments.buckets,
        )

        if not bucket_names:
            LOGGER.warning("No S3 buckets found.")
            return 0

        all_findings = []
        inspection_failed = False

        for bucket_name in bucket_names:
            LOGGER.info("Inspecting required tags for bucket: %s", bucket_name)

            try:
                findings = checker.check_bucket(bucket_name)
                all_findings.extend(findings)
            except RequiredTagsCheckError:
                inspection_failed = True
                LOGGER.exception(
                    "Tag inspection failed for bucket %s.",
                    bucket_name,
                )

        if arguments.json_output:
            print(
                json.dumps(
                    [
                        finding.to_dict()
                        for finding in all_findings
                    ],
                    indent=2,
                )
            )
        else:
            for finding in all_findings:
                status = "PASS" if finding.passed else "FAIL"

                print(
                    f"[{status}] {finding.bucket_name} "
                    f"| {finding.check} "
                    f"| {finding.message}"
                )

        failed_findings = [
            finding
            for finding in all_findings
            if not finding.passed
        ]

        if inspection_failed:
            return 2

        if failed_findings:
            return 1

        LOGGER.info("All required-tag checks passed.")
        return 0

    except (
        RequiredTagsCheckError,
        BotoCoreError,
        ClientError,
        ValueError,
    ):
        LOGGER.exception("S3 required-tag validation could not complete.")
        return 2


if __name__ == "__main__":
    sys.exit(main())