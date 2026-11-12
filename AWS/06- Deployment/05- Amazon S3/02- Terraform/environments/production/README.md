# README

## Overview

This directory contains the Terraform root configuration for deploying the production Amazon S3 environment.

The deployment provisions:

- A production source S3 bucket.
- A replica S3 bucket in a separate AWS Region.
- Versioning on both buckets.
- Server-side encryption configuration.
- An IAM role and policy for S3 replication.
- A cross-Region replication configuration.
- Replication metrics and optional Replication Time Control (RTC).

The configuration reuses the shared Terraform modules under `modules/` and keeps production-specific settings isolated from development and staging.

Production deployments require stricter change control, access management, resource protection, and operational verification than non-production environments.

## Directory Structure

```text
production/
├── main.tf
├── terraform.tfvars.example
├── backend.hcl.example
└── README.md
```

The shared modules are located outside the environment directory:

```text
02- Terraform/
├── modules/
│   ├── s3-bucket/
│   └── s3-replication/
└── environments/
    ├── dev/
    ├── staging/
    └── production/
```

`main.tf` contains the Terraform version requirements, provider configurations, input variables, module declarations, local values, and outputs.

## Architecture

The production environment uses Cross-Region Replication (CRR) to maintain a replica of eligible objects in a separate AWS Region.

```mermaid
flowchart TB
    TF[Terraform Production Configuration]

    subgraph Source["Source Region: ap-south-1"]
        SB[Production Source Bucket]
        SV[Versioning]
        SE[Server-Side Encryption]
        IAM[IAM Replication Role]
        RC[Replication Configuration]

        SB --> SV
        SB --> SE
        IAM --> RC
        SV --> RC
    end

    subgraph Destination["Replica Region: ap-southeast-1"]
        RB[Production Replica Bucket]
        RV[Versioning]
        RE[Server-Side Encryption]

        RB --> RV
        RB --> RE
    end

    TF --> SB
    TF --> RB
    TF --> IAM
    RC -->|Asynchronous replication| RB
```

### Component Responsibilities

| Component | Responsibility |
|---|---|
| Source bucket | Stores production objects |
| Replica bucket | Stores replicated object versions |
| Versioning | Enables object-level replication |
| Encryption | Protects stored objects |
| IAM replication role | Provides S3 with replication permissions |
| Replication configuration | Defines which objects are replicated and where |
| Replication metrics | Exposes replication progress and failure indicators |
| Terraform remote state | Maintains deployment state independently of the environment |

Replication is asynchronous. It does not provide synchronous writes, automatic application failover, or guaranteed immediate consistency between Regions.

## Environment Configuration

### AWS Regions

The default configuration uses:

| Setting | Default |
|---|---|
| Source Region | `ap-south-1` |
| Replica Region | `ap-southeast-1` |
| Environment | `production` |
| Source versioning | Enabled |
| Replica versioning | Enabled |
| Replication | Enabled |
| Replication metrics | Enabled |
| Replication Time Control | Disabled |
| Force destroy | Disabled |
| Destination storage class | `STANDARD` |

Change the Regions only after evaluating service availability, data residency requirements, latency, recovery objectives, and cost.

### Required Inputs

The following variables must be supplied before deployment:

| Variable | Description |
|---|---|
| `source_account_id` | AWS account ID that owns the source bucket |
| `source_bucket_name` | Globally unique source bucket name |
| `replica_bucket_name` | Globally unique replica bucket name |

The example variable file contains placeholders. Replace them with actual production values before deployment.

### Optional Configuration

| Variable | Default | Purpose |
|---|---|---|
| `source_kms_key_arn` | `null` | Customer-managed KMS key for source encryption |
| `destination_kms_key_arn` | `null` | Customer-managed KMS key for replica encryption |
| `replication_filter_prefix` | `""` | Limits replication to a key prefix |
| `destination_storage_class` | `STANDARD` | Storage class for replicated objects |
| `replication_metrics_enabled` | `true` | Enables replication metrics |
| `replication_time_control_enabled` | `false` | Enables the 15-minute replication SLA for eligible objects |
| `force_destroy` | `false` | Controls deletion of non-empty buckets |

Keep `force_destroy` disabled in production. Bucket deletion should be an explicitly approved operation with a verified data-retention and recovery plan.

## Prerequisites

### Terraform

Install Terraform and verify the executable:

