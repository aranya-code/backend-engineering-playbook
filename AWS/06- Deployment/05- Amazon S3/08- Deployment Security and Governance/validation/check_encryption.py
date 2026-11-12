import argparse
import json
import logging
import sys
from dataclasses import dataclass
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError


LOGGER = logging.getLogger("s3_security.encryption")

DEFAULT_ENCRYPTION_ALGORITHM = "AES256"
SUPPORTED_ENCRYPTION_ALGORITHMS = {
    "AES256",
    "aws:kms",
    "aws:kms:dsse",
}


@dataclass(frozen=True)
class SecurityFinding:
    """Represent an S3 encryption security finding."""

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


class EncryptionCheckError(Exception):
    """Represent an error during S3 encryption validation."""


class S3EncryptionChecker:
    """Validate default server-side encryption for S3 buckets."""

    def __init__(
        self,
        s3_client: Any | None = None,
        expected_algorithm: str | None = None,
        expected_kms_key_id: str | None = None,
        require_bucket_key: bool = False,
    ) -> None:
        self.s3_client = s3_client or boto3.client("s3")
        self.expected_algorithm = expected_algorithm
        self.expected_kms_key_id = expected_kms_key_id
        self.require_bucket_key = require_bucket_key

        if (
            expected_algorithm is not None
            and expected_algorithm not in SUPPORTED_ENCRYPTION_ALGORITHMS
        ):
            raise ValueError(
                f"Unsupported encryption algorithm: {expected_algorithm}"
            )

        if (
            expected_kms_key_id
            and expected_algorithm not in {"aws:kms", "aws:kms:dsse"}
        ):
            raise ValueError(
                "A KMS key ID requires an expected KMS encryption algorithm."
            )

    def check_bucket(self, bucket_name: str) -> list[SecurityFinding]:
        """Validate the bucket's default server-side encryption."""
        try:
            response = self.s3_client.get_bucket_encryption(
                Bucket=bucket_name
            )
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")

            if error_code == "ServerSideEncryptionConfigurationNotFoundError":
                return [
                    SecurityFinding(
                        bucket_name=bucket_name,
                        check="default_encryption",
                        passed=False,
                        message=(
                            "Default server-side encryption configuration "
                            "is missing."
                        ),
                    )
                ]

            raise EncryptionCheckError(
                f"Unable to inspect encryption for {bucket_name}: "
                f"{error_code}"
            ) from exc

        except BotoCoreError as exc:
            raise EncryptionCheckError(
                f"Unable to inspect encryption for {bucket_name}: {exc}"
            ) from exc

        rules = response.get(
            "ServerSideEncryptionConfiguration", {}
        ).get("Rules", [])

        if not rules:
            return [
                SecurityFinding(
                    bucket_name=bucket_name,
                    check="default_encryption",
                    passed=False,
                    message=(
                        "Encryption configuration exists but contains "
                        "no rules."
                    ),
                )
            ]

        findings = []

        for index, rule in enumerate(rules):
            findings.extend(
                self._validate_rule(
                    bucket_name=bucket_name,
                    rule=rule,
                    rule_index=index,
                )
            )

        return findings

    def _validate_rule(
        self,
        bucket_name: str,
        rule: dict[str, Any],
        rule_index: int,
    ) -> list[SecurityFinding]:
        """Validate one server-side encryption configuration rule."""
        encryption = rule.get("ApplyServerSideEncryptionByDefault", {})
        algorithm = encryption.get("SSEAlgorithm")
        kms_key_id = encryption.get("KMSMasterKeyID")
        rule_name = f"encryption_rule_{rule_index}"

        findings = []

        algorithm_supported = algorithm in SUPPORTED_ENCRYPTION_ALGORITHMS

        findings.append(
            SecurityFinding(
                bucket_name=bucket_name,
                check=f"{rule_name}_algorithm",
                passed=algorithm_supported,
                message=(
                    f"Encryption algorithm is {algorithm}."
                    if algorithm_supported
                    else (
                        "Encryption algorithm is missing or unsupported: "
                        f"{algorithm!r}."
                    )
                ),
            )
        )

        if self.expected_algorithm:
            matches_expected = algorithm == self.expected_algorithm

            findings.append(
                SecurityFinding(
                    bucket_name=bucket_name,
                    check=f"{rule_name}_expected_algorithm",
                    passed=matches_expected,
                    message=(
                        f"Encryption algorithm matches "
                        f"{self.expected_algorithm}."
                        if matches_expected
                        else (
                            f"Expected {self.expected_algorithm}, "
                            f"but found {algorithm!r}."
                        )
                    ),
                )
            )

        if algorithm in {"aws:kms", "aws:kms:dsse"}:
            findings.extend(
                self._validate_kms_configuration(
                    bucket_name=bucket_name,
                    rule_name=rule_name,
                    kms_key_id=kms_key_id,
                    rule=rule,
                )
            )

        return findings

    def _validate_kms_configuration(
        self,
        bucket_name: str,
        rule_name: str,
        kms_key_id: str | None,
        rule: dict[str, Any],
    ) -> list[SecurityFinding]:
        """Validate KMS key configuration and optional bucket-key policy."""
        findings = []

        if self.expected_kms_key_id:
            key_matches = kms_key_id == self.expected_kms_key_id

            findings.append(
                SecurityFinding(
                    bucket_name=bucket_name,
                    check=f"{rule_name}_kms_key",
                    passed=key_matches,
                    message=(
                        "Configured KMS key matches the expected key."
                        if key_matches
                        else (
                            f"Expected KMS key {self.expected_kms_key_id}, "
                            f"but found {kms_key_id!r}."
                        )
                    ),
                )
            )
        else:
            findings.append(
                SecurityFinding(
                    bucket_name=bucket_name,
                    check=f"{rule_name}_kms_key",
                    passed=bool(kms_key_id),
                    message=(
                        "A KMS key identifier is configured."
                        if kms_key_id
                        else "KMS encryption is configured without an "
                        "explicit KMS key identifier."
                    ),
                )
            )

        if self.require_bucket_key:
            bucket_key_enabled = (
                rule.get("BucketKeyEnabled") is True
            )

            findings.append(
                SecurityFinding(
                    bucket_name=bucket_name,
                    check=f"{rule_name}_bucket_key",
                    passed=bucket_key_enabled,
                    message=(
                        "S3 Bucket Key is enabled."
                        if bucket_key_enabled
                        else "S3 Bucket Key is missing or disabled."
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
        raise EncryptionCheckError(
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
        description="Validate S3 bucket default encryption."
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
        "--algorithm",
        choices=sorted(SUPPORTED_ENCRYPTION_ALGORITHMS),
        help="Require a specific default encryption algorithm.",
    )
    parser.add_argument(
        "--kms-key-id",
        help="Require a specific KMS key ID or ARN.",
    )
    parser.add_argument(
        "--require-bucket-key",
        action="store_true",
        help="Require S3 Bucket Key for KMS encryption rules.",
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
    """Run encryption checks and return an appropriate exit code."""
    arguments = parse_arguments()
    configure_logging(arguments.verbose)

    try:
        session = boto3.Session(region_name=arguments.region)
        s3_client = session.client("s3")

        checker = S3EncryptionChecker(
            s3_client=s3_client,
            expected_algorithm=arguments.algorithm,
            expected_kms_key_id=arguments.kms_key_id,
            require_bucket_key=arguments.require_bucket_key,
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
            LOGGER.info("Inspecting encryption for bucket: %s", bucket_name)

            try:
                findings = checker.check_bucket(bucket_name)
                all_findings.extend(findings)
            except EncryptionCheckError:
                inspection_failed = True
                LOGGER.exception(
                    "Encryption inspection failed for bucket %s.",
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

        LOGGER.info("All encryption checks passed.")
        return 0

    except (EncryptionCheckError, BotoCoreError, ClientError, ValueError):
        LOGGER.exception("S3 encryption validation could not complete.")
        return 2


if __name__ == "__main__":
    sys.exit(main())