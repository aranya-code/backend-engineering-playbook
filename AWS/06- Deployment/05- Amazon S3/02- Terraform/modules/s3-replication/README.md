# README

## Overview

The `s3-replication` module provisions and manages Amazon S3 Cross-Region Replication (CRR) for an existing source bucket and destination bucket.

It creates the IAM role and permissions required by the S3 replication service, then configures a replication rule on the source bucket. The module supports:

- Prefix-based object filtering.
- Configurable replication rule status.
- Destination storage-class selection.
- Optional delete-marker replication.
- Optional SSE-KMS replication configuration.
- Replication metrics.
- S3 Replication Time Control (RTC).
- IAM trust-policy restrictions using the source account and source bucket ARN.

The module is designed to be composed with bucket-provisioning modules or existing S3 buckets. It does not create or configure the source and destination buckets themselves.

Replication is asynchronous. It improves regional data availability and supports disaster recovery designs, but does not independently provide application failover or guarantee immediate destination consistency.

## Module Structure

```text
s3-replication/
├── main.tf
├── variables.tf
├── outputs.tf
└── README.md
```

| File | Responsibility |
|---|---|
| `main.tf` | IAM role, IAM policy, and S3 replication configuration |
| `variables.tf` | Module input contracts and validation |
| `outputs.tf` | Replication role, configuration, and destination details |
| `README.md` | Usage, architecture, requirements, and operational guidance |

## Architecture

```mermaid
flowchart TB
    subgraph SOURCE["Source AWS Region"]
        SB["Source S3 Bucket"]
        SV["Source Bucket Versioning"]
        RC["S3 Replication Configuration"]
    end

    subgraph IAM["Source AWS Account"]
        ROLE["IAM Replication Role"]
        POLICY["Replication IAM Policy"]
    end

    subgraph DESTINATION["Destination AWS Region"]
        DB["Destination S3 Bucket"]
        DV["Destination Bucket Versioning"]
        KMS["Destination KMS Key (Optional)"]
    end

    SB --> SV
    SV --> RC
    RC -->|"S3 assumes role"| ROLE
    ROLE --> POLICY
    POLICY -->|"Read eligible versions"| SB
    POLICY -->|"Replicate objects"| DB
    DB --> DV
    KMS -.->|"Encrypt replicas"| DB
```

### Responsibility Boundaries

| Component | Managed by this module? | Responsibility |
|---|---:|---|
| Source S3 bucket | No | Stores original objects |
| Destination S3 bucket | No | Stores replicated objects |
| Source versioning | No | Enables replication of object versions |
| Destination versioning | No | Satisfies replication requirements |
| IAM replication role | Yes | Allows S3 to assume a dedicated role |
| IAM replication policy | Yes | Grants source read and destination replication permissions |
| Replication configuration | Yes | Defines the replication rule and destination |
| Destination bucket policy | No | Required for applicable cross-account configurations |
| KMS keys and key policies | No | Must authorize the replication role when SSE-KMS is used |

The caller remains responsible for provisioning and securing both buckets and their encryption keys.

## Prerequisites

Before using the module, ensure that:

- The source bucket exists.
- The destination bucket exists.
- Both buckets have versioning enabled.
- The destination bucket is in the intended destination Region.
- The source and destination bucket ARNs are correct.
- The deployment identity can create IAM roles and policies.
- The deployment identity can configure replication on the source bucket.
- KMS keys and key policies are configured when SSE-KMS is used.

The module does not enable bucket versioning automatically. Manage versioning through the bucket module or existing infrastructure before configuring replication.

## Module Inputs

The module exposes the following inputs.

### Bucket and Account Inputs

| Variable | Description |
|---|---|
| `source_bucket_id` | Source bucket identifier |
| `source_bucket_arn` | Source bucket ARN |
| `source_account_id` | AWS account ID owning the source bucket and replication role |
| `destination_bucket_arn` | Destination bucket ARN |
| `destination_account_id` | Optional destination account ID for cross-account scenarios |

The source account ID is used to constrain the IAM trust relationship.

For cross-account replication, the destination account must separately authorize the replication role through its destination bucket policy and applicable KMS key policies.

### IAM and Rule Inputs

| Variable | Description |
|---|---|
| `replication_role_name` | Name of the IAM replication role |
| `replication_rule_id` | Replication rule identifier |
| `replication_rule_priority` | Rule priority |
| `replication_enabled` | Enables or disables the replication rule |

Use stable role and rule names to make infrastructure changes predictable.

### Filtering and Destination Inputs

| Variable | Description |
|---|---|
| `replication_filter_prefix` | Prefix used to select eligible objects |
| `delete_marker_replication_enabled` | Controls delete-marker replication |
| `destination_storage_class` | Storage class used for replicated objects |

