# README

## Overview

This example provisions a versioned Amazon S3 bucket using Terraform. It demonstrates how to preserve object history, recover from accidental overwrites and deletions, and manage noncurrent object versions through lifecycle configuration.

The configuration uses native AWS provider resources rather than the reusable `s3-bucket` module. This makes the individual S3 resources and their dependencies explicit.

The example configures:

- S3 bucket creation.
- Bucket Owner Enforced Object Ownership.
- S3 Block Public Access.
- Bucket versioning.
- Server-side encryption using SSE-S3 by default, with optional SSE-KMS.
- Lifecycle expiration of noncurrent object versions after 90 days.
- Automatic abortion of incomplete multipart uploads after 7 days.
- Terraform outputs for bucket and configuration details.

This is a standalone example intended to demonstrate versioning and lifecycle behavior. Production deployments should adapt retention periods, encryption, IAM permissions, monitoring, and state management to their workload requirements.

## Project Structure

```text
versioned-bucket/
├── main.tf
└── README.md
```

All Terraform configuration is contained in `main.tf`, including:

| Configuration | Responsibility |
|---|---|
| `terraform` | Terraform and AWS provider version constraints. |
| `provider` | AWS Region and default resource tags. |
| `variable` | Bucket name, encryption, deletion behavior, and tags. |
| `resource` | Bucket, ownership controls, public access block, versioning, encryption, and lifecycle configuration. |
| `output` | Bucket identifiers and configuration details. |

## Architecture

```mermaid
flowchart TD
    A["Terraform CLI"] --> B["AWS Provider"]
    B --> C["S3 Bucket"]
    C --> D["Object Ownership Controls"]
    C --> E["Block Public Access"]
    C --> F["Versioning"]
    C --> G["Server-side Encryption"]
    C --> H["Lifecycle Configuration"]
    F --> I["Current Object Version"]
    F --> J["Noncurrent Object Versions"]
    H --> K["Expire Noncurrent Versions after 90 Days"]
    H --> L["Abort Incomplete Multipart Uploads after 7 Days"]
```

### Resource Responsibilities

| Resource | Responsibility |
|---|---|
| `aws_s3_bucket.versioned` | Creates the S3 bucket. |
| `aws_s3_bucket_ownership_controls.versioned` | Enforces bucket-owner ownership and disables ACL-based ownership management. |
| `aws_s3_bucket_public_access_block.versioned` | Blocks public access through bucket-level public-access controls. |
| `aws_s3_bucket_versioning.versioned` | Enables versioning. |
| `aws_s3_bucket_server_side_encryption_configuration.versioned` | Configures default server-side encryption. |
| `aws_s3_bucket_lifecycle_configuration.versioned` | Expires noncurrent versions and aborts incomplete multipart uploads. |

## Prerequisites

Install the following tools:

| Tool | Purpose |
|---|---|
| Terraform | Infrastructure provisioning. |
| AWS CLI | Identity verification and S3 inspection. |
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
aws configure --profile s3-versioning
```

Set the profile before running Terraform.

**Linux/macOS**

```bash
export AWS_PROFILE=s3-versioning
```

**Windows PowerShell**

```powershell
$env:AWS_PROFILE = "s3-versioning"
```

Verify the active identity:

```bash
aws sts get-caller-identity
```

Ensure the identity belongs to the intended AWS account. Do not store long-lived AWS credentials in Terraform source files or version control.

## Configuration

### Bucket Name

The `bucket_name` variable must contain a globally unique S3 general-purpose bucket name.

Example:

```hcl
bucket_name = "your-org-versioned-documents-example"
```

Replace the placeholder before deployment.

Use names that identify the workload and environment without exposing sensitive information.

### AWS Region

The default Region is:

```hcl
aws_region = "ap-south-1"
```

Change this value when deploying to another Region.

### Versioning

Versioning is enabled directly through:

```hcl
resource "aws_s3_bucket_versioning" "versioned" {
  bucket = aws_s3_bucket.versioned.id

  versioning_configuration {
    status = "Enabled"
  }
}
```

When versioning is enabled, S3 preserves multiple versions of an object under the same key.

For example, uploading a new object to `documents/report.pdf` creates a new version rather than replacing the previous version permanently.

Versioning supports:

- Recovery from accidental overwrites.
- Recovery from ordinary object deletions.
- Retention of historical object versions.
- Replication workflows that require versioned buckets.

Versioning does not provide a complete backup or disaster recovery strategy. A user or role with sufficient permissions can permanently delete specific object versions.

Once versioning has been enabled on a bucket, it cannot be returned to the never-versioned state. It can be suspended, but existing versions remain.

### Server-side Encryption

The default configuration uses SSE-S3:

```hcl
kms_key_arn = null
```

The encryption resource selects the algorithm based on whether a KMS key ARN is provided:

| Configuration | Encryption |
|---|---|
| `kms_key_arn = null` | SSE-S3 using `AES256`. |
| `kms_key_arn` contains a customer-managed key ARN | SSE-KMS using `aws:kms`. |

To use SSE-KMS, provide a valid customer-managed key ARN:

```hcl
kms_key_arn = "arn:aws:kms:ap-south-1:123456789012:key/example-key-id"
```

The KMS key must be in the same Region as the bucket. Its key policy and the applicable IAM permissions must authorize the required operations.

S3 Bucket Keys are enabled only when SSE-KMS is configured and `bucket_key_enabled` is true.

### Lifecycle Configuration

The example configures two lifecycle actions.

| Lifecycle action | Configuration | Behavior |
|---|---|---|
| Noncurrent version expiration | 90 days | Expires eligible noncurrent object versions after they have been noncurrent for the configured period. |
| Incomplete multipart upload cleanup | 7 days | Aborts incomplete multipart uploads after the configured period. |

The lifecycle configuration does not expire current object versions.

This distinction matters because versioned buckets can accumulate historical versions even when application code deletes or overwrites objects.

Lifecycle processing is asynchronous. Do not assume that an eligible version will disappear at the exact moment its configured age is reached.

The example uses an empty lifecycle filter, so the rules apply across the bucket.

For production workloads, choose retention periods based on recovery requirements, compliance obligations, and storage costs.

## Deployment

Run the following commands from the `examples/versioned-bucket` directory.

### Initialize Terraform

```bash
terraform init
```

Terraform downloads the AWS provider and initializes the working directory.

This example does not configure a remote backend, so Terraform uses local state by default.

### Format the Configuration

```bash
terraform fmt -recursive
```

### Validate the Configuration

```bash
terraform validate
```

This checks Terraform configuration syntax and internal consistency. It does not prove that AWS permissions or resource creation will succeed.

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
- The encryption algorithm is correct.
- Lifecycle expiration and multipart cleanup periods are correct.
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
```

### Verify Versioning

```bash
aws s3api get-bucket-versioning \
  --bucket your-org-versioned-documents-example
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
  --bucket your-org-versioned-documents-example
```

Confirm that the returned encryption algorithm matches the configured SSE-S3 or SSE-KMS strategy.

### Verify Public Access Block

```bash
aws s3api get-public-access-block \
  --bucket your-org-versioned-documents-example
```

Confirm that all four public-access restrictions are enabled.

### Verify Object Ownership

```bash
aws s3api get-bucket-ownership-controls \
  --bucket your-org-versioned-documents-example
```

Confirm that the ownership rule uses `BucketOwnerEnforced`.

### Verify Lifecycle Configuration

```bash
aws s3api get-bucket-lifecycle-configuration \
  --bucket your-org-versioned-documents-example
```

Inspect the returned rules and confirm:

- Noncurrent version expiration is configured for 90 days.
- Incomplete multipart uploads are aborted after 7 days.
- Both rules are enabled.

## Test Object Versioning

A practical verification should demonstrate how S3 preserves object versions when the same key is uploaded more than once.

### Upload the First Version

Create a sample file:

```bash
echo "Document version one" > document.txt
```

Upload it:

```bash
aws s3 cp document.txt \
  s3://your-org-versioned-documents-example/document.txt
```

### Upload a Second Version

Modify the file:

```bash
echo "Document version two" > document.txt
```

Upload it again using the same object key:

```bash
aws s3 cp document.txt \
  s3://your-org-versioned-documents-example/document.txt
```

S3 creates a new current version while preserving the previous version.

### List Object Versions

```bash
aws s3api list-object-versions \
  --bucket your-org-versioned-documents-example \
  --prefix document.txt
```

Inspect the `Versions` array.

It should contain multiple versions of `document.txt`, including their version IDs and current-version indicators.

### Download a Specific Version

Copy the version ID from the previous command:

```bash
aws s3api get-object \
  --bucket your-org-versioned-documents-example \
  --key document.txt \
  --version-id YOUR_VERSION_ID \
  historical-document.txt
```

Inspect the downloaded file:

```bash
cat historical-document.txt
```

This demonstrates recovery of a historical object version without changing the current version.

### Delete the Current Object

```bash
aws s3api delete-object \
  --bucket your-org-versioned-documents-example \
  --key document.txt
```

In a versioned bucket, an ordinary delete request generally creates a delete marker rather than permanently deleting previous versions.

Inspect the result:

```bash
aws s3api list-object-versions \
  --bucket your-org-versioned-documents-example \
  --prefix document.txt
```

The delete marker should appear in the `DeleteMarkers` array.

### Restore a Historical Version

To make a historical version current again, copy that version onto the same object key:

```bash
aws s3api copy-object \
  --bucket your-org-versioned-documents-example \
  --copy-source "your-org-versioned-documents-example/document.txt?versionId=YOUR_VERSION_ID" \
  --key document.txt
```

This creates a new current version containing the historical object's data. It does not remove the historical versions or the delete marker.

## Test Lifecycle Behavior

The configured noncurrent version expiration period is 90 days.

To verify the lifecycle configuration:

```bash
aws s3api get-bucket-lifecycle-configuration \
  --bucket your-org-versioned-documents-example
```

Do not wait for an ordinary short-lived test to expire versions. Lifecycle processing is asynchronous, and the configured retention period is intentionally long.

For a production environment, validate lifecycle behavior using a dedicated test bucket and a carefully designed test policy. Do not shorten retention on a bucket containing business-critical data merely to accelerate a test.

### Incomplete Multipart Upload Cleanup

The lifecycle rule also aborts incomplete multipart uploads after 7 days.

Inspect active multipart uploads:

```bash
aws s3api list-multipart-uploads \
  --bucket your-org-versioned-documents-example
```

This helps identify uploads that have been initiated but not completed or aborted.

## Production Considerations

### Versioning Is Not a Backup

Versioning protects against several accidental object-level changes, but it does not independently protect against:

- Permanent deletion of object versions.
- Unauthorized deletion by a sufficiently privileged principal.
- Account-level compromise.
- Region-wide recovery requirements.
- Incorrect retention configuration.

For stronger recovery controls, evaluate S3 Object Lock, cross-account backups, replication, and independently protected recovery procedures.

### Lifecycle Retention

The example expires noncurrent versions after 90 days.

Before adopting this policy, determine:

- Required historical retention.
- Regulatory or contractual retention obligations.
- Recovery point objectives.
- Expected object update frequency.
- Storage costs for noncurrent versions.
- Whether Object Lock or legal holds apply.

Lifecycle expiration does not override Object Lock retention or legal holds.

### IAM Permissions

Use workload-specific IAM roles and least-privilege policies.

A backend application that only uploads and downloads objects should not receive permission to permanently delete object versions unless its workflow requires it.

For version-aware recovery operations, permissions may include:

- `s3:GetObjectVersion`
- `s3:ListBucketVersions`
- `s3:DeleteObjectVersion` only when permanent version deletion is explicitly required.

Keep application permissions separate from infrastructure deployment permissions.

### Monitoring and Cost

Versioning increases storage consumption because previous versions remain stored.

Monitor:

- Total bucket storage.
- Number of object versions.
- Noncurrent version storage.
- Incomplete multipart uploads.
- Lifecycle execution and retention behavior.
- S3 request and retrieval costs.

S3 Storage Lens and S3 Inventory can help analyze object and version storage at scale.

### Terraform State

This example uses local state for simplicity.

For shared or production deployments, configure a secured remote backend with encryption, restricted access, versioning, and state locking.

Do not share a local state file across engineers or CI/CD runners.

### Resource Ownership

The example manages the bucket's lifecycle configuration through `aws_s3_bucket_lifecycle_configuration.versioned`.

Do not introduce another Terraform resource or module that manages the same bucket's complete lifecycle configuration. Multiple owners can overwrite one another's configuration and cause unexpected drift.

## Troubleshooting

### Versioning Is Not Enabled

**Symptom:** `get-bucket-versioning` does not return `Enabled`.

**Possible causes:**

- Terraform was not applied successfully.
- The CLI is inspecting a different bucket or account.
- Another deployment changed the versioning state.

Verify the active identity and bucket:

```bash
aws sts get-caller-identity

aws s3api get-bucket-versioning \
  --bucket your-org-versioned-documents-example
```

Review Terraform state and the execution plan before making corrective changes.

### Previous Versions Are Not Visible

**Symptom:** `aws s3 ls` displays only the current object.

**Cause:** The ordinary `aws s3 ls` command does not show the complete version history.

Use:

```bash
aws s3api list-object-versions \
  --bucket your-org-versioned-documents-example
```

The caller must have permission to list object versions.

### Deleted Object Still Has Storage Charges

**Symptom:** An object was deleted, but bucket storage does not decrease as expected.

**Cause:** An ordinary delete request creates a delete marker. Previous object versions remain stored.

Inspect:

```bash
aws s3api list-object-versions \
  --bucket your-org-versioned-documents-example
```

Review the `Versions` and `DeleteMarkers` arrays. Use lifecycle retention or an approved permanent deletion workflow to manage historical versions.

### Lifecycle Rules Are Not Removing Versions

**Symptom:** Noncurrent versions remain after the configured expiration period.

**Possible causes:**

- The versions have not yet become eligible for expiration.
- Lifecycle processing has not completed.
- Object Lock retention or legal holds prevent deletion.
- The lifecycle configuration differs from the expected configuration.

Inspect the active rules:

```bash
aws s3api get-bucket-lifecycle-configuration \
  --bucket your-org-versioned-documents-example
```

Lifecycle execution is asynchronous. Do not interpret a short delay as proof that the configuration is broken.

### Terraform Cannot Delete the Bucket

**Symptom:** `terraform destroy` fails because the bucket is not empty.

**Cause:** Versioned buckets can contain historical versions and delete markers even after ordinary object deletion.

Inspect all versions:

```bash
aws s3api list-object-versions \
  --bucket your-org-versioned-documents-example
```

Review retention and recovery requirements before permanently deleting versions.

The example uses `force_destroy = false` to avoid automatic deletion of bucket contents.

## Cleanup

Destroying the Terraform configuration can fail while the bucket contains objects, versions, or delete markers.

First review the proposed destruction:

```bash
terraform plan -destroy
```

If the bucket contains data, decide whether it must be retained or permanently deleted.

For a disposable test bucket, remove object versions and delete markers only after confirming that the data is safe to discard. A versioned bucket requires version-aware deletion; deleting current keys alone is insufficient.

After the bucket is empty, run:

```bash
terraform destroy
```

Verify that the bucket no longer exists:

```bash
aws s3api head-bucket \
  --bucket your-org-versioned-documents-example
```

A failed request is expected after successful deletion, although the exact error depends on caller permissions and AWS response behavior.

Do not manually delete Terraform-managed resources without a deliberate state-reconciliation plan.

## Key Takeaways

- S3 versioning preserves historical object versions and supports recovery from accidental overwrites and ordinary deletions.
- An ordinary delete in a versioned bucket creates a delete marker; it does not permanently remove historical versions.
- Lifecycle rules can manage noncurrent versions and incomplete multipart uploads, but execution is asynchronous.
- Versioning increases storage consumption and must be paired with deliberate retention, monitoring, and recovery policies.
- Protect versioned data with least-privilege IAM, appropriate retention controls, and tested recovery procedures.