"""Document submission endpoints for the S3 ingestion pipeline.

The API validates uploaded documents and stores them in a private S3 bucket.
S3 ObjectCreated notifications trigger the ingestion Lambda, which extracts
metadata and publishes downstream processing events.

Document extraction and ingestion orchestration remain outside this module.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import PurePosixPath
from threading import Lock
from typing import Any
from urllib.parse import quote
from uuid import uuid4

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from ingestion.document_validator import (
    DocumentValidationError,
    DocumentValidator,
)

logger = logging.getLogger(__name__)

DEFAULT_AWS_REGION = "ap-south-1"
DEFAULT_UPLOAD_PREFIX = "incoming"
DEFAULT_MAX_DOCUMENT_SIZE_BYTES = 50 * 1024 * 1024
FILE_SIGNATURE_READ_SIZE = 8192

S3_CLIENT_CONFIG = Config(
    retries={
        "max_attempts": 3,
        "mode": "standard",
    },
    connect_timeout=5,
    read_timeout=60,
    max_pool_connections=50,
)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

document_validator = DocumentValidator()
_s3_client_lock = Lock()


@lru_cache(maxsize=1)
def _get_s3_client() -> Any:
    """Create and cache an S3 client using the AWS credential provider chain."""
    region_name = (
        os.getenv("AWS_REGION")
        or DEFAULT_AWS_REGION
    )

    return boto3.client(
        "s3",
        region_name=region_name,
        config=S3_CLIENT_CONFIG,
    )


def _get_bucket_name() -> str:
    """Return the configured destination bucket."""
    bucket_name = os.getenv("DOCUMENTS_BUCKET_NAME")

    if not bucket_name:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document storage is not configured.",
        )

    if bucket_name != bucket_name.strip():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document storage configuration is invalid.",
        )

    return bucket_name


def _get_upload_prefix() -> str:
    """Return a validated S3 prefix for incoming documents."""
    prefix = os.getenv(
        "DOCUMENTS_UPLOAD_PREFIX",
        DEFAULT_UPLOAD_PREFIX,
    ).strip("/")

    if not prefix:
        return DEFAULT_UPLOAD_PREFIX

    path_parts = prefix.split("/")

    if (
        any(part in {"", ".", ".."} for part in path_parts)
        or "\\" in prefix
        or any(
            ord(character) < 32 or ord(character) == 127
            for character in prefix
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document upload prefix configuration is invalid.",
        )

    return prefix


def _build_object_key(filename: str) -> str:
    """Generate a unique S3 object key without using user-controlled paths."""
    extension = PurePosixPath(filename).suffix.lower()
    prefix = _get_upload_prefix()

    return f"{prefix}/{uuid4().hex}{extension}"


def _validate_and_upload(
    *,
    file_object: Any,
    filename: str,
    content_type: str,
    bucket_name: str,
    object_key: str,
) -> int:
    """Validate a file and upload its stream to S3.

    The uploaded file is seekable because FastAPI's UploadFile uses a
    SpooledTemporaryFile. The file is inspected without loading the complete
    document into application memory.

    Returns:
        Number of bytes uploaded.

    Raises:
        DocumentValidationError: If document metadata or signature is invalid.
        ClientError: If S3 rejects the upload.
        BotoCoreError: If the AWS SDK encounters an operational error.
        OSError: If the temporary upload stream cannot be read.
    """
    file_object.seek(0, os.SEEK_END)
    size_bytes = file_object.tell()
    file_object.seek(0)

    document_validator.validate_document(
        filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
    )

    file_header = file_object.read(FILE_SIGNATURE_READ_SIZE)
    file_object.seek(0)

    document_validator.validate_file_signature(
        filename=filename,
        content_type=content_type,
        file_header=file_header,
    )

    encoded_filename = quote(
        filename,
        safe="",
    )

    s3_client = _get_s3_client()

    s3_client.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=file_object,
        ContentLength=size_bytes,
        ContentType=content_type,
        ContentDisposition=(
            f"attachment; filename*=UTF-8''{encoded_filename}"
        ),
        Metadata={
            "original-filename": encoded_filename,
        },
    )

    return size_bytes


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a document for asynchronous processing",
    response_description="Document accepted for ingestion.",
)
async def upload_document(
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """Validate and upload a document to the configured S3 bucket.

    S3 ObjectCreated notifications initiate the ingestion workflow. This
    endpoint does not extract metadata or wait for downstream processing.

    Supported formats and maximum size are enforced by DocumentValidator.
    """
    filename = file.filename
    content_type = file.content_type

    if not filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A document filename is required.",
        )

    if not content_type:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="A document content type is required.",
        )

    bucket_name = _get_bucket_name()
    object_key = _build_object_key(filename)

    try:
        size_bytes = await run_in_threadpool(
            _validate_and_upload,
            file_object=file.file,
            filename=filename,
            content_type=content_type,
            bucket_name=bucket_name,
            object_key=object_key,
        )

    except DocumentValidationError as exc:
        max_size_bytes = document_validator.max_size_bytes

        if (
            "exceeds the maximum allowed size" in str(exc)
            or "exceeds the maximum" in str(exc)
        ):
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="Document exceeds the maximum permitted size.",
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except (ClientError, BotoCoreError) as exc:
        logger.exception(
            "S3 document upload failed.",
            extra={
                "bucket_name": bucket_name,
                "object_key": object_key,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Document storage operation failed.",
        ) from exc

    except (OSError, ValueError) as exc:
        logger.exception(
            "Document upload could not be completed.",
            extra={
                "object_key": object_key,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document upload could not be completed.",
        ) from exc

    logger.info(
        "Document uploaded and accepted for ingestion.",
        extra={
            "bucket_name": bucket_name,
            "object_key": object_key,
            "size_bytes": size_bytes,
            "content_type": content_type,
        },
    )

    return {
        "object_id": f"{bucket_name}/{object_key}",
        "bucket_name": bucket_name,
        "object_key": object_key,
        "filename": filename,
        "content_type": content_type,
        "size_bytes": size_bytes,
        "processing_status": "PENDING",
        "message": "Document uploaded and accepted for asynchronous ingestion.",
    }