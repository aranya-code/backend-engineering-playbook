# README

## Overview

This example provisions an Amazon S3 bucket with configurable lifecycle management using Terraform.

It demonstrates how to automate object retention, storage-class transitions, noncurrent version expiration, and incomplete multipart upload cleanup through a single S3 lifecycle configuration.

The configuration includes:

- S3 bucket creation.
- Bucket Owner Enforced Object Ownership.
- S3 Block Public Access.
- Bucket versioning.
- Server-side encryption using SSE-S3 by default, with optional SSE-KMS.
- Optional expiration of current object versions.
- Configurable transitions to S3 Standard-IA and S3 Glacier Flexible Retrieval.
- Expiration of noncurrent object versions.
- Automatic abortion of incomplete multipart uploads.
- Configurable lifecycle prefix filtering.
- Terraform outputs for bucket and lifecycle configuration details.

The example uses native AWS provider resources so that lifecycle behavior and resource dependencies remain explicit.

## Project Structure

```text
lifecycle-managed-bucket/
├── main.tf
└── README.md
```

All Terraform configuration is contained in `main.tf`, including:

| Configuration | Responsibility |
|---|---|
| `terraform` | Terraform and AWS provider version constraints. |
| `provider` | AWS Region and default resource tags. |
| `variable` | Bucket, encryption, lifecycle retention, and transition settings. |
| `locals` | Lifecycle transition definitions and ordering validation. |
| `resource` | Bucket, security controls, versioning, encryption, and lifecycle configuration. |
| `output` | Bucket identifiers and lifecycle configuration details. |

## Architecture

```mermaid
flowchart TD
    A["Application uploads objects"] --> B["S3 Bucket"]
    B --> C["Current Object Versions"]
    B --> D["Noncurrent Object Versions"]
    B --> E["Incomplete Multipart Uploads"]

    C --> F{"Lifecycle policy"}
    F --> G["Optional current-version expiration"]
    F --> H["Optional STANDARD_IA transition"]
    H --> I["Optional GLACIER transition"]

    D --> J["Noncurrent version expiration"]

    E --> K["Abort incomplete multipart uploads"]

    G --> L["Reduced retained storage"]
    I --> L
    J --> L
    K --> M["Incomplete upload parts removed"]
```

### Resource Responsibilities

| Resource | Responsibility |
|---|---|
| `aws_s3_bucket.lifecycle_managed` | Creates the S3 bucket. |
| `aws_s3_bucket_ownership_controls.lifecycle_managed` | Enforces bucket-owner ownership and disables ACL-based ownership management. |
| `aws_s3_bucket_public_access_block.lifecycle_managed` | Blocks public access through bucket-level public-access controls. |
| `aws_s3_bucket_versioning.lifecycle_managed` | Enables versioning for noncurrent-version lifecycle management. |
| `aws_s3_bucket_server_side_encryption_configuration.lifecycle_managed` | Configures default server-side encryption. |
| `aws_s3_bucket_lifecycle_configuration.lifecycle_managed` | Manages expiration, storage transitions, and incomplete multipart upload cleanup. |

## Prerequisites

Install the following tools:

| Tool | Purpose |
|---|---|
| Terraform | Infrastructure provisioning. |
| AWS CLI | AWS identity verification and S3 inspection. |
| AWS account | Hosts the S3 bucket. |
| IAM permissions | Allows Terraform to create and configure the required resources. |

Verify the installations:

```bash
terraform version
aws --version
```

### Configure AWS Credentials

Use an IAM role, IAM Identity Center profile, or another supported temporary credential mechanism.

For an AWS CLI profile:

```bash
aws configure --profile s3-lifecycle
```

Set the profile before running Terraform.

**Linux/macOS**

```bash
export AWS_PROFILE=s3-lifecycle
```

**Windows PowerShell**

```powershell
$env:AWS_PROFILE = "s3-lifecycle"
```

