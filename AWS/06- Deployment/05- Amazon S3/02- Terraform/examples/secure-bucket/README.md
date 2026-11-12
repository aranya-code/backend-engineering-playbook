# README

## Overview

This example demonstrates how to provision a secure Amazon S3 bucket using the reusable `s3-bucket` Terraform module developed in this playbook.

It provides a practical starting point for backend services that need private object storage for documents, application uploads, media files, or other workload data.

The example delegates bucket creation and baseline security configuration to the reusable module rather than duplicating individual S3 resources.

The configuration enables:

- S3 bucket versioning.
- S3 Block Public Access and Object Ownership controls through the module.
- Server-side encryption.
- Optional customer-managed AWS KMS encryption.
- Optional server access logging.
- Optional lifecycle configuration.
- Resource tagging.
- Protection against accidental deletion of non-empty buckets.

The example uses conservative defaults and is intended for development and learning. Production deployments should additionally evaluate workload-specific IAM policies, KMS key policies, logging requirements, retention controls, and infrastructure state management.

## Project Structure

```text
secure-bucket/
├── main.tf
├── variables.tf
├── outputs.tf
└── README.md
```

| File | Responsibility |
|---|---|
| `main.tf` | Configures the AWS provider and invokes the reusable S3 bucket module. |
| `variables.tf` | Declares configurable inputs such as the bucket name, encryption key, versioning, and tags. |
| `outputs.tf` | Exposes bucket identifiers, encryption details, versioning status, and logging configuration. |
| `README.md` | Documents prerequisites, deployment, verification, and cleanup. |

The module is referenced using:

```hcl
source = "../../modules/s3-bucket"
```

This path is relative to the `examples/secure-bucket` directory.

## Architecture

The example uses a root Terraform configuration that delegates S3 resource management to the shared module.

```mermaid
flowchart TD
    A["Terraform CLI"] --> B["secure-bucket root configuration"]
    B --> C["AWS Provider"]
    B --> D["s3-bucket module"]
    D --> E["S3 Bucket"]
    D --> F["Public Access Block"]
    D --> G["Object Ownership Controls"]
    D --> H["Versioning"]
    D --> I["Server-side Encryption"]
    D --> J["Optional Lifecycle Configuration"]
    D --> K["Optional Server Access Logging"]
    E --> L["Private Application Storage"]
```

### Component Responsibilities

| Component | Responsibility |
|---|---|
| Terraform root configuration | Supplies configuration values and selects the AWS provider. |
| AWS provider | Authenticates Terraform and communicates with AWS APIs. |
| `s3-bucket` module | Creates and configures the bucket and its supported security controls. |
| S3 versioning | Preserves object versions and supports recovery from accidental overwrites or deletions. |
| Server-side encryption | Encrypts objects at rest. |
| Public access block | Prevents unintended public access through supported S3 public-access mechanisms. |
| Object Ownership | Establishes bucket-owner-enforced ownership behavior and disables ACL-based ownership management where configured by the module. |

## Prerequisites

Install the following tools:

| Tool | Purpose |
|---|---|
| Terraform | Infrastructure provisioning. |
| AWS CLI | AWS identity verification and resource inspection. |
| AWS account | Hosts the S3 bucket and related resources. |
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
aws configure --profile s3-example
```

Select the profile before running Terraform:

**Linux/macOS**

```bash
export AWS_PROFILE=s3-example
```

**Windows PowerShell**

```powershell
$env:AWS_PROFILE = "s3-example"
```

Verify the active identity:

```bash
aws sts get-caller-identity
```

Do not place AWS access keys in Terraform source files, `.tfvars` files, or version control.

## Configuration

### Bucket Name

The `bucket_name` variable must contain a globally unique S3 general-purpose bucket name.

Example:

```hcl
bucket_name = "your-org-secure-s3-example-bucket"
```

Replace this value before deployment.

Use a naming convention that identifies the organization, workload, environment, and purpose without exposing sensitive information.

For example:

```text
company-dev-document-storage
company-staging-media-storage
company-production-backup-storage
```

S3 bucket names are globally unique within the applicable AWS partition. A name already allocated by another account cannot be reused.

### AWS Region

The current `main.tf` configures the AWS provider directly with:

```hcl
provider "aws" {
  region = "ap-south-1"
}
```

Although `variables.tf` declares an `aws_region` variable, the current provider configuration does not reference it. Changing that variable alone will not change the deployment Region.

To make the Region configurable, update the provider configuration in `main.tf`:

```hcl
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}
```

The example defaults to `ap-south-1`.

### Encryption

The module supports two encryption approaches through `kms_key_arn`:

| Configuration | Encryption behavior |
|---|---|
| `kms_key_arn = null` | Uses the module's default SSE-S3 behavior. |
| `kms_key_arn = "arn:aws:kms:..."` | Uses the specified customer-managed KMS key for SSE-KMS. |

The example defaults to SSE-S3:

```hcl
kms_key_arn        = null
bucket_key_enabled = true
```

For SSE-KMS, provide a valid customer-managed KMS key ARN:

```hcl
kms_key_arn = "arn:aws:kms:ap-south-1:123456789012:key/example-key-id"
```

The KMS key must be in the same Region as the S3 bucket. Its key policy and applicable IAM permissions must authorize the principals that need to use it.

S3 Bucket Keys can reduce KMS request costs for supported SSE-KMS workloads.

### Versioning

Versioning is enabled by default:

```hcl
versioning_enabled = true
```

This preserves multiple versions of an object under the same key.

Versioning is useful for:

- Recovering from accidental overwrites.
- Recovering from ordinary object deletions.
- Maintaining historical object versions.
- Supporting replication configurations that require versioned buckets.

Versioning does not replace backups, retention controls, or a disaster recovery strategy.

### Lifecycle Configuration

The example passes an empty lifecycle rule collection:

```hcl
lifecycle_rules = []
```

This is intentional when lifecycle management is handled separately by the dedicated `s3-lifecycle` module.

Only one Terraform resource should manage the complete lifecycle configuration of a given bucket. Avoid configuring the same bucket lifecycle independently through both modules.

### Server Access Logging

Logging is optional:

```hcl
logging_target_bucket = null
logging_target_prefix = "s3-access-logs/"
```

To enable server access logging, provide the name of an existing logging bucket:

```hcl
logging_target_bucket = "your-org-s3-access-logs"
logging_target_prefix = "secure-bucket/"
```

The logging target bucket must be configured to accept S3 server access logs. Verify the required permissions, ownership settings, and encryption compatibility before enabling logging.

Do not configure a bucket to write access logs to itself.

## Deployment

Run all Terraform commands from the `examples/secure-bucket` directory.

### Initialize Terraform

```bash
terraform init
```

Terraform downloads the required AWS provider and initializes the local working directory.

The example does not configure a remote backend. Terraform therefore uses local state by default.

### Format the Configuration

```bash
terraform fmt -recursive
```

This formats Terraform configuration files.

### Validate the Configuration

```bash
terraform validate
```

This checks Terraform configuration syntax and internal consistency. It does not verify that AWS will authorize or successfully create every resource.

### Review the Execution Plan

```bash
terraform plan
```

Inspect the planned changes before applying them.

Confirm:

- The intended AWS account and Region.
- The globally unique bucket name.
- Versioning configuration.
- Encryption configuration.
- Public access and ownership controls.
- Optional logging and lifecycle settings.
- Resource tags.
- Whether the plan contains unexpected replacement or deletion operations.

### Apply the Configuration

```bash
terraform apply
```

Review the plan and confirm the operation when prompted.

Terraform creates the S3 bucket and the resources managed by the reusable module.

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
terraform output bucket_versioning_enabled
terraform output bucket_encryption_algorithm
terraform output server_access_logging_enabled
```

### Verify the Bucket

```bash
aws s3api head-bucket \
  --bucket your-org-secure-s3-example-bucket
```

A successful response indicates that the caller can access the bucket.

### Verify Versioning

```bash
aws s3api get-bucket-versioning \
  --bucket your-org-secure-s3-example-bucket
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
  --bucket your-org-secure-s3-example-bucket
```

Inspect the returned server-side encryption configuration and confirm that it matches the selected encryption strategy.

### Verify Public Access Block

```bash
aws s3api get-public-access-block \
  --bucket your-org-secure-s3-example-bucket
```

Confirm that the expected public-access restrictions are enabled.

### Verify Object Ownership

```bash
aws s3api get-bucket-ownership-controls \
  --bucket your-org-secure-s3-example-bucket
```

Confirm that the ownership configuration matches the module's intended setting.

### Verify Server Access Logging

If logging is enabled:

```bash
aws s3api get-bucket-logging \
  --bucket your-org-secure-s3-example-bucket
```

If logging is not configured, the API response will not contain a logging configuration.

## Test Object Operations

Use the AWS CLI to upload a sample file:

```bash
echo "S3 secure bucket verification" > sample.txt

aws s3 cp sample.txt \
  s3://your-org-secure-s3-example-bucket/sample.txt
```

Inspect the object:

```bash
aws s3api head-object \
  --bucket your-org-secure-s3-example-bucket \
  --key sample.txt
```

Download it:

```bash
aws s3 cp \
  s3://your-org-secure-s3-example-bucket/sample.txt \
  downloaded-sample.txt
```

Compare the files:

```bash
diff sample.txt downloaded-sample.txt
```

On Windows PowerShell, use:

```powershell
Compare-Object `
  (Get-Content sample.txt) `
  (Get-Content downloaded-sample.txt)
```

Delete the test object:

```bash
aws s3 rm \
  s3://your-org-secure-s3-example-bucket/sample.txt
```

These operations verify basic object access. They do not constitute a complete security, recovery, or production-readiness test.

## Security Considerations

### Keep the Bucket Private

Do not make the bucket public to simplify application access.

For backend workloads, use IAM roles with narrowly scoped permissions.

A typical application role may require only:

- `s3:PutObject` for uploads.
- `s3:GetObject` for downloads.
- `s3:DeleteObject` when deletion is part of the application workflow.
- `s3:ListBucket` only when listing is required.

Scope object permissions to the required bucket and prefixes.

### Use Temporary Credentials

Prefer:

- IAM roles attached to EC2 instances.
- ECS task roles.
- EKS workload identity integrations.
- Lambda execution roles.
- GitHub Actions OIDC federation.

Avoid long-lived IAM user access keys in application configuration.

### Protect KMS Keys

When SSE-KMS is enabled:

- Restrict key administration permissions.
- Grant cryptographic permissions only to required principals.
- Ensure the KMS key policy authorizes the relevant application and service roles.
- Review key rotation and deletion policies.
- Avoid disabling or scheduling deletion of keys while encrypted objects still depend on them.

S3 authorization and KMS authorization are separate permission layers. An application may have S3 object permissions and still receive an access-denied response because it lacks the required KMS permissions.

### Protect Terraform State

The example uses local Terraform state for simplicity.

For shared or production environments, use a secured remote backend with:

- Encryption at rest.
- Versioning and recovery controls.
- Restricted access.
- State locking.
- Separate state keys for independent environments.

Terraform state can contain sensitive infrastructure metadata. Treat it as sensitive even when application secrets are not intentionally stored in it.

## Production Considerations

This example establishes a baseline bucket configuration. It is not a complete production security architecture.

Before using it for production workloads, evaluate the following:

| Concern | Recommendation |
|---|---|
| IAM | Use workload-specific roles and least-privilege permissions. |
| Encryption | Select SSE-S3 or SSE-KMS based on compliance and operational requirements. |
| Versioning | Define recovery procedures and manage noncurrent versions. |
| Lifecycle | Establish retention and transition rules based on data access patterns. |
| Logging | Configure a separate logging destination and validate delivery. |
| Monitoring | Monitor request activity, storage usage, errors, and unexpected cost growth. |
| Data recovery | Define recovery objectives and test restoration procedures. |
| Terraform state | Use a secured remote backend with locking and versioning. |
| Resource protection | Keep `force_destroy = false` and review destructive plans carefully. |
| Access control | Review bucket policies, IAM policies, and KMS key policies together. |

### Destructive Operations

The example uses:

```hcl
force_destroy = false
```

This prevents Terraform from automatically deleting a bucket while it contains objects.

Do not enable `force_destroy` as a routine workaround for failed bucket deletion. Investigate object versions, delete markers, retention controls, and other dependencies before removing data.

## Troubleshooting

### Bucket Name Already Exists

**Symptom:** Bucket creation fails because the requested name is unavailable.

**Cause:** S3 general-purpose bucket names must be globally unique within the applicable AWS partition.

**Resolution:** Choose another name and update `bucket_name`.

### Access Denied During Deployment

**Symptom:** Terraform receives `AccessDenied` while creating or configuring bucket resources.

**Possible causes:**

- The active AWS identity lacks required S3 permissions.
- An organization-level service control policy denies the operation.
- An explicit IAM or resource-policy deny applies.
- The caller is operating in the wrong AWS account.

Verify the active identity:

```bash
aws sts get-caller-identity
```

Review the failed API operation and the permissions required by the Terraform deployment role.

### KMS Encryption Configuration Fails

**Symptom:** Terraform cannot configure SSE-KMS.

**Possible causes:**

- The KMS key ARN is invalid.
- The KMS key belongs to a different Region.
- The deployment identity lacks required KMS permissions.
- The key policy does not authorize the deployment principal.

Verify the key:

```bash
aws kms describe-key \
  --key-id arn:aws:kms:ap-south-1:123456789012:key/example-key-id
```

Review both the IAM policy and the KMS key policy.

### Bucket Deletion Fails

**Symptom:** Terraform cannot destroy the bucket.

**Possible causes:**

- The bucket contains objects.
- Object versions or delete markers remain.
- Object retention or legal holds prevent deletion.
- Other resources still depend on the bucket.

Inspect object versions:

```bash
aws s3api list-object-versions \
  --bucket your-org-secure-s3-example-bucket
```

Review the data and retention requirements before attempting deletion.

### Terraform Reports Configuration Drift

**Symptom:** Terraform plans changes to bucket configuration that were not expected.

**Possible causes:**

- A user or external automation changed the bucket outside Terraform.
- Another Terraform configuration manages the same resource.
- AWS defaults or provider behavior differ from the recorded state.

Inspect the plan:

```bash
terraform plan
```

Identify the resource and attribute responsible for the difference. Reconcile the configuration and state deliberately rather than blindly applying changes.

## Cleanup

Before destroying the example, verify that the bucket does not contain data that must be retained.

Review the proposed destruction:

```bash
terraform plan -destroy
```

If the plan is correct, run:

```bash
terraform destroy
```

Because `force_destroy` is disabled, Terraform will not automatically remove a non-empty bucket.

If the bucket contains objects, first review and remove only the data that is safe to delete. For a versioned bucket, deleting current object keys alone may leave historical versions and delete markers.

After cleanup, verify that the bucket no longer exists:

```bash
aws s3api head-bucket \
  --bucket your-org-secure-s3-example-bucket
```

A failed request is expected after successful deletion, although the exact error depends on the caller's permissions and AWS response.

Do not manually delete Terraform-managed resources unless you have a deliberate state-reconciliation plan.

## Key Takeaways

- The example provisions an S3 bucket through the reusable `s3-bucket` module rather than duplicating resource definitions.
- Versioning, private-access controls, and server-side encryption provide a baseline for secure object storage.
- SSE-KMS requires correct authorization at both the S3 and KMS permission layers.
- Keep lifecycle configuration under a single Terraform owner and use `force_destroy = false` to reduce accidental data loss.
- Use remote, encrypted, access-controlled Terraform state with locking for shared and production deployments.