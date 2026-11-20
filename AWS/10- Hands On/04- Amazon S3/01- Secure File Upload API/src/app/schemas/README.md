# README

## Overview

The `schemas` package contains the Pydantic models that define the request and response contracts for the Secure File Upload API.

These schemas establish a consistent boundary between incoming HTTP data, application services, and serialized API responses. They are responsible for validating and describing data structures, not for implementing authentication, authorization, file processing, or S3 operations.

The package currently separates schemas by responsibility:

| Module | Responsibility |
|---|---|
| `object.py` | Object metadata and deletion response models |
| `upload.py` | Direct upload and presigned upload request and response models |
| `__init__.py` | Package-level documentation |

## Package Structure

```text
schemas/
├── __init__.py
├── object.py
├── upload.py
└── README.md
```

## Module Responsibilities

### `object.py`

Defines response models associated with stored S3 objects.

**`ObjectMetadataResponse`**

Represents metadata returned when retrieving information about an object.

Fields include:

- `object_id`: Application-level identifier assigned to the object.
- `filename`: Sanitized original filename.
- `content_type`: MIME content type associated with the object.
- `size_bytes`: Object size in bytes.
- `last_modified`: Optional timestamp of the last S3 modification.
- `etag`: Optional S3 entity tag.

**`ObjectDeletionResponse`**

Represents the result of an object deletion operation.

Fields include:

- `object_id`: Identifier of the deleted object.
- `deleted`: Indicates whether the deletion operation completed.

### `upload.py`

Defines request and response models for file upload workflows.

**`PresignedUploadRequest`**

Validates the information required to initiate a presigned upload.

Fields include:

- `filename`: Original filename supplied by the client.
- `content_type`: Declared MIME content type.
- `size_bytes`: Expected file size in bytes.

The schema enforces non-empty filename and content type values, maximum string lengths, and a positive expected file size.

**`PresignedUploadResponse`**

Represents the upload instructions returned to a client.

Fields include:

- `object_id`: Application-level object identifier.
- `upload_url`: Presigned S3 upload URL.
- `expires_in`: URL validity period in seconds.
- `required_headers`: Headers the client must include when uploading.

**`ObjectUploadResponse`**

Represents the result of a completed application-managed upload.

Fields include:

- `object_id`: Application-level object identifier.
- `filename`: Sanitized original filename.
- `content_type`: MIME content type.
- `size_bytes`: Uploaded object size in bytes.

## Schema Design Conventions

### Pydantic Validation

The project uses Pydantic v2 models with `BaseModel`, `Field`, and `ConfigDict`.

Use field constraints to reject invalid API data at the request boundary.

```python
from pydantic import BaseModel, ConfigDict, Field


class ExampleUploadRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    filename: str = Field(
        min_length=1,
        max_length=255,
    )
    size_bytes: int = Field(gt=0)
```

Important conventions:

- Use `Field` for constraints and API documentation metadata.
- Use `extra="forbid"` when unexpected input fields should be rejected.
- Use `str_strip_whitespace=True` when surrounding whitespace should not be retained.
- Use `default_factory` for mutable default values such as dictionaries and lists.
- Use explicit optional types and defaults.
- Keep validation rules close to the fields they govern.

### Request and Response Separation

Request schemas and response schemas serve different API responsibilities.

| Concern | Request schema | Response schema |
|---|---|---|
| Primary purpose | Validate client input | Define API output |
| Typical constraints | Required fields, lengths, ranges | Serialization and response structure |
| Unexpected fields | Usually rejected | Usually rejected |
| Sensitive data | Must not accept unnecessary secrets | Must not expose internal credentials |
| API documentation | Describes accepted input | Describes returned data |

Do not reuse a response model as a request model merely because some fields overlap. Separate models allow request validation and response serialization to evolve independently.

### Schema Validation Boundaries

Pydantic validation does not replace application-level validation.

For this project, distinguish the following responsibilities:

| Validation concern | Responsible layer |
|---|---|
| Required fields and data types | Pydantic schemas |
| Filename sanitization | Upload validation service |
| Allowed MIME types | Upload validation service |
| Actual file content verification | Upload validation service |
| Maximum upload size | Upload validation and upload handling |
| User authentication | Authentication dependency |
| Object ownership and access authorization | API/service authorization logic |
| S3 object operations | S3 service |

A declared `content_type` is client-provided metadata. It does not prove that the uploaded file contains data matching that MIME type.

Similarly, validating `size_bytes` in a presigned upload request does not automatically enforce the actual size of the object uploaded directly to S3. The upload workflow must independently enforce or verify the relevant size constraint.

## Integration with FastAPI

Schemas should be imported by API route modules and used in endpoint declarations.

Example:

```python
from fastapi import APIRouter

from app.schemas.object import ObjectMetadataResponse
from app.schemas.upload import (
    PresignedUploadRequest,
    PresignedUploadResponse,
)

router = APIRouter(prefix="/objects", tags=["Objects"])


@router.post(
    "/presigned-upload",
    response_model=PresignedUploadResponse,
)
async def create_presigned_upload(
    payload: PresignedUploadRequest,
) -> PresignedUploadResponse:
    """Initiate a presigned upload."""
    ...


@router.get(
    "/{object_id}",
    response_model=ObjectMetadataResponse,
)
async def get_object_metadata(
    object_id: str,
) -> ObjectMetadataResponse:
    """Retrieve object metadata."""
    ...
```

The example illustrates schema usage; actual endpoint implementations and storage operations belong in the API and service layers.

## API Contract Considerations

### Stable Response Contracts

Treat response schemas as externally visible API contracts.

Changes to response fields can affect:

- Frontend applications.
- Mobile clients.
- Other backend services.
- API consumers and automated integrations.
- Generated OpenAPI clients.

Prefer backward-compatible changes when evolving an established API.

### Avoid Exposing Internal Storage Details

Do not expose internal S3 object keys, bucket names, AWS credentials, KMS key identifiers, or raw SDK response objects unless the API contract explicitly requires them.

Use application-level identifiers such as `object_id` to identify resources externally. Resolve those identifiers to storage keys inside the application.

### Presigned URL Handling

A presigned URL is a temporary bearer capability. Anyone possessing a valid URL can use it within the permissions and constraints encoded in the signature.

Therefore:

- Do not log complete presigned URLs.
- Do not expose them in unrelated API responses.
- Keep expiration periods appropriately short.
- Ensure required headers match the signed request.
- Avoid treating URL generation as proof that an upload completed.
- Verify uploaded objects before marking an upload workflow as complete.

## Testing

Test schemas independently from API endpoints and S3 operations.

Recommended test coverage includes:

| Test area | Expected verification |
|---|---|
| Required fields | Missing required values are rejected |
| String constraints | Empty and oversized values are rejected |
| Numeric constraints | Invalid file sizes are rejected |
| Extra fields | Unexpected fields are rejected where configured |
| Whitespace handling | Configured string normalization works |
| Optional metadata | Missing optional values use their defaults |
| Mutable defaults | Separate model instances do not share dictionaries |
| URL validation | Invalid presigned URL values are rejected |
| Serialization | Valid models serialize to the expected API representation |

Example:

```python
import pytest
from pydantic import ValidationError

from app.schemas.upload import PresignedUploadRequest


def test_presigned_upload_request_accepts_valid_data() -> None:
    request = PresignedUploadRequest(
        filename="report.pdf",
        content_type="application/pdf",
        size_bytes=1024,
    )

    assert request.filename == "report.pdf"
    assert request.content_type == "application/pdf"
    assert request.size_bytes == 1024


def test_presigned_upload_request_rejects_empty_filename() -> None:
    with pytest.raises(ValidationError):
        PresignedUploadRequest(
            filename=" ",
            content_type="application/pdf",
            size_bytes=1024,
        )


def test_presigned_upload_request_rejects_non_positive_size() -> None:
    with pytest.raises(ValidationError):
        PresignedUploadRequest(
            filename="report.pdf",
            content_type="application/pdf",
            size_bytes=0,
        )
```

Run the test suite from the project root:

```bash
pytest tests/unit -v
```

Run Ruff against the schema package:

```bash
ruff check src/app/schemas
ruff format --check src/app/schemas
```

## Best Practices

- Keep schemas focused on API data contracts rather than business logic.
- Separate request models from response models.
- Use explicit field constraints and meaningful descriptions.
- Avoid exposing internal S3 implementation details.
- Treat client-provided filenames, MIME types, and file sizes as untrusted input.
- Keep object ownership and authorization checks outside Pydantic schemas.
- Avoid duplicating validation logic across API routes and service implementations.
- Test invalid inputs as thoroughly as valid inputs.
- Treat changes to response schemas as API contract changes.
- Keep schema definitions consistent with the actual service and endpoint interfaces.

## Common Mistakes

| Mistake | Impact | Recommended approach |
|---|---|---|
| Putting S3 operations inside schemas | Couples API contracts to infrastructure | Keep storage operations in service classes |
| Trusting client MIME types | Allows misleading content metadata | Validate actual file content separately |
| Trusting declared upload size | Can permit oversized direct uploads | Enforce and verify actual uploaded size |
| Reusing one model for unrelated operations | Creates fragile API contracts | Define purpose-specific models |
| Returning raw S3 responses | Leaks infrastructure details | Map SDK results to explicit response schemas |
| Using mutable defaults directly | Can create shared mutable state | Use `default_factory` |
| Accepting arbitrary extra fields | Weakens request contracts | Use `extra="forbid"` where appropriate |

## Key Takeaways

- The `schemas` package defines the API data contracts for upload operations and stored objects.
- Pydantic validates data structures, but business validation and authorization belong in their respective application layers.
- Keep request and response models separate to preserve clear API boundaries.
- Treat client-provided file metadata as untrusted until independently validated.
- Keep S3-specific implementation details inside the service layer rather than exposing them through API schemas.