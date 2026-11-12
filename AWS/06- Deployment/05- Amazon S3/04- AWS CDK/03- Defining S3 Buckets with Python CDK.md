# 03- Defining S3 Buckets with Python CDK

## Overview

AWS Cloud Development Kit (CDK) provides a Python programming interface for defining and managing Amazon S3 infrastructure. The `aws_s3` module exposes constructs for creating buckets and configuring properties such as versioning, encryption, public-access blocking, ownership controls, lifecycle rules, event notifications, and resource retention.

For production backend systems, an S3 bucket should be treated as an infrastructure resource with an explicit security, availability, retention, and operational configuration.

A bucket definition affects more than object storage. It influences:

- How application services authenticate and access objects.
- Whether uploaded objects are encrypted.
- Whether public access is possible.
- How accidental overwrites and deletions are handled.
- How long data remains stored.
- Whether infrastructure deployments can replace or delete the bucket.
- How S3 integrates with CloudFront, Lambda, SQS, and other AWS services.

This document focuses on defining S3 buckets using Python CDK, with practical configurations suitable for backend applications.

## S3 CDK Module

The primary module for defining S3 resources is:

```python
from aws_cdk import aws_s3 as s3
```

The most commonly used construct is `s3.Bucket`.

It is an L2 construct that provides a higher-level interface over the CloudFormation `AWS::S3::Bucket` resource.

### Common S3 CDK Constructs

| Construct | Purpose |
|---|---|
| `s3.Bucket` | Creates and configures an S3 bucket. |
| `s3.CfnBucket` | Defines the underlying CloudFormation bucket resource directly. |
| `s3.BucketEncryption` | Selects the bucket's default server-side encryption configuration. |
| `s3.BlockPublicAccess` | Configures public-access blocking. |
| `s3.ObjectOwnership` | Configures ownership and ACL behavior. |
| `s3.LifecycleRule` | Defines lifecycle transitions and expiration behavior. |
| `s3.Transition` | Defines a storage-class transition. |
| `s3.StorageClass` | Identifies an S3 storage class. |
| `s3.EventType` | Identifies supported S3 event types. |
| `s3.NotificationKeyFilter` | Filters notification events by object key prefix or suffix. |

## Creating a Basic S3 Bucket

The simplest implementation creates a bucket using the L2 `Bucket` construct.

```python
from aws_cdk import Stack
from aws_cdk import aws_s3 as s3
from constructs import Construct


class StorageStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        super().__init__(
            scope,
            construct_id,
            **kwargs,
        )

        self.bucket = s3.Bucket(
            self,
            "ApplicationBucket",
        )
```

The constructor arguments have specific meanings:

| Argument | Purpose |
|---|---|
| `scope` | Parent construct, usually the stack. |
| `construct_id` | Logical identifier within the construct tree. |
| Additional keyword arguments | Bucket configuration properties. |

### Construct ID Versus Physical Bucket Name

The construct ID:

```python
"ApplicationBucket"
```

identifies the resource within the CDK construct tree.

It does not necessarily become the physical S3 bucket name.

When `bucket_name` is omitted, CloudFormation generates a physical bucket name.

This is useful because S3 bucket names must be globally unique.

Use generated names when:

- The application does not require a predictable bucket name.
- Infrastructure may be deployed into multiple accounts.
- Multiple environments need independent bucket resources.
- Avoiding naming collisions is important.

Use an explicit bucket name only when external integrations or operational requirements need a predictable identifier.

## Bucket Naming

S3 general purpose bucket names must follow S3 naming requirements and be unique within the applicable global namespace.

A naming convention should identify the organization, application, environment, and purpose.

Example:

```text
company-document-service-dev
company-document-service-staging
company-document-service-production
```

These names are illustrative and may already be registered by another AWS customer.

### Explicit Bucket Name

```python
bucket = s3.Bucket(
    self,
    "DocumentBucket",
    bucket_name="company-document-service-dev",
)
```

### Naming Considerations

- Use lowercase letters and numbers where practical.
- Avoid sensitive information in bucket names.
- Include environment identifiers when appropriate.
- Avoid unstable values such as timestamps unless uniqueness requires them.
- Do not assume a bucket name can be reused immediately after deletion.
- Consider account and Region boundaries when designing deployment conventions.

