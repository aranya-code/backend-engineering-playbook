#!/usr/bin/env python3
"""Inspect and evaluate the S3 lifecycle configuration for the data lake."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


LOGGER = logging.getLogger("data_lake.lifecycle")

DEFAULT_REGION = os.getenv("AWS_REGION", "ap-south-1")
DEFAULT_BUCKET_NAME = os.getenv("DATA_LAKE_BUCKET_NAME")

LIFECYCLE_ACTION_KEYS = {
    "Expiration",
    "Transitions",
    "NoncurrentVersionExpiration",
    "NoncurrentVersionTransitions",
    "AbortIncompleteMultipartUpload",
}

SUPPORTED_STORAGE_CLASSES = {
    "STANDARD_IA",
    "ONEZONE_IA",
    "INTELLIGENT_TIERING",
    "GLACIER",
    "DEEP_ARCHIVE",
    "GLACIER_IR",
    "EXPRESS_ONEZONE",
}


class LifecycleEvaluationError(RuntimeError):
    """Raised when lifecycle configuration cannot be evaluated."""


def configure_logging(verbose: bool = False) -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def validate_bucket_name(bucket_name: str) -> str:
    """Validate the configured bucket name."""
    normalized_name = bucket_name.strip()

    if not normalized_name:
        raise ValueError("S3 bucket name cannot be empty.")

    if normalized_name.startswith("s3://"):
        raise ValueError(
            "Provide a bucket name, not an S3 URI."
        )

    if "/" in normalized_name:
        raise ValueError(
            "Bucket name must not contain an object key or prefix."
        )

    return normalized_name


def validate_region(region: str) -> str:
    """Validate and normalize the AWS Region."""
    normalized_region = region.strip()

    if not normalized_region:
        raise ValueError("AWS Region cannot be empty.")

    return normalized_region


def validate_prefix(prefix: str | None) -> str | None:
    """Normalize an optional object-key prefix."""
    if prefix is None:
        return None

    normalized_prefix = prefix.strip().lstrip("/")

    if not normalized_prefix:
        return None

    if normalized_prefix.startswith("s3://"):
        raise ValueError(
            "Prefix must be an object-key prefix, not an S3 URI."
        )

    return normalized_prefix


def create_s3_client(region: str) -> Any:
    """Create an S3 client using the standard AWS credential chain."""
    client_config = Config(
        retries={
            "mode": "standard",
            "max_attempts": 5,
        },
        connect_timeout=10,
        read_timeout=30,
    )

    return boto3.client(
        "s3",
        region_name=region,
        config=client_config,
    )


def get_lifecycle_configuration(
    s3_client: Any,
    bucket_name: str,
) -> dict[str, Any] | None:
    """Retrieve the bucket lifecycle configuration."""
    try:
        response = s3_client.get_bucket_lifecycle_configuration(
            Bucket=bucket_name,
        )
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get(
            "Code",
            "Unknown",
        )

        if error_code == "NoSuchLifecycleConfiguration":
            return None

        raise LifecycleEvaluationError(
            f"Unable to retrieve lifecycle configuration for "
            f"{bucket_name!r}: {error_code}"
        ) from exc

    return response


def describe_filter(
    lifecycle_filter: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return a normalized description of a lifecycle rule filter."""
    if not lifecycle_filter:
        return {
            "scope": "all_objects",
            "prefix": None,
            "tags": [],
            "size_constraints": {},
        }

    if "Prefix" in lifecycle_filter:
        return {
            "scope": "prefix",
            "prefix": lifecycle_filter["Prefix"],
            "tags": [],
            "size_constraints": {},
        }

    if "Tag" in lifecycle_filter:
        tag = lifecycle_filter["Tag"]

        return {
            "scope": "tag",
            "prefix": None,
            "tags": [
                {
                    "key": tag.get("Key"),
                    "value": tag.get("Value"),
                }
            ],
            "size_constraints": {},
        }

    if "ObjectSizeGreaterThan" in lifecycle_filter:
        return {
            "scope": "object_size",
            "prefix": None,
            "tags": [],
            "size_constraints": {
                "greater_than": (
                    lifecycle_filter["ObjectSizeGreaterThan"]
                ),
            },
        }

    if "ObjectSizeLessThan" in lifecycle_filter:
        return {
            "scope": "object_size",
            "prefix": None,
            "tags": [],
            "size_constraints": {
                "less_than": lifecycle_filter["ObjectSizeLessThan"],
            },
        }

    if "And" in lifecycle_filter:
        and_filter = lifecycle_filter["And"]
        tags = [
            {
                "key": tag.get("Key"),
                "value": tag.get("Value"),
            }
            for tag in and_filter.get("Tags", [])
        ]

        return {
            "scope": "combined",
            "prefix": and_filter.get("Prefix"),
            "tags": tags,
            "size_constraints": {
                "greater_than": and_filter.get(
                    "ObjectSizeGreaterThan"
                ),
                "less_than": and_filter.get(
                    "ObjectSizeLessThan"
                ),
            },
        }

    return {
        "scope": "unknown",
        "prefix": None,
        "tags": [],
        "size_constraints": {},
    }


