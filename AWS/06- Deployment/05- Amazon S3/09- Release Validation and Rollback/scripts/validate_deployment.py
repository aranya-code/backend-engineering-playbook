import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import boto3
from botocore.exceptions import BotoCoreError, ClientError


LOGGER = logging.getLogger("s3_deployment_validation")


@dataclass(frozen=True)
class DeploymentFinding:
    """Represent an individual deployment validation result."""

    check: str
    passed: bool
    message: str
    severity: str = "HIGH"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable finding."""
        return {
            "check": self.check,
            "passed": self.passed,
            "severity": self.severity,
            "message": self.message,
        }


class DeploymentValidationError(Exception):
    """Represent an error that prevents reliable deployment validation."""


class S3DeploymentValidator:
    """Validate deployed S3 resources and application endpoints."""

    def __init__(
        self,
        s3_client: Any | None = None,
        expected_encryption: str = "AES256",
        expected_kms_key_id: str | None = None,
        require_versioning: bool = True,
        require_public_access_block: bool = True,
        expected_replication_destination: str | None = None,
        expected_replication_role_arn: str | None = None,
        require_lifecycle_configuration: bool = False,
        require_replication: bool = False,
        website_url: str | None = None,
        expected_http_status: int = 200,
        timeout_seconds: float = 10.0,
        retries: int = 3,
    ) -> None:
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
                "An expected KMS key requires aws:kms or aws:kms:dsse."
            )

        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")

        if retries < 1:
            raise ValueError("retries must be at least one.")

        if not 100 <= expected_http_status <= 599:
            raise ValueError("expected_http_status must be between 100 and 599.")

        self.s3_client = s3_client or boto3.client("s3")
        self.expected_encryption = expected_encryption
        self.expected_kms_key_id = expected_kms_key_id
        self.require_versioning = require_versioning
        self.require_public_access_block = require_public_access_block
        self.expected_replication_destination = (
            expected_replication_destination
        )
        self.expected_replication_role_arn = expected_replication_role_arn
        self.require_lifecycle_configuration = (
            require_lifecycle_configuration
        )
        self.require_replication = require_replication
        self.website_url = website_url
        self.expected_http_status = expected_http_status
        self.timeout_seconds = timeout_seconds
        self.retries = retries

    def validate_bucket(
        self,
        bucket_name: str,
    ) -> list[DeploymentFinding]:
        """Validate the required configuration of one deployed bucket."""
        if not bucket_name or not bucket_name.strip():
            raise ValueError("Bucket name must not be empty.")

        findings = []

        checks = [
            self._check_bucket_access,
            self._check_encryption,
            self._check_versioning,
        ]

        if self.require_public_access_block:
            checks.append(self._check_public_access_block)

        if self.require_lifecycle_configuration:
            checks.append(self._check_lifecycle)

        if self.require_replication:
            checks.append(self._check_replication)

        for check in checks:
            try:
                findings.extend(check(bucket_name))
            except DeploymentValidationError:
                raise
            except (ClientError, BotoCoreError) as exc:
                raise DeploymentValidationError(
                    f"{check.__name__} failed for {bucket_name}: {exc}"
                ) from exc

        return findings

    def validate_website(self) -> list[DeploymentFinding]:
        """Verify an HTTP or HTTPS deployment endpoint."""
        if not self.website_url:
            return []

        findings = []

        for attempt in range(1, self.retries + 1):
            try:
                request = Request(
                    self.website_url,
                    headers={
                        "User-Agent": "s3-deployment-validator/1.0",
                    },
                    method="GET",
                )

                with urlopen(
                    request,
                    timeout=self.timeout_seconds,
                ) as response:
                    actual_status = response.status

                passed = actual_status == self.expected_http_status

                findings.append(
                    self._finding(
                        "website_smoke_test",
                        passed,
                        (
                            f"Endpoint returned HTTP {actual_status}."
                            if passed
                            else (
                                f"Expected HTTP {self.expected_http_status}, "
                                f"but received HTTP {actual_status}."
                            )
                        ),
                        severity="INFO" if passed else "HIGH",
                    )
                )

                return findings

            except HTTPError as exc:
                actual_status = exc.code

                if actual_status == self.expected_http_status:
                    findings.append(
                        self._finding(
                            "website_smoke_test",
                            True,
                            f"Endpoint returned HTTP {actual_status}.",
                            severity="INFO",
                        )
                    )
                    return findings

                message = (
                    f"Endpoint returned HTTP {actual_status}; expected "
                    f"HTTP {self.expected_http_status}."
                )

                if attempt == self.retries:
                    findings.append(
                        self._finding(
                            "website_smoke_test",
                            False,
                            message,
                        )
                    )
                    return findings

                LOGGER.warning(
                    "Website check attempt %d/%d failed: %s",
                    attempt,
                    self.retries,
                    message,
                )

            except (URLError, TimeoutError, OSError) as exc:
                if attempt == self.retries:
                    findings.append(
                        self._finding(
                            "website_smoke_test",
                            False,
                            f"Endpoint request failed: {exc}",
                        )
                    )
                    return findings

                LOGGER.warning(
                    "Website check attempt %d/%d failed: %s",
                    attempt,
                    self.retries,
                    exc,
                )

            time.sleep(min(2 ** (attempt - 1), 8))

        return findings

    def _check_bucket_access(
        self,
        bucket_name: str,
    ) -> list[DeploymentFinding]:
        """Verify that the bucket can be inspected."""
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
        except (ClientError, BotoCoreError) as exc:
            raise DeploymentValidationError(
                f"Cannot access bucket {bucket_name}: {exc}"
            ) from exc

        return [
            self._finding(
                "bucket_access",
                True,
                f"Bucket {bucket_name} is accessible.",
                severity="INFO",
            )
        ]

    def _check_encryption(
        self,
        bucket_name: str,
    ) -> list[DeploymentFinding]:
        """Verify default server-side encryption."""
        try:
            response = self.s3_client.get_bucket_encryption(
                Bucket=bucket_name
            )
        except ClientError as exc:
            if self._error_code(exc) == (
                "ServerSideEncryptionConfigurationNotFoundError"
            ):
                return [
                    self._finding(
                        "default_encryption",
                        False,
                        "Default server-side encryption is not configured.",
                    )
                ]

            raise DeploymentValidationError(
                f"Unable to inspect encryption for {bucket_name}: {exc}"
            ) from exc

        rules = response.get(
            "ServerSideEncryptionConfiguration", {}
        ).get("Rules", [])

        if not rules:
            return [
                self._finding(
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

            algorithm_matches = algorithm == self.expected_encryption

            findings.append(
                self._finding(
                    f"encryption_rule_{index}_algorithm",
                    algorithm_matches,
                    (
                        f"Default encryption uses {algorithm}."
                        if algorithm_matches
                        else (
                            f"Expected {self.expected_encryption}, "
                            f"but found {algorithm!r}."
                        )
                    ),
                    severity="INFO" if algorithm_matches else "HIGH",
                )
            )

            if self.expected_kms_key_id and algorithm_matches:
                key_matches = kms_key_id == self.expected_kms_key_id

                findings.append(
                    self._finding(
                        f"encryption_rule_{index}_kms_key",
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

        return findings

    def _check_versioning(
        self,
        bucket_name: str,
    ) -> list[DeploymentFinding]:
        """Verify bucket versioning status."""
        response = self.s3_client.get_bucket_versioning(
            Bucket=bucket_name
        )

        status = response.get("Status")
        enabled = status == "Enabled"

        if not self.require_versioning:
            return [
                self._finding(
                    "versioning_status",
                    True,
                    f"Versioning status is {status or 'Not configured'}.",
                    severity="INFO",
                )
            ]

        return [
            self._finding(
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

    def _check_public_access_block(
        self,
        bucket_name: str,
    ) -> list[DeploymentFinding]:
        """Verify all four bucket-level Block Public Access settings."""
        required_settings = (
            "BlockPublicAcls",
            "IgnorePublicAcls",
            "BlockPublicPolicy",
            "RestrictPublicBuckets",
        )

        try:
            response = self.s3_client.get_public_access_block(
                Bucket=bucket_name
            )
        except ClientError as exc:
            if self._error_code(exc) == (
                "NoSuchPublicAccessBlockConfiguration"
            ):
                return [
                    self._finding(
                        "public_access_block",
                        False,
                        "Bucket-level Block Public Access is not configured.",
                    )
                ]

            raise DeploymentValidationError(
                f"Unable to inspect public access settings for "
                f"{bucket_name}: {exc}"
            ) from exc

        configuration = response.get(
            "PublicAccessBlockConfiguration",
            {},
        )

        missing_settings = [
            setting
            for setting in required_settings
            if configuration.get(setting) is not True
        ]

        passed = not missing_settings

        return [
            self._finding(
                "public_access_block",
                passed,
                (
                    "All four Block Public Access settings are enabled."
                    if passed
                    else (
                        "Missing or disabled settings: "
                        f"{', '.join(missing_settings)}."
                    )
                ),
                severity="INFO" if passed else "HIGH",
            )
        ]

    def _check_lifecycle(
        self,
        bucket_name: str,
    ) -> list[DeploymentFinding]:
        """Verify that lifecycle configuration exists and has rules."""
        try:
            response = self.s3_client.get_bucket_lifecycle_configuration(
                Bucket=bucket_name
            )
        except ClientError as exc:
            if self._error_code(exc) == "NoSuchLifecycleConfiguration":
                return [
                    self._finding(
                        "lifecycle_configuration",
                        False,
                        "Bucket has no lifecycle configuration.",
                    )
                ]

            raise DeploymentValidationError(
                f"Unable to inspect lifecycle configuration for "
                f"{bucket_name}: {exc}"
            ) from exc

        rules = response.get("Rules", [])
        enabled_rules = [
            rule
            for rule in rules
            if rule.get("Status") == "Enabled"
        ]

        passed = bool(enabled_rules)

        return [
            self._finding(
                "lifecycle_configuration",
                passed,
                (
                    f"Found {len(enabled_rules)} enabled lifecycle rule(s)."
                    if passed
                    else "No enabled lifecycle rules were found."
                ),
                severity="INFO" if passed else "HIGH",
            )
        ]

    def _check_replication(
        self,
        bucket_name: str,
    ) -> list[DeploymentFinding]:
        """Verify replication rules and configured destinations."""
        try:
            response = self.s3_client.get_bucket_replication(
                Bucket=bucket_name
            )
        except ClientError as exc:
            if self._error_code(exc) == (
                "ReplicationConfigurationNotFoundError"
            ):
                return [
                    self._finding(
                        "replication_configuration",
                        False,
                        "Bucket has no replication configuration.",
                    )
                ]

            raise DeploymentValidationError(
                f"Unable to inspect replication for {bucket_name}: {exc}"
            ) from exc

        configuration = response.get("ReplicationConfiguration", {})
        rules = configuration.get("Rules", [])
        role_arn = configuration.get("Role")

        if not rules:
            return [
                self._finding(
                    "replication_rules",
                    False,
                    "Replication configuration contains no rules.",
                )
            ]

        findings = []

        if self.expected_replication_role_arn:
            role_matches = role_arn == self.expected_replication_role_arn

            findings.append(
                self._finding(
                    "replication_role",
                    role_matches,
                    (
                        "Replication role matches the expected role."
                        if role_matches
                        else (
                            f"Expected role "
                            f"{self.expected_replication_role_arn}, "
                            f"but found {role_arn!r}."
                        )
                    ),
                )
            )

        enabled_rules = [
            rule
            for rule in rules
            if rule.get("Status") == "Enabled"
        ]

        findings.append(
            self._finding(
                "replication_enabled_rules",
                bool(enabled_rules),
                (
                    f"Found {len(enabled_rules)} enabled replication rule(s)."
                    if enabled_rules
                    else "No enabled replication rules were found."
                ),
                severity="INFO" if enabled_rules else "HIGH",
            )
        )

        if self.expected_replication_destination:
            matching_rules = [
                rule
                for rule in enabled_rules
                if self._bucket_name_from_arn(
                    rule.get("Destination", {}).get("Bucket")
                ) == self.expected_replication_destination
            ]

            findings.append(
                self._finding(
                    "replication_destination",
                    bool(matching_rules),
                    (
                        "An enabled replication rule targets the expected "
                        f"destination {self.expected_replication_destination}."
                        if matching_rules
                        else (
                            "No enabled replication rule targets "
                            f"{self.expected_replication_destination}."
                        )
                    ),
                )
            )

        return findings

    @staticmethod
    def _bucket_name_from_arn(
        bucket_arn: str | None,
    ) -> str | None:
        """Extract a bucket name from an S3 bucket ARN."""
        prefix = "arn:aws:s3:::"

        if not bucket_arn or not bucket_arn.startswith(prefix):
            return None

        bucket_name = bucket_arn[len(prefix):]

        if not bucket_name or "/" in bucket_name:
            return None

        return bucket_name

    @staticmethod
    def _error_code(exc: ClientError) -> str:
        """Extract an AWS service error code."""
        return exc.response.get("Error", {}).get("Code", "Unknown")

    @staticmethod
    def _finding(
        check: str,
        passed: bool,
        message: str,
        severity: str = "HIGH",
    ) -> DeploymentFinding:
        """Create a deployment validation finding."""
        return DeploymentFinding(
            check=check,
            passed=passed,
            message=message,
            severity=severity,
        )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate deployed Amazon S3 resources and application endpoints."
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
        help="Expected KMS key ID or ARN.",
    )
    parser.add_argument(
        "--skip-versioning-check",
        action="store_true",
        help="Do not require bucket versioning to be enabled.",
    )
    parser.add_argument(
        "--skip-public-access-check",
        action="store_true",
        help="Do not require bucket-level Block Public Access settings.",
    )
    parser.add_argument(
        "--require-lifecycle",
        action="store_true",
        help="Require at least one enabled lifecycle rule.",
    )
    parser.add_argument(
        "--require-replication",
        action="store_true",
        help="Require at least one enabled replication rule.",
    )
    parser.add_argument(
        "--replication-destination",
        help="Expected replication destination bucket name.",
    )
    parser.add_argument(
        "--replication-role-arn",
        help="Expected replication IAM role ARN.",
    )
    parser.add_argument(
        "--website-url",
        help="Optional HTTP or HTTPS endpoint for a smoke test.",
    )
    parser.add_argument(
        "--expected-http-status",
        type=int,
        default=200,
        help="Expected website response status. Defaults to 200.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP smoke-test timeout in seconds.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Number of HTTP smoke-test attempts.",
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
    """Run deployment validation and return a CI-friendly exit code."""
    arguments = parse_arguments()
    configure_logging(arguments.verbose)

    try:
        session = boto3.Session(region_name=arguments.region)
        s3_client = session.client("s3")

        validator = S3DeploymentValidator(
            s3_client=s3_client,
            expected_encryption=arguments.encryption,
            expected_kms_key_id=arguments.kms_key_id,
            require_versioning=not arguments.skip_versioning_check,
            require_public_access_block=(
                not arguments.skip_public_access_check
            ),
            expected_replication_destination=(
                arguments.replication_destination
            ),
            expected_replication_role_arn=(
                arguments.replication_role_arn
            ),
            require_lifecycle_configuration=arguments.require_lifecycle,
            require_replication=arguments.require_replication,
            website_url=arguments.website_url,
            expected_http_status=arguments.expected_http_status,
            timeout_seconds=arguments.timeout,
            retries=arguments.retries,
        )

        all_findings = []
        inspection_failed = False

        for bucket_name in sorted(set(arguments.buckets)):
            LOGGER.info(
                "Validating deployed S3 bucket %s.",
                bucket_name,
            )

            try:
                all_findings.extend(
                    validator.validate_bucket(bucket_name)
                )
            except DeploymentValidationError:
                inspection_failed = True
                LOGGER.exception(
                    "Deployment validation could not complete for %s.",
                    bucket_name,
                )

        try:
            all_findings.extend(validator.validate_website())
        except (DeploymentValidationError, ValueError):
            inspection_failed = True
            LOGGER.exception("Website smoke test could not complete.")

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
                    f"[{status}] {finding.check} "
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
                "%d deployment validation check(s) failed.",
                len(failed_findings),
            )
            return 1

        LOGGER.info("All deployment validation checks passed.")
        return 0

    except (
        BotoCoreError,
        ClientError,
        DeploymentValidationError,
        ValueError,
    ):
        LOGGER.exception("Deployment validation could not complete.")
        return 2


if __name__ == "__main__":
    sys.exit(main())