An explicit bucket name is a physical resource property. Changing it can require bucket replacement rather than an in-place update.

For production data buckets, replacement must be treated as a migration rather than an ordinary configuration change.

## Bucket Configuration Properties

The `s3.Bucket` construct exposes properties that control security, data protection, lifecycle behavior, and resource management.

A production-oriented bucket should configure these properties according to its workload rather than relying on implicit defaults.

### Common Properties

| Property | Purpose |
|---|---|
| `bucket_name` | Sets the physical bucket name. |
| `versioned` | Enables S3 versioning. |
| `encryption` | Configures default server-side encryption. |
| `encryption_key` | Specifies a customer-managed KMS key when using SSE-KMS. |
| `block_public_access` | Controls public-access blocking. |
| `object_ownership` | Configures object ownership and ACL behavior. |
| `enforce_ssl` | Adds a policy denying insecure transport. |
| `lifecycle_rules` | Configures lifecycle behavior during bucket creation. |
| `removal_policy` | Controls CloudFormation removal behavior. |
| `auto_delete_objects` | Configures automatic object deletion when supported with destructive removal behavior. |
| `event_bridge_enabled` | Enables delivery of supported S3 events to EventBridge. |

Property availability and behavior should be checked against the CDK library version used by the project.

## Private Bucket Configuration

Most backend applications should use private S3 buckets.

A private bucket should block public access and avoid ACL-based access control unless a specific integration requires otherwise.

```python
from aws_cdk import RemovalPolicy
from aws_cdk import Stack
from aws_cdk import aws_s3 as s3
from constructs import Construct


class PrivateStorageStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        super().__init__(
            scope,
            construct_id,
            **kwargs,
        )

        self.bucket = s3.Bucket(
            self,
            "PrivateApplicationBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.RETAIN,
        )
```

### Block Public Access

```python
block_public_access=s3.BlockPublicAccess.BLOCK_ALL
```

This enables the supported S3 public-access block controls.

It protects against public exposure through bucket policies and ACL-related mechanisms.

It does not replace IAM permissions or application authorization.

### Object Ownership

```python
object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED
```

This configures bucket-owner-enforced ownership and disables ACL-based access control.

It is suitable for most modern application storage architectures.

### HTTPS Enforcement

```python
enforce_ssl=True
```

CDK adds a bucket policy denying requests that do not use secure transport.

Applications should use HTTPS S3 endpoints for uploads, downloads, and object operations.

### Production Considerations

For private application storage:

- Keep public-access blocking enabled.
- Use IAM roles for application access.
- Avoid granting public read or write permissions.
- Prefer bucket-owner-enforced ownership.
- Enforce HTTPS.
- Review bucket policies independently of application code.
- Use CloudFront Origin Access Control when private S3 content must be delivered publicly through a controlled CDN.

Detailed policy evaluation and access-control design should be maintained in the dedicated S3 security documentation.

## Server-Side Encryption

S3 supports multiple server-side encryption mechanisms.

CDK exposes encryption configuration through `s3.BucketEncryption`.

### Encryption Options

| CDK value | Encryption type | Typical use |
|---|---|---|
| `UNENCRYPTED` | No default encryption configured by the bucket | Avoid for new production application buckets. |
| `S3_MANAGED` | SSE-S3 | General-purpose encrypted object storage. |
| `KMS_MANAGED` | SSE-KMS with an AWS managed KMS key | Workloads requiring KMS-based encryption controls without managing a customer key. |
| `KMS` | SSE-KMS with a specified customer-managed key | Workloads requiring customer-managed key policies and lifecycle control. |

S3 automatically encrypts new object uploads by default using SSE-S3 unless another encryption configuration is selected.

Explicit CDK configuration is still useful because it makes infrastructure requirements visible and testable.

### SSE-S3

Use S3-managed encryption:

```python
bucket = s3.Bucket(
    self,
    "S3EncryptedBucket",
    encryption=s3.BucketEncryption.S3_MANAGED,
)
```

SSE-S3 is suitable for many application storage workloads.

Advantages:

- AWS manages the encryption keys.
- Minimal application configuration.
- No customer-managed KMS key administration.
- Suitable for general encrypted object storage.

