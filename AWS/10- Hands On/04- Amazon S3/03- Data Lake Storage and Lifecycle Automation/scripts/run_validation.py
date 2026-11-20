#!/usr/bin/env python3
"""Run local, Terraform, and optional AWS validation for the data lake project."""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TERRAFORM_DIR = PROJECT_ROOT / "infrastructure" / "terraform"
SAMPLE_DATA_PATH = PROJECT_ROOT / "data" / "samples" / "sample_events.json"
TESTS_DIR = PROJECT_ROOT / "tests"

LOGGER = logging.getLogger("data_lake_validation")

EXPECTED_BUCKET_RESOURCES = {
    "raw_data": "aws_s3_bucket.raw_data",
    "processed_data": "aws_s3_bucket.processed_data",
    "analytics": "aws_s3_bucket.analytics",
}

EXPECTED_SAMPLE_FIELDS = {
    "event_id",
    "event_timestamp",
    "event_date",
    "tenant_id",
    "event_type",
    "user_id",
    "amount",
    "currency",
    "source",
    "attributes",
}


@dataclass
class ValidationResult:
    """Collect validation outcomes without stopping at the first failure."""

    checks: int = 0
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def successful(self) -> bool:
        return not self.failures

    def passed(self, message: str) -> None:
        self.checks += 1
        LOGGER.info("[PASS] %s", message)

    def failed(self, message: str) -> None:
        self.checks += 1
        self.failures.append(message)
        LOGGER.error("[FAIL] %s", message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)
        LOGGER.warning("[WARN] %s", message)