def prefix_matches(
    rule_prefix: str | None,
    required_prefix: str,
) -> bool:
    """
    Determine whether a rule's prefix can cover the requested prefix.

    An empty rule prefix applies to all object keys. A rule prefix that
    is an ancestor of the requested prefix also covers that scope.
    """
    if rule_prefix is None or rule_prefix == "":
        return True

    return required_prefix.startswith(rule_prefix)


def evaluate_prefix_coverage(
    lifecycle_filter: dict[str, Any] | None,
    required_prefix: str | None,
) -> dict[str, Any] | None:
    """Evaluate whether a lifecycle filter covers the requested prefix."""
    if required_prefix is None:
        return None

    filter_details = describe_filter(lifecycle_filter)
    rule_prefix = filter_details.get("prefix")

    if filter_details["scope"] == "unknown":
        return {
            "required_prefix": required_prefix,
            "matches": None,
            "reason": "Unsupported lifecycle filter structure.",
        }

    if filter_details["scope"] == "tag":
        return {
            "required_prefix": required_prefix,
            "matches": None,
            "reason": (
                "Tag-based filters cannot be evaluated using "
                "prefix information alone."
            ),
        }

    if filter_details["scope"] == "combined":
        if filter_details.get("tags"):
            return {
                "required_prefix": required_prefix,
                "matches": None,
                "reason": (
                    "Combined tag filters require object-tag inspection."
                ),
            }

        size_constraints = filter_details.get(
            "size_constraints",
            {},
        )

        if any(
            value is not None
            for value in size_constraints.values()
        ):
            return {
                "required_prefix": required_prefix,
                "matches": None,
                "reason": (
                    "Combined size filters require object-size evaluation."
                ),
            }

    matches = prefix_matches(
        rule_prefix=rule_prefix,
        required_prefix=required_prefix,
    )

    return {
        "required_prefix": required_prefix,
        "rule_prefix": rule_prefix or "",
        "matches": matches,
        "reason": (
            "Rule prefix covers the requested prefix."
            if matches
            else "Rule prefix does not cover the requested prefix."
        ),
    }


def summarize_transition(
    transition: dict[str, Any],
    versioned: bool = False,
) -> dict[str, Any]:
    """Normalize a lifecycle transition action."""
    summary: dict[str, Any] = {
        "storage_class": transition.get("StorageClass"),
    }

    if versioned:
        summary["noncurrent_days"] = transition.get(
            "NoncurrentDays"
        )
        summary["newer_noncurrent_versions"] = transition.get(
            "NewerNoncurrentVersions"
        )
    else:
        summary["days"] = transition.get("Days")
        summary["date"] = (
            transition["Date"].isoformat()
            if isinstance(transition.get("Date"), datetime)
            else transition.get("Date")
        )

    return summary