Limitations:

- Does not provide the same customer-managed key policy controls as SSE-KMS.
- Does not support the same KMS-based audit and key-management workflows.

### SSE-KMS With an AWS Managed Key

```python
bucket = s3.Bucket(
    self,
    "KmsManagedBucket",
    encryption=s3.BucketEncryption.KMS_MANAGED,
)
```

This uses an AWS managed KMS key for S3 encryption.

It provides KMS-based encryption without requiring the application team to create and maintain a customer-managed key.

### SSE-KMS With a Customer-Managed Key

Create a KMS key:

```python
from aws_cdk import aws_kms as kms

key = kms.Key(
    self,
    "ApplicationStorageKey",
    enable_key_rotation=True,
)
```

Use the key in the bucket:

```python
bucket = s3.Bucket(
    self,
    "CustomerManagedEncryptedBucket",
    encryption=s3.BucketEncryption.KMS,
    encryption_key=key,
    block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
    enforce_ssl=True,
)
```

This provides control over the key policy, rotation configuration, and key lifecycle.

### Encryption Permissions

SSE-KMS introduces an additional authorization boundary.

An application may have permission to access an S3 object but still fail because it lacks the required KMS permissions.

Typical permissions depend on the operation:

| Operation | Relevant permissions |
|---|---|
| Upload an SSE-KMS object | `s3:PutObject`, and applicable KMS permissions such as `kms:GenerateDataKey`. |
| Download an SSE-KMS object | `s3:GetObject` and `kms:Decrypt`. |
| Multipart upload using SSE-KMS | Required S3 multipart permissions and applicable KMS permissions. |

The exact KMS permissions depend on the encryption mode, operation, and key policy.

Do not assume that granting `s3:GetObject` automatically grants access to encrypted object contents.

## Versioning

Versioning preserves multiple object versions under the same object key.

Enable it using:

```python
bucket = s3.Bucket(
    self,
    "VersionedBucket",
    versioned=True,
)
```

### Why Versioning Matters

Consider an application storing a document:

```text
documents/invoice-1001.pdf
```

If the object is uploaded again using the same key, S3 creates a new version when versioning is enabled.

This allows previous versions to remain available.

Versioning is useful for:

- Recovering from accidental overwrites.
- Recovering from ordinary object deletion.
- Maintaining historical object versions.
- Supporting replication requirements.
- Protecting data against some application-level mistakes.

### Production Considerations

Versioning increases storage consumption because previous versions remain stored.

A production design should define:

- Current-version retention.
- Noncurrent-version expiration.
- Recovery requirements.
- Delete-marker handling.
- Replication behavior.
- Lifecycle cost implications.

Versioning is not a complete backup strategy. It does not independently protect against every account-level, administrative, or regional failure.

## Resource Removal Policies

CDK removal policies determine what happens to a resource when its CloudFormation stack is deleted or the resource is removed from the stack.

For S3 buckets, this decision is particularly important because buckets can contain application data.

### RemovalPolicy.RETAIN

```python
from aws_cdk import RemovalPolicy

bucket = s3.Bucket(
    self,
    "ProductionBucket",
    removal_policy=RemovalPolicy.RETAIN,
)
```

The bucket is retained when the stack is deleted.

Use this for:

- Production document storage.
- Customer uploads.
- Application backups.
- Long-lived datasets.
- Buckets containing data that must survive infrastructure deletion.

Retained resources can become unmanaged after stack deletion, so maintain an ownership and cleanup process.

### RemovalPolicy.DESTROY

```python
bucket = s3.Bucket(
    self,
    "DevelopmentBucket",
    removal_policy=RemovalPolicy.DESTROY,
)
```

The bucket is configured for deletion when the owning stack is removed, subject to CloudFormation and S3 deletion requirements.

A non-empty bucket can prevent deletion.

For versioned buckets, historical versions and delete markers also matter.

### Automatic Object Deletion

For disposable development resources:

```python
bucket = s3.Bucket(
    self,
    "DisposableDevelopmentBucket",
    removal_policy=RemovalPolicy.DESTROY,
    auto_delete_objects=True,
)
```

This configures additional deletion behavior to empty the bucket before removal.

It is destructive and should not be used casually.

