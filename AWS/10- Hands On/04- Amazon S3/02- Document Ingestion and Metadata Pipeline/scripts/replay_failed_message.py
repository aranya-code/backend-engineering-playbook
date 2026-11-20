#!/usr/bin/env python3
"""Perform read-only validation of an SQS failed-message queue.

This utility inspects queue attributes and reports message counts and
redrive configuration. It does not receive, replay, send, or delete messages.

Replay and other remediation operations must be implemented separately
and executed through an explicitly authorized workflow.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError


logger = logging.getLogger("replay_failed_message")

QUEUE_ATTRIBUTES = ["All"]

MESSAGE_COUNT_ATTRIBUTES = (
    "ApproximateNumberOfMessages",
    "ApproximateNumberOfMessagesNotVisible",
    "ApproximateNumberOfMessagesDelayed",
)


def configure_logging(verbose: bool = False) -> None:
    """Configure command-line logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )


def parse_redrive_policy(
    attributes: dict[str, str],
) -> dict[str, Any] | None:
    """Parse the queue redrive policy when one is configured."""
    raw_policy = attributes.get("RedrivePolicy")

    if not raw_policy:
        return None

    try:
        policy = json.loads(raw_policy)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "The queue contains an invalid RedrivePolicy JSON attribute."
        ) from exc

    if not isinstance(policy, dict):
        raise ValueError(
            "The queue RedrivePolicy must be a JSON object."
        )

    return policy


def validate_queue_attributes(
    attributes: dict[str, str],
) -> dict[str, Any]:
    """Validate and normalize the read-only queue inspection results."""
    queue_arn = attributes.get("QueueArn")

    if not queue_arn:
        raise ValueError("The queue response does not contain QueueArn.")

    if not queue_arn.startswith("arn:"):
        raise ValueError("The queue returned an invalid QueueArn.")

    message_counts: dict[str, int] = {}

    for attribute_name in MESSAGE_COUNT_ATTRIBUTES:
        raw_value = attributes.get(attribute_name, "0")

        try:
            count = int(raw_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid queue attribute value for {attribute_name}."
            ) from exc

        if count < 0:
            raise ValueError(
                f"Queue attribute {attribute_name} cannot be negative."
            )

        message_counts[attribute_name] = count

    redrive_policy = parse_redrive_policy(attributes)

    return {
        "queue_arn": queue_arn,
        "message_counts": message_counts,
        "redrive_policy": redrive_policy,
        "visibility_timeout_seconds": int(
            attributes.get("VisibilityTimeout", "0")
        ),
        "message_retention_period_seconds": int(
            attributes.get("MessageRetentionPeriod", "0")
        ),
        "receive_message_wait_time_seconds": int(
            attributes.get("ReceiveMessageWaitTimeSeconds", "0")
        ),
        "sqs_managed_sse_enabled": (
            attributes.get("SqsManagedSseEnabled", "false").lower()
            == "true"
        ),
        "kms_master_key_id": attributes.get("KmsMasterKeyId"),
    }


def inspect_failed_message_queue(
    *,
    queue_url: str,
    region_name: str | None = None,
) -> dict[str, Any]:
    """Inspect SQS queue attributes without changing queue state.

    The function intentionally uses only GetQueueAttributes. It does not
    call ReceiveMessage, SendMessage, DeleteMessage, or other operations
    that can alter message or queue state.

    Approximate message counts are operational indicators, not exact
    transactional counts.
    """
    if not queue_url or queue_url != queue_url.strip():
        raise ValueError("A non-empty SQS queue URL is required.")

    if not queue_url.startswith("https://"):
        raise ValueError("The SQS queue URL must use HTTPS.")

    sqs_client = boto3.client(
        "sqs",
        region_name=region_name,
    )

    response = sqs_client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=QUEUE_ATTRIBUTES,
    )

    attributes = response.get("Attributes")

    if not isinstance(attributes, dict):
        raise ValueError(
            "SQS returned an invalid queue attributes response."
        )

    result = validate_queue_attributes(attributes)

    return {
        "inspection_status": "completed",
        "read_only": True,
        **result,
    }


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Inspect an SQS failed-message queue without receiving, "
            "replaying, or deleting messages."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "queue_url",
        help="URL of the SQS queue to inspect.",
    )

    parser.add_argument(
        "--region",
        default=None,
        help=(
            "AWS Region for the SQS client. If omitted, the AWS SDK "
            "default Region resolution is used."
        ),
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging.",
    )

    return parser


def main() -> int:
    """Execute the read-only queue inspection workflow."""
    parser = build_argument_parser()
    args = parser.parse_args()

    configure_logging(args.verbose)

    try:
        result = inspect_failed_message_queue(
            queue_url=args.queue_url,
            region_name=args.region,
        )

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            )
        )

        logger.info("SQS queue inspection completed.")
        logger.info("Queue ARN: %s", result["queue_arn"])

        for attribute_name, count in result["message_counts"].items():
            logger.info("%s: %s", attribute_name, count)

        logger.info(
            "No messages were received, replayed, or deleted."
        )

        return 0

    except ValueError as exc:
        logger.error("%s", exc)
        return 1

    except ClientError as exc:
        error_response = exc.response.get("Error", {})
        error_code = error_response.get("Code", "Unknown")
        error_message = error_response.get("Message", str(exc))

        logger.error(
            "SQS inspection failed (%s): %s",
            error_code,
            error_message,
        )
        return 1

    except BotoCoreError as exc:
        logger.error("AWS SDK operation failed: %s", exc)
        return 1

    except (TypeError, KeyError) as exc:
        logger.error("Unexpected SQS response structure: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())