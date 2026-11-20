"""Processing status management for the S3 document pipeline.

Persists document processing state in DynamoDB and provides consistent
status retrieval for API handlers, background workers, and operational
scripts.

The manager accepts a DynamoDB Table resource, keeping AWS resource
construction outside this module and allowing tests to inject Moto-backed
or mocked table instances.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


class ProcessingStatus(str, Enum):
    """Supported document processing states."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProcessingStatusError(RuntimeError):
    """Raised when processing status persistence or retrieval fails."""


class ProcessingStatusManager:
    """Manage document processing states in a DynamoDB table.

    The DynamoDB table must have a partition key named ``object_id``.
    Status updates modify the existing metadata item rather than creating
    a separate item. This supports using either the metadata table or a
    dedicated processing-status table with the same key convention.

    Status transitions are intentionally not enforced here. SQS and Lambda
    retries may legitimately move a previously failed document back into
    PROCESSING. Workflow-level idempotency and concurrency control must be
    handled by the processing worker or a dedicated lease mechanism.
    """

    def __init__(self, *, table: Any) -> None:
        """Initialize the manager with a DynamoDB Table resource."""
        if table is None:
            raise ValueError("A DynamoDB table resource is required.")

        if not callable(getattr(table, "update_item", None)):
            raise TypeError(
                "The supplied table must provide an update_item method."
            )

        if not callable(getattr(table, "get_item", None)):
            raise TypeError(
                "The supplied table must provide a get_item method."
            )

        self.table = table

    @staticmethod
    def _validate_object_id(object_id: str) -> str:
        """Validate and normalize the document identifier."""
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError("object_id must be a non-empty string.")

        normalized_object_id = object_id.strip()

        if len(normalized_object_id) > 2048:
            raise ValueError("object_id exceeds the supported length.")

        return normalized_object_id

    @staticmethod
    def _normalize_status(
        status: ProcessingStatus | str,
    ) -> ProcessingStatus:
        """Convert a status value into the supported enum."""
        if isinstance(status, ProcessingStatus):
            return status

        if not isinstance(status, str):
            raise ValueError(
                "Processing status must be a ProcessingStatus or string."
            )

        try:
            return ProcessingStatus(status.strip().upper())
        except ValueError as exc:
            supported_statuses = ", ".join(
                item.value for item in ProcessingStatus
            )
            raise ValueError(
                f"Unsupported processing status {status!r}. "
                f"Supported values: {supported_statuses}."
            ) from exc

    @staticmethod
    def _validate_message(message: str | None) -> str | None:
        """Validate an optional processing status message."""
        if message is None:
            return None

        if not isinstance(message, str):
            raise ValueError("Processing status message must be a string.")

        normalized_message = message.strip()

        if len(normalized_message) > 4000:
            raise ValueError(
                "Processing status message cannot exceed 4000 characters."
            )

        return normalized_message or None

    @staticmethod
    def _current_timestamp() -> str:
        """Return the current UTC timestamp in ISO 8601 format."""
        return datetime.now(UTC).isoformat()

    def update_status(
        self,
        *,
        object_id: str,
        status: ProcessingStatus | str,
        message: str | None = None,
    ) -> dict[str, Any]:
        """Update the processing status of an existing document.

        The update is atomic at the DynamoDB item level. It preserves
        unrelated metadata attributes and prevents accidental creation
        of an item when the document does not exist.

        Args:
            object_id: Partition key identifying the document.
            status: New processing state.
            message: Optional status detail or failure description.

        Returns:
            The updated DynamoDB item attributes.

        Raises:
            ValueError: If an input value is invalid.
            ProcessingStatusError: If the DynamoDB update fails.
        """
        normalized_object_id = self._validate_object_id(object_id)
        normalized_status = self._normalize_status(status)
        normalized_message = self._validate_message(message)
        timestamp = self._current_timestamp()

        update_expression = (
            "SET #processing_status = :processing_status, "
            "#updated_at = :updated_at"
        )

        expression_attribute_names = {
            "#object_id": "object_id",
            "#processing_status": "processing_status",
            "#updated_at": "updated_at",
        }

        expression_attribute_values: dict[str, Any] = {
            ":processing_status": normalized_status.value,
            ":updated_at": timestamp,
        }

        if normalized_message is not None:
            update_expression += ", #status_message = :status_message"
            expression_attribute_names["#status_message"] = (
                "status_message"
            )
            expression_attribute_values[":status_message"] = (
                normalized_message
            )

        if normalized_status == ProcessingStatus.COMPLETED:
            update_expression += ", #completed_at = :completed_at"
            expression_attribute_names["#completed_at"] = "completed_at"
            expression_attribute_values[":completed_at"] = timestamp

        elif normalized_status == ProcessingStatus.FAILED:
            update_expression += ", #failed_at = :failed_at"
            expression_attribute_names["#failed_at"] = "failed_at"
            expression_attribute_values[":failed_at"] = timestamp

        elif normalized_status == ProcessingStatus.PROCESSING:
            update_expression += ", #started_at = :started_at"
            expression_attribute_names["#started_at"] = "started_at"
            expression_attribute_values[":started_at"] = timestamp

        try:
            response = self.table.update_item(
                Key={"object_id": normalized_object_id},
                UpdateExpression=update_expression,
                ConditionExpression="attribute_exists(#object_id)",
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW",
            )

        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")

            if error_code == "ConditionalCheckFailedException":
                raise ProcessingStatusError(
                    f"No metadata record exists for object "
                    f"{normalized_object_id!r}."
                ) from exc

            logger.exception(
                "DynamoDB rejected a document processing status update.",
                extra={
                    "object_id": normalized_object_id,
                    "processing_status": normalized_status.value,
                    "error_code": error_code,
                },
            )

            raise ProcessingStatusError(
                "Failed to update document processing status."
            ) from exc

        except BotoCoreError as exc:
            logger.exception(
                "AWS SDK failure while updating document processing status.",
                extra={
                    "object_id": normalized_object_id,
                    "processing_status": normalized_status.value,
                },
            )

            raise ProcessingStatusError(
                "Unable to update document processing status."
            ) from exc

        attributes = response.get("Attributes")

        if not isinstance(attributes, dict):
            raise ProcessingStatusError(
                "DynamoDB did not return the updated document attributes."
            )

        logger.info(
            "Document processing status updated.",
            extra={
                "object_id": normalized_object_id,
                "processing_status": normalized_status.value,
            },
        )

        return attributes

    def get_status(
        self,
        *,
        object_id: str,
        consistent_read: bool = True,
    ) -> dict[str, Any] | None:
        """Retrieve a document's current processing status.

        Args:
            object_id: Partition key identifying the document.
            consistent_read: Whether to request a strongly consistent
                read. Strong consistency is supported by DynamoDB tables
                but not by global secondary indexes.

        Returns:
            The complete DynamoDB item, or None if it does not exist.

        Raises:
            ValueError: If an input value is invalid.
            ProcessingStatusError: If the DynamoDB read fails.
        """
        normalized_object_id = self._validate_object_id(object_id)

        if not isinstance(consistent_read, bool):
            raise ValueError("consistent_read must be a boolean.")

        try:
            response = self.table.get_item(
                Key={"object_id": normalized_object_id},
                ConsistentRead=consistent_read,
            )

        except (ClientError, BotoCoreError) as exc:
            logger.exception(
                "Failed to retrieve document processing status.",
                extra={"object_id": normalized_object_id},
            )

            raise ProcessingStatusError(
                "Unable to retrieve document processing status."
            ) from exc

        item = response.get("Item")

        if item is None:
            return None

        if not isinstance(item, dict):
            raise ProcessingStatusError(
                "DynamoDB returned an invalid document status record."
            )

        return item