# README

## Overview

This directory contains the development environment configuration for the Amazon S3 Terraform deployment. It composes the reusable S3 modules into a development infrastructure stack with:

- A versioned primary S3 bucket.
- A versioned destination S3 bucket in a separate AWS Region.
- Cross-Region Replication (CRR) between the buckets.
- Optional customer-managed AWS KMS encryption.
- Replication metrics and optional Replication Time Control (RTC).
- Environment-specific configuration and Terraform state management.

The configuration is intended to demonstrate how reusable Terraform modules are composed into a deployable environment. It keeps the bucket and replication implementations in the shared `modules/` directory while defining environment-specific inputs, providers, and outputs here.

## Directory Structure

```text
environments/
└── dev/
    ├── main.tf
    ├── terraform.tfvars.example
    ├── backend.hcl.example
    └── README.md
```

| File | Responsibility |
|---|---|
| `main.tf` | Declares Terraform and AWS provider requirements, input variables, providers, module instances, and outputs |
| `terraform.tfvars.example` | Provides example values for development environment variables |
| `backend.hcl.example` | Provides partial configuration for the remote S3 Terraform backend |
| `README.md` | Documents deployment, validation, operations, and cleanup |

The environment references these reusable modules:

```text
02- Terraform/
├── modules/
│   ├── s3-bucket/
│   └── s3-replication/
└── environments/
    └── dev/
```

The `s3-bucket` module manages bucket-level configuration. The `s3-replication` module manages the replication IAM role, permissions, and source bucket replication configuration.

## Architecture

The development environment deploys two versioned buckets in different Regions.

```mermaid
flowchart TB
    TF[Terraform Development Environment]

    subgraph SourceRegion["Source Region: ap-south-1"]
        SB[Source S3 Bucket]
        SV[Versioning Enabled]
        SE[Default Encryption]
        SB --> SV
        SB --> SE
    end

    subgraph ReplicaRegion["Destination Region: ap-southeast-1"]
        DB[Destination S3 Bucket]
        DV[Versioning Enabled]
        DE[Default Encryption]
        DB --> DV
        DB --> DE
    end

    IAM[Replication IAM Role]
    RC[S3 Replication Configuration]
    KMS[Optional KMS Permissions]
    MON[Replication Metrics]

    TF --> SB
    TF --> DB
    TF --> IAM
    TF --> RC

    IAM --> RC
    RC --> SB
    RC --> DB
    KMS -.-> IAM
    RC --> MON
    SB -. Object Replication .-> DB
```

### Component Responsibilities

| Component | Responsibility |
|---|---|
| Source bucket | Stores original objects and object versions |
| Destination bucket | Stores replicated object versions |
| Versioning | Provides the version history required for replication |
| Replication IAM role | Allows Amazon S3 to assume a role and replicate eligible objects |
| Replication configuration | Defines the rule, prefix filter, destination, and replication behavior |
| KMS configuration | Supports replication of SSE-KMS-encrypted objects when correctly configured |
| Replication metrics | Provides visibility into replication progress and failures |

### Data Flow

1. An application or authorized user uploads an object to the source bucket.
2. S3 creates an object version because versioning is enabled.
3. S3 evaluates the replication rule and its prefix filter.
4. S3 assumes the configured replication IAM role.
5. The role authorizes S3 to read the source object version and write the replica.
6. S3 replicates the eligible object to the destination bucket.
7. Replication metrics provide operational visibility when enabled.

Replication is asynchronous. A successful source upload does not guarantee that the destination object is immediately available.

## Environment Configuration

### AWS Regions

The environment uses two AWS provider configurations:

| Provider | Default Region | Purpose |
|---|---|---|
| `aws` | `ap-south-1` | Source bucket and replication configuration |
| `aws.replica` | `ap-southeast-1` | Destination bucket |

The destination bucket module receives the aliased provider explicitly:

```hcl
providers = {
  aws = aws.replica
}
```

The replication configuration is managed through the source Region's default provider.

### Input Variables

The root module declares the environment configuration in `main.tf`.

