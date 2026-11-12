from aws_cdk import App
from aws_cdk.assertions import Match
from aws_cdk.assertions import Template

from stacks.s3_stack import S3Stack


def create_stack_template(
    *,
    transition_after_days: int = 30,
    expiration_after_days: int | None = None,
    noncurrent_version_expiration_after_days: int | None = 90,
    abort_incomplete_multipart_upload_after_days: int = 7,
) -> Template:
    """Create a synthesized template for the S3 stack."""
    app = App()

    stack = S3Stack(
        app,
        "TestS3Stack",
        bucket_name="test-application-bucket",
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


def test_stack_creates_one_s3_bucket() -> None:
    """Verify that the stack provisions exactly one S3 bucket."""
    template = create_stack_template()

    template.resource_count_is("AWS::S3::Bucket", 1)


def test_bucket_has_secure_configuration() -> None:
    """Verify encryption, versioning, and public-access restrictions."""
    template = create_stack_template()

    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "VersioningConfiguration": {
                "Status": "Enabled",
            },
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
                ],
            },
            "BucketEncryption": {
                "ServerSideEncryptionConfiguration": [
                    {
                        "ServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256",
                        }
                    }
                ],
            },
        },
    )


def test_bucket_enforces_https_requests() -> None:
    """Verify that insecure transport is explicitly denied."""
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


def test_bucket_has_standard_ia_transition() -> None:
    """Verify the default lifecycle transition to STANDARD_IA."""
    template = create_stack_template()

    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "LifecycleConfiguration": {
                "Rules": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Id": "ManageObjectLifecycle",
                                "Status": "Enabled",
                                "Transitions": [
                                    {
                                        "StorageClass": "STANDARD_IA",
                                        "TransitionInDays": 30,
                                    }
                                ],
                            }
                        )
                    ]
                )
            }
        },
    )


def test_bucket_expires_noncurrent_versions() -> None:
    """Verify the default noncurrent-version expiration rule."""
    template = create_stack_template()

    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "LifecycleConfiguration": {
                "Rules": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Id": "ManageObjectLifecycle",
                                "NoncurrentVersionExpiration": {
                                    "NoncurrentDays": 90,
                                },
                            }
                        )
                    ]
                )
            }
        },
    )


def test_bucket_aborts_incomplete_multipart_uploads() -> None:
    """Verify automatic cleanup of incomplete multipart uploads."""
    template = create_stack_template()

    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "LifecycleConfiguration": {
                "Rules": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Id": "AbortIncompleteMultipartUploads",
                                "Status": "Enabled",
                                "AbortIncompleteMultipartUpload": {
                                    "DaysAfterInitiation": 7,
                                },
                            }
                        )
                    ]
                )
            }
        },
    )


def test_custom_lifecycle_configuration() -> None:
    """Verify that custom lifecycle values reach the bucket resource."""
    template = create_stack_template(
        transition_after_days=60,
        expiration_after_days=365,
        noncurrent_version_expiration_after_days=120,
        abort_incomplete_multipart_upload_after_days=14,
    )

    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "LifecycleConfiguration": {
                "Rules": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Id": "ManageObjectLifecycle",
                                "Status": "Enabled",
                                "Transitions": [
                                    {
                                        "StorageClass": "STANDARD_IA",
                                        "TransitionInDays": 60,
                                    }
                                ],
                                "ExpirationInDays": 365,
                                "NoncurrentVersionExpiration": {
                                    "NoncurrentDays": 120,
                                },
                            }
                        ),
                        Match.object_like(
                            {
                                "Id": "AbortIncompleteMultipartUploads",
                                "AbortIncompleteMultipartUpload": {
                                    "DaysAfterInitiation": 14,
                                },
                            }
                        ),
                    ]
                )
            }
        },
    )


def test_current_object_expiration_is_omitted_by_default() -> None:
    """Verify that current objects are not expired without configuration."""
    template = create_stack_template()

    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "LifecycleConfiguration": {
                "Rules": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Id": "ManageObjectLifecycle",
                                "Status": "Enabled",
                            }
                        )
                    ]
                )
            }
        },
    )

    template.resource_properties_count_is(
        "AWS::S3::Bucket",
        {
            "LifecycleConfiguration": {
                "Rules": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Id": "ManageObjectLifecycle",
                                "ExpirationInDays": Match.absent(),
                            }
                        )
                    ]
                )
            }
        },
        1,
    )


def test_noncurrent_version_expiration_can_be_disabled() -> None:
    """Verify that noncurrent-version expiration can be omitted."""
    template = create_stack_template(
        noncurrent_version_expiration_after_days=None,
    )

    template.resource_properties_count_is(
        "AWS::S3::Bucket",
        {
            "LifecycleConfiguration": {
                "Rules": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Id": "ManageObjectLifecycle",
                                "NoncurrentVersionExpiration": Match.absent(),
                            }
                        )
                    ]
                )
            }
        },
        1,
    )


def test_stack_exposes_bucket_outputs() -> None:
    """Verify that the stack exports essential bucket attributes."""
    template = create_stack_template()

    template.has_output(
        "S3BucketName",
        {
            "Description": "Name of the application S3 bucket.",
        },
    )

    template.has_output(
        "S3BucketArn",
        {
            "Description": "ARN of the application S3 bucket.",
        },
    )

    template.has_output(
        "S3BucketRegionalDomainName",
        {
            "Description": (
                "Regional domain name of the application S3 bucket."
            ),
        },
    )


def test_transition_period_must_be_at_least_thirty_days() -> None:
    """Reject lifecycle transitions earlier than the supported minimum."""
    app = App()

    try:
        S3Stack(
            app,
            "InvalidTransitionStack",
            bucket_name="test-invalid-transition-bucket",
            transition_after_days=29,
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError for a transition period below 30 days."
    )


def test_expiration_must_be_greater_than_transition_period() -> None:
    """Reject expiration configured before or on the transition day."""
    app = App()

    try:
        S3Stack(
            app,
            "InvalidExpirationStack",
            bucket_name="test-invalid-expiration-bucket",
            transition_after_days=30,
            expiration_after_days=30,
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError when expiration is not greater "
        "than the transition period."
    )