Do not enable automatic object deletion for production data buckets simply to make `cdk destroy` succeed.

### Removal Policy Comparison

| Policy | Behavior | Recommended use |
|---|---|---|
| `RETAIN` | Keeps the physical resource after stack deletion. | Production and persistent storage. |
| `DESTROY` | Attempts to delete the resource. | Disposable environments. |
| `SNAPSHOT` | Creates a snapshot before deletion where supported. | Not a general S3 backup mechanism. |

A removal policy is an infrastructure lifecycle control, not an object retention policy.

S3 lifecycle rules and application-level retention must be designed separately.

## Lifecycle Rules

Lifecycle rules manage object transitions and expiration based on configured filters and time periods.

CDK supports lifecycle configuration directly through the bucket construct.

### Transition to Infrequent Access

```python
from aws_cdk import Duration
from aws_cdk import aws_s3 as s3

bucket = s3.Bucket(
    self,
    "LifecycleBucket",
    lifecycle_rules=[
        s3.LifecycleRule(
            id="TransitionOldDocuments",
            prefix="documents/",
            transitions=[
                s3.Transition(
                    storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                    transition_after=Duration.days(30),
                ),
            ],
        ),
    ],
)
```

This transitions eligible objects under `documents/` to S3 Standard-IA after the configured period.

Lifecycle behavior is asynchronous. The configured age is an eligibility condition, not a guaranteed exact transition timestamp.

### Multiple Storage-Class Transitions

```python
bucket = s3.Bucket(
    self,
    "ArchiveBucket",
    lifecycle_rules=[
        s3.LifecycleRule(
            id="ArchiveApplicationData",
            prefix="archive/",
            transitions=[
                s3.Transition(
                    storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                    transition_after=Duration.days(30),
                ),
                s3.Transition(
                    storage_class=s3.StorageClass.GLACIER,
                    transition_after=Duration.days(90),
                ),
            ],
        ),
    ],
)
```

This configuration defines transitions for matching objects.

Before deploying lifecycle rules, validate:

- Storage-class eligibility.
- Minimum storage-duration requirements.
- Retrieval costs.
- Transition request charges.
- Object size considerations.
- Access patterns.
- Retention requirements.

### Noncurrent Version Expiration

For versioned buckets, lifecycle configuration can expire noncurrent versions.

```python
bucket = s3.Bucket(
    self,
    "VersionedArchiveBucket",
    versioned=True,
    lifecycle_rules=[
        s3.LifecycleRule(
            id="ExpireOldVersions",
            noncurrent_version_expiration=Duration.days(180),
        ),
    ],
)
```

This removes eligible noncurrent versions after the configured period.

It is destructive and must be aligned with recovery and compliance requirements.

### Incomplete Multipart Upload Cleanup

Multipart uploads that are not completed or aborted can leave billable parts stored in S3.

Configure cleanup:

```python
bucket = s3.Bucket(
    self,
    "MultipartCleanupBucket",
    lifecycle_rules=[
        s3.LifecycleRule(
            id="AbortIncompleteUploads",
            abort_incomplete_multipart_upload_after=Duration.days(7),
        ),
    ],
)
```

This is useful for systems that support large file uploads through SDKs or presigned multipart workflows.

It reduces storage waste from abandoned uploads.

## Bucket Tags

Tags are key-value metadata attached to AWS resources.

They are useful for:

- Cost allocation.
- Environment identification.
- Application ownership.
- Resource inventory.
- Governance.
- Operational automation.

CDK tags can be applied to a bucket:

```python
from aws_cdk import Tags

bucket = s3.Bucket(
    self,
    "TaggedBucket",
)

Tags.of(bucket).add(
    "Application",
    "document-service",
)

Tags.of(bucket).add(
    "Environment",
    "production",
)

Tags.of(bucket).add(
    "ManagedBy",
    "aws-cdk",
)
```

For consistent tagging, define organizational conventions and apply them at the application or stack level where appropriate.

Do not confuse AWS resource tags with S3 object tags. They are different mechanisms with different purposes.

## Reusable Bucket Configuration

Production systems commonly need multiple buckets with consistent security settings.

Instead of repeating the same properties, define a reusable construct.

### Secure Bucket Construct

`secure_bucket.py`

