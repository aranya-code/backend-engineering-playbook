from aws_cdk import Duration
from aws_cdk import RemovalPolicy
from aws_cdk import aws_s3 as s3
from constructs import Construct


class LifecycleBucket(Construct):
    """Create a secure S3 bucket with configurable lifecycle management."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        bucket_name: str,
        versioned: bool = True,
        removal_policy: RemovalPolicy = RemovalPolicy.RETAIN,
        encryption: s3.BucketEncryption = s3.BucketEncryption.S3_MANAGED,
        transition_after_days: int = 30,
        expiration_after_days: int | None = None,
        noncurrent_version_expiration_after_days: int | None = 90,
        abort_incomplete_multipart_upload_after_days: int = 7,
    ) -> None:
        super().__init__(scope, construct_id)

        if not isinstance(bucket_name, str) or not bucket_name.strip():
            raise ValueError("bucket_name must be a non-empty string.")

        if not isinstance(versioned, bool):
            raise TypeError("versioned must be a boolean.")

        if not isinstance(removal_policy, RemovalPolicy):
            raise TypeError("removal_policy must be a RemovalPolicy value.")

        if not isinstance(encryption, s3.BucketEncryption):
            raise TypeError("encryption must be an S3 BucketEncryption value.")

        if (
            not isinstance(transition_after_days, int)
            or isinstance(transition_after_days, bool)
            or transition_after_days < 30
        ):
            raise ValueError(
                "transition_after_days must be an integer of at least 30."
            )

        if expiration_after_days is not None:
            if (
                not isinstance(expiration_after_days, int)
                or isinstance(expiration_after_days, bool)
                or expiration_after_days <= transition_after_days
            ):
                raise ValueError(
                    "expiration_after_days must be an integer greater "
                    "than transition_after_days."
                )

        if noncurrent_version_expiration_after_days is not None:
            if (
                not isinstance(noncurrent_version_expiration_after_days, int)
                or isinstance(
                    noncurrent_version_expiration_after_days,
                    bool,
                )
                or noncurrent_version_expiration_after_days <= 0
            ):
                raise ValueError(
                    "noncurrent_version_expiration_after_days must be "
                    "a positive integer or None."
                )

            if not versioned:
                raise ValueError(
                    "Noncurrent version expiration requires versioning."
                )

        if (
            not isinstance(abort_incomplete_multipart_upload_after_days, int)
            or isinstance(
                abort_incomplete_multipart_upload_after_days,
                bool,
            )
            or abort_incomplete_multipart_upload_after_days <= 0
        ):
            raise ValueError(
                "abort_incomplete_multipart_upload_after_days must be "
                "a positive integer."
            )

        self.bucket = s3.Bucket(
            self,
            "LifecycleBucket",
            bucket_name=bucket_name.strip(),
            versioned=versioned,
            encryption=encryption,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            enforce_ssl=True,
            removal_policy=removal_policy,
            auto_delete_objects=False,
        )

        lifecycle_rule = s3.LifecycleRule(
            id="ManageObjectLifecycle",
            enabled=True,
            transitions=[
                s3.Transition(
                    storage_class=s3.StorageClass.STANDARD_IA,
                    transition_after=Duration.days(
                        transition_after_days
                    ),
                )
            ],
            expiration=(
                Duration.days(expiration_after_days)
                if expiration_after_days is not None
                else None
            ),
            noncurrent_version_expiration=(
                Duration.days(noncurrent_version_expiration_after_days)
                if noncurrent_version_expiration_after_days is not None
                else None
            ),
        )

        self.bucket.add_lifecycle_rule(lifecycle_rule)

        self.bucket.add_lifecycle_rule(
            s3.LifecycleRule(
                id="AbortIncompleteMultipartUploads",
                enabled=True,
                abort_incomplete_multipart_upload_after=Duration.days(
                    abort_incomplete_multipart_upload_after_days
                ),
            )
        )