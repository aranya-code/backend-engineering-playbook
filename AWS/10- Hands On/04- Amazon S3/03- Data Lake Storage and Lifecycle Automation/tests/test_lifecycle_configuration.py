"""Tests for the S3 data lake lifecycle configuration.

These tests inspect the Terraform lifecycle configuration statically. They do
not require AWS credentials, provision resources, or wait for actual S3
storage-class transitions.

The tests protect the project's lifecycle contract:

- Lifecycle rules apply only to the configured raw-events prefix.
- Current objects transition to Standard-IA and then Glacier Flexible
  Retrieval.
- Current object expiration can be disabled.
- Noncurrent-version expiration is conditional on bucket versioning.
- Incomplete multipart uploads are cleaned up.
- Terraform preconditions prevent invalid transition and retention ordering.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE_TERRAFORM_PATH = (
    PROJECT_ROOT
    / "infrastructure"
    / "terraform"
    / "lifecycle.tf"
)
VARIABLES_TERRAFORM_PATH = (
    PROJECT_ROOT
    / "infrastructure"
    / "terraform"
    / "variables.tf"
)


@pytest.fixture(scope="module")
def lifecycle_terraform() -> str:
    """Load the lifecycle Terraform configuration."""
    assert LIFECYCLE_TERRAFORM_PATH.is_file(), (
        f"Lifecycle Terraform file not found: {LIFECYCLE_TERRAFORM_PATH}"
    )

    return LIFECYCLE_TERRAFORM_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def variables_terraform() -> str:
    """Load lifecycle variable declarations."""
    assert VARIABLES_TERRAFORM_PATH.is_file(), (
        f"Terraform variables file not found: {VARIABLES_TERRAFORM_PATH}"
    )

    return VARIABLES_TERRAFORM_PATH.read_text(encoding="utf-8")


def extract_block(
    source: str,
    declaration: str,
) -> str:
    """Extract a balanced Terraform block beginning at a declaration.

    This lightweight parser is sufficient for checking the project's
    straightforward Terraform resource and variable blocks. It intentionally
    does not attempt to interpret Terraform expressions or heredocs.
    """
    declaration_match = re.search(
        re.escape(declaration) + r"\s*\{",
        source,
    )

    assert declaration_match is not None, (
        f"Terraform declaration not found: {declaration}"
    )

    opening_brace = source.find(
        "{",
        declaration_match.start(),
    )

    depth = 0
    in_string = False
    escaped = False

    for index in range(opening_brace, len(source)):
        character = source[index]

        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False

            continue

        if character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1

            if depth == 0:
                return source[opening_brace : index + 1]

    raise AssertionError(
        f"Unbalanced Terraform block: {declaration}"
    )


def extract_variable_block(
    source: str,
    variable_name: str,
) -> str:
    """Extract one Terraform variable declaration."""
    return extract_block(
        source,
        f'variable "{variable_name}"',
    )


def test_lifecycle_resource_targets_raw_data_bucket(
    lifecycle_terraform: str,
) -> None:
    """Lifecycle management must be attached to the raw data bucket."""
    resource = extract_block(
        lifecycle_terraform,
        'resource "aws_s3_bucket_lifecycle_configuration" "raw_data"',
    )

    assert "bucket = aws_s3_bucket.raw_data.id" in resource


def test_lifecycle_configuration_is_conditionally_created(
    lifecycle_terraform: str,
) -> None:
    """The lifecycle resource must respect the project feature flag."""
    resource = extract_block(
        lifecycle_terraform,
        'resource "aws_s3_bucket_lifecycle_configuration" "raw_data"',
    )

    assert (
        "count = var.enable_lifecycle_configuration ? 1 : 0"
        in resource
    )


def test_lifecycle_rule_is_enabled(
    lifecycle_terraform: str,
) -> None:
    """The configured raw-data lifecycle rule must be enabled."""
    resource = extract_block(
        lifecycle_terraform,
        'resource "aws_s3_bucket_lifecycle_configuration" "raw_data"',
    )

    rule = extract_block(
        resource,
        "rule",
    )

    assert 'id     = "raw-events-storage-transition-and-retention"' in rule
    assert 'status = "Enabled"' in rule


def test_lifecycle_rule_filters_raw_events_prefix(
    lifecycle_terraform: str,
) -> None:
    """Lifecycle actions must not affect unrelated bucket prefixes."""
    resource = extract_block(
        lifecycle_terraform,
        'resource "aws_s3_bucket_lifecycle_configuration" "raw_data"',
    )

    rule = extract_block(
        resource,
        "rule",
    )

    filter_block = extract_block(
        rule,
        "filter",
    )

    assert 'prefix = "${var.raw_data_prefix}/"' in filter_block


def test_standard_ia_transition_uses_configured_day(
    lifecycle_terraform: str,
) -> None:
    """Current objects must transition to Standard-IA at the configured age."""
    resource = extract_block(
        lifecycle_terraform,
        'resource "aws_s3_bucket_lifecycle_configuration" "raw_data"',
    )

    transitions = re.findall(
        r"transition\s*\{([^{}]*)\}",
        resource,
        flags=re.DOTALL,
    )

    assert any(
        re.search(
            r"days\s*=\s*var\.lifecycle_transition_to_ia_days",
            transition,
        )
        and re.search(
            r'storage_class\s*=\s*"STANDARD_IA"',
            transition,
        )
        for transition in transitions
    )


def test_glacier_transition_uses_configured_day(
    lifecycle_terraform: str,
) -> None:
    """Current objects must transition to Glacier Flexible Retrieval."""
    resource = extract_block(
        lifecycle_terraform,
        'resource "aws_s3_bucket_lifecycle_configuration" "raw_data"',
    )

    transitions = re.findall(
        r"transition\s*\{([^{}]*)\}",
        resource,
        flags=re.DOTALL,
    )

    assert any(
        re.search(
            r"days\s*=\s*var\.lifecycle_transition_to_glacier_days",
            transition,
        )
        and re.search(
            r'storage_class\s*=\s*"GLACIER"',
            transition,
        )
        for transition in transitions
    )


def test_current_object_expiration_can_be_disabled(
    lifecycle_terraform: str,
) -> None:
    """A zero expiration value must omit the expiration configuration."""
    resource = extract_block(
        lifecycle_terraform,
        'resource "aws_s3_bucket_lifecycle_configuration" "raw_data"',
    )

    expiration = extract_block(
        resource,
        "dynamic \"expiration\"",
    )

    assert (
        "var.lifecycle_expiration_days > 0"
        in expiration
    )
    assert "for_each" in expiration
    assert "days = expiration.value" in expiration


def test_noncurrent_version_expiration_requires_versioning(
    lifecycle_terraform: str,
) -> None:
    """Noncurrent-version cleanup must only be configured with versioning."""
    resource = extract_block(
        lifecycle_terraform,
        'resource "aws_s3_bucket_lifecycle_configuration" "raw_data"',
    )

    noncurrent_expiration = extract_block(
        resource,
        'dynamic "noncurrent_version_expiration"',
    )

    assert "var.enable_bucket_versioning" in noncurrent_expiration
    assert "var.noncurrent_version_expiration_days > 0" in (
        noncurrent_expiration
    )
    assert "noncurrent_days = noncurrent_version_expiration.value" in (
        noncurrent_expiration
    )


def test_incomplete_multipart_uploads_are_aborted(
    lifecycle_terraform: str,
) -> None:
    """Incomplete multipart uploads must have a configured cleanup policy."""
    resource = extract_block(
        lifecycle_terraform,
        'resource "aws_s3_bucket_lifecycle_configuration" "raw_data"',
    )

    abort_rule = extract_block(
        resource,
        "abort_incomplete_multipart_upload",
    )

    assert (
        "days_after_initiation = "
        "var.abort_incomplete_multipart_upload_days"
        in abort_rule
    )


def test_lifecycle_configuration_depends_on_bucket_versioning(
    lifecycle_terraform: str,
) -> None:
    """Lifecycle configuration must be applied after versioning."""
    resource = extract_block(
        lifecycle_terraform,
        'resource "aws_s3_bucket_lifecycle_configuration" "raw_data"',
    )

    assert re.search(
        r"depends_on\s*=\s*\[\s*"
        r"aws_s3_bucket_versioning\.raw_data\s*"
        r"\]",
        resource,
    )


def test_glacier_transition_must_follow_standard_ia(
    lifecycle_terraform: str,
) -> None:
    """Terraform must reject a Glacier transition before Standard-IA."""
    resource = extract_block(
        lifecycle_terraform,
        'resource "aws_s3_bucket_lifecycle_configuration" "raw_data"',
    )

    lifecycle = extract_block(
        resource,
        "lifecycle",
    )

    assert (
        "var.lifecycle_transition_to_glacier_days >"
        in lifecycle
    )
    assert "var.lifecycle_transition_to_ia_days" in lifecycle
    assert (
        "The Glacier transition must occur after the "
        "Standard-IA transition."
        in lifecycle
    )


def test_expiration_must_follow_glacier_transition(
    lifecycle_terraform: str,
) -> None:
    """Enabled expiration must occur after the Glacier transition."""
    resource = extract_block(
        lifecycle_terraform,
        'resource "aws_s3_bucket_lifecycle_configuration" "raw_data"',
    )

    lifecycle = extract_block(
        resource,
        "lifecycle",
    )

    assert "var.lifecycle_expiration_days == 0" in lifecycle
    assert (
        "var.lifecycle_expiration_days > "
        "var.lifecycle_transition_to_glacier_days"
        in lifecycle
    )
    assert (
        "Raw data expiration must occur after the configured "
        "Glacier transition"
        in lifecycle
    )


@pytest.mark.parametrize(
    ("variable_name", "expected_default"),
    [
        ("lifecycle_transition_to_ia_days", "30"),
        ("lifecycle_transition_to_glacier_days", "90"),
        ("lifecycle_expiration_days", "365"),
        ("noncurrent_version_expiration_days", "90"),
        ("abort_incomplete_multipart_upload_days", "7"),
    ],
)
def test_lifecycle_variables_have_expected_defaults(
    variables_terraform: str,
    variable_name: str,
    expected_default: str,
) -> None:
    """Lifecycle defaults must match the documented project configuration."""
    variable = extract_variable_block(
        variables_terraform,
        variable_name,
    )

    assert re.search(
        rf"\bdefault\s*=\s*{re.escape(expected_default)}\b",
        variable,
    )


def test_standard_ia_minimum_transition_age_is_validated(
    variables_terraform: str,
) -> None:
    """Standard-IA transitions must respect the configured minimum age."""
    variable = extract_variable_block(
        variables_terraform,
        "lifecycle_transition_to_ia_days",
    )

    assert re.search(
        r"condition\s*=\s*var\.lifecycle_transition_to_ia_days\s*>=\s*30",
        variable,
    )


def test_glacier_transition_age_is_validated(
    variables_terraform: str,
) -> None:
    """Glacier transition age must be greater than the Standard-IA age."""
    variable = extract_variable_block(
        variables_terraform,
        "lifecycle_transition_to_glacier_days",
    )

    assert (
        "var.lifecycle_transition_to_glacier_days > "
        "var.lifecycle_transition_to_ia_days"
        in variable
    )


def test_zero_expiration_is_supported(
    variables_terraform: str,
) -> None:
    """Zero must remain a valid value to disable current object expiration."""
    variable = extract_variable_block(
        variables_terraform,
        "lifecycle_expiration_days",
    )

    assert "var.lifecycle_expiration_days >= 0" in variable


def test_noncurrent_expiration_allows_disabled_value(
    variables_terraform: str,
) -> None:
    """Zero must disable noncurrent-version expiration."""
    variable = extract_variable_block(
        variables_terraform,
        "noncurrent_version_expiration_days",
    )

    assert (
        "var.noncurrent_version_expiration_days >= 0"
        in variable
    )


def test_multipart_cleanup_requires_positive_age(
    variables_terraform: str,
) -> None:
    """Incomplete multipart upload cleanup must use a positive day count."""
    variable = extract_variable_block(
        variables_terraform,
        "abort_incomplete_multipart_upload_days",
    )

    assert (
        "var.abort_incomplete_multipart_upload_days >= 1"
        in variable
    )


def test_lifecycle_configuration_does_not_target_other_buckets(
    lifecycle_terraform: str,
) -> None:
    """This project's lifecycle policy is intentionally scoped to raw data."""
    resource = extract_block(
        lifecycle_terraform,
        'resource "aws_s3_bucket_lifecycle_configuration" "raw_data"',
    )

    assert "aws_s3_bucket.processed_data" not in resource
    assert "aws_s3_bucket.analytics" not in resource
    assert "aws_s3_bucket_lifecycle_configuration" in resource


def test_lifecycle_configuration_does_not_hardcode_bucket_names(
    lifecycle_terraform: str,
) -> None:
    """Lifecycle configuration must use Terraform resource references."""
    resource = extract_block(
        lifecycle_terraform,
        'resource "aws_s3_bucket_lifecycle_configuration" "raw_data"',
    )

    assert "bucket = aws_s3_bucket.raw_data.id" in resource
    assert "s3://" not in resource