def configure_logging(verbose: bool = False) -> None:
    """Configure consistent console logging."""

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def run_command(
    command: list[str],
    *,
    working_directory: Path,
    result: ValidationResult,
    description: str,
    required: bool = True,
) -> bool:
    """Execute a command and record its result."""

    LOGGER.info("Running: %s", description)

    try:
        completed = subprocess.run(
            command,
            cwd=working_directory,
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
    except FileNotFoundError:
        message = (
            f"Required executable was not found for '{description}': "
            f"{command[0]}"
        )

        if required:
            result.failed(message)
        else:
            result.warning(message)

        return False
    except OSError as exc:
        result.failed(f"Unable to execute '{description}': {exc}")
        return False

    if completed.stdout.strip():
        LOGGER.info("%s", completed.stdout.strip())

    if completed.stderr.strip():
        if completed.returncode == 0:
            LOGGER.debug("%s", completed.stderr.strip())
        else:
            LOGGER.error("%s", completed.stderr.strip())

    if completed.returncode != 0:
        result.failed(
            f"{description} failed with exit code "
            f"{completed.returncode}."
        )
        return False

    result.passed(description)
    return True


def validate_sample_dataset(result: ValidationResult) -> None:
    """Validate the supplied JSON sample dataset and its event structure."""

    if not SAMPLE_DATA_PATH.is_file():
        result.failed(f"Sample dataset does not exist: {SAMPLE_DATA_PATH}")
        return

    try:
        with SAMPLE_DATA_PATH.open("r", encoding="utf-8") as sample_file:
            events = json.load(sample_file)
    except (OSError, json.JSONDecodeError) as exc:
        result.failed(f"Unable to load sample dataset: {exc}")
        return

    if not isinstance(events, list):
        result.failed("Sample dataset must contain a top-level JSON array.")
        return

    if not events:
        result.failed("Sample dataset contains no events.")
        return

    result.passed(f"Loaded {len(events)} sample events.")

    event_ids: set[str] = set()
    event_dates: set[str] = set()
    event_types: set[str] = set()
    currencies: set[str] = set()

    for index, event in enumerate(events):
        location = f"Sample event at index {index}"

        if not isinstance(event, dict):
            result.failed(f"{location} must be a JSON object.")
            continue

        missing_fields = EXPECTED_SAMPLE_FIELDS.difference(event)

        if missing_fields:
            result.failed(
                f"{location} is missing fields: "
                f"{', '.join(sorted(missing_fields))}."
            )
            continue

        event_id = event.get("event_id")
        event_timestamp = event.get("event_timestamp")
        event_date = event.get("event_date")
        amount = event.get("amount")

        if not isinstance(event_id, str) or not event_id.strip():
            result.failed(f"{location} has an invalid event_id.")
        elif event_id in event_ids:
            result.failed(f"{location} has a duplicate event_id.")
        else:
            event_ids.add(event_id)

        if not isinstance(event_timestamp, str):
            result.failed(f"{location} has an invalid event_timestamp.")
        elif not event_timestamp.endswith("Z"):
            result.failed(
                f"{location} event_timestamp must use the UTC Z suffix."
            )
        elif not isinstance(event_date, str):
            result.failed(f"{location} has an invalid event_date.")
        elif event_timestamp[:10] != event_date:
            result.failed(
                f"{location} event_date does not match its timestamp date."
            )
        else:
            event_dates.add(event_date)

        if not isinstance(amount, str):
            result.failed(f"{location} amount must be a decimal string.")
        else:
            try:
                float(amount)
            except ValueError:
                result.failed(f"{location} amount is not numeric.")

        for field_name in (
            "tenant_id",
            "event_type",
            "user_id",
            "currency",
            "source",
        ):
            value = event.get(field_name)

            if not isinstance(value, str) or not value.strip():
                result.failed(
                    f"{location} field '{field_name}' must be "
                    "a non-empty string."
                )

        attributes = event.get("attributes")

        if not isinstance(attributes, dict):
            result.failed(f"{location} attributes must be a JSON object.")

        if isinstance(event.get("event_type"), str):
            event_types.add(event["event_type"])

        if isinstance(event.get("currency"), str):
            currencies.add(event["currency"])

    if len(event_ids) == len(events):
        result.passed("Sample event identifiers are unique.")

    if event_dates:
        result.passed(
            f"Sample dataset contains {len(event_dates)} distinct event dates."
        )

    if event_types:
        result.passed(
            "Sample event types: "
            + ", ".join(sorted(event_types))
            + "."
        )

    if currencies:
        result.passed(
            "Sample currencies: "
            + ", ".join(sorted(currencies))
            + "."
        )


def validate_project_structure(result: ValidationResult) -> None:
    """Check required project directories and implementation files."""

    required_paths = [
        PROJECT_ROOT / "data" / "samples",
        PROJECT_ROOT / "infrastructure" / "terraform",
        PROJECT_ROOT / "scripts",
        PROJECT_ROOT / "src" / "analytics",
        PROJECT_ROOT / "src" / "catalog",
        PROJECT_ROOT / "src" / "ingestion",
        PROJECT_ROOT / "src" / "lifecycle",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "src" / "ingestion" / "validate_dataset.py",
        PROJECT_ROOT / "src" / "ingestion" / "upload_dataset.py",
        PROJECT_ROOT / "src" / "lifecycle" / "evaluate_lifecycle_rules.py",
        PROJECT_ROOT / "src" / "lifecycle" / "verify_storage_transitions.py",
        PROJECT_ROOT / "src" / "analytics" / "validate_query_results.py",
    ]

    missing_paths = [
        path for path in required_paths if not path.exists()
    ]

    if missing_paths:
        for path in missing_paths:
            result.failed(
                f"Required project path is missing: "
                f"{path.relative_to(PROJECT_ROOT)}"
            )
        return

    result.passed("Required project directories and implementation files exist.")


def validate_python_sources(result: ValidationResult) -> None:
    """Compile project Python sources without executing application code."""

    source_directories = [
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "scripts",
        PROJECT_ROOT / "src",
        PROJECT_ROOT / "tests",
    ]

    source_files = [
        path
        for directory in source_directories
        for path in directory.rglob("*.py")
        if "__pycache__" not in path.parts
    ]

    if not source_files:
        result.failed("No Python source files were found.")
        return

    compile_command = [
        sys.executable,
        "-m",
        "compileall",
        "-q",
        *[str(path) for path in source_files],
    ]

    run_command(
        compile_command,
        working_directory=PROJECT_ROOT,
        result=result,
        description=f"Compile {len(source_files)} Python source files",
    )


def validate_pytest_suite(
    result: ValidationResult,
    *,
    test_path: str | None = None,
) -> None:
    """Run the project's automated test suite."""

    if not TESTS_DIR.is_dir():
        result.failed(f"Tests directory does not exist: {TESTS_DIR}")
        return

    target = test_path or str(TESTS_DIR)

    run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            target,
        ],
        working_directory=PROJECT_ROOT,
        result=result,
        description="Run project pytest suite",
    )


