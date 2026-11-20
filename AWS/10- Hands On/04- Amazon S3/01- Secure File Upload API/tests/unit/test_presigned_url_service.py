"""Unit tests for S3 presigned URL generation."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from botocore.config import Config

from app.config import Settings
from app.services.presigned_url_service import PresignedUrlService


pytestmark = pytest.mark.unit


@pytest.fixture
def settings() -> Settings:
    """Provide deterministic settings without loading environment variables."""
    return Settings.model_construct(
        aws_region="ap-south-1",
        s3_bucket_name="unit-test-uploads",
        s3_kms_key_id=None,
        presigned_url_expiration_seconds=300,
    )


@pytest.fixture
def s3_client() -> MagicMock:
    """Provide a mocked Boto3 S3 client."""
    client = MagicMock()
    client.generate_presigned_url.return_value = (
        "https://unit-test-uploads.s3.amazonaws.com/presigned"
    )
    return client


@pytest.fixture
def presigned_url_service(
    settings: Settings,
    s3_client: MagicMock,
) -> PresignedUrlService:
    """Create the service with an injected S3 client."""
    return PresignedUrlService(
        settings=settings,
        s3_client=s3_client,
    )


class TestPresignedUrlServiceInitialization:
    """Tests for service initialization and client injection."""

    def test_uses_injected_s3_client(
        self,
        settings: Settings,
        s3_client: MagicMock,
    ) -> None:
        """Avoid creating a new AWS client when one is injected."""
        service = PresignedUrlService(
            settings=settings,
            s3_client=s3_client,
        )

        assert service is not None

    def test_creates_s3_client_when_none_is_injected(
        self,
        settings: Settings,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Create a regional S3 client when no client is provided."""
        import app.services.presigned_url_service as service_module

        client = MagicMock()
        client_factory = MagicMock(return_value=client)

        monkeypatch.setattr(
            service_module.boto3,
            "client",
            client_factory,
        )

        service = PresignedUrlService(
            settings=settings,
            s3_client=None,
        )

        assert service is not None

        client_factory.assert_called_once()

        call_kwargs = client_factory.call_args.kwargs

        assert call_kwargs["service_name"] == "s3"
        assert call_kwargs["region_name"] == settings.aws_region

        client_config = call_kwargs["config"]

        assert isinstance(client_config, Config)
        assert client_config.signature_version == "s3v4"


