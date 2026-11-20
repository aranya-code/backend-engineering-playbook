"""Unit tests for S3 object storage operations."""

from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import Settings
from app.services.s3_service import (
    S3ObjectNotFoundError,
    S3OperationError,
    S3Service,
)


pytestmark = pytest.mark.unit


@pytest.fixture
def settings() -> Settings:
    """Provide deterministic application settings."""
    return Settings.model_construct(
        aws_region="ap-south-1",
        s3_bucket_name="unit-test-uploads",
        s3_kms_key_id=None,
    )


@pytest.fixture
def s3_client() -> MagicMock:
    """Provide a mocked Boto3 S3 client."""
    client = MagicMock()
    client.head_object.return_value = {
        "ContentLength": 1024,
        "ContentType": "application/pdf",
        "LastModified": datetime(2026, 11, 11, tzinfo=UTC),
        "ETag": '"test-etag"',
        "Metadata": {
            "owner": "user-123",
            "document-type": "invoice",
        },
        "VersionId": "version-123",
        "ServerSideEncryption": "aws:kms",
        "SSEKMSKeyId": "test-kms-key",
    }
    client.get_object.return_value = {
        "Body": BytesIO(b"test file contents"),
        "ContentLength": 19,
        "ContentType": "text/plain",
        "ETag": '"download-etag"',
    }
    client.delete_object.return_value = {
        "VersionId": "version-123",
        "DeleteMarker": True,
    }
    return client


@pytest.fixture
def s3_service(
    settings: Settings,
    s3_client: MagicMock,
) -> S3Service:
    """Create the S3 service with an injected client."""
    return S3Service(
        settings=settings,
        s3_client=s3_client,
    )


def make_client_error(
    error_code: str,
    operation: str,
) -> ClientError:
    """Build a realistic AWS SDK ClientError."""
    return ClientError(
        {
            "Error": {
                "Code": error_code,
                "Message": f"Simulated {error_code} error",
            },
            "ResponseMetadata": {
                "HTTPStatusCode": 404 if error_code == "NoSuchKey" else 500,
            },
        },
        operation,
    )