def validate_terraform(
    result: ValidationResult,
    *,
    initialize: bool,
) -> None:
    """Check Terraform formatting and validate the root configuration."""

    if not TERRAFORM_DIR.is_dir():
        result.failed(
            f"Terraform directory does not exist: {TERRAFORM_DIR}"
        )
        return

    if initialize:
        initialized = run_command(
            [
                "terraform",
                "init",
                "-backend=false",
                "-input=false",
                "-no-color",
            ],
            working_directory=TERRAFORM_DIR,
            result=result,
            description="Initialize Terraform without configuring a backend",
        )

        if not initialized:
            return

    formatting_ok = run_command(
        [
            "terraform",
            "fmt",
            "-check",
            "-recursive",
        ],
        working_directory=TERRAFORM_DIR,
        result=result,
        description="Check Terraform formatting",
    )

    if not formatting_ok:
        LOGGER.warning(
            "Terraform validation will continue, but formatting must be fixed."
        )

    run_command(
        [
            "terraform",
            "validate",
            "-no-color",
        ],
        working_directory=TERRAFORM_DIR,
        result=result,
        description="Validate Terraform configuration",
    )


def extract_bucket_names_from_state(
    state: dict[str, Any],
) -> dict[str, str]:
    """Extract the three project bucket names from Terraform state."""

    bucket_names: dict[str, str] = {}

    def inspect_resources(resources: list[dict[str, Any]]) -> None:
        for resource in resources:
            resource_type = resource.get("type")
            resource_name = resource.get("name")
            address = f"{resource_type}.{resource_name}"

            for logical_name, expected_address in (
                EXPECTED_BUCKET_RESOURCES.items()
            ):
                if address != expected_address:
                    continue

                instances = resource.get("instances", [])

                if not instances:
                    continue

                attributes = instances[0].get("attributes", {})
                bucket_name = attributes.get("bucket")

                if isinstance(bucket_name, str) and bucket_name:
                    bucket_names[logical_name] = bucket_name

    inspect_resources(state.get("resources", []))

    for module in state.get("child_modules", []):
        inspect_resources(module.get("resources", []))

    return bucket_names


def load_terraform_state(
    result: ValidationResult,
) -> dict[str, str] | None:
    """Read Terraform state without printing its contents."""

    completed = subprocess.run(
        ["terraform", "state", "pull"],
        cwd=TERRAFORM_DIR,
        check=False,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )

    if completed.returncode != 0:
        error_message = completed.stderr.strip() or "Unknown Terraform error."
        result.failed(
            "Unable to read Terraform state. Deploy the project first "
            "and verify the configured Terraform workspace. "
            f"Details: {error_message}"
        )
        return None

    try:
        state = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        result.failed(f"Terraform returned invalid state JSON: {exc}")
        return None

    bucket_names = extract_bucket_names_from_state(state)

    missing_buckets = (
        set(EXPECTED_BUCKET_RESOURCES) - set(bucket_names)
    )

    if missing_buckets:
        result.failed(
            "Terraform state does not contain all expected S3 buckets: "
            + ", ".join(sorted(missing_buckets))
        )
        return None

    result.passed("Retrieved all three S3 bucket names from Terraform state.")
    return bucket_names