```python
from aws_cdk import RemovalPolicy
from aws_cdk import aws_s3 as s3
from constructs import Construct


class SecureBucket(Construct):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        bucket_name: str | None = None,
        versioned: bool = True,
        retain_on_delete: bool = True,
    ) -> None:
        super().__init__(scope, construct_id)

        removal_policy = (
            RemovalPolicy.RETAIN
            if retain_on_delete
            else RemovalPolicy.DESTROY
        )

        self.bucket = s3.Bucket(
            self,
            "Bucket",
            bucket_name=bucket_name,
            versioned=versioned,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            enforce_ssl=True,
            removal_policy=removal_policy,
        )
```

### Use the Construct in a Stack

```python
from aws_cdk import Stack
from constructs import Construct

from s3_cdk.constructs.secure_bucket import SecureBucket


class ApplicationStorageStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        super().__init__(
            scope,
            construct_id,
            **kwargs,
        )

        self.upload_storage = SecureBucket(
            self,
            "UploadStorage",
            versioned=True,
            retain_on_delete=True,
        )

        self.processed_storage = SecureBucket(
            self,
            "ProcessedStorage",
            versioned=True,
            retain_on_delete=True,
        )
```

The reusable construct standardizes common configuration while allowing the stack to define application-specific resource composition.

For larger systems, extend the construct with carefully selected options rather than exposing every underlying `Bucket` property without a clear requirement.

## Bucket Access Grants

CDK provides grant methods that attach common IAM permissions to a principal.

For example, a Lambda function may need to read objects from a bucket.

```python
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_s3 as s3

bucket = s3.Bucket(
    self,
    "InputBucket",
)

processor = lambda_.Function(
    self,
    "Processor",
    runtime=lambda_.Runtime.PYTHON_3_12,
    handler="handler.main",
    code=lambda_.Code.from_asset("lambda"),
)

bucket.grant_read(processor)
```

Common grant methods include:

| Method | Purpose |
|---|---|
| `grant_read()` | Grants common object read permissions. |
| `grant_write()` | Grants common object write permissions. |
| `grant_read_write()` | Grants common read and write permissions. |
| `grant_delete()` | Grants object deletion permissions. |
| `grant_put()` | Grants object upload permissions. |
| `grant_list()` | Grants bucket listing permissions. |

These methods are convenient, but the generated policy should still be reviewed.

### Prefix-Restricted Access

For a processor that only needs objects under `incoming/`, use scoped grants:

```python
bucket.grant_read(
    processor,
    "incoming/*",
)
```

This is preferable to unrestricted access when the workload only needs a subset of the bucket.

For more complex requirements, define explicit IAM statements and distinguish bucket-level permissions from object-level permissions.

## S3 Event Notifications

A bucket can publish object events to supported destinations.

CDK supports Lambda, SQS, and SNS notification destinations through the S3 notification module.

Example:

```python
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_notifications as notifications

bucket = s3.Bucket(
    self,
    "IncomingBucket",
)

processor = lambda_.Function(
    self,
    "FileProcessor",
    runtime=lambda_.Runtime.PYTHON_3_12,
    handler="handler.main",
    code=lambda_.Code.from_asset("lambda"),
)

bucket.add_event_notification(
    s3.EventType.OBJECT_CREATED,
    notifications.LambdaDestination(processor),
    s3.NotificationKeyFilter(
        prefix="incoming/",
    ),
)
```

CDK configures the notification destination and the required Lambda invocation permission.

### Event Processing Considerations

S3 event notifications are delivered at least once.

Consumers should tolerate duplicate notifications and should not assume event ordering.

Production processors should:

- Validate event structure.
- Use object keys and version identifiers where appropriate.
- Implement idempotent processing.
- Handle retries safely.
- Separate input and output prefixes.
- Monitor failures.
- Avoid recursive event triggers.

For workloads that need buffering and controlled consumer concurrency, SQS can be used between S3 and the processing service.

## Bucket Outputs

CloudFormation outputs expose useful resource information after deployment.

CDK can define outputs using `CfnOutput`.

```python
from aws_cdk import CfnOutput

CfnOutput(
    self,
    "BucketName",
    value=bucket.bucket_name,
    description="Application S3 bucket name",
)

CfnOutput(
    self,
    "BucketArn",
    value=bucket.bucket_arn,
    description="Application S3 bucket ARN",
)
```