```bash
terraform version
```

The root configuration declares Terraform `>= 1.5.0`. However, the S3 backend configuration uses native S3 state locking through `use_lockfile`, which requires Terraform 1.10 or later.

Use Terraform 1.10 or later for this deployment.

### AWS CLI

Install the AWS CLI and configure an approved production authentication method.

Verify the active identity:

```bash
aws sts get-caller-identity
```

Confirm that the returned account ID matches the intended production account.

Do not deploy using personal IAM user access keys or credentials shared between environments. Prefer an approved IAM role, IAM Identity Center, or CI/CD OIDC federation with short-lived credentials.

### AWS Permissions

The deployment identity requires permissions to manage the resources declared by the shared modules, including:

- S3 bucket creation and configuration.
- S3 versioning and encryption configuration.
- S3 public-access and ownership controls.
- IAM role and policy creation.
- S3 replication configuration.
- Required read operations for Terraform planning and state refresh.
- KMS operations when customer-managed keys are configured.

Use a dedicated deployment role with narrowly scoped permissions. Do not grant unrestricted administrator permissions merely to make Terraform deployment succeed.

### Pre-existing Terraform State Bucket

The remote state bucket must exist before Terraform initialization.

The state bucket should have:

- Versioning enabled.
- Server-side encryption enabled.
- Block Public Access enabled.
- Restricted access to approved deployment identities.
- Appropriate retention and recovery controls.
- Monitoring and audit logging.

The state bucket should be managed independently from this production deployment. Do not use the production source or replica bucket as the Terraform state bucket.

## Configuration

### Prepare the Variable File

Copy the example file:

```bash
cp terraform.tfvars.example terraform.tfvars
```

On Windows PowerShell:

```powershell
Copy-Item terraform.tfvars.example terraform.tfvars
```

Update the required values:

```hcl
aws_region         = "ap-south-1"
replica_aws_region = "ap-southeast-1"

source_account_id = "123456789012"

source_bucket_name  = "your-org-production-s3-source-documents"
replica_bucket_name = "your-org-production-s3-replica-documents"
```

Review the remaining settings before deployment.

Do not commit `terraform.tfvars` if it contains account-specific configuration or sensitive infrastructure details. Add it to the repository's `.gitignore` where appropriate.

### Configure Customer-Managed KMS Keys

When using SSE-KMS, configure both key ARNs:

```hcl
source_kms_key_arn      = "arn:aws:kms:ap-south-1:123456789012:key/SOURCE-KEY-ID"
destination_kms_key_arn = "arn:aws:kms:ap-southeast-1:123456789012:key/DESTINATION-KEY-ID"
```

The replication role needs the appropriate identity-based permissions and authorization through both KMS key policies.

Verify that:

- The source key is available in the source Region.
- The destination key is available in the replica Region.
- The replication role can decrypt source objects.
- The replication role can encrypt destination objects.
- The destination bucket encryption configuration is compatible with the replication rule.

KMS permissions are separate from S3 object permissions. A successful S3 authorization check does not guarantee that the KMS operation will succeed.

## Remote State Configuration

The `backend.hcl.example` file contains the partial S3 backend configuration.

Copy it before initialization:

```bash
cp backend.hcl.example backend.hcl
```

Replace the state bucket placeholder with the name of the existing remote state bucket.

The production state key is:

```text
amazon-s3/production/terraform.tfstate
```

This isolates production state from development and staging.

Initialize Terraform:

```bash
terraform init -backend-config=backend.hcl
```

For an existing local state that must be migrated, review the migration plan carefully before confirming Terraform's migration prompt.

Do not copy state files manually between environments. Use Terraform's supported state migration workflow.

## Deployment Workflow

Production infrastructure changes should follow a controlled deployment process.

```mermaid
flowchart TD
    A[Update Terraform Configuration] --> B[Review Variable Values]
    B --> C[terraform fmt -check]
    C --> D[terraform init]
    D --> E[terraform validate]
    E --> F[terraform plan]
    F --> G{Plan Approved?}
    G -->|No| H[Revise Configuration]
    H --> C
    G -->|Yes| I[terraform apply]
    I --> J[Verify AWS Resources]
    J --> K[Verify Replication]
    K --> L[Record Deployment Evidence]
```

### Initialize Terraform

```bash
terraform init -backend-config=backend.hcl
```

### Format the Configuration

