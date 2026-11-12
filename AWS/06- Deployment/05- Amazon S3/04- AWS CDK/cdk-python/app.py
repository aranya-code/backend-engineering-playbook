import os

import aws_cdk as cdk

from stacks.s3_stack import S3Stack


def get_required_environment_variable(name: str) -> str:
    """Return a required environment variable or raise a clear error."""
    value = os.getenv(name)

    if value is None or not value.strip():
        raise ValueError(
            f"Required environment variable '{name}' is not configured."
        )

    return value.strip()


def get_optional_integer_environment_variable(
    name: str,
    default: int,
) -> int:
    """Return an optional environment variable as an integer."""
    value = os.getenv(name)

    if value is None or not value.strip():
        return default

    try:
        parsed_value = int(value)
    except ValueError as exc:
        raise ValueError(
            f"Environment variable '{name}' must be an integer."
        ) from exc

    if parsed_value <= 0:
        raise ValueError(
            f"Environment variable '{name}' must be greater than zero."
        )

    return parsed_value


def get_optional_integer_or_none(name: str) -> int | None:
    """Return an optional positive integer or None when unset."""
    value = os.getenv(name)

    if value is None or not value.strip():
        return None

    try:
        parsed_value = int(value)
    except ValueError as exc:
        raise ValueError(
            f"Environment variable '{name}' must be an integer."
        ) from exc

    if parsed_value <= 0:
        raise ValueError(
            f"Environment variable '{name}' must be greater than zero."
        )

    return parsed_value


def main() -> None:
    """Create and synthesize the Amazon S3 CDK application."""
    bucket_name = get_required_environment_variable("S3_BUCKET_NAME")

    transition_after_days = get_optional_integer_environment_variable(
        "S3_TRANSITION_AFTER_DAYS",
        default=30,
    )

    expiration_after_days = get_optional_integer_or_none(
        "S3_EXPIRATION_AFTER_DAYS"
    )

    noncurrent_version_expiration_after_days = (
        get_optional_integer_environment_variable(
            "S3_NONCURRENT_VERSION_EXPIRATION_AFTER_DAYS",
            default=90,
        )
    )

    abort_incomplete_multipart_upload_after_days = (
        get_optional_integer_environment_variable(
            "S3_ABORT_INCOMPLETE_MULTIPART_UPLOAD_AFTER_DAYS",
            default=7,
        )
    )

    if (
        expiration_after_days is not None
        and expiration_after_days <= transition_after_days
    ):
        raise ValueError(
            "S3_EXPIRATION_AFTER_DAYS must be greater than "
            "S3_TRANSITION_AFTER_DAYS."
        )

    account = os.getenv("CDK_DEFAULT_ACCOUNT")
    region = os.getenv("CDK_DEFAULT_REGION")

    environment = cdk.Environment(
        account=account,
        region=region,
    )

    app = cdk.App()

    S3Stack(
        app,
        "ApplicationS3Stack",
        env=environment,
        bucket_name=bucket_name,
        transition_after_days=transition_after_days,
        expiration_after_days=expiration_after_days,
        noncurrent_version_expiration_after_days=(
            noncurrent_version_expiration_after_days
        ),
        abort_incomplete_multipart_upload_after_days=(
            abort_incomplete_multipart_upload_after_days
        ),
    )

    app.synth()


if __name__ == "__main__":
    main()