def summarize_rule(
    rule: dict[str, Any],
    required_prefix: str | None = None,
) -> dict[str, Any]:
    """Build a readable summary of one lifecycle rule."""
    lifecycle_filter = rule.get("Filter")
    filter_details = describe_filter(lifecycle_filter)

    expiration = rule.get("Expiration")
    noncurrent_expiration = rule.get(
        "NoncurrentVersionExpiration"
    )
    abort_multipart = rule.get("AbortIncompleteMultipartUpload")

    transitions = [
        summarize_transition(transition)
        for transition in rule.get("Transitions", [])
    ]

    noncurrent_transitions = [
        summarize_transition(
            transition,
            versioned=True,
        )
        for transition in rule.get(
            "NoncurrentVersionTransitions",
            [],
        )
    ]

    return {
        "id": rule.get("ID"),
        "status": rule.get("Status"),
        "filter": filter_details,
        "prefix_coverage": evaluate_prefix_coverage(
            lifecycle_filter,
            required_prefix,
        ),
        "expiration": expiration,
        "transitions": transitions,
        "noncurrent_version_expiration": noncurrent_expiration,
        "noncurrent_version_transitions": noncurrent_transitions,
        "abort_incomplete_multipart_upload": abort_multipart,
    }


def validate_rule(
    rule: dict[str, Any],
    rule_index: int,
) -> list[dict[str, str]]:
    """Validate lifecycle rule structure and identify potential issues."""
    findings: list[dict[str, str]] = []
    rule_id = rule.get("ID") or f"rule-{rule_index}"

    if rule.get("Status") not in {"Enabled", "Disabled"}:
        findings.append(
            {
                "severity": "error",
                "rule_id": rule_id,
                "message": (
                    "Rule status must be either Enabled or Disabled."
                ),
            }
        )

    if not rule.get("ID"):
        findings.append(
            {
                "severity": "warning",
                "rule_id": rule_id,
                "message": (
                    "Rule has no explicit ID. Assign stable identifiers "
                    "to simplify auditing and troubleshooting."
                ),
            }
        )

    lifecycle_filter = rule.get("Filter")

    if lifecycle_filter:
        filter_details = describe_filter(lifecycle_filter)

        if filter_details["scope"] == "unknown":
            findings.append(
                {
                    "severity": "error",
                    "rule_id": rule_id,
                    "message": (
                        "Rule contains an unrecognized filter structure."
                    ),
                }
            )

        if filter_details["scope"] == "combined":
            size_constraints = filter_details.get(
                "size_constraints",
                {},
            )
            minimum_size = size_constraints.get("greater_than")
            maximum_size = size_constraints.get("less_than")

            if (
                minimum_size is not None
                and maximum_size is not None
                and minimum_size >= maximum_size
            ):
                findings.append(
                    {
                        "severity": "error",
                        "rule_id": rule_id,
                        "message": (
                            "Combined object-size filter has an invalid "
                            "or empty size range."
                        ),
                    }
                )

    actions = LIFECYCLE_ACTION_KEYS.intersection(rule)

    if not actions:
        findings.append(
            {
                "severity": "warning",
                "rule_id": rule_id,
                "message": (
                    "Rule has no lifecycle actions configured."
                ),
            }
        )

    for transition in rule.get("Transitions", []):
        storage_class = transition.get("StorageClass")

        if storage_class not in SUPPORTED_STORAGE_CLASSES:
            findings.append(
                {
                    "severity": "error",
                    "rule_id": rule_id,
                    "message": (
                        "Transition uses an unsupported or missing "
                        f"storage class: {storage_class!r}."
                    ),
                }
            )

        days = transition.get("Days")

        if days is not None and days < 0:
            findings.append(
                {
                    "severity": "error",
                    "rule_id": rule_id,
                    "message": (
                        "Transition days cannot be negative."
                    ),
                }
            )

    for transition in rule.get("NoncurrentVersionTransitions", []):
        storage_class = transition.get("StorageClass")
        noncurrent_days = transition.get("NoncurrentDays")

        if storage_class not in SUPPORTED_STORAGE_CLASSES:
            findings.append(
                {
                    "severity": "error",
                    "rule_id": rule_id,
                    "message": (
                        "Noncurrent-version transition uses an "
                        f"unsupported or missing storage class: "
                        f"{storage_class!r}."
                    ),
                }
            )

        if noncurrent_days is not None and noncurrent_days < 0:
            findings.append(
                {
                    "severity": "error",
                    "rule_id": rule_id,
                    "message": (
                        "Noncurrent transition days cannot be negative."
                    ),
                }
            )

    expiration = rule.get("Expiration", {})

    expiration_days = expiration.get("Days")

    if expiration_days is not None and expiration_days < 0:
        findings.append(
            {
                "severity": "error",
                "rule_id": rule_id,
                "message": (
                    "Expiration days cannot be negative."
                ),
            }
        )

    noncurrent_expiration = rule.get(
        "NoncurrentVersionExpiration",
        {},
    )
    noncurrent_days = noncurrent_expiration.get(
        "NoncurrentDays"
    )

    if noncurrent_days is not None and noncurrent_days < 0:
        findings.append(
            {
                "severity": "error",
                "rule_id": rule_id,
                "message": (
                    "Noncurrent-version expiration days cannot be negative."
                ),
            }
        )

    abort_multipart = rule.get(
        "AbortIncompleteMultipartUpload",
        {},
    )
    abort_days = abort_multipart.get("DaysAfterInitiation")

    if abort_days is not None and abort_days < 0:
        findings.append(
            {
                "severity": "error",
                "rule_id": rule_id,
                "message": (
                    "Incomplete multipart upload cleanup days "
                    "cannot be negative."
                ),
            }
        )

    if rule.get("Status") == "Disabled":
        findings.append(
            {
                "severity": "warning",
                "rule_id": rule_id,
                "message": (
                    "Rule is disabled and will not perform lifecycle "
                    "actions while disabled."
                ),
            }
        )

    return findings