| Variable | Example | Purpose |
|---|---|---|
| `aws_region` | `ap-south-1` | Source Region |
| `replica_aws_region` | `ap-southeast-1` | Destination Region |
| `source_account_id` | `123456789012` | AWS account ID owning the source bucket |
| `source_bucket_name` | `your-org-dev-s3-source-documents` | Source bucket name |
| `replica_bucket_name` | `your-org-dev-s3-replica-documents` | Destination bucket name |
| `force_destroy` | `false` | Controls deletion of non-empty buckets |
| `source_kms_key_arn` | `null` | Optional source KMS key ARN |
| `destination_kms_key_arn` | `null` | Optional destination KMS key ARN |
| `replication_role_name` | `dev-s3-replication-role` | Replication IAM role name |
| `replication_filter_prefix` | `""` | Object key prefix selected for replication |
| `replication_enabled` | `true` | Enables or disables the replication rule |
| `destination_storage_class` | `STANDARD` | Storage class for destination replicas |
| `replication_metrics_enabled` | `true` | Enables replication metrics |
| `replication_time_control_enabled` | `false` | Enables Replication Time Control |
| `tags` | Map of strings | Common resource tags |

The `terraform.tfvars.example` file contains example assignments. Copy it to `terraform.tfvars` and replace the placeholders before deployment.

```bash
cp terraform.tfvars.example terraform.tfvars
```

Do not commit environment-specific values that contain sensitive information. Terraform state and plan files can contain sensitive configuration and must be protected accordingly.

### Bucket Naming

S3 bucket names are globally unique within the applicable AWS partition. Choose names that are:

- Globally unique.
- Lowercase and DNS-compatible.
- Environment-specific.
- Meaningful to the owning project or application.

Example:

```hcl
source_bucket_name  = "company-dev-s3-source-documents"
replica_bucket_name = "company-dev-s3-replica-documents"
```

These are examples only. Confirm that the names are available before deployment.

## Prerequisites

Install and configure the following tools:

| Tool | Purpose |
|---|---|
| Terraform | Infrastructure provisioning |
| AWS CLI | Account verification and operational inspection |
| AWS credentials | Authentication for Terraform and AWS API calls |
| Git | Source control |

Use a supported Terraform version satisfying the constraint in `main.tf` and the AWS provider version specified by the root module.

### Verify Terraform

```bash
terraform version
```

### Verify AWS CLI

```bash
aws --version
```

### Verify AWS Identity

```bash
aws sts get-caller-identity
```

Confirm that the returned account ID matches `source_account_id`.

Terraform should authenticate through the standard AWS credential chain, such as:

- AWS CLI profiles.
- Environment-based credentials.
- IAM roles attached to compute environments.
- Web identity credentials.
- CI/CD OIDC federation.

Avoid hardcoding access keys in Terraform files or variable files.

## Remote Terraform State

The environment includes `backend.hcl.example` as a partial S3 backend configuration.

Remote state is important because Terraform state records resource identifiers, attributes, dependencies, and metadata required to manage infrastructure safely.

### Backend Configuration

The example configuration contains:

```hcl
bucket       = "your-org-terraform-state"
key          = "amazon-s3/dev/terraform.tfstate"
region       = "ap-south-1"
encrypt      = true
use_lockfile = true
```

Replace the bucket placeholder with an existing S3 state bucket.

The backend bucket must exist before Terraform initialization. Terraform cannot create the bucket used by its own backend during the same initialization process.

### State Bucket Requirements

The remote state bucket should have:

- Versioning enabled.
- Server-side encryption.
- Block Public Access enabled.
- Restricted IAM access.
- A separate administrative and recovery process.
- Appropriate retention and monitoring controls.

The backend bucket should be managed independently from the S3 infrastructure whose state it stores. This avoids a dependency cycle during initialization and teardown.

### Initialize the Backend

Run initialization from this directory:

```bash
terraform init -backend-config=backend.hcl.example
```

For a customized backend configuration:

```bash
terraform init -backend-config=backend.hcl
```

The backend configuration is read during initialization. If the backend settings change, use `terraform init -reconfigure` or `terraform init -migrate-state` as appropriate.

Do not use `-reconfigure` casually when existing state must be migrated. Confirm the current state location and migration plan first.

## Deployment Workflow

Run all commands from:

```text
06- Deployment/05- Amazon S3/02- Terraform/environments/dev/
```

### Prepare Configuration

Copy the example variable file:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and provide:

- A valid AWS account ID.
- Globally unique source and destination bucket names.
- Appropriate Regions.
- Optional KMS key ARNs.
- Environment-specific tags.

