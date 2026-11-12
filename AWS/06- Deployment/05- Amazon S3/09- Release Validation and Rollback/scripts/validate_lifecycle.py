import argparse
import json
import logging
import sys
from dataclasses import dataclass
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError


LOGGER = logging.getLogger("s3_lifecycle_validation")


@dataclass(frozen=True)
class LifecycleFinding:
    """Represent an S3 lifecycle validation result."""

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


class LifecycleValidationError(Exception):
    """Represent an error that prevents reliable lifecycle validation."""


class S3LifecycleValidator:
    """Validate S3 lifecycle configuration against release requirements."""

    def __init__(
        self,
        s3_client: Any | None = None,
        required_rule_ids: set[str] | None = None,
        required_status: str = "Enabled",
        require_abort_incomplete_multipart: bool = False,
        require_noncurrent_expiration: bool = False,
    ) -> None:
        if required_status not in {"Enabled", "Disabled"}:
            raise ValueError(
                "required_status must be either 'Enabled' or 'Disabled'."
            )

        self.s3_client = s3_client or boto3.client("s3")
        self.required_rule_ids = set(required_rule_ids or set())
        self.required_status = required_status
        self.require_abort_incomplete_multipart = (
            require_abort_incomplete_multipart
        )
        self.require_noncurrent_expiration = require_noncurrent_expiration

    def validate_bucket(
        self,
        bucket_name: str,
    ) -> list[LifecycleFinding]:
        """Validate lifecycle rules configured on a bucket."""
        if not bucket_name or not bucket_name.strip():
            raise ValueError("Bucket name must not be empty.")

        try:
            response = self.s3_client.get_bucket_lifecycle_configuration(
                Bucket=bucket_name
            )
        except ClientError as exc:
            error_code = self._error_code(exc)

            if error_code == "NoSuchLifecycleConfiguration":
                return self._validate_missing_configuration(bucket_name)

            raise LifecycleValidationError(
                f"Unable to retrieve lifecycle configuration for "
                f"{bucket_name}: {error_code}"
            ) from exc
        except BotoCoreError as exc:
            raise LifecycleValidationError(
                f"Unable to retrieve lifecycle configuration for "
                f"{bucket_name}: {exc}"
            ) from exc

        rules = response.get("Rules", [])

        if not rules:
            return self._validate_missing_configuration(bucket_name)

        findings = []
        observed_rule_ids = set()

        for index, rule in enumerate(rules):
            rule_id = rule.get("ID")

            if rule_id:
                observed_rule_ids.add(rule_id)

            findings.extend(
                self._validate_rule(
                    bucket_name=bucket_name,
                    rule=rule,
                    rule_index=index,
                )
            )

        missing_rule_ids = self.required_rule_ids - observed_rule_ids

        findings.append(
            self._finding(
                bucket_name,
                "required_rule_ids",
                not missing_rule_ids,
                (
                    "All required lifecycle rule IDs are present."
                    if not missing_rule_ids
                    else (
                        "Missing required lifecycle rule IDs: "
                        f"{', '.join(sorted(missing_rule_ids))}."
                    )
                ),
                severity="INFO" if not missing_rule_ids else "HIGH",
            )
        )

        return findings

    def _validate_missing_configuration(
        self,
        bucket_name: str,
    ) -> list[LifecycleFinding]:
        """Report missing lifecycle configuration."""
        return [
            self._finding(
                bucket_name,
                "lifecycle_configuration",
                False,
                "Bucket has no lifecycle configuration.",
            ),
            self._finding(
                bucket_name,
                "required_rule_ids",
                not self.required_rule_ids,
                (
                    "No specific lifecycle rule IDs were required."
                    if not self.required_rule_ids
                    else (
                        "Required lifecycle rules are missing: "
                        f"{', '.join(sorted(self.required_rule_ids))}."
                    )
                ),
            ),
        ]

    def _validate_rule(
        self,
        bucket_name: str,
        rule: dict[str, Any],
        rule_index: int,
    ) -> list[LifecycleFinding]:
        """Validate an individual lifecycle rule."""
        rule_id = rule.get("ID") or f"rule_{rule_index}"
        prefix = f"rule_{rule_id}"
        findings = []

        status = rule.get("Status")
        status_matches = status == self.required_status

        findings.append(
            self._finding(
                bucket_name,
                f"{prefix}_status",
                status_matches,
                (
                    f"Rule '{rule_id}' has status {status}."
                    if status_matches
                    else (
                        f"Rule '{rule_id}' must have status "
                        f"{self.required_status}; found {status!r}."
                    )
                ),
                severity="INFO" if status_matches else "HIGH",
            )
        )

        expiration = rule.get("Expiration")
        noncurrent_expiration = rule.get("NoncurrentVersionExpiration")
        abort_multipart = rule.get("AbortIncompleteMultipartUpload")

        if self.require_abort_incomplete_multipart:
            configured = (
                isinstance(abort_multipart, dict)
                and abort_multipart.get("DaysAfterInitiation", 0) > 0
            )

            findings.append(
                self._finding(
                    bucket_name,
                    f"{prefix}_abort_incomplete_multipart",
                    configured,
                    (
                        f"Rule '{rule_id}' configures incomplete multipart "
                        "upload cleanup."
                        if configured
                        else (
                            f"Rule '{rule_id}' does not configure a valid "
                            "AbortIncompleteMultipartUpload action."
                        )
                    ),
                    severity="INFO" if configured else "HIGH",
                )
            )

        if self.require_noncurrent_expiration:
            configured = (
                isinstance(noncurrent_expiration, dict)
                and noncurrent_expiration.get(
                    "NoncurrentDays",
                    0,
                ) > 0
            )

            findings.append(
                self._finding(
                    bucket_name,
                    f"{prefix}_noncurrent_expiration",
                    configured,
                    (
                        f"Rule '{rule_id}' configures noncurrent version "
                        "expiration."
                        if configured
                        else (
                            f"Rule '{rule_id}' does not configure a valid "
                            "NoncurrentVersionExpiration action."
                        )
                    ),
                    severity="INFO" if configured else "HIGH",
                )
            )

        has_lifecycle_action = any(
            (
                isinstance(expiration, dict),
                isinstance(noncurrent_expiration, dict),
                isinstance(abort_multipart, dict),
                bool(rule.get("Transitions")),
                bool(rule.get("NoncurrentVersionTransitions")),
                bool(rule.get("Expiration", {}).get("ExpiredObjectDeleteMarker")),
            )
        )

        findings.append(
            self._finding(
                bucket_name,
                f"{prefix}_actions",
                has_lifecycle_action,
                (
                    f"Rule '{rule_id}' contains at least one lifecycle action."
                    if has_lifecycle_action
                    else (
                        f"Rule '{rule_id}' has no recognized lifecycle action."
                    )
                ),
                severity="INFO" if has_lifecycle_action else "HIGH",
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
    ) -> LifecycleFinding:
        """Create a lifecycle validation finding."""
        return LifecycleFinding(
            bucket_name=bucket_name,
            check=check,
            passed=passed,
            message=message,
            severity=severity,
        )


def parse_rule_ids(values: list[str] | None) -> set[str]:
    """Parse comma-separated lifecycle rule IDs."""
    if not values:
        return set()

    rule_ids = {
        item.strip()
        for value in values
        for item in value.split(",")
        if item.strip()
    }

    if not rule_ids:
        raise ValueError("At least one non-empty rule ID is required.")

    return rule_ids


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate Amazon S3 lifecycle configuration before release."
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
        "--required-rule-id",
        action="append",
        dest="required_rule_ids",
        help=(
            "Required lifecycle rule ID. Accepts comma-separated values "
            "and can be repeated."
        ),
    )
    parser.add_argument(
        "--required-status",
        choices=("Enabled", "Disabled"),
        default="Enabled",
        help="Expected status for every lifecycle rule.",
    )
    parser.add_argument(
        "--require-abort-incomplete-multipart",
        action="store_true",
        help="Require incomplete multipart upload cleanup in each rule.",
    )
    parser.add_argument(
        "--require-noncurrent-expiration",
        action="store_true",
        help="Require noncurrent version expiration in each rule.",
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
    """Run lifecycle validation and return a CI-friendly exit code."""
    arguments = parse_arguments()
    configure_logging(arguments.verbose)

    try:
        required_rule_ids = parse_rule_ids(arguments.required_rule_ids)

        session = boto3.Session(region_name=arguments.region)
        s3_client = session.client("s3")

        validator = S3LifecycleValidator(
            s3_client=s3_client,
            required_rule_ids=required_rule_ids,
            required_status=arguments.required_status,
            require_abort_incomplete_multipart=(
                arguments.require_abort_incomplete_multipart
            ),
            require_noncurrent_expiration=(
                arguments.require_noncurrent_expiration
            ),
        )

        all_findings = []
        inspection_failed = False

        for bucket_name in sorted(set(arguments.buckets)):
            LOGGER.info(
                "Validating lifecycle configuration for bucket %s.",
                bucket_name,
            )

            try:
                findings = validator.validate_bucket(bucket_name)
                all_findings.extend(findings)
            except LifecycleValidationError:
                inspection_failed = True
                LOGGER.exception(
                    "Lifecycle validation could not complete for %s.",
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
                "%d lifecycle validation check(s) failed.",
                len(failed_findings),
            )
            return 1

        LOGGER.info("All S3 lifecycle checks passed.")
        return 0

    except (
        BotoCoreError,
        ClientError,
        LifecycleValidationError,
        ValueError,
    ):
        LOGGER.exception("S3 lifecycle validation could not complete.")
        return 2


if __name__ == "__main__":
    sys.exit(main())