def validate_bucket_configuration(
    s3_client: Any,
    *,
    bucket_name: str,
    logical_name: str,
    result: ValidationResult,
) -> None:
    """Verify security and storage configuration for a project bucket."""

    try:
        s3_client.head_bucket(Bucket=bucket_name)
        result.passed(f"{logical_name} bucket is accessible: {bucket_name}.")
    except Exception as exc:
        result.failed(
            f"Unable to access {logical_name} bucket '{bucket_name}': {exc}"
        )
        return

    try:
        response = s3_client.get_public_access_block(
            Bucket=bucket_name
        )
        configuration = response["PublicAccessBlockConfiguration"]

        required_settings = (
            "BlockPublicAcls",
            "IgnorePublicAcls",
            "BlockPublicPolicy",
            "RestrictPublicBuckets",
        )

        missing_settings = [
            setting
            for setting in required_settings
            if configuration.get(setting) is not True
        ]

        if missing_settings:
            result.failed(
                f"{logical_name} bucket has incomplete public access "
                f"blocking: {', '.join(missing_settings)}."
            )
        else:
            result.passed(
                f"{logical_name} bucket blocks all public access."
            )
    except Exception as exc:
        result.failed(
            f"Unable to verify public access blocking for "
            f"{logical_name} bucket: {exc}"
        )

    try:
        response = s3_client.get_bucket_ownership_controls(
            Bucket=bucket_name
        )
        rules = response.get("OwnershipControls", {}).get("Rules", [])

        if any(
            rule.get("ObjectOwnership") == "BucketOwnerEnforced"
            for rule in rules
        ):
            result.passed(
                f"{logical_name} bucket enforces BucketOwnerEnforced ownership."
            )
        else:
            result.failed(
                f"{logical_name} bucket does not enforce "
                "BucketOwnerEnforced ownership."
            )
    except Exception as exc:
        result.failed(
            f"Unable to verify ownership controls for "
            f"{logical_name} bucket: {exc}"
        )

    try:
        response = s3_client.get_bucket_encryption(
            Bucket=bucket_name
        )
        rules = response.get("ServerSideEncryptionConfiguration", {}).get(
            "Rules",
            [],
        )

        uses_kms = any(
            rule.get(
                "ApplyServerSideEncryptionByDefault",
                {},
            ).get("SSEAlgorithm") == "aws:kms"
            for rule in rules
        )

        if uses_kms:
            result.passed(
                f"{logical_name} bucket has default SSE-KMS encryption."
            )
        else:
            result.failed(
                f"{logical_name} bucket does not have default SSE-KMS encryption."
            )
    except Exception as exc:
        result.failed(
            f"Unable to verify encryption for {logical_name} bucket: {exc}"
        )

    try:
        response = s3_client.get_bucket_versioning(
            Bucket=bucket_name
        )
        status = response.get("Status", "Disabled")

        if status in {"Enabled", "Suspended"}:
            result.passed(
                f"{logical_name} bucket versioning status is {status}."
            )
        else:
            result.warning(
                f"{logical_name} bucket versioning is not enabled."
            )
    except Exception as exc:
        result.failed(
            f"Unable to verify versioning for {logical_name} bucket: {exc}"
        )


def validate_raw_bucket_lifecycle(
    s3_client: Any,
    *,
    bucket_name: str,
    result: ValidationResult,
) -> None:
    """Verify the raw bucket lifecycle rule and its expected prefix."""

    try:
        response = s3_client.get_bucket_lifecycle_configuration(
            Bucket=bucket_name
        )
    except Exception as exc:
        error_code = getattr(
            getattr(exc, "response", {}).get("Error", {}),
            "Code",
            "",
        )

        if error_code == "NoSuchLifecycleConfiguration":
            result.failed(
                "Raw data bucket has no lifecycle configuration."
            )
        else:
            result.failed(
                f"Unable to retrieve raw data lifecycle configuration: {exc}"
            )
        return

    rules = response.get("Rules", [])

    expected_rule = next(
        (
            rule
            for rule in rules
            if rule.get("ID")
            == "raw-events-storage-transition-and-retention"
        ),
        None,
    )

    if expected_rule is None:
        result.failed(
            "Expected raw data lifecycle rule was not found."
        )
        return

    if expected_rule.get("Status") != "Enabled":
        result.failed("Raw data lifecycle rule is not enabled.")
    else:
        result.passed("Raw data lifecycle rule is enabled.")

    filter_prefix = (
        expected_rule.get("Filter", {}).get("Prefix")
        or expected_rule.get("Filter", {}).get("And", {}).get("Prefix")
        or ""
    )

    if not filter_prefix.endswith("raw/events/"):
        result.warning(
            "Lifecycle rule prefix differs from the expected default "
            "'raw/events/'. Verify it against the active Terraform variables."
        )
    else:
        result.passed(
            "Lifecycle rule targets the expected raw/events/ prefix."
        )

    transitions = {
        transition.get("StorageClass")
        for transition in expected_rule.get("Transitions", [])
    }

    if {"STANDARD_IA", "GLACIER"}.issubset(transitions):
        result.passed(
            "Lifecycle rule includes Standard-IA and Glacier transitions."
        )
    else:
        result.failed(
            "Lifecycle rule is missing a Standard-IA or Glacier transition."
        )

    multipart_cleanup = expected_rule.get(
        "AbortIncompleteMultipartUpload",
        {},
    )

    if multipart_cleanup.get("DaysAfterInitiation", 0) > 0:
        result.passed(
            "Lifecycle rule configures incomplete multipart upload cleanup."
        )
    else:
        result.failed(
            "Lifecycle rule does not configure incomplete multipart upload cleanup."
        )


