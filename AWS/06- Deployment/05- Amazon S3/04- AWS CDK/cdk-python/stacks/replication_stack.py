import re

from aws_cdk import CfnOutput
from aws_cdk import RemovalPolicy
from aws_cdk import Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from constructs import Construct


_S3_BUCKET_ARN_PATTERN = re.compile(
    r"^arn:(?P<partition>[a-z0-9-]+):s3:::(?P<bucket>[a-z0-9][a-z0-9.-]{1,61}[a-z0-9])$"
)
_REGION_PATTERN = re.compile(r"^[a-z]{2}(?:-[a-z0-9]+)+-\\d$")


def validate_destination_bucket_arn(value: str) -> str:
    """Validate a literal S3 bucket ARN and return it unchanged.

    This intentionally rejects unresolved CDK tokens. The stack accepts an
    externally managed destination bucket, so its ARN must be known at
    synthesis time for validation and IAM resource scoping.
    """
    if not isinstance(value, str):
        raise TypeError("destination_bucket_arn must be a string.")

    match = _S3_BUCKET_ARN_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError(
            "destination_bucket_arn must have the form "
            "'arn:<partition>:s3:::<bucket-name>' with a valid bucket name."
        )

    bucket_name = match.group("bucket")
    reserved_prefixes = ("xn--", "sthree-", "amzn_s3_demo_")
    reserved_suffixes = (
        "-s3alias",
        "--ol-s3",
        ".mrap",
        "--x-s3",
        "--table-s3",
    )
    if (
        ".." in bucket_name
        or re.fullmatch(r"\\d{1,3}(?:\\.\\d{1,3}){3}", bucket_name)
        or ".-" in bucket_name
        or "-." in bucket_name
        or bucket_name.startswith(reserved_prefixes)
        or bucket_name.endswith(reserved_suffixes)
    ):
        raise ValueError(
            "destination_bucket_arn contains an invalid S3 bucket name."
        )

    return value


class ReplicationStack(Stack):
    """Provision a versioned S3 source bucket with cross-Region replication.

    The destination bucket is externally managed. For cross-account
    replication, its bucket policy must be deployed in the destination
    account and destination Region; see docs/replication.md.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        source_bucket_name: str,
        destination_bucket_arn: str,
        destination_region: str,
        destination_account_id: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if not isinstance(source_bucket_name, str) or not source_bucket_name.strip():
            raise ValueError("source_bucket_name must be a non-empty string.")

        destination_bucket_arn = validate_destination_bucket_arn(
            destination_bucket_arn
        )

        if (
            not isinstance(destination_region, str)
            or not _REGION_PATTERN.fullmatch(destination_region)
        ):
            raise ValueError(
                "destination_region must be a valid AWS Region identifier."
            )

        if destination_account_id is not None:
            if (
                not isinstance(destination_account_id, str)
                or not re.fullmatch(r"\\d{12}", destination_account_id)
            ):
                raise ValueError(
                    "destination_account_id must contain exactly 12 digits."
                )

        self.source_bucket = s3.Bucket(
            self,
            "ReplicationSourceBucket",
            bucket_name=source_bucket_name.strip(),
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
        )

        replication_role = iam.Role(
            self,
            "S3ReplicationRole",
            assumed_by=iam.ServicePrincipal("s3.amazonaws.com"),
            description=(
                "Allows Amazon S3 to replicate object versions from "
                "the source bucket to the destination bucket."
            ),
        )

        replication_role.add_to_policy(
            iam.PolicyStatement(
                sid="ReadSourceBucketConfiguration",
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetReplicationConfiguration",
                    "s3:ListBucket",
                ],
                resources=[self.source_bucket.bucket_arn],
            )
        )

        replication_role.add_to_policy(
            iam.PolicyStatement(
                sid="ReadSourceObjectVersions",
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObjectVersionForReplication",
                    "s3:GetObjectVersionAcl",
                    "s3:GetObjectVersionTagging",
                ],
                resources=[self.source_bucket.arn_for_objects("*")],
            )
        )

        replication_role.add_to_policy(
            iam.PolicyStatement(
                sid="ReplicateObjectsToDestination",
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:ReplicateObject",
                    "s3:ReplicateDelete",
                    "s3:ReplicateTags",
                ],
                resources=[f"{destination_bucket_arn}/*"],
            )
        )

        destination = {
            "Bucket": destination_bucket_arn,
            "StorageClass": "STANDARD",
        }
        if destination_account_id is not None:
            destination["Account"] = destination_account_id

        replication_configuration = {
            "Role": replication_role.role_arn,
            "Rules": [
                {
                    "ID": "ReplicateAllObjects",
                    "Status": "Enabled",
                    "Destination": destination,
                    "DeleteMarkerReplication": {"Status": "Enabled"},
                }
            ],
        }

        self.source_bucket.add_property_override(
            "ReplicationConfiguration",
            replication_configuration,
        )

        CfnOutput(
            self,
            "SourceBucketName",
            value=self.source_bucket.bucket_name,
            description="Name of the S3 replication source bucket.",
        )
        CfnOutput(
            self,
            "SourceBucketArn",
            value=self.source_bucket.bucket_arn,
            description="ARN of the S3 replication source bucket.",
        )
        CfnOutput(
            self,
            "DestinationBucketArn",
            value=destination_bucket_arn,
            description="ARN of the S3 replication destination bucket.",
        )
        CfnOutput(
            self,
            "DestinationRegion",
            value=destination_region,
            description="Region containing the externally managed destination bucket.",
        )
        CfnOutput(
            self,
            "ReplicationRoleArn",
            value=replication_role.role_arn,
            description="Grant this role destination-bucket permissions for cross-account replication.",
        )
