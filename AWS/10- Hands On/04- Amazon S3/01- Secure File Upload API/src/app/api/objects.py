"""Object-management endpoints for the Secure File Upload API.

The API generates server-controlled object identifiers and keys. Clients never
supply raw S3 keys, and every object operation is scoped to the authenticated
principal's upload prefix.
"""

from __future__ import annotations

import logging
import mimetypes
import re
import uuid
from collections.abc import Mapping
from typing import Any
from urllib.parse import quote

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from starlette.responses import RedirectResponse, Response

from app.config import Settings, get_settings
from app.dependencies.authentication import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/objects",
    tags=["Objects"],
)

_OBJECT_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


class PresignedUploadRequest(BaseModel):
    """Request parameters for initiating a direct-to-S3 upload."""

    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=3, max_length=255)
    content_length: int = Field(gt=0)


class PresignedUploadResponse(BaseModel):
    """Details required by a client to upload directly to S3."""

    object_id: str
    upload_url: str
    method: str = "PUT"
    headers: dict[str, str]
    expires_in: int


class ObjectUploadResponse(BaseModel):
    """Metadata returned after an API-mediated upload."""

    object_id: str
    filename: str
    content_type: str
    size_bytes: int
    status: str = "uploaded"


class ObjectMetadataResponse(BaseModel):
    """Object metadata returned by the metadata endpoint."""

    object_id: str
    content_type: str | None = None
    size_bytes: int | None = None
    etag: str | None = None
    last_modified: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class ObjectDeletionResponse(BaseModel):
    """Confirmation returned after an object deletion request."""

    object_id: str
    status: str = "deleted"


def _get_principal_id(principal: Any) -> str:
    """Extract a stable identifier from the authenticated principal."""
    if isinstance(principal, Mapping):
        principal_id = (
            principal.get("sub")
            or principal.get("user_id")
            or principal.get("id")
        )
    else:
        principal_id = (
            getattr(principal, "sub", None)
            or getattr(principal, "user_id", None)
            or getattr(principal, "id", None)
        )

    if principal_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The authenticated principal has no valid identifier.",
        )

    normalized_id = str(principal_id).strip()

    if not normalized_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The authenticated principal has no valid identifier.",
        )

    return normalized_id


def _get_object_id(object_id: str) -> str:
    """Validate an opaque object identifier."""
    normalized_id = object_id.lower()

    if not _OBJECT_ID_PATTERN.fullmatch(normalized_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Object not found.",
        )

    return normalized_id


def _build_object_key(
    settings: Settings,
    principal_id: str,
    object_id: str,
) -> str:
    """Build an S3 key using only server-controlled path components."""
    prefix = settings.s3_upload_prefix.strip("/")
    owner_segment = quote(principal_id, safe="")

    if prefix:
        return f"{prefix}/{owner_segment}/{object_id}"

    return f"{owner_segment}/{object_id}"


def _sanitize_filename(filename: str) -> str:
    """Normalize a filename before storing it as object metadata."""
    basename = filename.replace("\\", "/").rsplit("/", maxsplit=1)[-1]
    sanitized = _FILENAME_PATTERN.sub("_", basename).strip("._")

    if not sanitized:
        return "upload"

    return sanitized[:255]


def _validate_upload(
    settings: Settings,
    filename: str,
    content_type: str,
    content_length: int,
) -> tuple[str, str]:
    """Validate upload metadata against application configuration."""
    sanitized_filename = _sanitize_filename(filename)
    normalized_content_type = content_type.strip().lower()

    if not normalized_content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A content type is required.",
        )

    if normalized_content_type not in settings.allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="The supplied content type is not allowed.",
        )

    if content_length <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file must not be empty.",
        )

    if content_length > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="The uploaded file exceeds the maximum allowed size.",
        )

    return sanitized_filename, normalized_content_type


