import pytest

from aws_cdk import App
from aws_cdk.assertions import Match, Template

from stacks.replication_stack import (
    ReplicationStack,
    validate_destination_bucket_arn,
)

SOURCE_BUCKET = "test-replication-source-bucket"
DESTINATION_ARN = "arn:aws:s3:::test-replication-destination-bucket"
DESTINATION_REGION = "ap-south-1"
DESTINATION_ACCOUNT = "123456789012"


def create_template(
    *,
    destination_bucket_arn: str = DESTINATION_ARN,
    destination_region: str = DESTINATION_REGION,
    destination_account_id: str | None = None,
) -> Template:
    app = App()
    stack = ReplicationStack(
        app,
        "TestReplicationStack",
        source_bucket_name=SOURCE_BUCKET,
        destination_bucket_arn=destination_bucket_arn,
        destination_region=destination_region,
        destination_account_id=destination_account_id,
        env={"account": "111111111111", "region": "ap-south-1"},
    )
    return Template.from_stack(stack)


def test_replication_source_bucket_is_versioned_and_private() -> None:
    template = create_template()
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "VersioningConfiguration": {"Status": "Enabled"},
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            },
            "OwnershipControls": {
                "Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]
            },
            "BucketEncryption": {
                "ServerSideEncryptionConfiguration": [
                    {
                        "ServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256"
                        }
                    }
                ]
            },
        },
    )


def test_replication_configuration_has_supported_destination_properties() -> None:
    template = create_template()
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "ReplicationConfiguration": {
                "Rules": [
                    {
                        "ID": "ReplicateAllObjects",
                        "Status": "Enabled",
                        "Destination": {
                            "Bucket": DESTINATION_ARN,
                            "StorageClass": "STANDARD",
                        },
                        "DeleteMarkerReplication": {"Status": "Enabled"},
                    }
                ]
            }
        },
    )
    bucket = next(iter(template.find_resources("AWS::S3::Bucket").values()))
    destination = bucket["Properties"]["ReplicationConfiguration"]["Rules"][0]["Destination"]
    assert "Region" not in destination


def test_destination_account_is_included_only_when_supplied() -> None:
    template = create_template(destination_account_id=DESTINATION_ACCOUNT)
    bucket = next(iter(template.find_resources("AWS::S3::Bucket").values()))
    destination = bucket["Properties"]["ReplicationConfiguration"]["Rules"][0]["Destination"]
    assert destination["Account"] == DESTINATION_ACCOUNT


def test_replication_role_has_source_and_destination_permissions() -> None:
    template = create_template()
    policies = template.find_resources("AWS::IAM::Policy")
    assert policies
    statements = []
    for policy in policies.values():
        statements.extend(policy["Properties"]["PolicyDocument"]["Statement"])
    actions = {
        action
        for statement in statements
        for action in (
            statement["Action"]
            if isinstance(statement["Action"], list)
            else [statement["Action"]]
        )
    }
    assert "s3:GetReplicationConfiguration" in actions
    assert "s3:GetObjectVersionForReplication" in actions
    assert "s3:ReplicateObject" in actions
    assert "s3:ReplicateDelete" in actions


def test_replication_role_trusts_s3_service() -> None:
    template = create_template()
    template.has_resource_properties(
        "AWS::IAM::Role",
        {
            "AssumeRolePolicyDocument": {
                "Statement": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Principal": {"Service": "s3.amazonaws.com"},
                                "Action": "sts:AssumeRole",
                            }
                        )
                    ]
                )
            }
        },
    )


@pytest.mark.parametrize(
    "arn",
    [
        "",
        "not-an-arn",
        "arn:aws:s3:::",
        "arn:aws:s3:::bad_bucket_name",
        "arn:aws:s3:::bucket..name",
        "arn:aws:s3:::192.168.1.1",
        "arn:aws:s3:::bucket.-name",
        "arn:aws:s3:::bucket-.name",
        "arn:aws:s3:::xn--reserved",
        "arn:aws:s3:::reserved-s3alias",
        "arn:aws:s3:::reserved.mrap",
    ],
)
def test_invalid_destination_bucket_arns_are_rejected(arn: str) -> None:
    with pytest.raises(ValueError):
        validate_destination_bucket_arn(arn)


def test_valid_destination_bucket_arn_is_returned_unchanged() -> None:
    assert validate_destination_bucket_arn(DESTINATION_ARN) == DESTINATION_ARN


@pytest.mark.parametrize(
    "account_id",
    ["123", "abcdefghijkl", "12345678901", "1234567890123"],
)
def test_invalid_destination_account_id_is_rejected(account_id: str) -> None:
    with pytest.raises(ValueError, match="12 digits"):
        create_template(destination_account_id=account_id)


@pytest.mark.parametrize("region", ["", "invalid", "ap-south", "AP-SOUTH-1"])
def test_invalid_destination_region_is_rejected(region: str) -> None:
    with pytest.raises(ValueError, match="Region"):
        create_template(destination_region=region)


def test_replication_outputs_include_role_and_destination_region() -> None:
    template = create_template()
    template.has_output("ReplicationRoleArn")
    template.has_output("DestinationRegion")
    template.has_output("DestinationBucketArn")
