from aws_cdk import RemovalPolicy
from aws_cdk import aws_s3 as s3
from constructs import Construct


class SecureBucket(Construct):
    """Create an S3 bucket with secure production-oriented defaults."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        bucket_name: str,
        versioned: bool = True,
        removal_policy: RemovalPolicy = RemovalPolicy.RETAIN,
        encryption: s3.BucketEncryption = s3.BucketEncryption.S3_MANAGED,
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

        self.bucket = s3.Bucket(
            self,
            "SecureBucket",
            bucket_name=bucket_name.strip(),
            versioned=versioned,
            encryption=encryption,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            enforce_ssl=True,
            removal_policy=removal_policy,
            auto_delete_objects=False,
        )