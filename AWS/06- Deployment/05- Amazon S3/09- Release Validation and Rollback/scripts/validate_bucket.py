import argparse
import json
import logging
import sys
from dataclasses import dataclass
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError


LOGGER = logging.getLogger("s3_release_validation")

REQUIRED_PUBLIC_ACCESS_BLOCK_SETTINGS = (
    "BlockPublicAcls",
    "IgnorePublicAcls",
    "BlockPublicPolicy",
    "RestrictPublicBuckets",
)

REQUIRED_TAG_KEYS = {
    "Environment",
    "Owner",
    "Project",
    "CostCenter",
}


@dataclass(frozen=True)
class ValidationFinding:
    """Represent an individual bucket validation result."""

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


class BucketValidationError(Exception):
    """Represent an error that prevents reliable bucket validation."""


class S3BucketValidator:
    """Validate essential S3 bucket settings before release."""

    def __init__(
        self,
        s3_client: Any | None = None,
        expected_encryption: str = "AES256",
        expected_kms_key_id: str | None = None,
        required_tags: set[str] | None = None,
        require_versioning: bool = True,
        require_bucket_key: bool = False,
    ) -> None:
        self.s3_client = s3_client or boto3.client("s3")
        self.expected_encryption = expected_encryption
        self.expected_kms_key_id = expected_kms_key_id
        self.required_tags = (
            set(required_tags)
            if required_tags is not None
            else set(REQUIRED_TAG_KEYS)
        )
        self.require_versioning = require_versioning
        self.require_bucket_key = require_bucket_key

        supported_algorithms = {
            "AES256",
            "aws:kms",
            "aws:kms:dsse",
        }

        if expected_encryption not in supported_algorithms:
            raise ValueError(
                f"Unsupported encryption algorithm: {expected_encryption}"
            )

        if expected_kms_key_id and expected_encryption not in {
            "aws:kms",
            "aws:kms:dsse",
        }:
            raise ValueError(
                "A KMS key ID requires aws:kms or aws:kms:dsse encryption."
            )

        if not self.required_tags:
            raise ValueError("At least one required tag must be configured.")

    def validate_bucket(
        self,
        bucket_name: str,
    ) -> list[ValidationFinding]:
        """Run all configured release checks for a bucket."""
        if not bucket_name or not bucket_name.strip():
            raise ValueError("Bucket name must not be empty.")

        findings = []

        checks = (
            self._check_public_access_block,
            self._check_encryption,
            self._check_versioning,
            self._check_required_tags,
        )

        for check in checks:
            findings.extend(check(bucket_name))

        return findings

    def _check_public_access_block(
        self,
        bucket_name: str,
    ) -> list[ValidationFinding]:
        """Require all bucket-level Block Public Access settings."""
        check_name = "public_access_block"

        try:
            response = self.s3_client.get_public_access_block(
                Bucket=bucket_name
            )
        except ClientError as exc:
            error_code = self._error_code(exc)

            if error_code == "NoSuchPublicAccessBlockConfiguration":
                return [
                    self._finding(
                        bucket_name,
                        check_name,
                        False,
                        "Bucket-level Block Public Access configuration "
                        "is missing.",
                    )
                ]

            raise BucketValidationError(
                f"Unable to inspect public access settings for "
                f"{bucket_name}: {error_code}"
            ) from exc
        except BotoCoreError as exc:
            raise BucketValidationError(
                f"Unable to inspect public access settings for "
                f"{bucket_name}: {exc}"
            ) from exc

        configuration = response.get("PublicAccessBlockConfiguration", {})
        missing_settings = [
            setting
            for setting in REQUIRED_PUBLIC_ACCESS_BLOCK_SETTINGS
            if configuration.get(setting) is not True
        ]

        if missing_settings:
            return [
                self._finding(
                    bucket_name,
                    check_name,
                    False,
                    "The following Block Public Access settings are "
                    f"missing or disabled: {', '.join(missing_settings)}.",
                )
            ]

        return [
            self._finding(
                bucket_name,
                check_name,
                True,
                "All four bucket-level Block Public Access settings are enabled.",
                severity="INFO",
            )
        ]

    def _check_encryption(
        self,
        bucket_name: str,
    ) -> list[ValidationFinding]:
        """Validate the bucket's default encryption configuration."""
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
                        "Default server-side encryption configuration "
                        "is missing.",
                    )
                ]

            raise BucketValidationError(
                f"Unable to inspect encryption for {bucket_name}: "
                f"{error_code}"
            ) from exc
        except BotoCoreError as exc:
            raise BucketValidationError(
                f"Unable to inspect encryption for {bucket_name}: {exc}"
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
            encryption = rule.get("ApplyServerSideEncryptionByDefault", {})
            algorithm = encryption.get("SSEAlgorithm")
            kms_key_id = encryption.get("KMSMasterKeyID")
            check_prefix = f"encryption_rule_{index}"

            algorithm_matches = algorithm == self.expected_encryption

            findings.append(
                self._finding(
                    bucket_name,
                    f"{check_prefix}_algorithm",
                    algorithm_matches,
                    (
                        f"Encryption algorithm is {algorithm}."
                        if algorithm_matches
                        else (
                            f"Expected {self.expected_encryption}, "
                            f"but found {algorithm!r}."
                        )
                    ),
                    severity="INFO" if algorithm_matches else "HIGH",
                )
            )

            if not algorithm_matches:
                continue

            if self.expected_kms_key_id:
                key_matches = kms_key_id == self.expected_kms_key_id

                findings.append(
                    self._finding(
                        bucket_name,
                        f"{check_prefix}_kms_key",
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

            if (
                self.require_bucket_key
                and algorithm in {"aws:kms", "aws:kms:dsse"}
            ):
                bucket_key_enabled = rule.get("BucketKeyEnabled") is True

                findings.append(
                    self._finding(
                        bucket_name,
                        f"{check_prefix}_bucket_key",
                        bucket_key_enabled,
                        (
                            "S3 Bucket Key is enabled."
                            if bucket_key_enabled
                            else "S3 Bucket Key is missing or disabled."
                        ),
                    )
                )

        return findings

    def _check_versioning(
        self,
        bucket_name: str,
    ) -> list[ValidationFinding]:
        """Validate bucket versioning when required."""
        try:
            response = self.s3_client.get_bucket_versioning(
                Bucket=bucket_name
            )
        except (ClientError, BotoCoreError) as exc:
            raise BucketValidationError(
                f"Unable to inspect versioning for {bucket_name}: {exc}"
            ) from exc

        status = response.get("Status")
        enabled = status == "Enabled"

        if not self.require_versioning:
            return [
                self._finding(
                    bucket_name,
                    "versioning_status",
                    True,
                    f"Versioning status: {status or 'Not configured'}.",
                    severity="INFO",
                )
            ]

        return [
            self._finding(
                bucket_name,
                "versioning_enabled",
                enabled,
                (
                    "Bucket versioning is enabled."
                    if enabled
                    else (
                        "Bucket versioning is not enabled. "
                        f"Current status: {status or 'Not configured'}."
                    )
                ),
            )
        ]

    def _check_required_tags(
        self,
        bucket_name: str,
    ) -> list[ValidationFinding]:
        """Validate required bucket tag keys."""
        try:
            response = self.s3_client.get_bucket_tagging(
                Bucket=bucket_name
            )
        except ClientError as exc:
            error_code = self._error_code(exc)

            if error_code == "NoSuchTagSet":
                return [
                    self._finding(
                        bucket_name,
                        "required_tags",
                        False,
                        "Bucket has no tag set. Missing required tags: "
                        f"{', '.join(sorted(self.required_tags))}.",
                    )
                ]

            raise BucketValidationError(
                f"Unable to inspect tags for {bucket_name}: {error_code}"
            ) from exc
        except BotoCoreError as exc:
            raise BucketValidationError(
                f"Unable to inspect tags for {bucket_name}: {exc}"
            ) from exc

        actual_tags = {
            tag.get("Key")
            for tag in response.get("TagSet", [])
            if tag.get("Key")
        }

        missing_tags = self.required_tags - actual_tags

        if missing_tags:
            return [
                self._finding(
                    bucket_name,
                    "required_tags",
                    False,
                    "Missing required tag keys: "
                    f"{', '.join(sorted(missing_tags))}.",
                )
            ]

        return [
            self._finding(
                bucket_name,
                "required_tags",
                True,
                "All required tag keys are present.",
                severity="INFO",
            )
        ]

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
    ) -> ValidationFinding:
        """Create a validation finding."""
        return ValidationFinding(
            bucket_name=bucket_name,
            check=check,
            passed=passed,
            message=message,
            severity=severity,
        )


def parse_required_tags(values: list[str] | None) -> set[str]:
    """Parse comma-separated required tag keys."""
    if not values:
        return set(REQUIRED_TAG_KEYS)

    tags = {
        item.strip()
        for value in values
        for item in value.split(",")
        if item.strip()
    }

    if not tags:
        raise ValueError("At least one non-empty required tag is necessary.")

    return tags


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate essential S3 bucket configuration before release."
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
        "--encryption",
        choices=("AES256", "aws:kms", "aws:kms:dsse"),
        default="AES256",
        help="Expected default encryption algorithm.",
    )
    parser.add_argument(
        "--kms-key-id",
        help="Expected KMS key ID or ARN when using KMS encryption.",
    )
    parser.add_argument(
        "--require-bucket-key",
        action="store_true",
        help="Require S3 Bucket Key for KMS encryption rules.",
    )
    parser.add_argument(
        "--required-tags",
        action="append",
        help=(
            "Comma-separated required tag keys. Repeat to add more keys. "
            "Defaults to Environment,Owner,Project,CostCenter."
        ),
    )
    parser.add_argument(
        "--allow-versioning-disabled",
        action="store_true",
        help="Do not fail validation when bucket versioning is disabled.",
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


def configure_logging(verbose: bool = False) -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    """Execute bucket validation and return a CI-friendly exit code."""
    arguments = parse_arguments()
    configure_logging(arguments.verbose)

    try:
        required_tags = parse_required_tags(arguments.required_tags)

        if arguments.require_bucket_key and arguments.encryption not in {
            "aws:kms",
            "aws:kms:dsse",
        }:
            raise ValueError(
                "--require-bucket-key requires KMS encryption."
            )

        session = boto3.Session(region_name=arguments.region)
        s3_client = session.client("s3")

        validator = S3BucketValidator(
            s3_client=s3_client,
            expected_encryption=arguments.encryption,
            expected_kms_key_id=arguments.kms_key_id,
            required_tags=required_tags,
            require_versioning=not arguments.allow_versioning_disabled,
            require_bucket_key=arguments.require_bucket_key,
        )

        all_findings = []
        inspection_failed = False

        for bucket_name in sorted(set(arguments.buckets)):
            LOGGER.info("Validating S3 bucket: %s", bucket_name)

            try:
                findings = validator.validate_bucket(bucket_name)
                all_findings.extend(findings)
            except BucketValidationError:
                inspection_failed = True
                LOGGER.exception(
                    "Validation could not complete for bucket %s.",
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
                "%d validation check(s) failed.",
                len(failed_findings),
            )
            return 1

        LOGGER.info("All S3 bucket release checks passed.")
        return 0

    except (
        BucketValidationError,
        BotoCoreError,
        ClientError,
        ValueError,
    ):
        LOGGER.exception("S3 bucket validation could not complete.")
        return 2


if __name__ == "__main__":
    sys.exit(main())