class TestS3ServiceInitialization:
    """Tests for S3 service initialization."""

    def test_uses_injected_s3_client(
        self,
        settings: Settings,
        s3_client: MagicMock,
    ) -> None:
        """Use the supplied client instead of creating another client."""
        service = S3Service(
            settings=settings,
            s3_client=s3_client,
        )

        assert service is not None

    def test_creates_s3_client_when_none_is_injected(
        self,
        settings: Settings,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Create a regional S3 client when no client is injected."""
        import app.services.s3_service as service_module

        client = MagicMock()
        client_factory = MagicMock(return_value=client)

        monkeypatch.setattr(
            service_module.boto3,
            "client",
            client_factory,
        )

        service = S3Service(
            settings=settings,
            s3_client=None,
        )

        assert service is not None

        client_factory.assert_called_once_with(
            "s3",
            region_name=settings.aws_region,
            config=pytest.approx(
                client_factory.call_args.kwargs["config"]
            ),
        )

        client_config = client_factory.call_args.kwargs["config"]

        assert isinstance(client_config, Config)
        assert client_config.signature_version == "s3v4"
        assert client_config.retries["max_attempts"] == 3
        assert client_config.retries["mode"] == "standard"


class TestUploadFileobj:
    """Tests for uploading objects to S3."""

    def test_uploads_file_and_returns_object_metadata(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Upload a file and return the resulting object identifiers."""
        file_content = b"test file contents"
        file_object = BytesIO(file_content)

        result = s3_service.upload_fileobj(
            fileobj=file_object,
            object_key="uploads/report.pdf",
            content_type="application/pdf",
        )

        s3_client.upload_fileobj.assert_called_once()

        upload_kwargs = s3_client.upload_fileobj.call_args.kwargs

        assert upload_kwargs["Fileobj"] is file_object
        assert upload_kwargs["Bucket"] == "unit-test-uploads"
        assert upload_kwargs["Key"] == "uploads/report.pdf"
        assert upload_kwargs["ExtraArgs"]["ContentType"] == "application/pdf"

        assert result == {
            "object_key": "uploads/report.pdf",
            "etag": '"test-etag"',
            "version_id": "version-123",
        }

    def test_uploads_file_with_metadata(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Include custom metadata in the upload request."""
        file_object = BytesIO(b"invoice data")
        metadata = {
            "owner": "user-123",
            "document-type": "invoice",
        }

        s3_service.upload_fileobj(
            fileobj=file_object,
            object_key="uploads/invoice.pdf",
            content_type="application/pdf",
            metadata=metadata,
        )

        extra_args = s3_client.upload_fileobj.call_args.kwargs["ExtraArgs"]

        assert extra_args["Metadata"] == metadata

    def test_uploads_file_with_kms_encryption(
        self,
        s3_client: MagicMock,
    ) -> None:
        """Include SSE-KMS parameters when a KMS key is configured."""
        settings = Settings.model_construct(
            aws_region="ap-south-1",
            s3_bucket_name="unit-test-uploads",
            s3_kms_key_id="arn:aws:kms:ap-south-1:123456789012:key/test-key",
        )

        service = S3Service(
            settings=settings,
            s3_client=s3_client,
        )

        service.upload_fileobj(
            fileobj=BytesIO(b"encrypted content"),
            object_key="uploads/secure.pdf",
            content_type="application/pdf",
        )

        extra_args = s3_client.upload_fileobj.call_args.kwargs["ExtraArgs"]

        assert extra_args["ServerSideEncryption"] == "aws:kms"
        assert extra_args["SSEKMSKeyId"] == (
            "arn:aws:kms:ap-south-1:123456789012:key/test-key"
        )

    def test_uploads_file_without_explicit_kms_parameters(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Do not add explicit SSE-KMS parameters without a configured key."""
        s3_service.upload_fileobj(
            fileobj=BytesIO(b"plain content"),
            object_key="uploads/report.txt",
            content_type="text/plain",
        )

        extra_args = s3_client.upload_fileobj.call_args.kwargs["ExtraArgs"]

        assert "ServerSideEncryption" not in extra_args
        assert "SSEKMSKeyId" not in extra_args

    def test_upload_seeks_file_object_to_start(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Reset the file object's cursor before uploading."""
        file_object = BytesIO(b"complete file contents")
        file_object.seek(5)

        s3_service.upload_fileobj(
            fileobj=file_object,
            object_key="uploads/report.txt",
            content_type="text/plain",
        )

        assert file_object.tell() == 0
        assert (
            s3_client.upload_fileobj.call_args.kwargs["Fileobj"]
            is file_object
        )

    def test_checks_uploaded_object_metadata(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Retrieve object metadata after a successful upload."""
        s3_service.upload_fileobj(
            fileobj=BytesIO(b"test content"),
            object_key="uploads/report.txt",
            content_type="text/plain",
        )

        s3_client.head_object.assert_called_once_with(
            Bucket="unit-test-uploads",
            Key="uploads/report.txt",
        )

    def test_rejects_empty_object_key(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Reject an empty object key before making an S3 request."""
        with pytest.raises(ValueError):
            s3_service.upload_fileobj(
                fileobj=BytesIO(b"content"),
                object_key="",
                content_type="text/plain",
            )

        s3_client.upload_fileobj.assert_not_called()

    def test_rejects_object_key_with_leading_slash(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Reject absolute-looking object keys."""
        with pytest.raises(ValueError):
            s3_service.upload_fileobj(
                fileobj=BytesIO(b"content"),
                object_key="/uploads/report.txt",
                content_type="text/plain",
            )

        s3_client.upload_fileobj.assert_not_called()

    def test_rejects_object_key_with_backslash(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Reject object keys containing Windows path separators."""
        with pytest.raises(ValueError):
            s3_service.upload_fileobj(
                fileobj=BytesIO(b"content"),
                object_key="uploads\\report.txt",
                content_type="text/plain",
            )

        s3_client.upload_fileobj.assert_not_called()

    def test_rejects_object_key_with_control_character(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Reject object keys containing control characters."""
        with pytest.raises(ValueError):
            s3_service.upload_fileobj(
                fileobj=BytesIO(b"content"),
                object_key="uploads/report\x00.txt",
                content_type="text/plain",
            )

        s3_client.upload_fileobj.assert_not_called()

    def test_rejects_object_key_exceeding_s3_limit(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Reject object keys exceeding the 1,024-byte UTF-8 limit."""
        object_key = f"uploads/{'a' * 1020}"

        with pytest.raises(ValueError):
            s3_service.upload_fileobj(
                fileobj=BytesIO(b"content"),
                object_key=object_key,
                content_type="text/plain",
            )

        s3_client.upload_fileobj.assert_not_called()

    def test_rejects_empty_content_type(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Reject an empty content type before uploading."""
        with pytest.raises(ValueError):
            s3_service.upload_fileobj(
                fileobj=BytesIO(b"content"),
                object_key="uploads/report.txt",
                content_type="",
            )

        s3_client.upload_fileobj.assert_not_called()

    def test_rejects_invalid_content_type(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Reject content types that do not contain a MIME separator."""
        with pytest.raises(ValueError):
            s3_service.upload_fileobj(
                fileobj=BytesIO(b"content"),
                object_key="uploads/report.txt",
                content_type="invalid-content-type",
            )

        s3_client.upload_fileobj.assert_not_called()

    def test_wraps_upload_client_error(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Translate an AWS ClientError into the service exception."""
        s3_client.upload_fileobj.side_effect = make_client_error(
            "AccessDenied",
            "UploadFile",
        )

        with pytest.raises(S3OperationError) as exc_info:
            s3_service.upload_fileobj(
                fileobj=BytesIO(b"content"),
                object_key="uploads/report.txt",
                content_type="text/plain",
            )

        assert exc_info.value.operation == "upload_fileobj"
        assert exc_info.value.object_key == "uploads/report.txt"
        assert exc_info.value.error_code == "AccessDenied"


class TestHeadObject:
    """Tests for retrieving S3 object metadata."""

    def test_returns_normalized_object_metadata(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Map the S3 HeadObject response to the service metadata contract."""
        result = s3_service.head_object(
            object_key="uploads/report.pdf",
        )

        s3_client.head_object.assert_called_once_with(
            Bucket="unit-test-uploads",
            Key="uploads/report.pdf",
        )

        assert result == {
            "object_key": "uploads/report.pdf",
            "size_bytes": 1024,
            "content_type": "application/pdf",
            "last_modified": datetime(2026, 11, 11, tzinfo=UTC),
            "etag": '"test-etag"',
            "metadata": {
                "owner": "user-123",
                "document-type": "invoice",
            },
            "version_id": "version-123",
            "server_side_encryption": "aws:kms",
            "ssekms_key_id": "test-kms-key",
        }

    def test_handles_optional_metadata_fields(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Handle optional fields missing from the HeadObject response."""
        s3_client.head_object.return_value = {}

        result = s3_service.head_object(
            object_key="uploads/report.txt",
        )

        assert result == {
            "object_key": "uploads/report.txt",
            "size_bytes": 0,
            "content_type": None,
            "last_modified": None,
            "etag": None,
            "metadata": {},
            "version_id": None,
            "server_side_encryption": None,
            "ssekms_key_id": None,
        }

    def test_rejects_invalid_object_key(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Validate the object key before querying S3."""
        with pytest.raises(ValueError):
            s3_service.head_object(
                object_key="/uploads/report.pdf",
            )

        s3_client.head_object.assert_not_called()

    def test_raises_object_not_found_for_no_such_key(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Translate NoSuchKey into the dedicated not-found exception."""
        s3_client.head_object.side_effect = make_client_error(
            "NoSuchKey",
            "HeadObject",
        )

        with pytest.raises(S3ObjectNotFoundError) as exc_info:
            s3_service.head_object(
                object_key="uploads/missing.pdf",
            )

        assert exc_info.value.operation == "head_object"
        assert exc_info.value.object_key == "uploads/missing.pdf"
        assert exc_info.value.error_code == "NoSuchKey"

    def test_raises_object_not_found_for_not_found_response(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Translate a NotFound response into the dedicated exception."""
        s3_client.head_object.side_effect = make_client_error(
            "NotFound",
            "HeadObject",
        )

        with pytest.raises(S3ObjectNotFoundError):
            s3_service.head_object(
                object_key="uploads/missing.pdf",
            )

    def test_wraps_head_object_access_denied(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Translate non-not-found AWS errors into S3OperationError."""
        s3_client.head_object.side_effect = make_client_error(
            "AccessDenied",
            "HeadObject",
        )

        with pytest.raises(S3OperationError) as exc_info:
            s3_service.head_object(
                object_key="uploads/private.pdf",
            )

        assert not isinstance(exc_info.value, S3ObjectNotFoundError)
        assert exc_info.value.error_code == "AccessDenied"


class TestGetObject:
    """Tests for downloading objects from S3."""

    def test_returns_raw_s3_response(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Return the raw response so callers can consume the streaming body."""
        result = s3_service.get_object(
            object_key="uploads/report.txt",
        )

        s3_client.get_object.assert_called_once_with(
            Bucket="unit-test-uploads",
            Key="uploads/report.txt",
        )

        assert result is s3_client.get_object.return_value
        assert result["Body"].read() == b"test file contents"

    def test_rejects_invalid_object_key(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Reject invalid object keys before making an S3 request."""
        with pytest.raises(ValueError):
            s3_service.get_object(
                object_key="/uploads/report.txt",
            )

        s3_client.get_object.assert_not_called()

    def test_raises_object_not_found_for_missing_object(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Translate a missing-object response into the not-found exception."""
        s3_client.get_object.side_effect = make_client_error(
            "NoSuchKey",
            "GetObject",
        )

        with pytest.raises(S3ObjectNotFoundError) as exc_info:
            s3_service.get_object(
                object_key="uploads/missing.txt",
            )

        assert exc_info.value.operation == "get_object"
        assert exc_info.value.object_key == "uploads/missing.txt"
        assert exc_info.value.error_code == "NoSuchKey"

    def test_wraps_get_object_access_denied(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Translate access failures into S3OperationError."""
        s3_client.get_object.side_effect = make_client_error(
            "AccessDenied",
            "GetObject",
        )

        with pytest.raises(S3OperationError) as exc_info:
            s3_service.get_object(
                object_key="uploads/private.txt",
            )

        assert exc_info.value.error_code == "AccessDenied"


class TestDeleteObject:
    """Tests for deleting S3 objects."""

    def test_deletes_object_and_returns_normalized_result(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Delete an object and normalize the S3 response."""
        result = s3_service.delete_object(
            object_key="uploads/report.pdf",
        )

        s3_client.delete_object.assert_called_once_with(
            Bucket="unit-test-uploads",
            Key="uploads/report.pdf",
        )

        assert result == {
            "object_key": "uploads/report.pdf",
            "deleted": True,
            "version_id": "version-123",
            "delete_marker": True,
        }

    def test_handles_delete_response_without_optional_fields(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Handle delete responses that omit versioning information."""
        s3_client.delete_object.return_value = {}

        result = s3_service.delete_object(
            object_key="uploads/report.pdf",
        )

        assert result == {
            "object_key": "uploads/report.pdf",
            "deleted": True,
            "version_id": None,
            "delete_marker": False,
        }

    def test_rejects_invalid_object_key(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Validate the object key before attempting deletion."""
        with pytest.raises(ValueError):
            s3_service.delete_object(
                object_key="/uploads/report.pdf",
            )

        s3_client.delete_object.assert_not_called()

    def test_wraps_delete_access_denied(
        self,
        s3_service: S3Service,
        s3_client: MagicMock,
    ) -> None:
        """Translate AWS deletion failures into S3OperationError."""
        s3_client.delete_object.side_effect = make_client_error(
            "AccessDenied",
            "DeleteObject",
        )

        with pytest.raises(S3OperationError) as exc_info:
            s3_service.delete_object(
                object_key="uploads/protected.pdf",
            )

        assert exc_info.value.operation == "delete_object"
        assert exc_info.value.object_key == "uploads/protected.pdf"
        assert exc_info.value.error_code == "AccessDenied"