Outputs are useful for:

- Deployment verification.
- Integration with other stacks.
- Operational scripts.
- Passing infrastructure identifiers to deployment systems.

Avoid exposing credentials, secrets, or sensitive object metadata through CloudFormation outputs.

## Complete Production-Oriented Bucket Example

The following example combines private access, encryption, versioning, lifecycle management, retention, and tagging.

```python
from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    Tags,
)
from aws_cdk import aws_s3 as s3
from constructs import Construct


class ProductionStorageStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        environment_name: str,
        **kwargs,
    ) -> None:
        super().__init__(
            scope,
            construct_id,
            **kwargs,
        )

        bucket = s3.Bucket(
            self,
            "ApplicationDocuments",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="TransitionArchivedDocuments",
                    prefix="archive/",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30),
                        ),
                    ],
                ),
                s3.LifecycleRule(
                    id="AbortIncompleteUploads",
                    abort_incomplete_multipart_upload_after=Duration.days(7),
                ),
            ],
        )

        Tags.of(bucket).add(
            "Application",
            "document-service",
        )

        Tags.of(bucket).add(
            "Environment",
            environment_name,
        )

        Tags.of(bucket).add(
            "ManagedBy",
            "aws-cdk",
        )

        CfnOutput(
            self,
            "BucketName",
            value=bucket.bucket_name,
        )

        CfnOutput(
            self,
            "BucketArn",
            value=bucket.bucket_arn,
        )
```

### Configuration Rationale

| Configuration | Reason |
|---|---|
| Versioning | Supports recovery from accidental overwrites and ordinary deletions. |
| SSE-S3 | Provides server-side encryption with minimal key-management overhead. |
| Block Public Access | Prevents unintended public exposure. |
| Bucket-owner-enforced ownership | Avoids ACL-based ownership complexity. |
| HTTPS enforcement | Denies insecure transport. |
| Retention policy | Protects persistent data from stack deletion. |
| Lifecycle transition | Reduces storage cost for older archive objects. |
| Multipart cleanup | Removes eligible incomplete multipart uploads. |
| Resource tags | Supports ownership and cost allocation. |

This is a baseline configuration, not a universal production policy. Adapt encryption, lifecycle, retention, and access controls to the application's data classification and recovery requirements.

## Synthesis and Deployment

After defining the bucket, synthesize the application.

```bash
cdk synth
```

Review the generated CloudFormation template in `cdk.out/`.

Deploy the stack:

```bash
cdk deploy ProductionStorageStack
```

Review infrastructure changes before deployment:

```bash
cdk diff ProductionStorageStack
```

For production deployments, use an approved AWS identity and require review of destructive changes or resource replacements.

### Verify the Deployed Bucket

Inspect versioning:

```bash
aws s3api get-bucket-versioning \
  --bucket BUCKET_NAME
```

Inspect encryption:

```bash
aws s3api get-bucket-encryption \
  --bucket BUCKET_NAME
```

Inspect public-access configuration:

```bash
aws s3api get-public-access-block \
  --bucket BUCKET_NAME
```

Inspect ownership controls:

```bash
aws s3api get-bucket-ownership-controls \
  --bucket BUCKET_NAME
```

Inspect lifecycle configuration:

```bash
aws s3api get-bucket-lifecycle-configuration \
  --bucket BUCKET_NAME
```

These commands verify the actual deployed configuration rather than relying only on the CDK source.

## Testing Bucket Configuration

CDK assertions allow infrastructure definitions to be tested without deploying resources.

Example:

```python
import aws_cdk as cdk
from aws_cdk import assertions

from s3_cdk.stacks.storage_stack import ProductionStorageStack


def test_production_bucket_configuration():
    app = cdk.App()

    stack = ProductionStorageStack(
        app,
        "TestStorageStack",
        environment_name="production",
        env=cdk.Environment(
            account="111111111111",
            region="ap-south-1",
        ),
    )

    template = assertions.Template.from_stack(stack)

    template.resource_count_is(
        "AWS::S3::Bucket",
        1,
    )

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
                    },
                ],
            },
        },
    )
```

Run:

```bash
pytest tests/unit -v
```

