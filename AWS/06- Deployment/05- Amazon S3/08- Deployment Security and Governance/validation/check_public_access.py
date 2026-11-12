import argparse
import json
import logging
import sys
from dataclasses import dataclass
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError


LOGGER = logging.getLogger("s3_security.public_access")

PUBLIC_ACCESS_BLOCK_SETTINGS = (
    "BlockPublicAcls",
    "IgnorePublicAcls",
    "BlockPublicPolicy",
    "RestrictPublicBuckets",
)


@dataclass(frozen=True)
class SecurityFinding:
    """Represent an S3 public-access security finding."""

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


class PublicAccessCheckError(Exception):
    """Represent an error during public-access validation."""


class S3PublicAccessChecker:
    """Validate S3 bucket public-access protections."""

    def __init__(
        self,
        s3_client: Any | None = None,
        expected_bucket_settings: tuple[str, ...] = (
            PUBLIC_ACCESS_BLOCK_SETTINGS
        ),
    ) -> None:
        self.s3_client = s3_client or boto3.client("s3")
        self.expected_bucket_settings = expected_bucket_settings

    def check_bucket(self, bucket_name: str) -> list[SecurityFinding]:
        """
        Validate public-access block settings and bucket policy exposure.

        Missing public-access block configuration is treated as a failure.
        Bucket policy analysis is performed separately because public-access
        block settings and policy statements represent different controls.
        """
        findings: list[SecurityFinding] = []

        findings.extend(self._check_public_access_block(bucket_name))
        findings.extend(self._check_bucket_policy(bucket_name))

        return findings

    def _check_public_access_block(
        self,
        bucket_name: str,
    ) -> list[SecurityFinding]:
        try:
            response = self.s3_client.get_public_access_block(
                Bucket=bucket_name
            )
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")

            if error_code == "NoSuchPublicAccessBlockConfiguration":
                return [
                    SecurityFinding(
                        bucket_name=bucket_name,
                        check="public_access_block",
                        passed=False,
                        message=(
                            "Bucket-level Block Public Access configuration "
                            "is missing."
                        ),
                    )
                ]

            raise PublicAccessCheckError(
                f"Unable to inspect public-access settings for "
                f"{bucket_name}: {error_code}"
            ) from exc

        except BotoCoreError as exc:
            raise PublicAccessCheckError(
                f"Unable to inspect public-access settings for "
                f"{bucket_name}: {exc}"
            ) from exc

        configuration = response.get("PublicAccessBlockConfiguration", {})
        findings = []

        for setting in self.expected_bucket_settings:
            enabled = configuration.get(setting) is True

            findings.append(
                SecurityFinding(
                    bucket_name=bucket_name,
                    check=setting,
                    passed=enabled,
                    message=(
                        f"{setting} is enabled."
                        if enabled
                        else f"{setting} is missing or disabled."
                    ),
                )
            )

        return findings

    def _check_bucket_policy(
        self,
        bucket_name: str,
    ) -> list[SecurityFinding]:
        try:
            response = self.s3_client.get_bucket_policy(
                Bucket=bucket_name
            )
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")

            if error_code == "NoSuchBucketPolicy":
                return [
                    SecurityFinding(
                        bucket_name=bucket_name,
                        check="bucket_policy",
                        passed=True,
                        severity="INFO",
                        message=(
                            "No bucket policy is configured. "
                            "Review IAM and other access paths separately."
                        ),
                    )
                ]

            raise PublicAccessCheckError(
                f"Unable to inspect bucket policy for "
                f"{bucket_name}: {error_code}"
            ) from exc

        except BotoCoreError as exc:
            raise PublicAccessCheckError(
                f"Unable to inspect bucket policy for "
                f"{bucket_name}: {exc}"
            ) from exc

        try:
            policy = json.loads(response["Policy"])
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise PublicAccessCheckError(
                f"Bucket policy for {bucket_name} is not valid JSON."
            ) from exc

        statements = policy.get("Statement", [])

        if isinstance(statements, dict):
            statements = [statements]

        findings = []
        public_statements = []

        for statement in statements:
            if not isinstance(statement, dict):
                continue

            principal = statement.get("Principal")

            if self._has_public_principal(principal):
                public_statements.append(statement)

        findings.append(
            SecurityFinding(
                bucket_name=bucket_name,
                check="public_bucket_policy",
                passed=not public_statements,
                message=(
                    "No wildcard public principal was detected in the "
                    "bucket policy."
                    if not public_statements
                    else (
                        f"Detected {len(public_statements)} bucket policy "
                        "statement(s) with a wildcard public principal. "
                        "Review their actions, resources, and conditions."
                    )
                ),
            )
        )

        return findings

    @staticmethod
    def _has_public_principal(principal: Any) -> bool:
        """
        Identify wildcard principals in common S3 policy representations.

        This is a conservative static check, not a complete IAM policy
        evaluator. Conditions and other AWS authorization controls can
        affect whether a statement grants effective public access.
        """
        if principal == "*":
            return True

        if not isinstance(principal, dict):
            return False

        for principal_values in principal.values():
            if principal_values == "*":
                return True

            if isinstance(principal_values, list) and "*" in principal_values:
                return True

        return False


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
        raise PublicAccessCheckError(
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
        description="Validate S3 bucket public-access protections."
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
    """Run public-access checks and return an appropriate exit code."""
    arguments = parse_arguments()
    configure_logging(arguments.verbose)

    try:
        session = boto3.Session(region_name=arguments.region)
        s3_client = session.client("s3")

        checker = S3PublicAccessChecker(s3_client=s3_client)
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
            LOGGER.info("Inspecting bucket: %s", bucket_name)

            try:
                findings = checker.check_bucket(bucket_name)
                all_findings.extend(findings)
            except PublicAccessCheckError:
                inspection_failed = True
                LOGGER.exception(
                    "Security inspection failed for bucket %s.",
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

        LOGGER.info("All public-access checks passed.")
        return 0

    except (PublicAccessCheckError, BotoCoreError, ClientError):
        LOGGER.exception("S3 public-access validation could not complete.")
        return 2


if __name__ == "__main__":
    sys.exit(main())