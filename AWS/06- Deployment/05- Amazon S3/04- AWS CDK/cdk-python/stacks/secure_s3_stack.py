from aws_cdk import CfnOutput
from aws_cdk import RemovalPolicy
from aws_cdk import Stack
from constructs import Construct

from constructs.secure_bucket import SecureBucket


class SecureS3Stack(Stack):
    """Provision a private S3 bucket with secure default configuration."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        bucket_name: str,
        versioned: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if not bucket_name or not bucket_name.strip():
            raise ValueError("bucket_name must be a non-empty string.")

        self.bucket = SecureBucket(
            self,
            "ApplicationBucket",
            bucket_name=bucket_name,
            versioned=versioned,
            removal_policy=RemovalPolicy.RETAIN,
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