```bash
terraform fmt -check -recursive
```

To apply formatting:

```bash
terraform fmt -recursive
```

### Validate the Configuration

```bash
terraform validate
```

### Review the Deployment Plan

```bash
terraform plan \
  -var-file=terraform.tfvars \
  -out=production.tfplan
```

Review the plan before applying it.

Pay particular attention to:

- Bucket creation, replacement, or deletion.
- Changes to versioning.
- Encryption configuration changes.
- IAM policy modifications.
- Replication rule changes.
- KMS key changes.
- Resource replacement and destructive actions.
- Changes to remote state configuration.

A production plan should be reviewed and approved by an authorized engineer before execution.

### Apply the Approved Plan

```bash
terraform apply production.tfplan
```

Use the saved plan that was reviewed. If the configuration or state changes after planning, generate and review a new plan.

### Inspect Outputs

```bash
terraform output
```

Inspect individual outputs:

```bash
terraform output source_bucket_arn
terraform output replica_bucket_arn
terraform output replication_role_arn
terraform output replication_configuration_id
terraform output replication_rule_status
```

Treat infrastructure outputs as operational information. Avoid publishing sensitive values in unrestricted CI logs.

## Production Deployment Controls

Production infrastructure should use controlled changes rather than ad hoc local execution.

Recommended controls:

- Require pull-request review for Terraform changes.
- Run formatting and validation in CI.
- Generate and review deployment plans.
- Restrict production apply permissions.
- Use short-lived CI/CD credentials through OIDC federation.
- Require approval before production deployment.
- Preserve deployment logs and plan artifacts according to organizational policy.
- Keep Terraform state access restricted.
- Maintain a documented rollback and recovery procedure.

Do not allow development or staging deployment identities to modify production state or resources.

## Post-Deployment Verification

A successful Terraform apply confirms that Terraform completed its requested operations. It does not prove that the application-level replication workflow is functioning correctly.

Verify each component independently.

### Verify Source Bucket

```bash
aws s3api head-bucket \
  --bucket your-org-production-s3-source-documents \
  --region ap-south-1
```

Inspect versioning:

```bash
aws s3api get-bucket-versioning \
  --bucket your-org-production-s3-source-documents \
  --region ap-south-1
```

Expected versioning status:

```json
{
  "Status": "Enabled"
}
```

Inspect encryption:

```bash
aws s3api get-bucket-encryption \
  --bucket your-org-production-s3-source-documents \
  --region ap-south-1
```

### Verify Replica Bucket

```bash
aws s3api head-bucket \
  --bucket your-org-production-s3-replica-documents \
  --region ap-southeast-1
```

Inspect versioning:

```bash
aws s3api get-bucket-versioning \
  --bucket your-org-production-s3-replica-documents \
  --region ap-southeast-1
```

Inspect encryption:

```bash
aws s3api get-bucket-encryption \
  --bucket your-org-production-s3-replica-documents \
  --region ap-southeast-1
```

### Verify Replication Configuration

```bash
aws s3api get-bucket-replication \
  --bucket your-org-production-s3-source-documents \
  --region ap-south-1
```

Confirm:

- The replication role ARN is correct.
- The destination bucket ARN is correct.
- The replication rule is enabled.
- The prefix filter matches the intended objects.
- The destination storage class is correct.
- Delete-marker replication behavior matches the intended policy.
- KMS replication settings are correct when SSE-KMS is used.
- Metrics and RTC settings match the approved design.

### Verify IAM Role

```bash
aws iam get-role \
  --role-name production-s3-replication-role
```

Inspect the attached inline replication policy:

```bash
aws iam get-role-policy \
  --role-name production-s3-replication-role \
  --policy-name production-s3-replication-policy
```

Use the actual policy name generated by the replication module if it differs from the example.

## Replication Verification

Replication is asynchronous. A successful Terraform deployment does not guarantee that an object has already reached the destination bucket.

Upload a test object using a controlled test prefix:

```bash
aws s3 cp ./replication-test.txt \
  s3://your-org-production-s3-source-documents/replication-verification/replication-test.txt \
  --region ap-south-1
```

Inspect the source object's replication status:

```bash
aws s3api head-object \
  --bucket your-org-production-s3-source-documents \
  --key replication-verification/replication-test.txt \
  --region ap-south-1
```

The `ReplicationStatus` field indicates the replication state when available.

