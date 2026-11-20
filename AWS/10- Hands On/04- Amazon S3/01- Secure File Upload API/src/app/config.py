"""Application configuration for the Secure File Upload API."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load and validate application settings from environment variables.

    Environment variables take precedence over values in the optional .env file.
    AWS credentials are intentionally not defined here; Boto3 uses the standard
    AWS credential provider chain, including workload identity and IAM roles.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    app_name: str = "Secure File Upload API"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    aws_region: str = Field(
        default="ap-south-1",
        validation_alias="AWS_REGION",
    )
    s3_bucket_name: str = Field(
        validation_alias="S3_BUCKET_NAME",
    )
    s3_upload_prefix: str = Field(
        default="uploads/",
        validation_alias="S3_UPLOAD_PREFIX",
    )
    s3_kms_key_id: str | None = Field(
        default=None,
        validation_alias="S3_KMS_KEY_ID",
    )

    max_upload_size_bytes: Annotated[int, Field(gt=0)] = Field(
        default=10 * 1024 * 1024,
        validation_alias="MAX_UPLOAD_SIZE_BYTES",
    )
    allowed_content_types: tuple[str, ...] = Field(
        default=(
            "application/pdf",
            "application/json",
            "text/plain",
            "text/csv",
            "image/jpeg",
            "image/png",
        ),
        validation_alias="ALLOWED_CONTENT_TYPES",
    )

    presigned_url_expiration_seconds: Annotated[
        int,
        Field(ge=1, le=3600),
    ] = Field(
        default=300,
        validation_alias="PRESIGNED_URL_EXPIRATION_SECONDS",
    )

    jwt_secret_key: SecretStr | None = Field(
        default=None,
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        validation_alias="JWT_ALGORITHM",
    )
    access_token_expiration_minutes: Annotated[
        int,
        Field(gt=0),
    ] = Field(
        default=30,
        validation_alias="ACCESS_TOKEN_EXPIRATION_MINUTES",
    )

    log_level: str = Field(
        default="INFO",
        validation_alias="LOG_LEVEL",
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        """Normalize and validate the deployment environment."""
        normalized = value.strip().lower()

        allowed_environments = {
            "development",
            "dev",
            "test",
            "staging",
            "production",
            "prod",
        }

        if normalized not in allowed_environments:
            raise ValueError(
                "environment must be one of: development, dev, test, "
                "staging, production, prod"
            )

        return normalized

    @field_validator("aws_region")
    @classmethod
    def validate_aws_region(cls, value: str) -> str:
        """Reject empty or whitespace-padded AWS Region values."""
        normalized = value.strip()

        if not normalized:
            raise ValueError("AWS_REGION must not be empty")

        return normalized

    @field_validator("s3_bucket_name")
    @classmethod
    def validate_bucket_name(cls, value: str) -> str:
        """Ensure that the configured bucket name is not empty."""
        normalized = value.strip()

        if not normalized:
            raise ValueError("S3_BUCKET_NAME must not be empty")

        return normalized

    @field_validator("s3_upload_prefix")
    @classmethod
    def validate_upload_prefix(cls, value: str) -> str:
        """Normalize the upload prefix and reject unsafe path-like values."""
        normalized = value.strip()

        if normalized.startswith("/"):
            raise ValueError("S3_UPLOAD_PREFIX must be a relative prefix")

        if "\\" in normalized or "//" in normalized:
            raise ValueError(
                "S3_UPLOAD_PREFIX must not contain backslashes or "
                "consecutive slashes"
            )

        if ".." in normalized:
            raise ValueError("S3_UPLOAD_PREFIX must not contain '..'")

        if any(ord(character) < 32 or ord(character) == 127 for character in normalized):
            raise ValueError("S3_UPLOAD_PREFIX must not contain control characters")

        if normalized and not normalized.endswith("/"):
            normalized = f"{normalized}/"

        return normalized

    @field_validator("allowed_content_types")
    @classmethod
    def validate_allowed_content_types(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Normalize and validate the configured MIME type allowlist."""
        normalized = tuple(
            content_type.strip().lower()
            for content_type in value
            if content_type.strip()
        )

        if not normalized:
            raise ValueError("ALLOWED_CONTENT_TYPES must contain at least one MIME type")

        if any("/" not in content_type for content_type in normalized):
            raise ValueError(
                "Each allowed content type must use the type/subtype format"
            )

        return tuple(dict.fromkeys(normalized))

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Normalize the logging level and reject unsupported values."""
        normalized = value.strip().upper()
        allowed_levels = {
            "CRITICAL",
            "ERROR",
            "WARNING",
            "INFO",
            "DEBUG",
        }

        if normalized not in allowed_levels:
            raise ValueError(
                "LOG_LEVEL must be one of: CRITICAL, ERROR, WARNING, INFO, DEBUG"
            )

        return normalized

    def validate_production_settings(self) -> None:
        """Enforce settings that must be explicitly configured in production."""
        if self.environment in {"production", "prod"}:
            if self.debug:
                raise ValueError("DEBUG must be disabled in production")

            if self.jwt_secret_key is None:
                raise ValueError("JWT_SECRET_KEY must be configured in production")

            if not self.s3_kms_key_id:
                raise ValueError("S3_KMS_KEY_ID must be configured in production")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide application settings instance."""
    settings = Settings()
    settings.validate_production_settings()
    return settings