def evaluate_lifecycle_configuration(
    configuration: dict[str, Any] | None,
    bucket_name: str,
    region: str,
    required_prefix: str | None = None,
) -> dict[str, Any]:
    """
    Evaluate lifecycle rules without modifying bucket configuration.

    This is a configuration review. It does not predict the exact
    execution time of S3 lifecycle actions or inspect every object.
    """
    if configuration is None:
        return {
            "status": "missing_configuration",
            "bucket": bucket_name,
            "region": region,
            "evaluated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "required_prefix": required_prefix,
            "rule_count": 0,
            "enabled_rule_count": 0,
            "disabled_rule_count": 0,
            "rules": [],
            "findings": [
                {
                    "severity": "error",
                    "rule_id": None,
                    "message": (
                        "The bucket does not have a lifecycle "
                        "configuration."
                    ),
                }
            ],
            "limitations": [
                (
                    "No lifecycle configuration was available "
                    "for evaluation."
                )
            ],
        }

    rules = configuration.get("Rules", [])
    findings: list[dict[str, str]] = []

    rule_ids = [
        rule.get("ID")
        for rule in rules
        if rule.get("ID")
    ]
    duplicate_ids = [
        rule_id
        for rule_id, count in Counter(rule_ids).items()
        if count > 1
    ]

    for duplicate_id in duplicate_ids:
        findings.append(
            {
                "severity": "error",
                "rule_id": duplicate_id,
                "message": (
                    "Duplicate lifecycle rule ID detected."
                ),
            }
        )

    rule_summaries = []

    for index, rule in enumerate(rules, start=1):
        findings.extend(
            validate_rule(
                rule=rule,
                rule_index=index,
            )
        )

        summary = summarize_rule(
            rule=rule,
            required_prefix=required_prefix,
        )

        rule_summaries.append(summary)

        coverage = summary["prefix_coverage"]

        if coverage and coverage["matches"] is False:
            findings.append(
                {
                    "severity": "warning",
                    "rule_id": summary["id"] or f"rule-{index}",
                    "message": (
                        f"Rule does not cover requested prefix "
                        f"{required_prefix!r}."
                    ),
                }
            )

        if coverage and coverage["matches"] is None:
            findings.append(
                {
                    "severity": "info",
                    "rule_id": summary["id"] or f"rule-{index}",
                    "message": coverage["reason"],
                }
            )

    enabled_rule_count = sum(
        1
        for rule in rules
        if rule.get("Status") == "Enabled"
    )
    disabled_rule_count = sum(
        1
        for rule in rules
        if rule.get("Status") == "Disabled"
    )

    error_count = sum(
        1
        for finding in findings
        if finding["severity"] == "error"
    )
    warning_count = sum(
        1
        for finding in findings
        if finding["severity"] == "warning"
    )

    if error_count:
        status = "failed"
    elif warning_count:
        status = "completed_with_warnings"
    else:
        status = "passed"

    return {
        "status": status,
        "bucket": bucket_name,
        "region": region,
        "evaluated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "required_prefix": required_prefix,
        "rule_count": len(rules),
        "enabled_rule_count": enabled_rule_count,
        "disabled_rule_count": disabled_rule_count,
        "findings_summary": {
            "errors": error_count,
            "warnings": warning_count,
            "information": sum(
                1
                for finding in findings
                if finding["severity"] == "info"
            ),
        },
        "rules": rule_summaries,
        "findings": findings,
        "limitations": [
            (
                "The evaluator inspects lifecycle configuration only. "
                "It does not execute lifecycle actions."
            ),
            (
                "S3 lifecycle actions are asynchronous. Configuration "
                "inspection cannot establish the exact time an object "
                "will transition or expire."
            ),
            (
                "Prefix coverage does not establish tag or object-size "
                "eligibility for individual objects."
            ),
            (
                "Object-level eligibility, versioning state, minimum "
                "storage duration, retention controls, and object locks "
                "require additional inspection."
            ),
        ],
    }