Verify the active identity:

```bash
aws sts get-caller-identity
```

Ensure the identity belongs to the intended AWS account. Do not store long-lived AWS credentials in Terraform source files or version control.

## Configuration

### AWS Region

The default Region is:

```hcl
aws_region = "ap-south-1"
```

Change this value when deploying to another Region.

### Bucket Name

The `bucket_name` variable must contain a globally unique S3 general-purpose bucket name.

Example:

```hcl
bucket_name = "your-org-lifecycle-managed-documents"
```

Replace the placeholder before deployment.

### Encryption

The default configuration uses SSE-S3:

```hcl
kms_key_arn = null
```

To use SSE-KMS, provide a customer-managed KMS key ARN:

```hcl
kms_key_arn = "arn:aws:kms:ap-south-1:123456789012:key/example-key-id"
```

The KMS key must be in the same Region as the bucket. Its key policy and applicable IAM permissions must authorize the required operations.

S3 Bucket Keys are enabled only when SSE-KMS is configured and `bucket_key_enabled` is true.

### Lifecycle Configuration

The example exposes the following lifecycle variables:

| Variable | Default | Purpose |
|---|---:|---|
| `current_version_expiration_days` | `null` | Disables current object version expiration by default. |
| `noncurrent_version_expiration_days` | `90` | Expires eligible noncurrent versions after 90 days. |
| `abort_incomplete_multipart_upload_days` | `7` | Aborts incomplete multipart uploads after 7 days. |
| `transition_to_standard_ia_days` | `null` | Disables transition to Standard-IA by default. |
| `transition_to_glacier_days` | `null` | Disables transition to Glacier Flexible Retrieval by default. |
| `lifecycle_filter_prefix` | `""` | Applies lifecycle rules to the entire bucket by default. |

#### Current Object Expiration

To expire current objects after 365 days:

```hcl
current_version_expiration_days = 365
```

This is destructive: eligible current objects are expired. In a versioned bucket, expiration normally creates a delete marker rather than permanently deleting historical versions.

Keep this setting disabled unless the retention policy explicitly requires current-object expiration.

#### Noncurrent Version Expiration

The default policy is:

```hcl
noncurrent_version_expiration_days = 90
```

When an object is overwritten or deleted, previous versions can become noncurrent. This rule expires eligible noncurrent versions after the configured number of days.

This is useful for controlling the storage cost of historical versions while preserving a defined recovery window.

#### Storage-Class Transitions

To transition current objects to Standard-IA after 30 days and Glacier Flexible Retrieval after 120 days:

```hcl
transition_to_standard_ia_days = 30
transition_to_glacier_days     = 120
```

The example requires Standard-IA to occur before Glacier when both transitions are enabled.

Standard-IA is appropriate for long-lived data accessed infrequently but requiring millisecond retrieval. Glacier Flexible Retrieval is intended for archival data with retrieval delays and associated retrieval costs.

Consider minimum storage-duration charges, minimum billable object sizes, retrieval charges, and access patterns before selecting a transition policy.

The example does not configure transitions for noncurrent versions. Those require separate noncurrent-version transition rules and should be added when the workload needs them.

#### Prefix Filtering

By default, the lifecycle rules apply to the entire bucket:

```hcl
lifecycle_filter_prefix = ""
```

To scope them to a specific prefix:

```hcl
lifecycle_filter_prefix = "archive/"
```

Only objects whose keys match the configured prefix are affected by these rules.

Choose prefixes carefully. A broad or incorrect filter can apply retention and expiration behavior to data that should remain available.

### Example Configuration

The following values illustrate a policy that transitions current objects and expires historical versions:

```hcl
aws_region                             = "ap-south-1"
bucket_name                            = "your-org-lifecycle-managed-documents"
force_destroy                          = false
kms_key_arn                            = null
bucket_key_enabled                     = true
current_version_expiration_days        = null
noncurrent_version_expiration_days     = 90
abort_incomplete_multipart_upload_days = 7
transition_to_standard_ia_days         = 30
transition_to_glacier_days             = 120
lifecycle_filter_prefix                = "archive/"
```