An empty prefix selects all eligible objects.

For example:

```hcl
replication_filter_prefix = "documents/"
```

This selects object keys beginning with `documents/`.

### Encryption Inputs

| Variable | Description |
|---|---|
| `source_kms_key_arn` | Optional source KMS key ARN |
| `destination_kms_key_arn` | Optional destination KMS key ARN |

When source objects use SSE-KMS, configure the destination KMS key and ensure that the replication role is authorized to use both keys.

The module adds the relevant KMS permissions to its IAM policy and configures the replication rule for SSE-KMS-encrypted source objects.

IAM permissions alone do not guarantee KMS access. The KMS key policies must also authorize the required operations.

### Monitoring Inputs

| Variable | Description |
|---|---|
| `metrics_enabled` | Enables replication metrics |
| `replication_metrics_event_threshold_minutes` | Replication metrics event threshold |
| `replication_time_control_enabled` | Enables S3 Replication Time Control |

The configured metrics event threshold is 15 minutes.

RTC requires replication metrics to be enabled. RTC adds cost and should be enabled only when the workload requires its replication commitment.

### Tags

The `tags` map applies tags to supported IAM resources managed by the module.

Bucket tags remain the responsibility of the bucket-provisioning layer.

## IAM Permissions

The module creates a dedicated IAM role trusted by the S3 service.

### Trust Policy

The trust policy allows:

```text
s3.amazonaws.com
```

to assume the role using `sts:AssumeRole`.

It includes conditions for:

- `aws:SourceAccount`
- `aws:SourceArn`

These conditions constrain role assumption to the expected source account and source bucket.

### Replication Permissions

The module grants source bucket permissions for:

| Permission | Purpose |
|---|---|
| `s3:GetReplicationConfiguration` | Read the source replication configuration |
| `s3:ListBucket` | List source bucket contents |
| `s3:GetObjectVersionForReplication` | Read source object versions for replication |
| `s3:GetObjectVersionAcl` | Read source object version ACL information |
| `s3:GetObjectVersionTagging` | Read source object version tags |

Destination permissions include:

| Permission | Purpose |
|---|---|
| `s3:ReplicateObject` | Replicate object versions |
| `s3:ReplicateDelete` | Replicate eligible delete operations |
| `s3:ReplicateTags` | Replicate object tags |

When KMS keys are configured, the module also adds the corresponding source decryption and destination encryption permissions to the IAM policy.

Review the generated policy against the organization's IAM standards and the exact replication features enabled.

## Usage

The module expects existing source and destination buckets.

A typical root-module composition uses a bucket module for each Region and then passes their outputs into the replication module.

```hcl
module "source_bucket" {
  source = "../../modules/s3-bucket"

  bucket_name       = var.source_bucket_name
  versioning_enabled = true

  lifecycle_rules = []

  tags = var.tags
}

module "destination_bucket" {
  source = "../../modules/s3-bucket"

  providers = {
    aws = aws.destination
  }

  bucket_name       = var.destination_bucket_name
  versioning_enabled = true

  lifecycle_rules = []

  tags = var.tags
}

module "s3_replication" {
  source = "../../modules/s3-replication"

  source_bucket_id  = module.source_bucket.bucket_id
  source_bucket_arn = module.source_bucket.bucket_arn
  source_account_id = var.source_account_id

  destination_bucket_arn = module.destination_bucket.bucket_arn

  replication_role_name = "application-s3-replication-role"
  replication_rule_id   = "application-replication-rule"
  replication_rule_priority = 1

  replication_enabled = true

  replication_filter_prefix = "documents/"

  delete_marker_replication_enabled = false

  destination_storage_class = "STANDARD"

  source_kms_key_arn      = null
  destination_kms_key_arn = null

  metrics_enabled = true

  replication_time_control_enabled = false

  tags = var.tags

  depends_on = [
    module.source_bucket,
    module.destination_bucket
  ]
}
```

The example assumes that:

- `aws.destination` is configured for the destination Region.
- Both bucket modules enable versioning.
- Both buckets are managed by the same Terraform root configuration.
- The destination bucket is in the same AWS account.
- SSE-S3 is used for this example.

For production deployments, use environment-specific variables and a remote Terraform backend.

### Important Lifecycle Ownership Rule

The replication module owns the source bucket's complete replication configuration through one `aws_s3_bucket_replication_configuration` resource.

Do not configure another replication resource or module for the same source bucket. S3 replication configuration is a bucket-level configuration, and competing Terraform resources can overwrite or conflict with one another.

## Cross-Account Replication

The module can be used as part of a cross-account design, but the destination account must independently authorize replication.

The destination bucket policy must grant the source replication role the required permissions.

At a minimum, review the destination permissions needed for:

- `s3:ReplicateObject`
- `s3:ReplicateDelete`
- `s3:ReplicateTags`

The exact policy must match the replication features and ownership model being deployed.

When SSE-KMS is used, the destination KMS key policy must also authorize the source replication role to perform the required encryption operations.

Do not assume that passing a destination bucket ARN is sufficient to complete cross-account authorization.

## SSE-KMS Replication

SSE-KMS introduces an additional authorization boundary.

```mermaid
sequenceDiagram
    participant S3 as S3 Replication Service
    participant IAM as Replication IAM Role
    participant SK as Source KMS Key
    participant DK as Destination KMS Key
    participant DB as Destination Bucket

    S3->>IAM: AssumeRole
    IAM-->>S3: Temporary role credentials
    S3->>SK: Decrypt source object
    SK-->>S3: Decryption authorization
    S3->>DK: Encrypt replicated object
    DK-->>S3: Encryption authorization
    S3->>DB: Store replicated object
    DB-->>S3: Replication result
```

### Required Configuration

1. Configure `source_kms_key_arn` with the source key ARN.
2. Configure `destination_kms_key_arn` with a key in the destination Region.
3. Ensure the replication role has the required IAM permissions.
4. Update the source and destination KMS key policies as required.
5. Verify that the replication rule includes SSE-KMS source selection criteria.
6. Verify the destination encryption configuration.

### Common KMS Failure Causes

- The source key policy does not authorize the replication role.
- The destination key policy does not authorize the replication role.
- The destination key is in the wrong Region.
- The key is disabled or unavailable.
- An explicit deny or organizational policy blocks the operation.
- The replication role has S3 permissions but lacks KMS permissions.

Diagnose S3 and KMS authorization separately. An S3 `AccessDenied` response does not necessarily identify which authorization layer rejected the request.

## Replication Metrics and RTC

Replication metrics help identify replication delays and failures.

Use metrics when the workload needs operational visibility into replication progress.

RTC adds a 15-minute replication commitment for eligible objects and requires metrics to be enabled.

| Capability | Purpose | Consideration |
|---|---|---|
| Replication metrics | Exposes replication progress and failure indicators | Requires monitoring and alerting |
| RTC | Provides a 15-minute replication SLA for eligible objects | Additional cost |
| Object replication status | Shows the replication state of individual objects | Useful for targeted investigation |

Do not treat metrics or RTC as proof that every object is immediately available in the destination bucket.

## Operational Verification

### Inspect Replication Configuration

```bash
aws s3api get-bucket-replication \
  --bucket your-source-bucket \
  --region ap-south-1
```

Inspect the returned configuration for:

- IAM role ARN.
- Rule ID and status.
- Prefix filter.
- Destination bucket ARN.
- Destination storage class.
- Delete-marker replication setting.
- SSE-KMS encryption configuration.
- Metrics and RTC configuration.

### Inspect Object Replication Status

```bash
aws s3api head-object \
  --bucket your-source-bucket \
  --key documents/example.pdf \
  --region ap-south-1
```

Inspect `ReplicationStatus` when returned.

Possible source object replication states include:

- `PENDING`
- `COMPLETED`
- `FAILED`

Use object status together with replication metrics and CloudTrail evidence when investigating failures.

### Verify the Destination Object

```bash
aws s3api head-object \
  --bucket your-destination-bucket \
  --key documents/example.pdf \
  --region ap-southeast-1
```

A successful lookup confirms that the destination object is accessible. For integrity-sensitive workloads, compare appropriate checksums and object metadata.

### Verify Role Configuration

```bash
aws iam get-role \
  --role-name application-s3-replication-role
```

Inspect the trust policy and confirm that the S3 service principal and source restrictions are correct.

Inspect the inline policy:

```bash
aws iam get-role-policy \
  --role-name application-s3-replication-role \
  --policy-name application-s3-replication-role-policy
```

## Existing Objects and Batch Replication

The module configures ongoing replication for eligible objects. It does not automatically backfill all objects that existed before the replication rule was created.

Use S3 Batch Replication for eligible existing objects.

A Batch Replication workflow should include:

- An appropriate object manifest.
- Required IAM permissions.
- A batch operation job.
- Completion reporting.
- Failure investigation.
- Verification of destination object availability.

Do not assume that creating a replication rule makes historical source data available in the destination Region.

## Production Considerations

### Replication Is Asynchronous

A successful source write does not mean the destination copy is immediately available.

Applications that read from the destination Region must account for replication delay and possible temporary absence of newly written objects.

### Disaster Recovery

CRR is one component of a disaster recovery design.

A complete recovery strategy must also address:

- Application deployment in the recovery Region.
- Database recovery and consistency.
- DNS or traffic-routing changes.
- IAM and KMS availability.
- Recovery point objective (RPO).
- Recovery time objective (RTO).
- Replicated object verification.
- Failback procedures.

Replication alone does not provide automatic application failover.

### Versioning and Delete Markers

Both buckets must have versioning enabled.

Delete-marker replication is configurable and disabled by default in this module. Decide whether the destination should reflect source deletion behavior or retain data for recovery purposes.

Replication and lifecycle policies should be designed together. A destination lifecycle rule can expire replicated versions independently of the source bucket's lifecycle configuration.

### Ownership and ACLs

The example assumes Bucket Owner Enforced ownership controls are managed by the bucket layer.

For cross-account replication, validate the required destination ownership behavior and any ownership override configuration. The module does not implement an ownership override mechanism.

### Object Lock

If either bucket uses S3 Object Lock, review the replication requirements for retention metadata and legal holds. This module does not configure Object Lock or its associated permissions.

### Multiple Replication Rules

The current module creates one prefix-filtered replication rule.

It does not provide a complete interface for multiple rules, tag-based filters, or more advanced rule combinations. Extend the module deliberately if the application requires those capabilities.

### IAM Policy Ownership

The module manages an inline policy on its dedicated IAM role. Avoid adding unrelated permissions to that role outside the module unless the ownership boundary is explicitly documented.

### Terraform State

The module creates IAM and S3 configuration resources that should be managed through a consistent Terraform state boundary.

Use remote state, locking, restricted access, and reviewed plans for production deployments.

## Common Mistakes

| Mistake | Impact | Prevention |
|---|---|---|
| Source bucket versioning is disabled | Replication cannot operate as configured | Enable source versioning before applying the replication configuration |
| Destination versioning is disabled | Replication requirements are not met | Enable destination versioning |
| Source KMS key is configured without a destination key | Replicated encryption cannot be configured as intended | Configure a destination-Region KMS key |
| KMS key policies are incomplete | Replication fails despite IAM permissions | Validate both IAM and key policies |
| Existing objects are assumed to replicate | Historical objects are missing | Use S3 Batch Replication |
| Another Terraform resource manages replication | Configuration conflicts or drift | Maintain one replication configuration owner |
| RTC is enabled without metrics | Invalid configuration | Enable metrics when RTC is enabled |
| Cross-account destination policy is omitted | Destination writes are denied | Configure destination bucket authorization |
| Replication is treated as synchronous | Applications observe missing destination objects | Design for asynchronous consistency |
| Replication is treated as a complete DR solution | Application recovery remains untested | Build and validate a full recovery runbook |

## Troubleshooting

### Replication Configuration Fails

Inspect the source bucket configuration:

```bash
aws s3api get-bucket-versioning \
  --bucket your-source-bucket \
  --region ap-south-1
```

Then inspect the destination bucket versioning and confirm that both report `Enabled`.

Review the replication configuration inputs and confirm that the source and destination bucket ARNs are correct.

### Objects Remain Pending

Inspect the source object:

```bash
aws s3api head-object \
  --bucket your-source-bucket \
  --key documents/example.pdf \
  --region ap-south-1
```

Check:

- Whether the rule is enabled.
- Whether the key matches the prefix filter.
- Whether the object is eligible for replication.
- Whether the replication role can be assumed.
- Whether source and destination permissions are correct.
- Whether KMS authorization succeeds.

Use replication metrics to distinguish ongoing replication delay from a persistent failure.

### Replication Status Is Failed

Investigate the IAM trust policy and role permissions first.

For cross-account replication, inspect the destination bucket policy. For SSE-KMS, inspect both KMS key policies and the role's KMS permissions.

Use CloudTrail and available replication metrics to identify the failed authorization or service operation.

### Destination Object Is Missing

Check whether the object was created after the replication rule was configured. If it existed beforehand, determine whether it was included in an S3 Batch Replication job.

Verify the source object's replication status and the destination bucket Region before changing the rule or retrying uploads.

### Terraform Configuration Conflicts

If another Terraform state or deployment system manages the source bucket replication configuration, identify the authoritative owner before applying changes.

Do not create a second replication configuration resource to work around a state ownership problem. Reconcile state and infrastructure deliberately.

## Key Takeaways

- The module manages the IAM replication role, its permissions, and one S3 replication rule; bucket creation, versioning, destination policies, and KMS key policies remain external responsibilities.
- Both source and destination buckets must have versioning enabled before replication can operate.
- SSE-KMS replication requires authorization at both the IAM and KMS layers, with a destination-Region key for replicated objects.
- Existing objects require S3 Batch Replication; ongoing replication is asynchronous and should be monitored.
- Use one Terraform owner for each source bucket's complete replication configuration, and treat CRR as one component of a tested disaster recovery strategy.