def evaluate_bucket(
    bucket_name: str,
    region: str,
    required_prefix: str | None = None,
) -> dict[str, Any]:
    """Retrieve and evaluate the lifecycle configuration for a bucket."""
    s3_client = create_s3_client(region)

    configuration = get_lifecycle_configuration(
        s3_client=s3_client,
        bucket_name=bucket_name,
    )

    return evaluate_lifecycle_configuration(
        configuration=configuration,
        bucket_name=bucket_name,
        region=region,
        required_prefix=required_prefix,
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Inspect and evaluate the Amazon S3 lifecycle configuration "
            "for the data lake bucket."
        )
    )
    parser.add_argument(
        "--bucket",
        default=DEFAULT_BUCKET_NAME,
        help=(
            "S3 bucket name. Defaults to DATA_LAKE_BUCKET_NAME."
        ),
    )
    parser.add_argument(
        "--region",
        default=DEFAULT_REGION,
        help=f"AWS Region. Default: {DEFAULT_REGION}",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help=(
            "Optional object-key prefix to check against lifecycle "
            "rule prefix filters. Example: raw/events/"
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging.",
    )

    return parser.parse_args()


def main() -> int:
    """Execute lifecycle configuration evaluation."""
    arguments = parse_arguments()
    configure_logging(arguments.verbose)

    try:
        if not arguments.bucket:
            raise ValueError(
                "S3 bucket is required. Set DATA_LAKE_BUCKET_NAME "
                "or provide --bucket."
            )

        bucket_name = validate_bucket_name(arguments.bucket)
        region = validate_region(arguments.region)
        required_prefix = validate_prefix(arguments.prefix)

        LOGGER.info(
            "Evaluating lifecycle configuration for bucket %s.",
            bucket_name,
        )

        result = evaluate_bucket(
            bucket_name=bucket_name,
            region=region,
            required_prefix=required_prefix,
        )

    except ValueError as exc:
        LOGGER.error("Invalid configuration: %s", exc)
        return 1
    except LifecycleEvaluationError as exc:
        LOGGER.error("%s", exc)
        return 1
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get(
            "Code",
            "Unknown",
        )
        error_message = exc.response.get("Error", {}).get(
            "Message",
            str(exc),
        )
        LOGGER.error(
            "AWS S3 request failed: %s: %s",
            error_code,
            error_message,
        )
        return 1
    except BotoCoreError as exc:
        LOGGER.error("AWS SDK request failed: %s", exc)
        return 1

    print(json.dumps(result, indent=2, default=str))

    if result["status"] in {
        "failed",
        "missing_configuration",
    }:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())