### Initialize Terraform

```bash
terraform init -backend-config=backend.hcl.example
```

Initialization downloads the required provider and configures the backend.

### Format Terraform Files

```bash
terraform fmt -recursive
```

### Validate Configuration

```bash
terraform validate
```

Validation checks Terraform configuration syntax and internal consistency. It does not prove that AWS permissions, resource names, KMS policies, or service-side requirements are correct.

### Review the Execution Plan

```bash
terraform plan -var-file=terraform.tfvars -out=dev.tfplan
```

Inspect the plan before applying it. Pay particular attention to:

- Bucket creation and replacement.
- Versioning configuration.
- Encryption configuration.
- IAM role and policy changes.
- Replication configuration changes.
- Resource destruction.
- Any unexpected changes to existing infrastructure.

Protect the saved plan file because it may contain sensitive values.

### Apply the Plan

```bash
terraform apply dev.tfplan
```

Applying a saved plan executes the reviewed changes. Recreate the plan if configuration or infrastructure changes make it stale.

### Inspect Outputs

```bash
terraform output
```

Individual outputs can be inspected with:

```bash
terraform output source_bucket_id
terraform output replica_bucket_id
terraform output replication_role_arn
terraform output replication_configuration_id
terraform output replication_rule_status
```

## Encryption Configuration

The environment supports optional customer-managed KMS keys.

When both KMS key variables are `null`, the bucket module uses its default encryption configuration.

When SSE-KMS replication is required, configure both:

```hcl
source_kms_key_arn      = "arn:aws:kms:ap-south-1:123456789012:key/source-key-id"
destination_kms_key_arn = "arn:aws:kms:ap-southeast-1:123456789012:key/destination-key-id"
```

The keys must be valid for their respective Regions.

### KMS Requirements

SSE-KMS replication requires more than configuring the bucket encryption settings.

Verify that:

- The source key permits the replication role to decrypt source object data.
- The destination key permits the replication role to encrypt replica data and generate data keys.
- The replication role's IAM policy grants the required KMS actions.
- The KMS key policies authorize the role.
- The source and destination keys are compatible with the selected replication configuration.

An S3 `AccessDenied` response can originate from S3 authorization or KMS authorization. Diagnose both permission layers independently.

Do not place KMS key material or credentials in Terraform configuration.

## Replication Configuration

The environment creates one replication rule through the `s3-replication` module.

### Prefix Filtering

The default empty prefix selects all eligible objects.

To restrict replication to a specific object namespace:

```hcl
replication_filter_prefix = "documents/"
```

The prefix is an object-key filter, not a filesystem directory.

### Destination Storage Class

The default destination storage class is:

```hcl
destination_storage_class = "STANDARD"
```

Select a different supported storage class only after considering retrieval frequency, retrieval charges, minimum storage duration, and availability requirements.

### Delete Marker Replication

The environment explicitly disables delete marker replication:

```hcl
delete_marker_replication_enabled = false
```

This means delete markers are not replicated through this rule. Deleting an object in the source bucket does not necessarily produce the same visible deletion behavior in the destination bucket.

### Replication Metrics

Replication metrics are enabled by default:

```hcl
replication_metrics_enabled = true
```

Metrics help identify replication delays and failed replication operations.

### Replication Time Control

RTC is disabled by default:

```hcl
replication_time_control_enabled = false
```

Enable it only when the workload requires the additional replication-time commitment and the associated cost is acceptable.

RTC requires replication metrics to be enabled. The module validates this relationship.

## Pre-Deployment Checks

Before applying infrastructure changes, verify the following.

| Check | Expected condition |
|---|---|
| AWS identity | Authenticated account matches the intended account |
| Source Region | Correct source Region configured |
| Destination Region | Correct destination Region configured |
| Bucket names | Globally available and valid |
| Backend bucket | Exists and is accessible |
| Backend state | Correct state key and Region |
| IAM permissions | Terraform identity can manage required resources |
| KMS keys | Correct Region and permissions, if configured |
| Versioning | Enabled on both buckets |
| Replication role | Trust policy permits S3 to assume the role |
| Replication rule | Source and destination identifiers are correct |
| Destructive changes | Reviewed before applying |

## Post-Deployment Verification

A successful Terraform apply confirms that Terraform completed the requested resource operations. It does not prove that end-to-end object replication is functioning correctly.

### Verify Source Bucket

```bash
aws s3api get-bucket-versioning \
  --bucket YOUR_SOURCE_BUCKET \
  --region ap-south-1
```

Expected configuration:

```json
{
  "Status": "Enabled"
}
```

### Verify Destination Bucket

```bash
aws s3api get-bucket-versioning \
  --bucket YOUR_REPLICA_BUCKET \
  --region ap-southeast-1
```

Expected configuration:

```json
{
  "Status": "Enabled"
}
```

### Verify Replication Configuration

```bash
aws s3api get-bucket-replication \
  --bucket YOUR_SOURCE_BUCKET \
  --region ap-south-1
```

Inspect:

- Replication role ARN.
- Rule identifier.
- Rule status.
- Prefix filter.
- Destination bucket ARN.
- Destination storage class.
- Metrics configuration.
- RTC configuration, if enabled.

### Test Object Replication

Upload a test object:

```bash
aws s3 cp sample.txt s3://YOUR_SOURCE_BUCKET/verification/sample.txt \
  --region ap-south-1
```

Inspect the source object:

```bash
aws s3api head-object \
  --bucket YOUR_SOURCE_BUCKET \
  --key verification/sample.txt \
  --region ap-south-1
```

Inspect the destination object after replication has had time to complete:

```bash
aws s3api head-object \
  --bucket YOUR_REPLICA_BUCKET \
  --key verification/sample.txt \
  --region ap-southeast-1
```

Check the `ReplicationStatus` field where applicable. For a replicated destination object, the status is typically `REPLICA`.

Replication is asynchronous. Allow time for processing and investigate replication status or metrics if the object does not appear.

### Verify Terraform State

```bash
terraform state list
```

Review the managed resources and ensure they correspond to the intended development infrastructure.

## Operational Considerations

### Replication Is Not Immediate

CRR is asynchronous. Applications that require read-after-write behavior against the destination must account for replication delay.

Do not treat the destination bucket as a synchronously consistent copy of the source.

### Existing Objects

A replication rule generally applies to eligible objects created after the rule is configured. Existing objects require a separate backfill mechanism, such as S3 Batch Replication.

### Cross-Account Replication

The current environment example uses the source account ID and does not configure a separate destination account ID.

For a cross-account destination, additional configuration is required, including:

- Destination bucket policy permissions for the replication role.
- Appropriate destination account ownership behavior.
- KMS key policy permissions, if SSE-KMS is used.
- Explicit destination account configuration where required by the replication module interface.

Do not assume that configuring a destination bucket ARN alone is sufficient for cross-account replication.

### Versioning

Both source and destination buckets must have versioning enabled for replication.

Avoid suspending versioning while replication is active. Review the impact on existing versions and replication behavior before changing it.

### Replication Is Not Regional Failover

Replication provides asynchronous object copying. It does not automatically provide:

- Application traffic failover.
- DNS failover.
- Database replication.
- Cross-Region application deployment.
- Recovery orchestration.
- Guaranteed immediate destination availability.

A complete disaster recovery design requires application-level recovery procedures and tested recovery objectives.

### Terraform State Protection

Treat Terraform state as sensitive operational data.

Recommended controls:

- Restrict state bucket access to authorized deployment identities.
- Enable versioning on the state bucket.
- Encrypt state objects.
- Use native S3 state locking.
- Keep state separate from the infrastructure managed by this environment.
- Protect plan files and state backups.
- Avoid concurrent operations that bypass Terraform locking.

## Troubleshooting

### Terraform Cannot Access the Backend

**Symptoms:** `terraform init` fails with S3 access or backend configuration errors.

Check:

```bash
aws sts get-caller-identity
aws s3api head-bucket --bucket YOUR_TERRAFORM_STATE_BUCKET
```

Verify:

- Backend bucket exists.
- Backend Region is correct.
- IAM permissions allow state access.
- The configured key is correct.
- The identity has the required permissions for state locking when `use_lockfile` is enabled.

### Bucket Name Already Exists

**Symptoms:** Bucket creation fails because the requested name is unavailable.

S3 bucket names are globally unique. Change the corresponding value in `terraform.tfvars` and generate a new plan.

### Replication Configuration Fails