Additional assertions should verify:

- Encryption algorithm.
- Lifecycle configuration.
- HTTPS bucket policy.
- Removal and update policies.
- IAM permissions.
- Event notification configuration.
- Expected CloudFormation outputs.

Unit tests validate synthesized infrastructure. They do not prove that deployment succeeds or that the application can access the bucket.

Use integration tests in a controlled AWS account to validate actual S3 operations and authorization behavior.

## Common Mistakes and Production Pitfalls

| Mistake | Why it matters | Recommended approach |
|---|---|---|
| Assuming construct IDs are physical bucket names | CDK logical identifiers and physical resource names are different. | Use `bucket_name` when a predictable physical name is required. |
| Hardcoding bucket names across environments | Creates naming collisions and deployment coupling. | Use generated names or validated environment-specific naming conventions. |
| Leaving public-access behavior implicit | Can produce security assumptions that are not visible in the infrastructure code. | Explicitly configure `BLOCK_ALL` for private application buckets. |
| Treating encryption and authorization as the same concern | S3 access can succeed at the IAM layer but fail at the KMS layer. | Review S3 and KMS permissions independently. |
| Enabling versioning without lifecycle planning | Historical versions can accumulate and increase storage costs. | Define noncurrent-version retention and recovery requirements. |
| Using `DESTROY` on persistent storage | Stack deletion can cause data loss. | Use `RETAIN` for production data and controlled deletion workflows. |
| Enabling `auto_delete_objects` on production buckets | Can remove object data during stack destruction. | Restrict automatic deletion to disposable resources. |
| Assuming lifecycle actions happen at an exact time | Lifecycle processing is asynchronous. | Treat configured dates as eligibility thresholds. |
| Granting broad bucket permissions | Increases the impact of compromised application roles. | Use prefix-restricted grants and explicit IAM policies. |
| Triggering processing from the output prefix | Can cause recursive event processing. | Separate input and output prefixes or buckets. |
| Changing a physical bucket name in place | Can require resource replacement and data migration. | Plan bucket migrations explicitly. |
| Relying only on CDK unit tests | Tests do not validate real AWS authorization or runtime behavior. | Add deployment verification and integration tests. |

## Production Readiness Checklist

### Bucket Configuration

- [ ] Bucket naming follows a consistent convention.
- [ ] Physical names are globally unique when explicitly configured.
- [ ] Versioning matches recovery requirements.
- [ ] Default encryption is explicitly configured.
- [ ] Public access is blocked for private application buckets.
- [ ] Object ownership is configured appropriately.
- [ ] HTTPS-only access is enforced.
- [ ] Lifecycle rules match data access and retention requirements.
- [ ] Incomplete multipart uploads are cleaned up.
- [ ] Resource tags identify application ownership and environment.

### Security and Access

- [ ] Application access uses IAM roles or temporary credentials.
- [ ] IAM permissions are scoped to required actions and resources.
- [ ] KMS permissions are reviewed separately when SSE-KMS is used.
- [ ] Bucket policies do not unintentionally expose objects.
- [ ] Public access is provided through a controlled delivery architecture when required.
- [ ] Presigned URL authorization is enforced by the backend.

### Reliability and Operations

- [ ] Production buckets use appropriate retention policies.
- [ ] Version and lifecycle costs have been evaluated.
- [ ] Backup and recovery requirements are documented.
- [ ] Event consumers handle duplicate notifications.
- [ ] Bucket configuration is covered by CDK assertions.
- [ ] Deployment changes are reviewed using `cdk diff`.
- [ ] Actual deployed configuration is verified.
- [ ] Destructive deletion procedures require explicit approval.

## Key Takeaways

- Use the Python CDK `s3.Bucket` L2 construct for standard S3 bucket provisioning and reserve `s3.CfnBucket` for lower-level CloudFormation control.
- Configure private access, encryption, ownership controls, HTTPS enforcement, and versioning explicitly according to workload requirements.
- Treat versioning, lifecycle expiration, and CloudFormation removal policies as separate controls with different data-protection implications.
- Use reusable bucket constructs to standardize security and operational configuration across application stacks.
- Validate synthesized templates with CDK assertions and verify deployed bucket properties through AWS APIs and integration tests.