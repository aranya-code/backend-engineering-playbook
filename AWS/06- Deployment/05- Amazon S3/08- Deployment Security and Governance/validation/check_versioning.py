import argparse
import json
import logging
import sys
from dataclasses import dataclass
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError


LOGGER = logging.getLogger("s3_security.versioning")


@dataclass(frozen=True)
class SecurityFinding:
    """Represent an S3 versioning security finding."""

    bucket_name: str
    check: str
    passed: bool
    message: str
    severity: str = "HIGH"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "bucket": self.bucket_name,
            "check": self.check,
            "passed": self.passed,
            "severity": self.severity,
            "message": self.message,
        }


class VersioningCheckError(Exception):
    """Represent an error during S3 versioning validation."""


class S3VersioningChecker:
    """Validate S3 bucket versioning configuration."""

    def __init__(
        self,
        s3_client: Any | None = None,
        require_enabled: bool = True,
        require_mfa_delete: bool = False,
    ) -> None:
        self.s3_client = s3_client or boto3.client("s3")
        self.require_enabled = require_enabled
        self.require_mfa_delete = require_mfa_delete

    def check_bucket(self, bucket_name: str) -> list[SecurityFinding]:
        """Inspect versioning and MFA Delete configuration."""
        try:
            response = self.s3_client.get_bucket_versioning(
                Bucket=bucket_name
            )
        except (ClientError, BotoCoreError) as exc:
            raise VersioningCheckError(
                f"Unable to inspect versioning for {bucket_name}: {exc}"
            ) from exc

        status = response.get("Status")
        mfa_delete = response.get("MFADelete")

        findings = []

        if self.require_enabled:
            versioning_enabled = status == "Enabled"
            findings.append(
                SecurityFinding(
                    bucket_name=bucket_name,
                    check="versioning_enabled",
                    passed=versioning_enabled,
                    message=(
                        "Bucket versioning is enabled."
                        if versioning_enabled
                        else (
                            "Bucket versioning is not enabled. "
                            f"Current status: {status or 'Not configured'}."
                        )
                    ),
                )
            )
        else:
            findings.append(
                SecurityFinding(
                    bucket_name=bucket_name,
                    check="versioning_configuration",
                    passed=status in {"Enabled", "Suspended", None},
                    message=(
                        f"Bucket versioning status: "
                        f"{status or 'Not configured'}."
                    ),
                    severity="INFO",
                )
            )

        if self.require_mfa_delete:
            mfa_delete_enabled = mfa_delete == "Enabled"
            findings.append(
                SecurityFinding(
                    bucket_name=bucket_name,
                    check="mfa_delete_enabled",
                    passed=mfa_delete_enabled,
                    message=(
                        "MFA Delete is enabled."
                        if mfa_delete_enabled
                        else (
                            "MFA Delete is not enabled. "
                            f"Current status: "
                            f"{mfa_delete or 'Not configured'}."
                        )
                    ),
                )
            )

        return findings


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
        raise VersioningCheckError(
            f"Unable to list S3 buckets: {exc}"
        ) from exc

    return sorted(
        bucket["Name"]
        for bucket in response.get("Buckets", [])
        if bucket.get("Name")
    )


def configure_logging(verbose: bool = False) -> None:
    """Configure command-line logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate S3 bucket versioning configuration."
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
        "--allow-disabled",
        action="store_true",
        help="Report versioning status without requiring it to be enabled.",
    )
    parser.add_argument(
        "--require-mfa-delete",
        action="store_true",
        help="Require MFA Delete to be enabled.",
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
    """Run versioning checks and return an appropriate exit code."""
    arguments = parse_arguments()
    configure_logging(arguments.verbose)

    try:
        session = boto3.Session(region_name=arguments.region)
        s3_client = session.client("s3")

        checker = S3VersioningChecker(
            s3_client=s3_client,
            require_enabled=not arguments.allow_disabled,
            require_mfa_delete=arguments.require_mfa_delete,
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
            LOGGER.info(
                "Inspecting versioning configuration for bucket: %s",
                bucket_name,
            )

            try:
                findings = checker.check_bucket(bucket_name)
                all_findings.extend(findings)
            except VersioningCheckError:
                inspection_failed = True
                LOGGER.exception(
                    "Versioning inspection failed for bucket %s.",
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

        LOGGER.info("All versioning checks passed.")
        return 0

    except (VersioningCheckError, BotoCoreError, ClientError):
        LOGGER.exception("S3 versioning validation could not complete.")
        return 2


if __name__ == "__main__":
    sys.exit(main())