**Symptoms:** Terraform cannot create or update the replication configuration.

Check:

- Source bucket versioning is enabled.
- Destination bucket versioning is enabled.
- The IAM role trust policy permits S3 to assume the role.
- The replication policy grants required source and destination actions.
- The destination bucket and Region are correct.
- KMS permissions and key policies are correct when using SSE-KMS.
- No other Terraform resource manages the same source bucket replication configuration.

### Destination Object Is Missing

**Symptoms:** The source object exists, but the replica is not visible.

Check:

1. Whether the object matches the configured prefix filter.
2. Whether the replication rule is enabled.
3. Whether the object was created after replication was configured.
4. Whether the source object is eligible for replication.
5. Whether the replication role has the required permissions.
6. Whether destination bucket or KMS policies deny the operation.
7. Replication status and metrics.

Use S3 Batch Replication for eligible existing objects that require backfill.

### KMS Access Denied

**Symptoms:** Replication of SSE-KMS-encrypted objects fails.

Check the IAM policy attached to the replication role and the key policies for both KMS keys.

Verify source decrypt permissions and destination encryption permissions independently. An IAM allow does not automatically override a restrictive KMS key policy.

### Terraform Reports Resource Conflicts

**Symptoms:** Terraform reports that a bucket configuration is already managed or conflicts with another resource.

Identify the existing resource owner before changing configuration.

For S3 bucket configuration resources, avoid managing the same configuration through multiple Terraform resources or modules. In particular, only one resource should own a bucket's replication configuration.

Do not resolve conflicts by deleting existing state entries without first understanding the actual AWS resource and Terraform ownership.

## Updating the Environment

For normal infrastructure changes:

1. Update the relevant input values or module configuration.
2. Run `terraform fmt`.
3. Run `terraform validate`.
4. Generate a new execution plan.
5. Review resource replacement and deletion behavior.
6. Apply the reviewed plan.
7. Verify the resulting AWS configuration.

For module changes, review the module interface and all environments that consume it before applying the change.

Avoid making manual changes to Terraform-managed resources. If emergency manual changes are necessary, reconcile them through a reviewed Terraform plan.

## Destroying Development Infrastructure

Destroying this environment can delete buckets and their contents if `force_destroy` is enabled.

The default is:

```hcl
force_destroy = false
```

Keep this setting unless destructive cleanup is explicitly intended.

Review the planned destruction:

```bash
terraform plan -destroy -var-file=terraform.tfvars
```

Destroy only after confirming that:

- Required objects have been backed up or retained.
- Replication is no longer required.
- No application depends on either bucket.
- The destination contains no data that must be preserved.
- The Terraform state is accessible and recoverable.

Execute:

```bash
terraform destroy -var-file=terraform.tfvars
```

If a bucket contains objects or versions, Terraform may be unable to delete it while `force_destroy` is false. Handle data retention and deletion deliberately rather than enabling destructive cleanup as a workaround.

Do not destroy the remote Terraform state bucket as part of this environment cleanup. It is an independently managed dependency.

## Best Practices

- Keep environment-specific values in `terraform.tfvars`, not shared module source.
- Use globally unique, environment-specific bucket names.
- Keep source and destination bucket versioning enabled.
- Keep bucket encryption enabled and configure KMS deliberately.
- Use least-privilege IAM policies for Terraform and replication roles.
- Protect the remote state bucket independently.
- Use S3 native state locking to prevent concurrent state modifications.
- Review every Terraform plan before applying it.
- Keep `force_destroy` disabled by default.
- Monitor replication metrics and investigate persistent failures.
- Test object replication with actual uploads rather than relying only on Terraform outputs.
- Use S3 Batch Replication when existing objects need to be replicated.
- Treat replication as asynchronous data protection, not automatic application failover.
- Avoid multiple Terraform owners for the same bucket configuration.

## Key Takeaways

- The development environment composes reusable S3 bucket and replication modules across two AWS Regions.
- Both buckets require versioning, and replication depends on correctly configured IAM and, when applicable, KMS permissions.
- Remote Terraform state should use an independently managed, encrypted, versioned S3 bucket with native state locking.
- Terraform deployment success does not establish end-to-end replication success; verify with actual objects and replication status.
- Cross-Region Replication is asynchronous and must not be mistaken for a complete disaster recovery or application failover solution.