from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError


LOGGER = logging.getLogger("verify_bucket_security")

PUBLIC_ACCESS_BLOCK_SETTINGS = (
    "BlockPublicAcls",
    "IgnorePublicAcls",
    "BlockPublicPolicy",
    "RestrictPublicBuckets",
)

EXPECTED_OWNERSHIP = "BucketOwnerEnforced"
EXPECTED_VERSIONING = "Enabled"
EXPECTED_ENCRYPTION = "aws:kms"


@dataclass(frozen=True)
class CheckResult:
    """Represent the outcome of an individual security check."""

    name: str
    passed: bool
    details: str
    required: bool = True


class SecurityVerifier:
    """Inspect S3 bucket security configuration using read-only AWS APIs."""

    def __init__(
        self,
        bucket_name: str,
        region: str | None,
        expected_kms_key: str | None,
        require_tls_deny: bool,
        require_object_lock: bool,
    ) -> None:
        self.bucket_name = bucket_name
        self.expected_kms_key = expected_kms_key
        self.require_tls_deny = require_tls_deny
        self.require_object_lock = require_object_lock
        self.results: list[CheckResult] = []

        session = boto3.Session(region_name=region)
        self.s3 = session.client("s3")

    def record(
        self,
        name: str,
        passed: bool,
        details: str,
        required: bool = True,
    ) -> None:
        """Record and log the outcome of a security check."""
        result = CheckResult(
            name=name,
            passed=passed,
            details=details,
            required=required,
        )
        self.results.append(result)

        if passed:
            LOGGER.info("PASS: %s - %s", name, details)
        elif required:
            LOGGER.error("FAIL: %s - %s", name, details)
        else:
            LOGGER.warning("WARN: %s - %s", name, details)

    def check_bucket_access(self) -> bool:
        """Confirm that the configured bucket exists and is accessible."""
        try:
            response = self.s3.head_bucket(
                Bucket=self.bucket_name,
            )

            region = response.get("BucketRegion")

            self.record(
                "Bucket accessibility",
                True,
                (
                    f"Bucket '{self.bucket_name}' is accessible. "
                    f"Reported Region: {region or 'not returned'}."
                ),
            )
            return True

        except ClientError as exc:
            error = exc.response.get("Error", {})
            code = error.get("Code", "Unknown")
            message = error.get("Message", "No additional details.")

            self.record(
                "Bucket accessibility",
                False,
                f"AWS returned {code}: {message}",
            )
            return False

    def check_public_access_block(self) -> None:
        """Verify that all S3 Block Public Access settings are enabled."""
        try:
            response = self.s3.get_public_access_block(
                Bucket=self.bucket_name,
            )

            configuration = response.get(
                "PublicAccessBlockConfiguration",
                {},
            )

            disabled_settings = [
                setting
                for setting in PUBLIC_ACCESS_BLOCK_SETTINGS
                if configuration.get(setting) is not True
            ]

            if disabled_settings:
                self.record(
                    "Block Public Access",
                    False,
                    (
                        "The following settings are missing or disabled: "
                        + ", ".join(disabled_settings)
                    ),
                )
                return

            self.record(
                "Block Public Access",
                True,
                "All four account-independent bucket settings are enabled.",
            )

        except ClientError as exc:
            error = exc.response.get("Error", {})
            code = error.get("Code", "Unknown")

            self.record(
                "Block Public Access",
                False,
                (
                    f"Unable to inspect bucket public access settings. "
                    f"AWS returned {code}."
                ),
            )

    def check_ownership_controls(self) -> None:
        """Verify that bucket ownership is enforced and ACLs are disabled."""
        try:
            response = self.s3.get_bucket_ownership_controls(
                Bucket=self.bucket_name,
            )

            rules = response.get(
                "OwnershipControls",
                {},
            ).get("Rules", [])

            ownership_modes = {
                rule.get("ObjectOwnership")
                for rule in rules
            }

            passed = EXPECTED_OWNERSHIP in ownership_modes

            self.record(
                "Object Ownership",
                passed,
                (
                    "Bucket ownership is enforced and ACLs are disabled."
                    if passed
                    else (
                        "Expected BucketOwnerEnforced ownership. "
                        f"Found: {sorted(ownership_modes)}."
                    )
                ),
            )

        except ClientError as exc:
            error = exc.response.get("Error", {})
            code = error.get("Code", "Unknown")

            self.record(
                "Object Ownership",
                False,
                (
                    "Unable to inspect ownership controls. "
                    f"AWS returned {code}."
                ),
            )

    def check_versioning(self) -> None:
        """Verify that bucket versioning is enabled."""
        try:
            response = self.s3.get_bucket_versioning(
                Bucket=self.bucket_name,
            )

            status = response.get("Status", "NotConfigured")
            passed = status == EXPECTED_VERSIONING

            self.record(
                "Bucket versioning",
                passed,
                (
                    "Versioning is enabled."
                    if passed
                    else (
                        f"Expected '{EXPECTED_VERSIONING}', "
                        f"found '{status}'."
                    )
                ),
            )

        except ClientError as exc:
            error = exc.response.get("Error", {})
            code = error.get("Code", "Unknown")

            self.record(
                "Bucket versioning",
                False,
                f"Unable to inspect versioning. AWS returned {code}.",
            )

    def check_default_encryption(self) -> None:
        """Verify default SSE-KMS encryption and an optional expected key."""
        try:
            response = self.s3.get_bucket_encryption(
                Bucket=self.bucket_name,
            )

            rules = response.get(
                "ServerSideEncryptionConfiguration",
                {},
            ).get("Rules", [])

            if not rules:
                self.record(
                    "Default encryption",
                    False,
                    "No default server-side encryption rules were returned.",
                )
                return

            invalid_rules: list[str] = []
            configured_keys: list[str] = []

            for index, rule in enumerate(rules, start=1):
                encryption = rule.get(
                    "ApplyServerSideEncryptionByDefault",
                    {},
                )

                algorithm = encryption.get("SSEAlgorithm")
                key_id = encryption.get("KMSMasterKeyID")

                if algorithm != EXPECTED_ENCRYPTION:
                    invalid_rules.append(
                        f"Rule {index} uses {algorithm or 'no algorithm'}"
                    )
                    continue

                if not key_id:
                    invalid_rules.append(
                        f"Rule {index} does not specify a KMS key identifier"
                    )
                    continue

                configured_keys.append(key_id)

                if (
                    self.expected_kms_key
                    and key_id != self.expected_kms_key
                ):
                    invalid_rules.append(
                        f"Rule {index} uses an unexpected KMS key"
                    )

            if invalid_rules:
                self.record(
                    "Default encryption",
                    False,
                    "; ".join(invalid_rules),
                )
                return

            self.record(
                "Default encryption",
                True,
                (
                    "SSE-KMS is configured for all returned encryption rules. "
                    f"KMS key identifiers: {', '.join(configured_keys)}."
                ),
            )

            bucket_key_enabled = any(
                rule.get("BucketKeyEnabled") is True
                for rule in rules
            )

            self.record(
                "S3 Bucket Keys",
                bucket_key_enabled,
                (
                    "S3 Bucket Keys are enabled."
                    if bucket_key_enabled
                    else "S3 Bucket Keys are not enabled in the returned rules."
                ),
                required=False,
            )

        except ClientError as exc:
            error = exc.response.get("Error", {})
            code = error.get("Code", "Unknown")

            self.record(
                "Default encryption",
                False,
                (
                    "Unable to inspect default encryption. "
                    f"AWS returned {code}."
                ),
            )

    @staticmethod
    def policy_has_tls_deny(policy: dict[str, Any]) -> bool:
        """
        Detect a bucket-policy Deny for requests using insecure transport.

        The check recognizes Bool and BoolIfExists conditions where
        aws:SecureTransport is explicitly false.
        """
        statements = policy.get("Statement", [])

        if isinstance(statements, dict):
            statements = [statements]

        for statement in statements:
            if not isinstance(statement, dict):
                continue

            if statement.get("Effect", "").lower() != "deny":
                continue

            condition = statement.get("Condition", {})

            if not isinstance(condition, dict):
                continue

            for operator in ("Bool", "BoolIfExists"):
                conditions = condition.get(operator, {})

                if not isinstance(conditions, dict):
                    continue

                secure_transport = conditions.get(
                    "aws:SecureTransport"
                )

                values = (
                    secure_transport
                    if isinstance(secure_transport, list)
                    else [secure_transport]
                )

                if any(
                    isinstance(value, str)
                    and value.lower() == "false"
                    for value in values
                ):
                    return True

        return False

    def check_tls_enforcement(self) -> None:
        """Verify that the bucket policy explicitly denies insecure transport."""
        try:
            response = self.s3.get_bucket_policy(
                Bucket=self.bucket_name,
            )

            policy_document = json.loads(
                response.get("Policy", "{}")
            )

            passed = self.policy_has_tls_deny(policy_document)

            self.record(
                "TLS enforcement",
                passed,
                (
                    "Bucket policy contains an explicit Deny for "
                    "requests using insecure transport."
                    if passed
                    else (
                        "No explicit Deny for "
                        "aws:SecureTransport=false was found."
                    )
                ),
                required=self.require_tls_deny,
            )

        except ClientError as exc:
            error = exc.response.get("Error", {})
            code = error.get("Code", "Unknown")

            if code in {"NoSuchBucketPolicy", "NoSuchPolicy"}:
                self.record(
                    "TLS enforcement",
                    False,
                    "The bucket does not have a bucket policy.",
                    required=self.require_tls_deny,
                )
                return

            self.record(
                "TLS enforcement",
                False,
                (
                    "Unable to inspect the bucket policy. "
                    f"AWS returned {code}."
                ),
                required=self.require_tls_deny,
            )

        except json.JSONDecodeError:
            self.record(
                "TLS enforcement",
                False,
                "The bucket policy response is not valid JSON.",
                required=self.require_tls_deny,
            )

    def check_object_lock(self) -> None:
        """Inspect Object Lock configuration when explicitly required."""
        try:
            response = self.s3.get_object_lock_configuration(
                Bucket=self.bucket_name,
            )

            configuration = response.get(
                "ObjectLockConfiguration",
                {},
            )

            enabled = (
                configuration.get("ObjectLockEnabled") == "Enabled"
            )

            self.record(
                "Object Lock",
                enabled,
                (
                    "Object Lock is enabled."
                    if enabled
                    else "Object Lock is not enabled."
                ),
                required=self.require_object_lock,
            )

        except ClientError as exc:
            error = exc.response.get("Error", {})
            code = error.get("Code", "Unknown")

            self.record(
                "Object Lock",
                False,
                (
                    "Unable to inspect Object Lock configuration. "
                    f"AWS returned {code}."
                ),
                required=self.require_object_lock,
            )

    def run(self) -> list[CheckResult]:
        """Execute all configured read-only security checks."""
        LOGGER.info(
            "Starting security verification for bucket '%s'.",
            self.bucket_name,
        )

        if not self.check_bucket_access():
            LOGGER.error(
                "Bucket access could not be established. "
                "Remaining checks were skipped."
            )
            return self.results

        self.check_public_access_block()
        self.check_ownership_controls()
        self.check_versioning()
        self.check_default_encryption()
        self.check_tls_enforcement()

        if self.require_object_lock:
            self.check_object_lock()

        return self.results


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Verify security controls on the Secure File Upload API "
            "Amazon S3 bucket using read-only AWS API operations."
        )
    )

    parser.add_argument(
        "--bucket",
        default=os.getenv("S3_BUCKET_NAME"),
        help="S3 bucket name. Defaults to S3_BUCKET_NAME.",
    )

    parser.add_argument(
        "--region",
        default=(
            os.getenv("AWS_REGION")
            or os.getenv("AWS_DEFAULT_REGION")
        ),
        help=(
            "AWS Region for the S3 client. Defaults to AWS_REGION "
            "or AWS_DEFAULT_REGION."
        ),
    )

    parser.add_argument(
        "--expected-kms-key",
        default=os.getenv("S3_KMS_KEY_ID"),
        help=(
            "Expected KMS key ID, ARN, or alias as returned by S3. "
            "Defaults to S3_KMS_KEY_ID. When omitted, any configured "
            "customer-managed KMS key is accepted."
        ),
    )

    parser.add_argument(
        "--allow-missing-tls-deny",
        action="store_true",
        help=(
            "Report missing TLS enforcement as a warning instead of "
            "a required security failure."
        ),
    )

    parser.add_argument(
        "--require-object-lock",
        action="store_true",
        help="Require Object Lock to be enabled on the bucket.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging.",
    )

    return parser.parse_args()