These are example values, not universal retention recommendations.

## Deployment

Run the following commands from the `examples/lifecycle-managed-bucket` directory.

### Initialize Terraform

```bash
terraform init
```

### Format the Configuration

```bash
terraform fmt -recursive
```

### Validate the Configuration

```bash
terraform validate
```

This checks Terraform syntax and internal configuration consistency. It does not prove that AWS permissions or resource creation will succeed.

### Review the Execution Plan

```bash
terraform plan
```

Review the plan carefully.

Confirm:

- The intended AWS account and Region.
- The bucket name.
- Versioning is enabled.
- Public access restrictions are enabled.
- Object Ownership is configured as expected.
- The encryption algorithm and KMS key are correct.
- Current-version expiration is enabled only when intended.
- Noncurrent-version expiration matches the recovery policy.
- Storage transitions occur in the intended order.
- Lifecycle prefix filtering is correct.
- Incomplete multipart upload cleanup is configured.
- No unexpected replacement or deletion operations are planned.

### Apply the Configuration

```bash
terraform apply
```

Review and approve the execution plan.

Terraform creates the bucket and its associated configuration resources.

## Verify the Deployment

### Inspect Terraform Outputs

```bash
terraform output
```

Retrieve individual outputs:

```bash
terraform output bucket_id
terraform output bucket_arn
terraform output bucket_region
terraform output bucket_versioning_status
terraform output bucket_encryption_algorithm
terraform output lifecycle_configuration_id
terraform output lifecycle_filter_prefix
terraform output noncurrent_version_expiration_days
terraform output abort_incomplete_multipart_upload_days
```

### Verify Versioning

```bash
aws s3api get-bucket-versioning \
  --bucket your-org-lifecycle-managed-documents
```

Expected configuration:

```json
{
  "Status": "Enabled"
}
```

### Verify Encryption

```bash
aws s3api get-bucket-encryption \
  --bucket your-org-lifecycle-managed-documents
```

Confirm that the returned algorithm matches the configured SSE-S3 or SSE-KMS strategy.

### Verify Public Access Block

```bash
aws s3api get-public-access-block \
  --bucket your-org-lifecycle-managed-documents
```

Confirm that all four public-access restrictions are enabled.

### Verify Object Ownership

```bash
aws s3api get-bucket-ownership-controls \
  --bucket your-org-lifecycle-managed-documents
```

Confirm that the ownership rule uses `BucketOwnerEnforced`.

### Verify Lifecycle Configuration

```bash
aws s3api get-bucket-lifecycle-configuration \
  --bucket your-org-lifecycle-managed-documents
```

Inspect the returned rules and confirm:

- Current-version expiration is present only when configured.
- Noncurrent-version expiration matches the configured retention period.
- Storage transitions match the configured storage classes and days.
- Incomplete multipart upload cleanup matches the configured period.
- Both lifecycle rules are enabled.
- Prefix filters match the intended object-key scope.

## Test Lifecycle Behavior

### Upload Sample Objects

Create a sample object:

```bash
echo "Lifecycle management test" > sample.txt
```

Upload it to the bucket:

```bash
aws s3 cp sample.txt \
  s3://your-org-lifecycle-managed-documents/archive/sample.txt
```

Inspect the object:

```bash
aws s3api head-object \
  --bucket your-org-lifecycle-managed-documents \
  --key archive/sample.txt
```

### Verify Object Storage Class

```bash
aws s3api head-object \
  --bucket your-org-lifecycle-managed-documents \
  --key archive/sample.txt \
  --query StorageClass
```

A newly uploaded object normally uses the bucket's default storage class unless the upload explicitly specifies another class.

After a configured lifecycle transition becomes eligible and S3 processes it, inspect the object again to verify its storage class.

