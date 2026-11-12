import argparse
import json
import logging
import sys
from dataclasses import dataclass
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError


LOGGER = logging.getLogger("s3_replication_validation")


@dataclass(frozen=True)
class ReplicationFinding:
    """Represent an S3 replication validation result."""

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


class ReplicationValidationError(Exception):
    """Represent an error that prevents reliable replication validation."""


class S3ReplicationValidator:
    """Validate S3 replication configuration and destination settings."""

    def __init__(
        self,
        s3_client: Any | None = None,
        expected_destination_bucket: str | None = None,
        expected_role_arn: str | None = None,
        required_rule_ids: set[str] | None = None,
        require_replication_metrics: bool = False,
        require_replication_time_control: bool = False,
        require_delete_marker_replication: bool = False,
    ) -> None:
        self.s3_client = s3_client or boto3.client("s3")
        self.expected_destination_bucket = expected_destination_bucket
        self.expected_role_arn = expected_role_arn
        self.required_rule_ids = set(required_rule_ids or set())
        self.require_replication_metrics = require_replication_metrics
        self.require_replication_time_control = (
            require_replication_time_control
        )
        self.require_delete_marker_replication = (
            require_delete_marker_replication
        )

    def validate_bucket(
        self,
        bucket_name: str,
    ) -> list[ReplicationFinding]:
        """Validate replication configuration for a source bucket."""
        if not bucket_name or not bucket_name.strip():
            raise ValueError("Source bucket name must not be empty.")

        try:
            response = self.s3_client.get_bucket_replication(
                Bucket=bucket_name
            )
        except ClientError as exc:
            error_code = self._error_code(exc)

            if error_code == "ReplicationConfigurationNotFoundError":
                return [
                    self._finding(
                        bucket_name,
                        "replication_configuration",
                        False,
                        "Bucket has no replication configuration.",
                    )
                ]

            raise ReplicationValidationError(
                f"Unable to retrieve replication configuration for "
                f"{bucket_name}: {error_code}"
            ) from exc
        except BotoCoreError as exc:
            raise ReplicationValidationError(
                f"Unable to retrieve replication configuration for "
                f"{bucket_name}: {exc}"
            ) from exc

        configuration = response.get("ReplicationConfiguration", {})
        rules = configuration.get("Rules", [])
        role_arn = configuration.get("Role")

        if not rules:
            return [
                self._finding(
                    bucket_name,
                    "replication_rules",
                    False,
                    "Replication configuration contains no rules.",
                )
            ]

        findings = []

        if self.expected_role_arn:
            role_matches = role_arn == self.expected_role_arn

            findings.append(
                self._finding(
                    bucket_name,
                    "replication_role",
                    role_matches,
                    (
                        "Replication role matches the expected role."
                        if role_matches
                        else (
                            f"Expected role {self.expected_role_arn}, "
                            f"but found {role_arn!r}."
                        )
                    ),
                )
            )
        elif not role_arn:
            findings.append(
                self._finding(
                    bucket_name,
                    "replication_role",
                    False,
                    "Replication configuration does not specify a role ARN.",
                )
            )
        else:
            findings.append(
                self._finding(
                    bucket_name,
                    "replication_role",
                    True,
                    "Replication configuration specifies a role ARN.",
                    severity="INFO",
                )
            )

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
                    "All required replication rule IDs are present."
                    if not missing_rule_ids
                    else (
                        "Missing required replication rule IDs: "
                        f"{', '.join(sorted(missing_rule_ids))}."
                    )
                ),
                severity="INFO" if not missing_rule_ids else "HIGH",
            )
        )

        return findings

    def _validate_rule(
        self,
        bucket_name: str,
        rule: dict[str, Any],
        rule_index: int,
    ) -> list[ReplicationFinding]:
        """Validate an individual replication rule."""
        rule_id = rule.get("ID") or f"rule_{rule_index}"
        prefix = f"rule_{rule_id}"
        findings = []

        status = rule.get("Status")
        enabled = status == "Enabled"

        findings.append(
            self._finding(
                bucket_name,
                f"{prefix}_status",
                enabled,
                (
                    f"Replication rule '{rule_id}' is enabled."
                    if enabled
                    else (
                        f"Replication rule '{rule_id}' is not enabled. "
                        f"Current status: {status!r}."
                    )
                ),
                severity="INFO" if enabled else "HIGH",
            )
        )

        destination = rule.get("Destination", {})
        destination_bucket_arn = destination.get("Bucket")
        destination_bucket = self._bucket_name_from_arn(
            destination_bucket_arn
        )

        if self.expected_destination_bucket:
            destination_matches = (
                destination_bucket == self.expected_destination_bucket
            )

            findings.append(
                self._finding(
                    bucket_name,
                    f"{prefix}_destination",
                    destination_matches,
                    (
                        f"Rule '{rule_id}' targets the expected destination "
                        f"bucket {self.expected_destination_bucket}."
                        if destination_matches
                        else (
                            f"Rule '{rule_id}' targets "
                            f"{destination_bucket_arn!r}; expected bucket "
                            f"{self.expected_destination_bucket!r}."
                        )
                    ),
                )
            )
        else:
            destination_configured = bool(destination_bucket_arn)

            findings.append(
                self._finding(
                    bucket_name,
                    f"{prefix}_destination",
                    destination_configured,
                    (
                        f"Rule '{rule_id}' has a destination bucket ARN."
                        if destination_configured
                        else (
                            f"Rule '{rule_id}' does not specify a "
                            "destination bucket ARN."
                        )
                    ),
                    severity="INFO" if destination_configured else "HIGH",
                )
            )

        if self.require_replication_metrics:
            metrics = destination.get("Metrics", {})
            metrics_enabled = (
                metrics.get("Status") == "Enabled"
                and bool(metrics.get("EventThreshold"))
            )

            findings.append(
                self._finding(
                    bucket_name,
                    f"{prefix}_replication_metrics",
                    metrics_enabled,
                    (
                        f"Replication metrics are enabled for rule "
                        f"'{rule_id}'."
                        if metrics_enabled
                        else (
                            f"Replication metrics or their event threshold "
                            f"are not enabled for rule '{rule_id}'."
                        )
                    ),
                )
            )

        if self.require_replication_time_control:
            rtc = destination.get("ReplicationTime", {})
            rtc_enabled = (
                rtc.get("Status") == "Enabled"
                and bool(rtc.get("Time"))
            )

            findings.append(
                self._finding(
                    bucket_name,
                    f"{prefix}_replication_time_control",
                    rtc_enabled,
                    (
                        f"Replication Time Control is enabled for rule "
                        f"'{rule_id}'."
                        if rtc_enabled
                        else (
                            f"Replication Time Control is not enabled "
                            f"for rule '{rule_id}'."
                        )
                    ),
                )
            )

        if self.require_delete_marker_replication:
            delete_marker = rule.get("DeleteMarkerReplication", {})
            delete_marker_enabled = (
                delete_marker.get("Status") == "Enabled"
            )

            findings.append(
                self._finding(
                    bucket_name,
                    f"{prefix}_delete_marker_replication",
                    delete_marker_enabled,
                    (
                        f"Delete marker replication is enabled for rule "
                        f"'{rule_id}'."
                        if delete_marker_enabled
                        else (
                            f"Delete marker replication is not enabled "
                            f"for rule '{rule_id}'."
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
        if not bucket_arn:
            return None

        prefix = "arn:aws:s3:::"

        if not bucket_arn.startswith(prefix):
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
        bucket_name: str,
        check: str,
        passed: bool,
        message: str,
        severity: str = "HIGH",
    ) -> ReplicationFinding:
        """Create a replication validation finding."""
        return ReplicationFinding(
            bucket_name=bucket_name,
            check=check,
            passed=passed,
            message=message,
            severity=severity,
        )


def parse_rule_ids(values: list[str] | None) -> set[str]:
    """Parse comma-separated replication rule IDs."""
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
            "Validate Amazon S3 replication configuration before release."
        )
    )

    parser.add_argument(
        "--bucket",
        action="append",
        dest="buckets",
        required=True,
        help=(
            "Source S3 bucket to validate. Repeat this option to validate "
            "multiple source buckets."
        ),
    )
    parser.add_argument(
        "--region",
        help="AWS Region used to configure the S3 client.",
    )
    parser.add_argument(
        "--destination-bucket",
        help="Expected destination bucket name.",
    )
    parser.add_argument(
        "--role-arn",
        help="Expected IAM replication role ARN.",
    )
    parser.add_argument(
        "--required-rule-id",
        action="append",
        dest="required_rule_ids",
        help=(
            "Required replication rule ID. Accepts comma-separated values "
            "and can be repeated."
        ),
    )
    parser.add_argument(
        "--require-replication-metrics",
        action="store_true",
        help="Require replication metrics and an event threshold.",
    )
    parser.add_argument(
        "--require-replication-time-control",
        action="store_true",
        help="Require Replication Time Control for each rule.",
    )
    parser.add_argument(
        "--require-delete-marker-replication",
        action="store_true",
        help="Require delete marker replication for each rule.",
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
    """Run replication validation and return a CI-friendly exit code."""
    arguments = parse_arguments()
    configure_logging(arguments.verbose)

    try:
        required_rule_ids = parse_rule_ids(arguments.required_rule_ids)

        session = boto3.Session(region_name=arguments.region)
        s3_client = session.client("s3")

        validator = S3ReplicationValidator(
            s3_client=s3_client,
            expected_destination_bucket=arguments.destination_bucket,
            expected_role_arn=arguments.role_arn,
            required_rule_ids=required_rule_ids,
            require_replication_metrics=(
                arguments.require_replication_metrics
            ),
            require_replication_time_control=(
                arguments.require_replication_time_control
            ),
            require_delete_marker_replication=(
                arguments.require_delete_marker_replication
            ),
        )

        all_findings = []
        inspection_failed = False

        for bucket_name in sorted(set(arguments.buckets)):
            LOGGER.info(
                "Validating replication configuration for source bucket %s.",
                bucket_name,
            )

            try:
                findings = validator.validate_bucket(bucket_name)
                all_findings.extend(findings)
            except ReplicationValidationError:
                inspection_failed = True
                LOGGER.exception(
                    "Replication validation could not complete for %s.",
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
                "%d replication validation check(s) failed.",
                len(failed_findings),
            )
            return 1

        LOGGER.info("All S3 replication checks passed.")
        return 0

    except (
        BotoCoreError,
        ClientError,
        ReplicationValidationError,
        ValueError,
    ):
        LOGGER.exception("S3 replication validation could not complete.")
        return 2


if __name__ == "__main__":
    sys.exit(main())