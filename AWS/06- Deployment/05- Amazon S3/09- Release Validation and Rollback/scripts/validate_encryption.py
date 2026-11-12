import argparse
import json
import logging
import sys
from dataclasses import dataclass
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError


LOGGER = logging.getLogger("s3_encryption_validation")

SUPPORTED_ENCRYPTION_ALGORITHMS = {
    "AES256",
    "aws:kms",
    "aws:kms:dsse",
}


@dataclass(frozen=True)
class EncryptionFinding:
    """Represent an S3 encryption validation result."""

    bucket_name: str
    check: str
    passed: bool
    message: str
    severity: str = "HIGH"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable finding."""
        return {
            "bucket": self.bucket_name,
            "check": self.check,
            "passed": self.passed,
            "severity": self.severity,
            "message": self.message,
        }


class EncryptionValidationError(Exception):
    """Represent an error that prevents reliable encryption validation."""


class S3EncryptionValidator:
    """Validate S3 bucket encryption configuration before release."""

    def __init__(
        self,
        s3_client: Any | None = None,
        expected_algorithm: str = "AES256",
        expected_kms_key_id: str | None = None,
        require_bucket_key: bool = False,
        require_encryption_context: bool = False,
    ) -> None:
        if expected_algorithm not in SUPPORTED_ENCRYPTION_ALGORITHMS:
            raise ValueError(
                f"Unsupported encryption algorithm: {expected_algorithm}"
            )

        if expected_kms_key_id and expected_algorithm not in {
            "aws:kms",
            "aws:kms:dsse",
        }:
            raise ValueError(
                "An expected KMS key requires aws:kms or aws:kms:dsse."
            )

        if require_bucket_key and expected_algorithm not in {
            "aws:kms",
            "aws:kms:dsse",
        }:
            raise ValueError(
                "S3 Bucket Key validation requires KMS encryption."
            )

        self.s3_client = s3_client or boto3.client("s3")
        self.expected_algorithm = expected_algorithm
        self.expected_kms_key_id = expected_kms_key_id
        self.require_bucket_key = require_bucket_key
        self.require_encryption_context = require_encryption_context

    def validate_bucket(
        self,
        bucket_name: str,
    ) -> list[EncryptionFinding]:
        """Validate default encryption and optional encryption settings."""
        if not bucket_name or not bucket_name.strip():
            raise ValueError("Bucket name must not be empty.")

        try:
            response = self.s3_client.get_bucket_encryption(
                Bucket=bucket_name
            )
        except ClientError as exc:
            error_code = self._error_code(exc)

            if error_code == "ServerSideEncryptionConfigurationNotFoundError":
                return [
                    self._finding(
                        bucket_name,
                        "default_encryption",
                        False,
                        "Default server-side encryption is not configured.",
                    )
                ]

            raise EncryptionValidationError(
                f"Unable to retrieve encryption configuration for "
                f"{bucket_name}: {error_code}"
            ) from exc
        except BotoCoreError as exc:
            raise EncryptionValidationError(
                f"Unable to retrieve encryption configuration for "
                f"{bucket_name}: {exc}"
            ) from exc

        rules = response.get(
            "ServerSideEncryptionConfiguration", {}
        ).get("Rules", [])

        if not rules:
            return [
                self._finding(
                    bucket_name,
                    "default_encryption",
                    False,
                    "Encryption configuration contains no rules.",
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
    ) -> list[EncryptionFinding]:
        """Validate one default encryption rule."""
        prefix = f"encryption_rule_{rule_index}"
        findings = []

        encryption = rule.get("ApplyServerSideEncryptionByDefault", {})
        algorithm = encryption.get("SSEAlgorithm")
        kms_key_id = encryption.get("KMSMasterKeyID")

        algorithm_matches = algorithm == self.expected_algorithm

        findings.append(
            self._finding(
                bucket_name,
                f"{prefix}_algorithm",
                algorithm_matches,
                (
                    f"Default encryption algorithm is {algorithm}."
                    if algorithm_matches
                    else (
                        f"Expected {self.expected_algorithm}, "
                        f"but found {algorithm!r}."
                    )
                ),
                severity="INFO" if algorithm_matches else "HIGH",
            )
        )

        if not algorithm_matches:
            return findings

        if self.expected_kms_key_id:
            key_matches = kms_key_id == self.expected_kms_key_id

            findings.append(
                self._finding(
                    bucket_name,
                    f"{prefix}_kms_key",
                    key_matches,
                    (
                        "Configured KMS key matches the expected key."
                        if key_matches
                        else (
                            f"Expected KMS key {self.expected_kms_key_id}, "
                            f"but found {kms_key_id!r}."
                        )
                    ),
                )
            )

        if self.require_bucket_key:
            bucket_key_enabled = rule.get("BucketKeyEnabled") is True

            findings.append(
                self._finding(
                    bucket_name,
                    f"{prefix}_bucket_key",
                    bucket_key_enabled,
                    (
                        "S3 Bucket Key is enabled."
                        if bucket_key_enabled
                        else "S3 Bucket Key is missing or disabled."
                    ),
                )
            )

        if self.require_encryption_context:
            context = rule.get("BlockedEncryptionTypes", {})
            findings.append(
                self._finding(
                    bucket_name,
                    f"{prefix}_encryption_context",
                    bool(context),
                    (
                        "Encryption-related rule metadata is present."
                        if context
                        else (
                            "No encryption-context restriction was found. "
                            "This check does not establish object-level "
                            "encryption context enforcement."
                        )
                    ),
                    severity="INFO" if context else "HIGH",
                )
            )

        return findings

    @staticmethod
    def _error_code(exc: ClientError) -> str:
        """Extract an AWS service error code."""
        return exc.response.get("Error", {}).get("Code", "Unknown")

    @staticmethod
    def _finding(
        bucket_name: str,
        check: str,
        passed: bool,
        message: str,
        severity: str = "HIGH",
    ) -> EncryptionFinding:
        """Create a validation finding."""
        return EncryptionFinding(
            bucket_name=bucket_name,
            check=check,
            passed=passed,
            message=message,
            severity=severity,
        )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate Amazon S3 default encryption configuration "
            "before release."
        )
    )

    parser.add_argument(
        "--bucket",
        action="append",
        dest="buckets",
        required=True,
        help=(
            "S3 bucket to validate. Repeat this option to validate "
            "multiple buckets."
        ),
    )
    parser.add_argument(
        "--region",
        help="AWS Region used to configure the S3 client.",
    )
    parser.add_argument(
        "--algorithm",
        choices=sorted(SUPPORTED_ENCRYPTION_ALGORITHMS),
        default="AES256",
        help="Expected default encryption algorithm.",
    )
    parser.add_argument(
        "--kms-key-id",
        help="Expected KMS key ID or ARN.",
    )
    parser.add_argument(
        "--require-bucket-key",
        action="store_true",
        help="Require S3 Bucket Key for the configured KMS encryption rule.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Print validation findings as JSON.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )

    return parser.parse_args()


def configure_logging(verbose: bool = False) -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    """Run encryption validation and return a CI-friendly exit code."""
    arguments = parse_arguments()
    configure_logging(arguments.verbose)

    try:
        session = boto3.Session(region_name=arguments.region)
        s3_client = session.client("s3")

        validator = S3EncryptionValidator(
            s3_client=s3_client,
            expected_algorithm=arguments.algorithm,
            expected_kms_key_id=arguments.kms_key_id,
            require_bucket_key=arguments.require_bucket_key,
        )

        all_findings = []
        inspection_failed = False

        for bucket_name in sorted(set(arguments.buckets)):
            LOGGER.info(
                "Validating default encryption for bucket %s.",
                bucket_name,
            )

            try:
                findings = validator.validate_bucket(bucket_name)
                all_findings.extend(findings)
            except EncryptionValidationError:
                inspection_failed = True
                LOGGER.exception(
                    "Encryption validation could not complete for %s.",
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
            LOGGER.error(
                "%d encryption validation check(s) failed.",
                len(failed_findings),
            )
            return 1

        LOGGER.info("All S3 encryption checks passed.")
        return 0

    except (
        BotoCoreError,
        ClientError,
        EncryptionValidationError,
        ValueError,
    ):
        LOGGER.exception("S3 encryption validation could not complete.")
        return 2


if __name__ == "__main__":
    sys.exit(main())