class TestGenerateUploadUrl:
    """Tests for presigned PUT URL generation."""

    def test_generates_upload_url(
        self,
        presigned_url_service: PresignedUrlService,
        s3_client: MagicMock,
    ) -> None:
        """Generate a presigned PUT URL for an object."""
        result = presigned_url_service.generate_upload_url(
            object_key="uploads/report.pdf",
            content_type="application/pdf",
        )

        assert result == (
            "https://unit-test-uploads.s3.amazonaws.com/presigned",
            {"Content-Type": "application/pdf"},
        )

        s3_client.generate_presigned_url.assert_called_once_with(
            ClientMethod="put_object",
            Params={
                "Bucket": "unit-test-uploads",
                "Key": "uploads/report.pdf",
                "ContentType": "application/pdf",
            },
            ExpiresIn=300,
            HttpMethod="PUT",
        )

    def test_uses_requested_expiration(
        self,
        presigned_url_service: PresignedUrlService,
        s3_client: MagicMock,
    ) -> None:
        """Override the configured expiration for an individual upload."""
        presigned_url_service.generate_upload_url(
            object_key="uploads/report.pdf",
            content_type="application/pdf",
            expires_in=600,
        )

        call_kwargs = s3_client.generate_presigned_url.call_args.kwargs

        assert call_kwargs["ExpiresIn"] == 600

    def test_uses_default_expiration_when_not_overridden(
        self,
        presigned_url_service: PresignedUrlService,
        s3_client: MagicMock,
    ) -> None:
        """Use the configured expiration when no override is supplied."""
        presigned_url_service.generate_upload_url(
            object_key="uploads/report.pdf",
            content_type="application/pdf",
        )

        call_kwargs = s3_client.generate_presigned_url.call_args.kwargs

        assert call_kwargs["ExpiresIn"] == 300

    def test_includes_metadata_in_upload_request(
        self,
        presigned_url_service: PresignedUrlService,
        s3_client: MagicMock,
    ) -> None:
        """Include object metadata in the signed PUT request and headers."""
        metadata = {
            "owner": "user-123",
            "document-type": "invoice",
        }

        result = presigned_url_service.generate_upload_url(
            object_key="uploads/invoice.pdf",
            content_type="application/pdf",
            metadata=metadata,
        )

        expected_headers = {
            "Content-Type": "application/pdf",
            "x-amz-meta-owner": "user-123",
            "x-amz-meta-document-type": "invoice",
        }

        assert result[1] == expected_headers

        call_kwargs = s3_client.generate_presigned_url.call_args.kwargs

        assert call_kwargs["Params"]["Metadata"] == metadata

    def test_includes_kms_encryption_parameters(
        self,
        s3_client: MagicMock,
    ) -> None:
        """Sign the upload request with the configured SSE-KMS parameters."""
        settings = Settings.model_construct(
            aws_region="ap-south-1",
            s3_bucket_name="unit-test-uploads",
            s3_kms_key_id="arn:aws:kms:ap-south-1:123456789012:key/test-key",
            presigned_url_expiration_seconds=300,
        )

        service = PresignedUrlService(
            settings=settings,
            s3_client=s3_client,
        )

        result = service.generate_upload_url(
            object_key="uploads/report.pdf",
            content_type="application/pdf",
        )

        expected_key_id = (
            "arn:aws:kms:ap-south-1:123456789012:key/test-key"
        )

        expected_headers = {
            "Content-Type": "application/pdf",
            "x-amz-server-side-encryption": "aws:kms",
            "x-amz-server-side-encryption-aws-kms-key-id": expected_key_id,
        }

        assert result[1] == expected_headers

        call_kwargs = s3_client.generate_presigned_url.call_args.kwargs

        assert call_kwargs["Params"]["ServerSideEncryption"] == "aws:kms"
        assert call_kwargs["Params"]["SSEKMSKeyId"] == expected_key_id

    def test_includes_metadata_and_kms_headers_together(
        self,
        s3_client: MagicMock,
    ) -> None:
        """Preserve both metadata and encryption requirements in the URL."""
        settings = Settings.model_construct(
            aws_region="ap-south-1",
            s3_bucket_name="unit-test-uploads",
            s3_kms_key_id="arn:aws:kms:ap-south-1:123456789012:key/test-key",
            presigned_url_expiration_seconds=300,
        )

        service = PresignedUrlService(
            settings=settings,
            s3_client=s3_client,
        )

        result = service.generate_upload_url(
            object_key="uploads/report.pdf",
            content_type="application/pdf",
            metadata={"owner": "user-123"},
        )

        assert result[1] == {
            "Content-Type": "application/pdf",
            "x-amz-meta-owner": "user-123",
            "x-amz-server-side-encryption": "aws:kms",
            "x-amz-server-side-encryption-aws-kms-key-id": (
                "arn:aws:kms:ap-south-1:123456789012:key/test-key"
            ),
        }

        call_kwargs = s3_client.generate_presigned_url.call_args.kwargs

        assert call_kwargs["Params"]["Metadata"] == {
            "owner": "user-123",
        }
        assert call_kwargs["Params"]["ServerSideEncryption"] == "aws:kms"

    def test_uses_put_http_method(
        self,
        presigned_url_service: PresignedUrlService,
        s3_client: MagicMock,
    ) -> None:
        """Generate upload URLs specifically for HTTP PUT requests."""
        presigned_url_service.generate_upload_url(
            object_key="uploads/report.pdf",
            content_type="application/pdf",
        )

        call_kwargs = s3_client.generate_presigned_url.call_args.kwargs

        assert call_kwargs["ClientMethod"] == "put_object"
        assert call_kwargs["HttpMethod"] == "PUT"

    def test_returns_generated_url_and_required_headers(
        self,
        presigned_url_service: PresignedUrlService,
        s3_client: MagicMock,
    ) -> None:
        """Return the generated URL together with the required client headers."""
        s3_client.generate_presigned_url.return_value = (
            "https://example.com/upload"
        )

        url, headers = presigned_url_service.generate_upload_url(
            object_key="uploads/report.pdf",
            content_type="application/pdf",
        )

        assert url == "https://example.com/upload"
        assert headers == {
            "Content-Type": "application/pdf",
        }