def configure_logging(verbose: bool) -> None:
    """Configure command-line logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def print_summary(results: list[CheckResult]) -> None:
    """Print a concise summary of security verification results."""
    required_checks = [
        result
        for result in results
        if result.required
    ]

    passed_checks = [
        result
        for result in required_checks
        if result.passed
    ]

    failed_checks = [
        result
        for result in required_checks
        if not result.passed
    ]

    warnings = [
        result
        for result in results
        if not result.required and not result.passed
    ]

    LOGGER.info("Security verification summary")
    LOGGER.info(
        "Required checks: %d passed, %d failed.",
        len(passed_checks),
        len(failed_checks),
    )
    LOGGER.info(
        "Optional checks with warnings: %d.",
        len(warnings),
    )

    if failed_checks:
        LOGGER.error("Required security checks failed:")
        for result in failed_checks:
            LOGGER.error("- %s: %s", result.name, result.details)

    if warnings:
        LOGGER.warning("Optional checks requiring attention:")
        for result in warnings:
            LOGGER.warning("- %s: %s", result.name, result.details)


def main() -> int:
    """Run S3 bucket security verification."""
    args = parse_args()
    configure_logging(args.verbose)

    if not args.bucket:
        LOGGER.error(
            "An S3 bucket name is required. Use --bucket or set S3_BUCKET_NAME."
        )
        return 2

    try:
        verifier = SecurityVerifier(
            bucket_name=args.bucket,
            region=args.region,
            expected_kms_key=args.expected_kms_key,
            require_tls_deny=not args.allow_missing_tls_deny,
            require_object_lock=args.require_object_lock,
        )

        results = verifier.run()
        print_summary(results)

    except NoCredentialsError:
        LOGGER.error(
            "AWS credentials were not found. Configure an AWS profile, "
            "environment credentials, or an IAM role."
        )
        return 2

    except (BotoCoreError, ClientError) as exc:
        LOGGER.error("AWS security verification failed: %s", exc)
        return 2

    required_failures = [
        result
        for result in results
        if result.required and not result.passed
    ]

    if required_failures:
        LOGGER.error(
            "Bucket security verification failed with %d required failure(s).",
            len(required_failures),
        )
        return 1

    LOGGER.info("Bucket security verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())