def _get_service(request: Request, service_name: str) -> Any:
    """Retrieve an application service initialized during application startup."""
    service = getattr(request.app.state, service_name, None)

    if service is None:
        logger.error(
            "application_service_unavailable",
            extra={"service": service_name},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The requested service is temporarily unavailable.",
        )

    return service


def _raise_storage_error(
    exc: Exception,
    operation: str,
    object_id: str,
) -> None:
    """Translate storage failures into safe HTTP responses."""
    error_code = None

    if isinstance(exc, ClientError):
        error_code = exc.response.get("Error", {}).get("Code")

    logger.exception(
        "s3_object_operation_failed",
        extra={
            "operation": operation,
            "object_id": object_id,
            "aws_error_code": error_code,
        },
    )

    if error_code in {"NoSuchKey", "NotFound", "404"}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Object not found.",
        ) from exc

    if error_code in {"AccessDenied", "InvalidAccessKeyId"}:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The storage service could not complete the operation.",
        ) from exc

    if isinstance(exc, (BotoCoreError, ClientError)):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The storage service could not complete the operation.",
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected storage error occurred.",
    ) from exc


def _format_last_modified(value: Any) -> str | None:
    """Convert an S3 timestamp into an ISO 8601 string."""
    if value is None:
        return None

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return str(value)