Verify the destination object:

```bash
aws s3api head-object \
  --bucket your-org-production-s3-replica-documents \
  --key replication-verification/replication-test.txt \
  --region ap-southeast-1
```

Do not assume that an object is replicated immediately after upload. Allow for asynchronous processing and investigate persistent `FAILED` or `PENDING` states.

### Existing Objects

A newly created replication rule does not automatically replicate all existing objects.

Use S3 Batch Replication when historical objects must be replicated. Plan the required inventory, permissions, job configuration, monitoring, and associated costs separately.

## Monitoring and Operational Readiness

Production replication requires continuous monitoring.

Monitor:

- Replication latency.
- Pending replication bytes.
- Pending operations.
- Failed replication operations.
- Replication rule status.
- Destination object availability.
- KMS authorization failures.
- IAM and bucket-policy changes.
- Storage growth in both Regions.

When replication metrics are enabled, use CloudWatch replication metrics to detect delayed or failed replication.

Replication Time Control provides a 15-minute SLA for eligible objects when configured. It is an additional paid capability and should be enabled only when justified by recovery requirements.

Replication metrics and RTC do not replace application-level integrity checks or disaster recovery testing.

## Security Considerations

### Bucket Access

Both buckets should remain private.

Verify:

- S3 Block Public Access is enabled.
- Bucket ownership controls enforce the intended ownership model.
- ACLs are not used unless explicitly required.
- Bucket policies follow least privilege.
- Only approved application and deployment roles can access objects.
- TLS is enforced for requests where required by the security baseline.

### IAM

The replication role should be assumed only by Amazon S3 through its trust policy.

Review the trust policy and permission policy whenever the replication architecture changes.

Avoid broad permissions such as unrestricted `s3:*` or `kms:*` unless a documented requirement justifies them.

### KMS

For SSE-KMS replication:

- Use customer-managed keys when organizational requirements demand them.
- Restrict key administration and usage permissions.
- Authorize the replication role in the relevant key policies.
- Monitor KMS access-denied events.
- Plan key rotation and key retirement carefully.

Disabling or deleting a KMS key can make encrypted objects inaccessible even when the S3 objects still exist.

## Cross-Account Considerations

The current production root configuration is designed for source and replica buckets in the same AWS account.

The replication module does not receive a `destination_account_id` value from this root configuration, and this environment does not provision a destination bucket policy for cross-account replication.

For a cross-account design, explicitly configure:

- Destination account ownership.
- Destination bucket policy permissions for the source replication role.
- Required IAM role permissions.
- KMS key policies and grants where applicable.
- Object ownership behavior.
- Provider authentication and deployment permissions in both accounts.

Do not assume that changing the destination bucket ARN alone enables cross-account replication.

## Lifecycle Management

The production root configuration currently passes an empty lifecycle rule list to both bucket modules:

```hcl
lifecycle_rules = []
```

This avoids having two Terraform resources manage the same bucket lifecycle configuration.

If lifecycle management is introduced, use the dedicated `s3-lifecycle` module and ensure that only one Terraform resource owns the complete lifecycle configuration for each bucket.

Before applying lifecycle policies in production, review:

- Current and noncurrent version expiration.
- Retention requirements.
- Legal holds and Object Lock requirements.
- Storage-class transition timing.
- Incomplete multipart upload cleanup.
- Replication and recovery dependencies.

Lifecycle expiration can permanently remove data when versioning and retention controls are not designed correctly.

## Common Deployment Issues

| Problem | Likely Cause | Recommended Action |
|---|---|---|
| `AccessDenied` during apply | Deployment role lacks required permissions | Review IAM permissions and explicit denies |
| Bucket name conflict | S3 bucket names are globally unique | Choose a different name |
| Replication configuration rejected | Source or destination versioning is disabled | Enable versioning on both buckets |
| Replication role cannot be assumed | Incorrect IAM trust policy | Verify the S3 service principal and trust conditions |
| Objects are not replicated | Rule filter, IAM, KMS, or destination policy issue | Inspect object status and replication configuration |
| SSE-KMS replication fails | Missing KMS key authorization | Review identity policies and both key policies |
| Terraform state lock error | Another deployment holds the lock | Identify the active operation before taking recovery action |
| State bucket unavailable | Incorrect backend bucket, Region, or permissions | Verify backend configuration and AWS identity |
| Bucket deletion fails | Non-empty or versioned bucket | Follow an approved retention and cleanup process |