def validate_aws_resources(result: ValidationResult) -> None:
    """Verify deployed S3 resources using the active AWS credentials."""

    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError:
        result.failed(
            "AWS validation requires boto3 and botocore. "
            "Install them with: python -m pip install boto3"
        )
        return

    try:
        session = boto3.Session()
        sts_client = session.client("sts")
        identity = sts_client.get_caller_identity()
        account_id = identity.get("Account", "unknown")

        result.passed(
            f"AWS credentials are valid for account {account_id}."
        )

        expected_account_id = os.environ.get("EXPECTED_AWS_ACCOUNT_ID")

        if expected_account_id and account_id != expected_account_id:
            result.failed(
                "Authenticated AWS account does not match "
                "EXPECTED_AWS_ACCOUNT_ID."
            )
            return

        region = (
            os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION")
            or "ap-south-1"
        )

        s3_client = session.client("s3", region_name=region)

    except (BotoCoreError, ClientError) as exc:
        result.failed(f"Unable to initialize AWS validation: {exc}")
        return

    bucket_names = load_terraform_state(result)

    if bucket_names is None:
        return

    for logical_name, bucket_name in bucket_names.items():
        validate_bucket_configuration(
            s3_client,
            bucket_name=bucket_name,
            logical_name=logical_name,
            result=result,
        )

    validate_raw_bucket_lifecycle(
        s3_client,
        bucket_name=bucket_names["raw_data"],
        result=result,
    )


def parse_arguments() -> argparse.Namespace:
    """Parse validation options."""

    parser = argparse.ArgumentParser(
        description=(
            "Validate the data lake sample dataset, Python code, "
            "tests, Terraform configuration, and optional AWS resources."
        )
    )

    parser.add_argument(
        "--aws",
        action="store_true",
        help=(
            "Validate deployed S3 resources. Requires boto3, valid AWS "
            "credentials, and an initialized Terraform workspace."
        ),
    )

    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip the pytest suite.",
    )

    parser.add_argument(
        "--skip-python-compile",
        action="store_true",
        help="Skip Python source compilation.",
    )

    parser.add_argument(
        "--skip-terraform",
        action="store_true",
        help="Skip Terraform formatting and validation.",
    )

    parser.add_argument(
        "--terraform-init",
        action="store_true",
        help=(
            "Run terraform init -backend=false before Terraform validation."
        ),
    )

    parser.add_argument(
        "--test-path",
        help=(
            "Optional pytest target relative to the project root. "
            "Defaults to the tests directory."
        ),
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )

    return parser.parse_args()


def print_report(result: ValidationResult) -> None:
    """Print the final validation report."""

    LOGGER.info("")
    LOGGER.info("=" * 72)
    LOGGER.info("DATA LAKE VALIDATION REPORT")
    LOGGER.info("=" * 72)
    LOGGER.info("Checks executed: %s", result.checks)
    LOGGER.info("Failures: %s", len(result.failures))
    LOGGER.info("Warnings: %s", len(result.warnings))

    if result.failures:
        LOGGER.error("Validation completed with failures.")

        for failure in result.failures:
            LOGGER.error(" - %s", failure)
    else:
        LOGGER.info("All executed validation checks passed.")

    if result.warnings:
        LOGGER.warning("Warnings:")

        for warning in result.warnings:
            LOGGER.warning(" - %s", warning)

    LOGGER.info("=" * 72)


def main() -> int:
    """Execute the configured validation workflow."""

    arguments = parse_arguments()
    configure_logging(arguments.verbose)

    result = ValidationResult()

    LOGGER.info("Project root: %s", PROJECT_ROOT)
    LOGGER.info("Starting data lake validation.")

    validate_project_structure(result)
    validate_sample_dataset(result)

    if not arguments.skip_python_compile:
        validate_python_sources(result)

    if not arguments.skip_tests:
        validate_pytest_suite(
            result,
            test_path=arguments.test_path,
        )

    if not arguments.skip_terraform:
        validate_terraform(
            result,
            initialize=arguments.terraform_init,
        )

    if arguments.aws:
        validate_aws_resources(result)

    print_report(result)

    return 0 if result.successful else 1


if __name__ == "__main__":
    raise SystemExit(main())