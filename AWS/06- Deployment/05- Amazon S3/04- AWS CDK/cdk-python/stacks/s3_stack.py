from aws_cdk import CfnOutput
from aws_cdk import RemovalPolicy
from aws_cdk import Stack
from constructs import Construct

from constructs.lifecycle_bucket import LifecycleBucket


class S3Stack(Stack):
    """Provision a production-oriented S3 bucket with lifecycle management."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        bucket_name: str,
        transition_after_days: int = 30,
        expiration_after_days: int | None = None,
        noncurrent_version_expiration_after_days: int | None = 90,
        abort_incomplete_multipart_upload_after_days: int = 7,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if not bucket_name or not bucket_name.strip():
            raise ValueError("bucket_name must be a non-empty string.")

        self.bucket = LifecycleBucket(
            self,
            "ApplicationBucket",
            bucket_name=bucket_name,
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN,
            transition_after_days=transition_after_days,
            expiration_after_days=expiration_after_days,
            noncurrent_version_expiration_after_days=(
                noncurrent_version_expiration_after_days
            ),
            abort_incomplete_multipart_upload_after_days=(
                abort_incomplete_multipart_upload_after_days
            ),
        )

        CfnOutput(
            self,
            "S3BucketName",
            value=self.bucket.bucket.bucket_name,
            description="Name of the application S3 bucket.",
        )

        CfnOutput(
            self,
            "S3BucketArn",
            value=self.bucket.bucket.bucket_arn,
            description="ARN of the application S3 bucket.",
        )

        CfnOutput(
            self,
            "S3BucketRegionalDomainName",
            value=self.bucket.bucket.bucket_regional_domain_name,
            description="Regional domain name of the application S3 bucket.",
        )