Never use `terraform force-unlock` without confirming that the lock belongs to a stale operation. Removing an active lock can allow concurrent state modifications.

## Drift Detection and Change Management

Run a plan periodically to identify infrastructure drift:

```bash
terraform plan \
  -var-file=terraform.tfvars
```

Investigate differences between Terraform state and actual AWS configuration.

Common sources of drift include:

- Manual bucket policy changes.
- Console modifications to encryption or versioning.
- IAM policy changes.
- Replication rule modifications.
- Changes made by other automation.

Do not blindly apply a plan that reverses an intentional security or operational change. Determine the source of the drift, update the Terraform configuration when appropriate, and obtain the required approval.

For resources created outside Terraform, evaluate `terraform import` or import blocks before attempting to recreate them.

## Production Change and Recovery Strategy

Production changes should be small, reviewed, and reversible where possible.

Before changing replication, encryption, or bucket configuration:

1. Review the current Terraform state and AWS configuration.
2. Confirm backup, versioning, and recovery requirements.
3. Generate a Terraform plan.
4. Review destructive actions and resource replacements.
5. Obtain production approval.
6. Apply the approved plan.
7. Verify the resulting AWS configuration.
8. Test the relevant object workflow.
9. Record deployment evidence.

Terraform rollback is not equivalent to data recovery. Reverting a Terraform configuration does not restore deleted object versions or reverse all changes to stored data.

For data recovery, use the appropriate versioning, replication, backup, and recovery procedures.

## Destruction and Resource Protection

Production buckets contain potentially critical data. Destruction must be treated as a controlled operational event.

The default configuration keeps:

```hcl
force_destroy = false
```

This prevents Terraform from automatically emptying non-empty buckets during deletion.

Before any destruction:

- Obtain explicit approval.
- Confirm data retention and legal requirements.
- Verify recovery copies and backup availability.
- Review all object versions and delete markers.
- Confirm replication dependencies.
- Confirm no application or service still depends on the buckets.
- Review the Terraform destroy plan.

Generate a destruction plan:

```bash
terraform plan \
  -destroy \
  -var-file=terraform.tfvars
```

Do not apply a production destruction plan without an approved decommissioning procedure.

For normal production operation, prefer targeted configuration changes over destroying and recreating buckets.

## Production Readiness Checklist

### Infrastructure

- [ ] Production AWS account and Regions verified.
- [ ] Source and replica bucket names approved.
- [ ] Remote state bucket exists independently.
- [ ] Remote state encryption and versioning verified.
- [ ] State locking enabled.
- [ ] Terraform version meets backend requirements.
- [ ] Provider and module versions reviewed.
- [ ] Production plan reviewed and approved.

### Security

- [ ] Production deployment identity uses short-lived credentials.
- [ ] IAM permissions follow least privilege.
- [ ] Both buckets have Block Public Access enabled.
- [ ] Bucket ownership controls are configured.
- [ ] Encryption configuration verified.
- [ ] KMS key policies reviewed when applicable.
- [ ] Replication role trust and permissions reviewed.
- [ ] State access restricted to authorized identities.

### Reliability and Recovery

- [ ] Versioning enabled on both buckets.
- [ ] Replication rule enabled.
- [ ] Replication filter reviewed.
- [ ] Destination storage class approved.
- [ ] Replication metrics enabled.
- [ ] RTC decision documented.
- [ ] Existing-object replication requirements evaluated.
- [ ] Recovery objectives documented.
- [ ] Recovery procedure tested.

### Operations

- [ ] CloudWatch monitoring configured.
- [ ] Replication failure alerts configured.
- [ ] Deployment logs retained.
- [ ] Drift detection process established.
- [ ] Destructive operations require approval.
- [ ] Operational ownership and escalation paths documented.

## Key Takeaways

- Keep production Terraform state isolated, encrypted, versioned, and protected with native S3 state locking.
- Use versioned source and destination buckets, least-privilege replication permissions, and correctly authorized KMS keys.
- Treat Cross-Region Replication as asynchronous data protection, not automatic application failover or a substitute for backup testing.
- Require reviewed Terraform plans, controlled production approvals, and independent post-deployment verification.
- Protect production data with explicit retention, recovery, and destruction procedures; never rely on Terraform rollback as a data-recovery mechanism.