@router.post(
    "",
    response_model=ObjectUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an object",
    description=(
        "Uploads a file through the API. The server validates the upload, "
        "generates the object identifier, and stores the object in the "
        "authenticated principal's S3 prefix."
    ),
)
async def upload_object(
    request: Request,
    file: UploadFile = File(...),
    principal: Any = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> ObjectUploadResponse:
    """Validate and upload a file through the API."""
    principal_id = _get_principal_id(principal)

    content_length = file.size

    if content_length is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file size could not be determined.",
        )

    filename, content_type = _validate_upload(
        settings=settings,
        filename=file.filename or "upload",
        content_type=file.content_type or "",
        content_length=content_length,
    )

    object_id = uuid.uuid4().hex
    object_key = _build_object_key(
        settings=settings,
        principal_id=principal_id,
        object_id=object_id,
    )

    s3_service = _get_service(request, "s3_service")

    try:
        await file.seek(0)

        await run_in_threadpool(
            s3_service.upload_fileobj,
            file.file,
            object_key,
            content_type,
            {
                "original-filename": filename,
                "owner-id": principal_id,
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_storage_error(
            exc=exc,
            operation="upload",
            object_id=object_id,
        )
    finally:
        await file.close()

    logger.info(
        "s3_object_uploaded",
        extra={
            "object_id": object_id,
            "size_bytes": content_length,
            "content_type": content_type,
        },
    )

    return ObjectUploadResponse(
        object_id=object_id,
        filename=filename,
        content_type=content_type,
        size_bytes=content_length,
    )


@router.post(
    "/presigned-upload",
    response_model=PresignedUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate a direct S3 upload",
    description=(
        "Creates a short-lived presigned URL for uploading directly to S3. "
        "The client must send the declared content type and upload the file "
        "using the returned HTTP method and headers."
    ),
)
async def initiate_presigned_upload(
    payload: PresignedUploadRequest,
    request: Request,
    principal: Any = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> PresignedUploadResponse:
    """Generate a presigned URL for a validated direct upload."""
    principal_id = _get_principal_id(principal)

    filename, content_type = _validate_upload(
        settings=settings,
        filename=payload.filename,
        content_type=payload.content_type,
        content_length=payload.content_length,
    )

    object_id = uuid.uuid4().hex
    object_key = _build_object_key(
        settings=settings,
        principal_id=principal_id,
        object_id=object_id,
    )

    presigned_url_service = _get_service(
        request,
        "presigned_url_service",
    )

    try:
        upload_url = await run_in_threadpool(
            presigned_url_service.generate_upload_url,
            object_key,
            content_type,
            {
                "original-filename": filename,
                "owner-id": principal_id,
            },
            settings.presigned_url_expiration_seconds,
        )
    except Exception as exc:
        _raise_storage_error(
            exc=exc,
            operation="generate_presigned_upload_url",
            object_id=object_id,
        )

    logger.info(
        "s3_presigned_upload_url_created",
        extra={"object_id": object_id},
    )

    return PresignedUploadResponse(
        object_id=object_id,
        upload_url=upload_url,
        headers={
            "Content-Type": content_type,
        },
        expires_in=settings.presigned_url_expiration_seconds,
    )


@router.get(
    "/{object_id}/download",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    summary="Download an object",
    description=(
        "Redirects the authenticated owner to a short-lived presigned "
        "download URL. The object key is derived server-side."
    ),
)
async def download_object(
    object_id: str,
    request: Request,
    principal: Any = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    """Generate a presigned download URL for an owned object."""
    principal_id = _get_principal_id(principal)
    normalized_object_id = _get_object_id(object_id)

    object_key = _build_object_key(
        settings=settings,
        principal_id=principal_id,
        object_id=normalized_object_id,
    )

    presigned_url_service = _get_service(
        request,
        "presigned_url_service",
    )

    try:
        download_url = await run_in_threadpool(
            presigned_url_service.generate_download_url,
            object_key,
            settings.presigned_url_expiration_seconds,
        )
    except Exception as exc:
        _raise_storage_error(
            exc=exc,
            operation="generate_presigned_download_url",
            object_id=normalized_object_id,
        )

    return RedirectResponse(
        url=download_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )


@router.get(
    "/{object_id}",
    response_model=ObjectMetadataResponse,
    summary="Retrieve object metadata",
    description=(
        "Returns metadata for an object belonging to the authenticated "
        "principal. Raw S3 keys are never accepted from the client."
    ),
)
async def get_object_metadata(
    object_id: str,
    request: Request,
    principal: Any = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> ObjectMetadataResponse:
    """Retrieve metadata for an owned S3 object."""
    principal_id = _get_principal_id(principal)
    normalized_object_id = _get_object_id(object_id)

    object_key = _build_object_key(
        settings=settings,
        principal_id=principal_id,
        object_id=normalized_object_id,
    )

    s3_service = _get_service(request, "s3_service")

    try:
        metadata = await run_in_threadpool(
            s3_service.head_object,
            object_key,
        )
    except Exception as exc:
        _raise_storage_error(
            exc=exc,
            operation="head_object",
            object_id=normalized_object_id,
        )

    if not isinstance(metadata, Mapping):
        logger.error(
            "s3_metadata_response_invalid",
            extra={"object_id": normalized_object_id},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The storage service returned an invalid response.",
        )

    return ObjectMetadataResponse(
        object_id=normalized_object_id,
        content_type=metadata.get("ContentType"),
        size_bytes=metadata.get("ContentLength"),
        etag=metadata.get("ETag"),
        last_modified=_format_last_modified(metadata.get("LastModified")),
        metadata=metadata.get("Metadata") or {},
    )


@router.delete(
    "/{object_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an object",
    description=(
        "Deletes an object belonging to the authenticated principal. "
        "When bucket versioning is enabled, S3 may create a delete marker "
        "rather than permanently removing previous object versions."
    ),
)
async def delete_object(
    object_id: str,
    request: Request,
    principal: Any = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> Response:
    """Delete an owned S3 object."""
    principal_id = _get_principal_id(principal)
    normalized_object_id = _get_object_id(object_id)

    object_key = _build_object_key(
        settings=settings,
        principal_id=principal_id,
        object_id=normalized_object_id,
    )

    s3_service = _get_service(request, "s3_service")

    try:
        await run_in_threadpool(
            s3_service.delete_object,
            object_key,
        )
    except Exception as exc:
        _raise_storage_error(
            exc=exc,
            operation="delete_object",
            object_id=normalized_object_id,
        )

    logger.info(
        "s3_object_deleted",
        extra={"object_id": normalized_object_id},
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )