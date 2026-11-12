# README

## Overview

This directory contains the Terraform root configuration for deploying the **staging Amazon S3 environment**.

The environment provisions:

- A versioned source S3 bucket.
- A versioned replica S3 bucket in a separate AWS Region.
- Server-side encryption configuration through the reusable S3 bucket module.
- An IAM role and policy that allow Amazon S3 to replicate eligible objects.
- A replication configuration connecting the source bucket to the replica bucket.
- Replication metrics for monitoring replication progress.

The staging configuration reuses the modules defined under `../../modules/` and keeps environment-specific settings in this root module.

The deployment is intended for validating infrastructure changes before promoting them to production. It uses conservative resource-deletion defaults and keeps Terraform state separate from the application buckets.

## Directory Structure

```text
environments/
└── staging/
    ├── main.tf
    ├── terraform.tfvars.example
    ├── backend.hcl.example
    └── README.md
```

| File | Responsibility |
|---|---|
| `main.tf` | Declares Terraform requirements, providers, variables, modules, locals, and outputs |
| `terraform.tfvars.example` | Provides example values for staging variables |
| `backend.hcl.example` | Provides partial configuration for the remote S3 backend |
| `README.md` | Documents deployment, verification, and operational procedures |

## Architecture

The staging environment deploys a source bucket in the primary Region and a replica bucket in the secondary Region.

```mermaid
flowchart TD
    TF["Terraform staging root module"]

    TF --> SB["Source S3 bucket module"]
    TF --> RB["Replica S3 bucket module"]
    TF --> RM["S3 replication module"]

    SB --> SOURCE["Versioned source bucket"]
    RB --> REPLICA["Versioned replica bucket"]

    RM --> IAM["Replication IAM role and policy"]
    IAM --> S3["Amazon S3 replication service"]

    SOURCE --> S3
    S3 --> REPLICA

    S3 --> METRICS["Replication metrics"]
```

### Component responsibilities

| Component | Responsibility |
|---|---|
| Source bucket | Stores original objects and maintains object versions |
| Replica bucket | Stores replicated object versions in the destination Region |
| Replication IAM role | Grants S3 the permissions required to replicate objects |
| Replication configuration | Defines the source-to-destination replication rule |
| Replication metrics | Exposes replication progress and failure indicators |
| Terraform backend | Stores staging infrastructure state independently of the deployed buckets |

## Environment Configuration

The root configuration defines the staging environment and its deployment parameters.

### AWS Regions

The example configuration uses:

| Setting | Default |
|---|---|
| Primary Region | `ap-south-1` |
| Replica Region | `ap-southeast-1` |

The source bucket is provisioned in the primary Region. The replica bucket is provisioned using the aliased `replica` provider in the destination Region.

The replication configuration itself is created in the source bucket's Region.

Change the Region values only after confirming that the selected Regions support the required S3 features and that your account has the necessary permissions.

### Required values

Update `terraform.tfvars.example` with values appropriate for your AWS account.

| Variable | Requirement | Example |
|---|---|---|
| `source_account_id` | Required | `123456789012` |
| `source_bucket_name` | Required, globally unique | `your-org-staging-s3-source-documents` |
| `replica_bucket_name` | Required, globally unique | `your-org-staging-s3-replica-documents` |
| `aws_region` | Optional | `ap-south-1` |
| `replica_aws_region` | Optional | `ap-southeast-1` |
| `force_destroy` | Optional | `false` |
| `replication_enabled` | Optional | `true` |
| `replication_metrics_enabled` | Optional | `true` |
| `replication_time_control_enabled` | Optional | `false` |

The bucket names must be globally unique across the S3 namespace and comply with S3 bucket naming requirements.

### Encryption configuration

The environment accepts optional customer-managed KMS key ARNs:

- `source_kms_key_arn`
- `destination_kms_key_arn`

When these values are `null`, the bucket module uses its default encryption configuration.

For SSE-KMS replication, configure compatible source and destination keys and authorize the replication role through both IAM permissions and the relevant KMS key policies.

The replication module requires destination encryption configuration when source KMS encryption is enabled.

### Replication configuration

The staging configuration enables replication and metrics by default.

| Setting | Default | Purpose |
|---|---|---|
| `replication_enabled` | `true` | Enables the replication rule |
| `replication_filter_prefix` | `""` | Selects eligible objects by prefix |
| `destination_storage_class` | `STANDARD` | Storage class used for replicated objects |
| `replication_metrics_enabled` | `true` | Enables replication metrics |
| `replication_time_control_enabled` | `false` | Controls whether S3 Replication Time Control is enabled |
| `replication_role_name` | `staging-s3-replication-role` | IAM role assumed by S3 |

An empty replication prefix selects all eligible objects.

Replication Time Control is optional and may introduce additional charges. Enable it only when the workload requires the corresponding replication SLA.

## Prerequisites

Before deploying the staging environment, verify the following requirements.

### Local tooling

Install:

- Terraform 1.5.0 or later.
- AWS CLI.
- Git.
- A supported shell environment.

Verify the installations:

```bash
terraform version
aws --version
git --version
```

### AWS credentials

Configure an AWS identity with permissions to manage:

- S3 buckets and bucket configurations.
- S3 replication configurations.
- IAM roles and IAM policies.
- KMS permissions and key policies when customer-managed keys are used.
- Remote Terraform state access and locking.

Use an IAM role or another short-lived credential mechanism where possible.

Do not store AWS access keys in Terraform files, variable files, or source control.

Verify the active identity:

```bash
aws sts get-caller-identity
```

Confirm that the returned account ID matches `source_account_id`.

### Remote state bucket

The Terraform state bucket must already exist before initializing this environment.

The state bucket is separate from both application buckets.

Recommended state bucket controls:

- S3 versioning enabled.
- Server-side encryption enabled.
- Block Public Access enabled.
- Access restricted to authorized deployment identities.
- State locking enabled through native S3 lock files.
- Independent backup and recovery procedures.

Do not use the source or replica application bucket as the Terraform state bucket.

## Remote State Configuration

The `backend.hcl.example` file contains partial configuration for the S3 backend.

The example uses:

```hcl
bucket       = "your-org-terraform-state"
key          = "amazon-s3/staging/terraform.tfstate"
region       = "ap-south-1"
encrypt      = true
use_lockfile = true
```

Replace the example backend bucket with an existing state bucket.

The `key` value isolates staging state from other environments.

Native S3 state locking through `use_lockfile` requires Terraform 1.10 or later. The backend bucket must support the required S3 operations.

### Initialize the backend

From this directory:

```bash
terraform init -backend-config=backend.hcl.example
```

For a customized backend configuration:

```bash
terraform init -backend-config=backend.hcl
```

Do not commit a backend configuration containing sensitive or organization-specific details unless your repository policy explicitly permits it.

If changing an existing backend configuration, review Terraform's backend migration behavior before using `-migrate-state` or `-reconfigure`.

## Configure Staging Variables

Create a local variable file from the example:

```bash
cp terraform.tfvars.example terraform.tfvars
```

On Windows PowerShell:

```powershell
Copy-Item terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and replace the placeholder values.

Example:

```hcl
aws_region         = "ap-south-1"
replica_aws_region = "ap-southeast-1"

source_account_id = "123456789012"

source_bucket_name  = "your-org-staging-s3-source-documents"
replica_bucket_name = "your-org-staging-s3-replica-documents"

force_destroy = false

source_kms_key_arn      = null
destination_kms_key_arn = null

replication_role_name = "staging-s3-replication-role"

replication_filter_prefix = ""

replication_enabled = true
destination_storage_class = "STANDARD"

replication_metrics_enabled = true
replication_time_control_enabled = false
```

The root module provides default tags for the staging environment. The example variable file intentionally contains only assignments for declared root variables.

Add `terraform.tfvars` to `.gitignore` if it contains account-specific or environment-specific values that should not be committed.

## Validate the Configuration

Run formatting:

```bash
terraform fmt -recursive
```

Validate the root module:

```bash
terraform validate
```

Inspect the working directory:

```bash
terraform providers
terraform workspace show
```

The environment uses a dedicated remote state key. Avoid switching workspaces or changing state configuration without a clear environment-isolation strategy.

## Deployment Workflow

Use the following workflow for staging deployments.

### Initialize

```bash
terraform init -backend-config=backend.hcl.example
```

### Review formatting and validation

```bash
terraform fmt -check -recursive
terraform validate
```

### Generate a deployment plan

```bash
terraform plan -var-file=terraform.tfvars -out=staging.tfplan
```

Review the plan carefully before applying it.

Pay particular attention to:

- Bucket creation or replacement.
- Bucket versioning changes.
- Encryption configuration changes.
- IAM role and policy modifications.
- Replication configuration changes.
- Resource destruction.
- KMS key references.
- Region and account identifiers.

### Apply the reviewed plan

```bash
terraform apply staging.tfplan
```

Do not apply an outdated plan after changing the configuration or variable values. Generate a new plan whenever the inputs or infrastructure definitions change.

### Inspect outputs

```bash
terraform output
```

Retrieve individual values:

```bash
terraform output source_bucket_id
terraform output replica_bucket_id
terraform output replication_role_arn
terraform output replication_rule_status
```

## Post-Deployment Verification

Terraform reporting a successful apply does not prove that object replication is functioning correctly.

Verify the deployed AWS configuration independently.

### Verify bucket existence

```bash
aws s3api head-bucket \
  --bucket your-org-staging-s3-source-documents \
  --region ap-south-1
```

```bash
aws s3api head-bucket \
  --bucket your-org-staging-s3-replica-documents \
  --region ap-southeast-1
```

A successful response indicates that the bucket is accessible to the current identity.

### Verify versioning

Source bucket:

```bash
aws s3api get-bucket-versioning \
  --bucket your-org-staging-s3-source-documents \
  --region ap-south-1
```

Replica bucket:

```bash
aws s3api get-bucket-versioning \
  --bucket your-org-staging-s3-replica-documents \
  --region ap-southeast-1
```

Both buckets must have versioning enabled for replication.

### Verify encryption

Source bucket:

```bash
aws s3api get-bucket-encryption \
  --bucket your-org-staging-s3-source-documents \
  --region ap-south-1
```

Replica bucket:

```bash
aws s3api get-bucket-encryption \
  --bucket your-org-staging-s3-replica-documents \
  --region ap-southeast-1
```

Confirm that the configured encryption algorithm and KMS key references match the intended environment configuration.

### Verify replication configuration

```bash
aws s3api get-bucket-replication \
  --bucket your-org-staging-s3-source-documents \
  --region ap-south-1
```

Inspect:

- Replication role ARN.
- Rule identifier.
- Rule status.
- Destination bucket ARN.
- Storage class.
- Prefix filter.
- Metrics configuration.
- Replication Time Control configuration, if enabled.

### Verify IAM role

```bash
aws iam get-role \
  --role-name staging-s3-replication-role
```

Inspect the attached inline policy:

```bash
aws iam list-role-policies \
  --role-name staging-s3-replication-role
```

Confirm that the trust policy allows the S3 service to assume the role and that the permissions cover the configured replication behavior.

## Replication Testing

Use a test object to verify the end-to-end replication flow.

Upload a sample object:

```bash
echo "Staging S3 replication verification" > replication-test.txt
```

```bash
aws s3 cp replication-test.txt \
  s3://your-org-staging-s3-source-documents/replication-tests/replication-test.txt \
  --region ap-south-1
```

Inspect the uploaded object's replication status:

```bash
aws s3api head-object \
  --bucket your-org-staging-s3-source-documents \
  --key replication-tests/replication-test.txt \
  --region ap-south-1
```

Inspect the `ReplicationStatus` field. It may initially be pending while S3 processes the object.

Check the destination:

```bash
aws s3api head-object \
  --bucket your-org-staging-s3-replica-documents \
  --key replication-tests/replication-test.txt \
  --region ap-southeast-1
```

Replication is asynchronous. Allow time for the operation to complete before treating the absence of the replica as a configuration failure.

A successful test should establish that:

- The source object exists.
- The source bucket has versioning enabled.
- The replication rule is enabled.
- The replication role can be assumed by S3.
- Required destination permissions are available.
- The replica object becomes available in the destination bucket.
- The destination object has the expected content and metadata.

For stronger integrity verification, compare object checksums where supported. Do not assume that matching object sizes alone establish data integrity.

### Existing objects

Live replication normally applies to eligible objects created after the replication configuration becomes active.

Existing objects require S3 Batch Replication or another explicit backfill process.

Do not assume that deploying the Terraform replication rule automatically copies the existing contents of the source bucket.

## Monitoring and Operations

The staging configuration enables replication metrics by default.

Monitor replication behavior using:

- S3 replication metrics.
- S3 Replication Time Control metrics when RTC is enabled.
- CloudWatch alarms for replication failures or excessive pending operations.
- CloudTrail for relevant S3 and IAM API activity.
- Application-level verification of replicated objects.

Useful operational indicators include:

| Indicator | Operational significance |
|---|---|
| Replication latency | Time taken for eligible objects to reach the destination |
| Operations pending replication | Objects awaiting replication |
| Operations failed replication | Objects that could not be replicated |
| Bytes pending replication | Outstanding data volume |
| Destination object availability | Whether expected replicas can be read |

For staging, use test objects and controlled workloads to verify configuration changes before promoting them to production.

Replication is asynchronous and does not provide automatic application failover. A recovery design must separately address application routing, data access, write ownership, and recovery procedures.

## Security Considerations

### Bucket access

The bucket module configures private bucket access controls and ownership settings.

Keep Block Public Access enabled unless a documented architecture requires otherwise.

Avoid granting broad S3 permissions to application or deployment roles.

### Replication permissions

The replication role should have only the permissions required by the replication configuration.

For cross-account replication, the destination bucket policy must explicitly authorize the replication role. The current staging root configuration does not define a separate cross-account destination bucket policy.

### KMS permissions

When using SSE-KMS:

- The replication role needs the required source-key decrypt permissions.
- The role needs the required destination-key encryption permissions.
- Source and destination KMS key policies must authorize the relevant principal.
- The destination key must be available in the destination bucket's Region.
- Validate KMS permissions independently from S3 bucket permissions.

An S3 `AccessDenied` response can originate from an S3 authorization failure or a KMS authorization failure.

### Terraform state

Terraform state can contain infrastructure metadata and sensitive values.

Restrict access to the remote state bucket and use encryption, versioning, and state locking.

Never commit local state files or sensitive variable files.

## Common Deployment Problems

| Problem | Likely cause | Diagnostic action |
|---|---|---|
| `AccessDenied` during bucket creation | Insufficient IAM permissions or organization policy | Inspect the active identity and IAM authorization |
| Bucket name already exists | S3 bucket names are globally unique | Select another bucket name |
| `BucketAlreadyOwnedByYou` | Bucket already exists in the same account | Import and manage it through the intended Terraform state |
| Replication configuration rejected | Versioning or replication permissions are missing | Inspect both bucket versioning configurations and IAM policies |
| Replication remains pending | Normal asynchronous processing or a permission/configuration issue | Inspect object replication status and replication metrics |
| Replica object is missing | Rule filter mismatch, permissions, or replication delay | Inspect the rule and source object status |
| KMS replication fails | Missing key policy or KMS permissions | Inspect both key policies and the replication role policy |
| Terraform state lock error | Another operation holds the state lock | Confirm no active operation before attempting recovery |
| Backend initialization fails | Incorrect state bucket, key, Region, or permissions | Verify backend configuration and S3 access |
| Provider Region mismatch | Incorrect provider or alias configuration | Inspect provider configuration and resource Regions |

Do not manually delete a Terraform state lock file while another Terraform operation may still be active.

## Change Management

Treat staging as the validation environment for infrastructure changes.

Recommended change process:

1. Update the reusable module or staging configuration.
2. Run `terraform fmt -check -recursive`.
3. Run `terraform validate`.
4. Generate and review a staging plan.
5. Check for unintended resource replacement or destruction.
6. Apply the reviewed plan.
7. Verify bucket security, versioning, encryption, and replication.
8. Run a controlled object replication test.
9. Record any operational findings before promoting the change.

Use separate Terraform state keys for development, staging, and production.

Do not share state between environments.

## Resource Protection and Cleanup

The staging configuration defaults `force_destroy` to `false`.

This prevents Terraform from automatically deleting non-empty buckets during destruction.

Before destroying the environment:

- Confirm that the buckets contain no data requiring retention.
- Inspect object versions and delete markers.
- Confirm that no application or test process depends on the buckets.
- Review replication and IAM dependencies.
- Confirm that the Terraform state belongs to staging.
- Verify that the remote state bucket is not part of this environment's resources.

### Destroy staging resources

Generate a destroy plan:

```bash
terraform plan -destroy \
  -var-file=terraform.tfvars \
  -out=staging-destroy.tfplan
```

Review the plan carefully.

If the buckets contain objects or versions, clean them up only after confirming that deletion is authorized and appropriate.

Then apply the reviewed destroy plan:

```bash
terraform apply staging-destroy.tfplan
```

Do not enable `force_destroy` merely to bypass deletion errors. Versioned buckets may contain historical object versions and delete markers that require explicit cleanup.

The Terraform backend bucket is independent and must not be deleted as part of this environment's cleanup.

## Production Readiness Considerations

The staging deployment is a validation configuration, not a complete production disaster-recovery implementation.

Before promoting the architecture, evaluate:

- Cross-account destination bucket policies where required.
- KMS key policies and key lifecycle management.
- Replication failure monitoring and alerting.
- S3 Batch Replication for existing objects.
- Object Lock and retention requirements.
- Recovery procedures and recovery objectives.
- Application routing and failover behavior.
- Data integrity verification.
- Terraform state backup and recovery.
- Cost implications of replication, storage classes, metrics, and RTC.

A replica bucket alone does not establish a complete disaster recovery strategy. Recovery must also account for application dependencies, permissions, regional service availability, and operational procedures.

## Key Takeaways

- The staging environment uses reusable Terraform modules to provision versioned source and replica buckets with S3 replication.
- Keep Terraform state in an independently managed, encrypted, versioned S3 backend with native state locking.
- Validate IAM, bucket policies, and KMS key policies separately when diagnosing replication failures.
- Verify actual object replication and monitor asynchronous replication status instead of relying only on successful Terraform deployment.
- Keep destructive operations conservative: review plans, protect retained data, and avoid enabling `force_destroy` as a shortcut.