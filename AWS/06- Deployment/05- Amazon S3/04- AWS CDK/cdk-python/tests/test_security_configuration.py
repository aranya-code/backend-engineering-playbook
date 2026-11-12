from aws_cdk import App
from aws_cdk.assertions import Match
from aws_cdk.assertions import Template

from stacks.s3_stack import S3Stack


def create_stack_template(
    *,
    bucket_name: str = "test-security-bucket",
    transition_after_days: int = 30,
    expiration_after_days: int | None = None,
    noncurrent_version_expiration_after_days: int | None = 90,
    abort_incomplete_multipart_upload_after_days: int = 7,
) -> Template:
    """Create a synthesized template for security configuration tests."""
    app = App()

    stack = S3Stack(
        app,
        "TestSecurityStack",
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

    return Template.from_stack(stack)


def test_bucket_blocks_all_public_access() -> None:
    """Verify that all S3 Block Public Access controls are enabled."""
    template = create_stack_template()

    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            }
        },
    )


def test_bucket_enforces_bucket_owner_ownership() -> None:
    """Verify that ACL-based ownership is disabled."""
    template = create_stack_template()

    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "OwnershipControls": {
                "Rules": [
                    {
                        "ObjectOwnership": "BucketOwnerEnforced",
                    }
                ]
            }
        },
    )


def test_bucket_uses_server_side_encryption() -> None:
    """Verify that the bucket uses default SSE-S3 encryption."""
    template = create_stack_template()

    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "BucketEncryption": {
                "ServerSideEncryptionConfiguration": [
                    {
                        "ServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256",
                        }
                    }
                ]
            }
        },
    )


def test_bucket_policy_denies_insecure_transport() -> None:
    """Verify that bucket access over insecure transport is denied."""
    template = create_stack_template()

    template.has_resource_properties(
        "AWS::S3::BucketPolicy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Effect": "Deny",
                                "Principal": "*",
                                "Action": "s3:*",
                                "Condition": {
                                    "Bool": {
                                        "aws:SecureTransport": "false",
                                    }
                                },
                            }
                        )
                    ]
                )
            }
        },
    )


def test_bucket_versioning_is_enabled() -> None:
    """Verify that object versioning is enabled."""
    template = create_stack_template()

    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "VersioningConfiguration": {
                "Status": "Enabled",
            }
        },
    )


def test_bucket_has_no_static_website_configuration() -> None:
    """Verify that the private application bucket is not a website bucket."""
    template = create_stack_template()

    template.resource_properties_count_is(
        "AWS::S3::Bucket",
        {
            "WebsiteConfiguration": Match.absent(),
        },
        1,
    )


def test_bucket_policy_contains_no_wildcard_allow_statement() -> None:
    """Reject bucket policies that grant wildcard-principal access."""
    template = create_stack_template()

    bucket_policies = template.find_resources("AWS::S3::BucketPolicy")

    for logical_id, resource in bucket_policies.items():
        statements = (
            resource.get("Properties", {})
            .get("PolicyDocument", {})
            .get("Statement", [])
        )

        for statement in statements:
            if statement.get("Effect") != "Allow":
                continue

            principal = statement.get("Principal")

            assert principal != "*", (
                f"Bucket policy {logical_id} contains a wildcard "
                "principal Allow statement."
            )

            if isinstance(principal, dict):
                assert principal.get("AWS") != "*", (
                    f"Bucket policy {logical_id} contains a wildcard "
                    "AWS principal Allow statement."
                )


def test_bucket_policy_has_no_public_access_grant() -> None:
    """Verify that no bucket policy grants access to public principals."""
    template = create_stack_template()

    bucket_policies = template.find_resources("AWS::S3::BucketPolicy")

    for logical_id, resource in bucket_policies.items():
        statements = (
            resource.get("Properties", {})
            .get("PolicyDocument", {})
            .get("Statement", [])
        )

        for statement in statements:
            if statement.get("Effect") != "Allow":
                continue

            principal = statement.get("Principal")

            if principal == "*":
                raise AssertionError(
                    f"Bucket policy {logical_id} grants access "
                    "to all principals."
                )

            if isinstance(principal, dict):
                aws_principal = principal.get("AWS")

                assert aws_principal != "*", (
                    f"Bucket policy {logical_id} grants access "
                    "to all AWS principals."
                )


def test_bucket_uses_private_access_defaults_with_custom_name() -> None:
    """Verify security settings remain enabled for a custom bucket name."""
    template = create_stack_template(
        bucket_name="test-custom-security-bucket",
    )

    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "BucketName": "test-custom-security-bucket",
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            },
            "OwnershipControls": {
                "Rules": [
                    {
                        "ObjectOwnership": "BucketOwnerEnforced",
                    }
                ]
            },
        },
    )