"""Processing-status endpoint for the S3 document ingestion pipeline.

Exposes the latest processing state stored in DynamoDB. The API reads status
records through ProcessingStatusManager and does not perform document
processing or modify processing state.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException, Path, status

from processing.processing_status import (
    ProcessingStatusError,
    ProcessingStatusManager,
)

logger = logging.getLogger(__name__)

DEFAULT_AWS_REGION = "ap-south-1"

DYNAMODB_CLIENT_CONFIG = Config(
    retries={
        "max_attempts": 3,
        "mode": "standard",
    },
    connect_timeout=5,
    read_timeout=10,
    max_pool_connections=20,
)

router = APIRouter(
    prefix="/processing-status",
    tags=["Processing Status"],
)


def _get_status_table_name() -> str:
    """Return the configured DynamoDB processing-status table name."""
    table_name = os.getenv("PROCESSING_STATUS_TABLE_NAME")

    if not table_name:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Processing-status storage is not configured.",
        )

    if table_name != table_name.strip():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Processing-status storage configuration is invalid.",
        )

    return table_name


@lru_cache(maxsize=1)
def _get_dynamodb_resource() -> Any:
    """Create and cache a DynamoDB resource using the AWS credential chain."""
    region_name = (
        os.getenv("AWS_REGION")
        or DEFAULT_AWS_REGION
    )

    return boto3.resource(
        "dynamodb",
        region_name=region_name,
        config=DYNAMODB_CLIENT_CONFIG,
    )


@lru_cache(maxsize=1)
def _get_status_manager() -> ProcessingStatusManager:
    """Create the processing-status manager for the configured table."""
    table_name = _get_status_table_name()
    dynamodb = _get_dynamodb_resource()
    table = dynamodb.Table(table_name)

    return ProcessingStatusManager(table=table)


def _validate_object_id(object_id: str) -> str:
    """Validate an object identifier received from the request path."""
    if not object_id or not object_id.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A valid object identifier is required.",
        )

    if object_id != object_id.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Object identifier cannot contain surrounding whitespace.",
        )

    if len(object_id.encode("utf-8")) > 1024:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Object identifier exceeds the maximum permitted length.",
        )

    if any(
        ord(character) < 32 or ord(character) == 127
        for character in object_id
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Object identifier contains invalid characters.",
        )

    return object_id


@router.get(
    "/{object_id:path}",
    status_code=status.HTTP_200_OK,
    summary="Retrieve document processing status",
    response_description="Latest processing status for the requested document.",
)
def get_processing_status(
    object_id: str = Path(
        ...,
        min_length=1,
        max_length=1024,
        description="Document object identifier returned by the upload endpoint.",
    ),
) -> dict[str, Any]:
    """Retrieve the latest processing status for a document.

    The endpoint performs a strongly consistent DynamoDB read through
    ProcessingStatusManager. It returns the latest status record and does not
    trigger processing or retry failed messages.

    The object identifier is accepted as a path parameter because the upload
    endpoint returns an identifier containing the bucket and S3 object key.
    """
    validated_object_id = _validate_object_id(object_id)

    try:
        status_manager = _get_status_manager()

        status_record = status_manager.get_status(
            object_id=validated_object_id,
            consistent_read=True,
        )

    except ProcessingStatusError as exc:
        logger.exception(
            "Unable to retrieve document processing status.",
            extra={
                "object_id": validated_object_id,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to retrieve document processing status.",
        ) from exc

    except (ClientError, BotoCoreError) as exc:
        logger.exception(
            "DynamoDB processing-status lookup failed.",
            extra={
                "object_id": validated_object_id,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Processing-status storage operation failed.",
        ) from exc

    except (ValueError, RuntimeError) as exc:
        logger.exception(
            "Processing-status lookup could not be completed.",
            extra={
                "object_id": validated_object_id,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Processing-status service is unavailable.",
        ) from exc

    if status_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No processing status was found for this document.",
        )

    return {
        "object_id": validated_object_id,
        "processing_status": status_record.get("processing_status"),
        "status_message": status_record.get("status_message"),
        "created_at": status_record.get("created_at"),
        "updated_at": status_record.get("updated_at"),
        "started_at": status_record.get("started_at"),
        "completed_at": status_record.get("completed_at"),
        "failed_at": status_record.get("failed_at"),
    }