class TestGenerateDownloadUrl:
    """Tests for presigned GET URL generation."""

    def test_generates_download_url(
        self,
        presigned_url_service: PresignedUrlService,
        s3_client: MagicMock,
    ) -> None:
        """Generate a presigned GET URL for an existing object key."""
        result = presigned_url_service.generate_download_url(
            object_key="uploads/report.pdf",
        )

        assert result == (
            "https://unit-test-uploads.s3.amazonaws.com/presigned"
        )

        s3_client.generate_presigned_url.assert_called_once_with(
            ClientMethod="get_object",
            Params={
                "Bucket": "unit-test-uploads",
                "Key": "uploads/report.pdf",
            },
            ExpiresIn=300,
            HttpMethod="GET",
        )

    def test_uses_requested_download_expiration(
        self,
        presigned_url_service: PresignedUrlService,
        s3_client: MagicMock,
    ) -> None:
        """Override the configured expiration for a download URL."""
        presigned_url_service.generate_download_url(
            object_key="uploads/report.pdf",
            expires_in=600,
        )

        call_kwargs = s3_client.generate_presigned_url.call_args.kwargs

        assert call_kwargs["ExpiresIn"] == 600

    def test_uses_default_download_expiration(
        self,
        presigned_url_service: PresignedUrlService,
        s3_client: MagicMock,
    ) -> None:
        """Use the configured expiration when no download override is given."""
        presigned_url_service.generate_download_url(
            object_key="uploads/report.pdf",
        )

        call_kwargs = s3_client.generate_presigned_url.call_args.kwargs

        assert call_kwargs["ExpiresIn"] == 300

    def test_uses_get_http_method(
        self,
        presigned_url_service: PresignedUrlService,
        s3_client: MagicMock,
    ) -> None:
        """Generate download URLs specifically for HTTP GET requests."""
        presigned_url_service.generate_download_url(
            object_key="uploads/report.pdf",
        )

        call_kwargs = s3_client.generate_presigned_url.call_args.kwargs

        assert call_kwargs["ClientMethod"] == "get_object"
        assert call_kwargs["HttpMethod"] == "GET"

    def test_does_not_add_upload_headers_to_download_url(
        self,
        presigned_url_service: PresignedUrlService,
        s3_client: MagicMock,
    ) -> None:
        """Keep upload-only metadata and content-type parameters out of GET."""
        presigned_url_service.generate_download_url(
            object_key="uploads/report.pdf",
        )

        params = s3_client.generate_presigned_url.call_args.kwargs["Params"]

        assert params == {
            "Bucket": "unit-test-uploads",
            "Key": "uploads/report.pdf",
        }

        assert "ContentType" not in params
        assert "Metadata" not in params
        assert "ServerSideEncryption" not in params
        assert "SSEKMSKeyId" not in params


class TestPresignedUrlIsolation:
    """Tests for object and bucket isolation in generated URLs."""

    @pytest.mark.parametrize(
        "object_key",
        [
            "uploads/report.pdf",
            "uploads/user-123/invoice.pdf",
            "uploads/2026/11/document.json",
        ],
    )
    def test_uses_exact_object_key(
        self,
        presigned_url_service: PresignedUrlService,
        s3_client: MagicMock,
        object_key: str,
    ) -> None:
        """Pass the requested object key to Boto3 without changing it."""
        presigned_url_service.generate_upload_url(
            object_key=object_key,
            content_type="application/pdf",
        )

        params: dict[str, Any] = (
            s3_client.generate_presigned_url.call_args.kwargs["Params"]
        )

        assert params["Key"] == object_key
        assert params["Bucket"] == "unit-test-uploads"

    def test_does_not_expose_kms_key_when_encryption_is_not_configured(
        self,
        presigned_url_service: PresignedUrlService,
        s3_client: MagicMock,
    ) -> None:
        """Do not add explicit KMS parameters when no KMS key is configured."""
        presigned_url_service.generate_upload_url(
            object_key="uploads/report.pdf",
            content_type="application/pdf",
        )

        params = s3_client.generate_presigned_url.call_args.kwargs["Params"]

        assert "ServerSideEncryption" not in params
        assert "SSEKMSKeyId" not in params