Lifecycle processing is asynchronous. Do not expect an immediate transition at the exact configured age.

### Test Noncurrent Version Management

Upload an initial version:

```bash
echo "Version one" > sample.txt

aws s3 cp sample.txt \
  s3://your-org-lifecycle-managed-documents/archive/sample.txt
```

Overwrite it:

```bash
echo "Version two" > sample.txt

aws s3 cp sample.txt \
  s3://your-org-lifecycle-managed-documents/archive/sample.txt
```

List the versions:

```bash
aws s3api list-object-versions \
  --bucket your-org-lifecycle-managed-documents \
  --prefix archive/sample.txt
```

The previous version should appear as noncurrent.

The configured lifecycle policy makes noncurrent versions eligible for expiration after 90 days. It does not immediately remove them.

### Verify Incomplete Multipart Uploads

Inspect active multipart uploads:

```bash
aws s3api list-multipart-uploads \
  --bucket your-org-lifecycle-managed-documents
```

The lifecycle rule aborts incomplete multipart uploads after the configured number of days.

Do not leave test multipart uploads running unnecessarily. For controlled cleanup, use the upload ID and explicitly abort the test upload:

```bash
aws s3api abort-multipart-upload \
  --bucket your-org-lifecycle-managed-documents \
  --key archive/large-file.bin \
  --upload-id YOUR_UPLOAD_ID
```

## Production Considerations

### Retention Is a Data Governance Decision

Lifecycle expiration is not merely a storage optimization setting.

Before enabling expiration, establish:

- Business and regulatory retention requirements.
- Recovery point and recovery time objectives.
- Required historical version retention.
- Legal hold and Object Lock requirements.
- Data ownership and deletion responsibilities.
- Whether downstream systems depend on historical objects.

Do not apply a short expiration period to shared or business-critical data without approval from the data owner.

### Versioning and Lifecycle Must Be Designed Together

Versioning preserves historical versions, while lifecycle rules control their retention.

A bucket with versioning enabled but no noncurrent-version lifecycle policy can accumulate historical data indefinitely.

Conversely, an aggressive noncurrent expiration policy can eliminate recovery points earlier than expected.

Choose the retention period based on actual recovery requirements rather than selecting an arbitrary number of days.

### Storage-Class Transition Economics

Storage-class transitions can reduce storage costs, but they can also introduce retrieval charges and minimum storage-duration charges.

Evaluate:

- Object size distribution.
- Access frequency.
- Retrieval latency requirements.
- Expected retention duration.
- Transition request charges.
- Retrieval and data transfer charges.
- Minimum billable object size.
- Minimum storage-duration charges.

Do not transition frequently accessed objects into archival classes simply because they are older.

### Lifecycle Processing Is Asynchronous

Lifecycle rules are evaluated and executed by S3 asynchronously.

Important operational implications:

- Objects do not transition at an exact scheduled instant.
- Expiration does not guarantee immediate physical removal at the configured age.
- Lifecycle configuration success does not mean every eligible object has already been processed.
- Object Lock retention and legal holds can prevent expiration.
- Monitoring should validate actual storage behavior rather than relying only on Terraform state.

### Encryption and KMS

When SSE-KMS is configured, the application and infrastructure roles need appropriate KMS permissions.

S3 authorization and KMS authorization are separate permission layers. An S3 operation can fail even when the S3 policy appears correct if the KMS key policy or IAM permissions do not authorize the operation.

Keep KMS key policies aligned with the workload's access model.

### IAM Permissions

Use workload-specific IAM roles and least-privilege policies.

Separate application permissions from infrastructure deployment permissions.

An application that only uploads and downloads objects should not receive lifecycle-management or permanent version-deletion permissions.

Terraform deployment identities require permissions to manage the bucket and its configuration resources. Restrict these permissions to the intended environment and resources where practical.

### Monitoring and Cost

Monitor:

- Total bucket storage.
- Current and noncurrent version storage.
- Storage-class distribution.
- Incomplete multipart uploads.
- Lifecycle configuration changes.
- S3 request and retrieval costs.
- Object expiration and retention behavior.

S3 Storage Lens and S3 Inventory can help analyze object storage and version distribution at scale.

Use cost allocation tags and AWS cost reporting to evaluate whether lifecycle policies are delivering the expected savings.

### Terraform Resource Ownership

This example manages the complete lifecycle configuration through one `aws_s3_bucket_lifecycle_configuration` resource.

Do not introduce another Terraform resource or module that manages the same bucket's lifecycle configuration. Multiple owners can overwrite one another's configuration and create drift.

If a dedicated lifecycle module is introduced later, migrate lifecycle ownership deliberately and ensure only one resource manages the complete configuration.

### Terraform State

This example uses local Terraform state by default.

For shared or production deployments, configure a secured remote backend with encryption, restricted access, versioning, and state locking.

Do not share a local state file across engineers or CI/CD runners.

## Common Mistakes

| Mistake | Why it is problematic | Recommended approach |
|---|---|---|
| Expiring current objects unintentionally | Current objects can become inaccessible through ordinary reads. | Keep current-version expiration disabled unless explicitly required. |
| Setting a short noncurrent retention period | Historical recovery points disappear earlier than expected. | Align retention with business recovery requirements. |
| Applying lifecycle rules to the wrong prefix | Unrelated objects may be transitioned or expired. | Review prefix filters and test with representative keys. |
| Assuming transitions happen immediately | Lifecycle processing is asynchronous. | Verify actual object state after sufficient processing time. |
| Ignoring minimum storage duration | Early deletion can still incur storage charges. | Evaluate storage-class billing constraints before transitioning. |
| Assuming versioning is a backup | Permanent version deletion and account compromise remain possible. | Use independent backup and recovery controls where required. |
| Managing lifecycle configuration from multiple resources | One configuration can overwrite another. | Maintain a single Terraform owner for the bucket lifecycle configuration. |
| Enabling `force_destroy` casually | Terraform may permanently remove bucket contents during destruction. | Keep it false for protected and production data. |

## Cleanup

Destroying the Terraform configuration can fail while the bucket contains objects, versions, delete markers, or incomplete multipart uploads.

First review the proposed destruction:

```bash
terraform plan -destroy
```

For a disposable test bucket, inspect its contents and confirm that all data can be permanently discarded.

List object versions and delete markers:

```bash
aws s3api list-object-versions \
  --bucket your-org-lifecycle-managed-documents
```

List incomplete multipart uploads:

```bash
aws s3api list-multipart-uploads \
  --bucket your-org-lifecycle-managed-documents
```

Remove retained data only through an approved deletion workflow. Lifecycle expiration is not an immediate cleanup mechanism and should not be relied upon to empty the bucket before Terraform destruction.

After the bucket is empty, run:

```bash
terraform destroy
```

Verify that the bucket no longer exists:

```bash
aws s3api head-bucket \
  --bucket your-org-lifecycle-managed-documents
```

A failed request is expected after successful deletion, although the exact error depends on caller permissions and AWS response behavior.

Do not manually delete Terraform-managed resources without a deliberate state-reconciliation plan.

## Key Takeaways

- S3 lifecycle configuration automates object expiration, storage-class transitions, noncurrent-version retention, and incomplete multipart upload cleanup.
- Current-version expiration and noncurrent-version expiration have different effects in a versioned bucket and must be configured deliberately.
- Storage-class transitions require workload-aware cost analysis, including retrieval charges and minimum storage-duration constraints.
- Lifecycle processing is asynchronous, so production verification must inspect actual object state rather than assume immediate execution.
- Maintain a single Terraform owner for each bucket's complete lifecycle configuration and protect retention policies through controlled infrastructure changes.