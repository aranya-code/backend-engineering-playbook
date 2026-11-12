# README

## Overview

The `s3-lifecycle` module manages the lifecycle configuration of an existing Amazon S3 bucket through Terraform.

It provides a reusable interface for defining lifecycle rules that control:

- Storage-class transitions for current object versions.
- Expiration of current object versions.
- Storage-class transitions for noncurrent object versions.
- Expiration of noncurrent object versions.
- Cleanup of incomplete multipart uploads.

Lifecycle policies help control storage costs, enforce retention strategies, and automate object management without requiring application-level cleanup jobs.

The module manages the bucket's complete lifecycle configuration. It does not create the bucket, enable versioning, or manage bucket encryption.

## Module Structure

```text
modules/
└── s3-lifecycle/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── versions.tf
    └── README.md
```

| File | Responsibility |
|---|---|
| `main.tf` | Defines the S3 lifecycle configuration and lifecycle rules |
| `variables.tf` | Declares lifecycle rule inputs and validation |
| `outputs.tf` | Exposes lifecycle configuration identifiers and rule details |
| `versions.tf` | Defines Terraform and AWS provider version requirements |
| `README.md` | Documents module usage and operational considerations |

## Requirements

| Dependency | Requirement |
|---|---|
| Terraform | `>= 1.5.0` |
| AWS provider | `~> 6.0` |
| AWS credentials | Configured through an AWS-supported credential provider |
| Existing S3 bucket | Must exist before lifecycle configuration is applied |
| IAM permissions | Must allow management of the bucket lifecycle configuration |

The root module is responsible for configuring the AWS provider and selecting the deployment Region.

The deployment identity must have permission to manage the bucket lifecycle configuration.

## Architecture

The module manages lifecycle rules independently of bucket creation.

```mermaid
flowchart TD
    A[Root Terraform Module] --> B[s3-bucket Module]
    A --> C[s3-lifecycle Module]

    B --> D[Existing S3 Bucket]
    C --> E[Lifecycle Configuration]

    E --> F[Current Version Transitions]
    E --> G[Current Version Expiration]
    E --> H[Noncurrent Version Management]
    E --> I[Incomplete Multipart Cleanup]

    D --> E
```

The bucket-owning module is responsible for creating the bucket and managing its versioning configuration. The lifecycle module receives the existing bucket identifier.

Lifecycle rules are evaluated by S3 asynchronously. Terraform configures the policy; it does not execute transitions or deletions itself.

## Features

| Feature | Implementation |
|---|---|
| Current-version transitions | Moves objects between supported storage classes |
| Current-version expiration | Expires objects based on age or date |
| Noncurrent-version transitions | Moves older object versions to lower-cost storage |
| Noncurrent-version expiration | Removes eligible noncurrent versions |
| Incomplete multipart cleanup | Aborts incomplete multipart uploads after a configured number of days |
| Rule filtering | Supports prefix and object-tag filters |
| Rule management | Supports enabled and disabled lifecycle rules |
| Input validation | Validates rule identifiers, transition settings, and expiration settings |

## Input Variables

The module exposes its configuration through `variables.tf`.

| Variable | Type | Default | Description |
|---|---|---|---|
| `bucket_id` | `string` | Required | Name or ID of the existing S3 bucket |
| `bucket_dependency` | `any` | `null` | Optional dependency reference to the bucket-owning resource or module |
| `lifecycle_rules` | `list(object(...))` | `[]` | Lifecycle rules to apply to the bucket |

At least one lifecycle rule must be supplied.

### Lifecycle Rule Structure

Each lifecycle rule supports the following attributes:

| Attribute | Type | Description |
|---|---|---|
| `id` | `string` | Unique rule identifier |
| `enabled` | `bool` | Whether the rule is enabled; defaults to `true` |
| `filter` | `object` | Optional prefix and tag filters |
| `transitions` | `list(object)` | Current-version storage-class transitions |
| `expiration` | `object` | Current-version expiration settings |
| `noncurrent_version_transitions` | `list(object)` | Transitions for noncurrent versions |
| `noncurrent_version_expiration` | `object` | Noncurrent-version expiration settings |
| `abort_incomplete_multipart_upload_days` | `number` | Days after initiation before incomplete multipart uploads are aborted |

### Filter Attributes

| Attribute | Type | Default | Description |
|---|---|---|---|
| `prefix` | `string` | `null` | Restricts the rule to objects with the specified key prefix |
| `tags` | `map(string)` | `{}` | Restricts the rule to objects matching the configured tags |

When both prefix and tags are configured, the rule applies to objects matching the combined filter.

An empty filter applies the rule to all objects in the bucket.

## Supported Storage Classes

The module accepts these storage classes for lifecycle transitions:

| Storage Class | Typical Workload |
|---|---|
| `STANDARD_IA` | Infrequently accessed data requiring millisecond retrieval |
| `ONEZONE_IA` | Re-creatable, infrequently accessed data stored in one Availability Zone |
| `INTELLIGENT_TIERING` | Data with changing or unpredictable access patterns |
| `GLACIER` | Archive data requiring asynchronous retrieval |
| `GLACIER_IR` | Archive data requiring millisecond retrieval |
| `DEEP_ARCHIVE` | Long-term archive data with infrequent retrieval requirements |

Choose storage classes based on access frequency, retrieval latency, minimum storage duration, retrieval charges, and availability requirements.

Lifecycle transitions are not automatically cost-effective for every object. Small objects and frequently accessed data may be unsuitable for certain storage classes.

## Usage

Reference the module from a root Terraform configuration after provisioning the bucket.

```hcl
module "application_files_bucket" {
  source = "./modules/s3-bucket"

  bucket_name       = "company-prod-application-files-2026"
  versioning_enabled = true

  tags = {
    Project     = "application-platform"
    Environment = "production"
  }
}

module "application_files_lifecycle" {
  source = "./modules/s3-lifecycle"

  bucket_id = module.application_files_bucket.bucket_id

  lifecycle_rules = [
    {
      id      = "archive-old-application-files"
      enabled = true

      filter = {
        prefix = "application-files/"
      }

      transitions = [
        {
          days          = 30
          storage_class = "STANDARD_IA"
        },
        {
          days          = 90
          storage_class = "GLACIER"
        }
      ]

      expiration = {
        days = 365
      }

      abort_incomplete_multipart_upload_days = 7
    }
  ]

  depends_on = [
    module.application_files_bucket
  ]
}
```

The explicit dependency ensures that the bucket is provisioned before the lifecycle configuration is applied.

The bucket-owning module must manage versioning separately when noncurrent-version lifecycle rules are required.

## Current-Version Lifecycle Management

Current-version rules operate on the current version of an object.

### Storage-Class Transitions

Transitions move eligible objects to another storage class after a specified number of days or on a specified date.

Example:

```hcl
transitions = [
  {
    days          = 30
    storage_class = "STANDARD_IA"
  },
  {
    days          = 90
    storage_class = "GLACIER"
  },
  {
    days          = 180
    storage_class = "DEEP_ARCHIVE"
  }
]
```

This policy is suitable for data that becomes progressively less likely to be accessed.

### Expiration

Expiration removes eligible current objects according to the configured lifecycle rule.

Example:

```hcl
expiration = {
  days = 365
}
```

For versioned buckets, expiration of the current version generally creates a delete marker rather than permanently deleting all versions.

Use noncurrent-version expiration when older versions must also be removed.

### Date-Based Configuration

A transition or expiration can use a specific date instead of a relative number of days.

Example:

```hcl
transitions = [
  {
    date          = "2027-01-01T00:00:00Z"
    storage_class = "GLACIER"
  }
]
```

The module requires exactly one of `days` or `date` for each transition.

For expiration, exactly one of `days`, `date`, or `expired_object_delete_marker` must be specified.

## Noncurrent-Version Lifecycle Management

When bucket versioning is enabled, overwriting or deleting an object can leave older versions in the bucket.

These versions continue to consume storage and can generate ongoing costs.

Noncurrent-version lifecycle rules help manage this retained data.

### Noncurrent-Version Transitions

Example:

```hcl
noncurrent_version_transitions = [
  {
    noncurrent_days = 30
    storage_class   = "STANDARD_IA"
  },
  {
    noncurrent_days = 90
    storage_class   = "GLACIER"
  }
]
```

### Noncurrent-Version Expiration

Example:

```hcl
noncurrent_version_expiration = {
  noncurrent_days = 180
}
```

This expires eligible noncurrent versions after the configured period.

### Retaining Newer Noncurrent Versions

The optional `newer_noncurrent_versions` attribute controls how many newer noncurrent versions are retained when evaluating a transition or expiration rule.

Example:

```hcl
noncurrent_version_expiration = {
  noncurrent_days           = 180
  newer_noncurrent_versions = 3
}
```

This configuration retains the three most recent noncurrent versions while allowing eligible older versions to expire.

### Production Considerations

- Enable bucket versioning in the bucket-owning module.
- Define retention requirements before configuring noncurrent expiration.
- Verify backup and recovery requirements before deleting historical versions.
- Consider legal, regulatory, and audit retention requirements.
- Remember that lifecycle expiration is asynchronous and should not be treated as an immediate deletion mechanism.

## Incomplete Multipart Upload Cleanup

Multipart uploads that are initiated but never completed can leave stored parts behind.

These parts consume storage and can incur charges.

Configure automatic cleanup using:

```hcl
abort_incomplete_multipart_upload_days = 7
```

S3 aborts incomplete multipart uploads after the configured number of days.

This is useful for backend services that support large file uploads, including Django, FastAPI, and asynchronous Celery-based upload workflows.

The lifecycle rule does not replace application-level cleanup for failed upload sessions that need immediate handling.

## Prefix and Tag Filtering

Lifecycle rules can target specific object groups.

### Prefix-Based Filtering

```hcl
filter = {
  prefix = "logs/"
}
```

This applies the rule to objects whose keys begin with `logs/`.

### Tag-Based Filtering

```hcl
filter = {
  tags = {
    retention = "temporary"
    service   = "document-processing"
  }
}
```

This applies the rule to objects matching the configured tags.

### Combined Filtering

```hcl
filter = {
  prefix = "uploads/"
  tags = {
    lifecycle = "archive"
  }
}
```

This targets objects under the `uploads/` prefix that also match the specified tag filter.

Object tags must be present and correctly assigned for tag-based rules to match.

## Complete Production Example

The following example combines transitions, expiration, noncurrent-version management, tag filtering, and incomplete multipart cleanup.

```hcl
module "document_storage_lifecycle" {
  source = "./modules/s3-lifecycle"

  bucket_id = "company-prod-document-storage-2026"

  lifecycle_rules = [
    {
      id      = "archive-completed-documents"
      enabled = true

      filter = {
        prefix = "documents/completed/"
      }

      transitions = [
        {
          days          = 30
          storage_class = "STANDARD_IA"
        },
        {
          days          = 90
          storage_class = "GLACIER"
        }
      ]

      expiration = {
        days = 730
      }

      noncurrent_version_transitions = [
        {
          noncurrent_days           = 30
          storage_class             = "GLACIER"
          newer_noncurrent_versions = 2
        }
      ]

      noncurrent_version_expiration = {
        noncurrent_days           = 365
        newer_noncurrent_versions = 2
      }

      abort_incomplete_multipart_upload_days = 7
    },
    {
      id      = "expire-temporary-uploads"
      enabled = true

      filter = {
        tags = {
          lifecycle = "temporary"
        }
      }

      expiration = {
        days = 14
      }

      abort_incomplete_multipart_upload_days = 3
    }
  ]

  depends_on = [
    module.document_storage_bucket
  ]
}
```

This example assumes that `module.document_storage_bucket` creates the bucket and enables versioning.

Review the retention policy carefully before applying it to production data.

## Outputs

The module exposes the following outputs through `outputs.tf`.

| Output | Description |
|---|---|
| `lifecycle_configuration_id` | ID of the managed lifecycle configuration |
| `lifecycle_rule_ids` | Identifiers of all configured lifecycle rules |
| `lifecycle_rule_count` | Number of configured lifecycle rules |
| `enabled_lifecycle_rule_ids` | IDs of enabled rules |
| `disabled_lifecycle_rule_ids` | IDs of disabled rules |
| `lifecycle_transitions` | Current-version transition settings by rule |
| `lifecycle_expirations` | Current-version expiration settings by rule |
| `noncurrent_version_transitions` | Noncurrent-version transition settings by rule |
| `noncurrent_version_expirations` | Noncurrent-version expiration settings by rule |
| `multipart_upload_abort_rules` | Multipart cleanup thresholds by rule |

These outputs expose the configured Terraform inputs and resource identifier. They do not report the number of objects transitioned, expired, or deleted by S3.

## Deployment Workflow

Run Terraform commands from the root module that references `s3-lifecycle`.

### Initialize

```bash
terraform init
```

### Format

```bash
terraform fmt -recursive
```

### Validate

```bash
terraform validate
```

### Review the Plan

```bash
terraform plan
```

Inspect the planned lifecycle configuration carefully, especially:

- Rule IDs and enabled status.
- Prefix and tag filters.
- Current-version transitions.
- Current-version expiration.
- Noncurrent-version transitions and expiration.
- Incomplete multipart upload cleanup thresholds.

Lifecycle configuration changes can affect large numbers of objects. Treat expiration and noncurrent-version deletion as destructive changes.

### Apply

```bash
terraform apply
```

Apply only after reviewing the lifecycle policy and confirming that it meets the intended retention requirements.

## Verification

Use the AWS CLI to inspect the deployed lifecycle configuration.

Set the bucket name:

```bash
BUCKET_NAME="company-prod-document-storage-2026"
```

### Inspect Lifecycle Configuration

```bash
aws s3api get-bucket-lifecycle-configuration \
  --bucket "$BUCKET_NAME"
```

Review the returned rules for:

- Rule identifiers and status.
- Prefix and tag filters.
- Transition storage classes and dates.
- Expiration settings.
- Noncurrent-version actions.
- Incomplete multipart upload cleanup.

If no lifecycle configuration exists, the command returns an error indicating that the configuration is not found.

### Inspect Bucket Versioning

```bash
aws s3api get-bucket-versioning \
  --bucket "$BUCKET_NAME"
```

Confirm that versioning is enabled when noncurrent-version lifecycle rules are expected to operate.

### Inspect Incomplete Multipart Uploads

```bash
aws s3api list-multipart-uploads \
  --bucket "$BUCKET_NAME"
```

Use this command to inspect outstanding multipart upload sessions.

### Inspect Object Versions

```bash
aws s3api list-object-versions \
  --bucket "$BUCKET_NAME" \
  --prefix "documents/completed/"
```

Review current versions, noncurrent versions, and delete markers when validating version-aware lifecycle behavior.

## Operational Considerations

### Lifecycle Execution Is Asynchronous

Terraform creates or updates the lifecycle configuration. S3 evaluates eligible objects and performs lifecycle actions asynchronously.

Do not assume that an object will transition or expire immediately when it reaches the configured threshold.

### Retention and Recovery

Before configuring expiration:

- Identify the required retention period.
- Confirm backup and recovery arrangements.
- Review versioning and delete-marker behavior.
- Check regulatory and legal retention obligations.
- Confirm whether historical versions must remain available.

Lifecycle expiration should not be used as the only control for strict deletion deadlines.

### Storage-Class Economics

Consider the complete cost model before selecting a transition target:

- Storage price.
- Minimum storage duration.
- Minimum billable object size.
- Retrieval charges.
- Request charges.
- Data retrieval latency.
- Availability and resilience requirements.

A transition to a lower-cost storage class can increase total cost if objects are frequently retrieved or retained for less than the minimum storage duration.

### Rule Ownership

An S3 bucket has one lifecycle configuration managed as a complete configuration document.

Do not manage the same bucket lifecycle configuration through multiple Terraform resources or modules. Multiple owners can overwrite one another's rules and cause configuration drift.

Keep lifecycle rule ownership centralized in one module or root configuration.

### Rule Limits and Complexity

S3 lifecycle configurations have service-defined rule limits. Keep the number of rules manageable and consolidate rules where filters and actions are compatible.

Avoid creating many overlapping rules without understanding how their filters and actions interact.

### Versioning Dependency

Noncurrent-version actions require a versioned bucket.

The lifecycle module does not enable or manage bucket versioning. Configure versioning through the bucket-owning module and establish an explicit dependency between the modules.

### Object Tagging

Tag-based lifecycle rules depend on object tags being assigned correctly.

For backend applications, make tagging part of the upload or ingestion workflow. Test that the expected tags are present before relying on them for retention or archival policies.

## Security Considerations

Lifecycle rules can permanently remove data. Treat lifecycle configuration as a security- and compliance-relevant change.

- Restrict permission to modify lifecycle configuration.
- Review expiration changes through Terraform plans.
- Use least-privilege IAM roles for infrastructure deployment.
- Preserve required historical versions.
- Validate retention requirements before enabling expiration.
- Use object tagging and prefixes consistently.
- Audit lifecycle configuration changes through appropriate AWS audit mechanisms.
- Avoid broad expiration rules on buckets containing mixed-purpose data.
- Protect Terraform state and deployment pipelines.

## Common Mistakes

| Mistake | Impact | Prevention |
|---|---|---|
| Applying lifecycle rules before bucket creation | Lifecycle resource cannot be configured | Establish a dependency on the bucket module |
| Configuring noncurrent-version actions without versioning | Expected historical-version management does not occur | Enable versioning in the bucket-owning module |
| Expiring current versions but ignoring noncurrent versions | Historical versions continue consuming storage | Configure noncurrent-version expiration where appropriate |
| Using an overly broad prefix filter | Unrelated objects may transition or expire | Use narrowly scoped prefixes and tags |
| Assuming expiration is immediate | Applications may still observe objects during asynchronous processing | Treat lifecycle execution as asynchronous |
| Ignoring minimum storage duration | Early deletion or transition can create additional charges | Evaluate storage-class economics |
| Using tag filters without assigning tags | Lifecycle rules do not match intended objects | Apply and verify tags during ingestion |
| Managing lifecycle configuration in multiple modules | Rules can overwrite each other | Maintain one authoritative lifecycle configuration |
| Deleting historical versions without recovery review | Required data may become unavailable | Validate retention and recovery requirements first |
| Treating lifecycle expiration as a compliance deletion deadline | Deletion timing may not meet strict requirements | Use a dedicated deletion workflow when strict timing is required |

## Production Best Practices

- Keep lifecycle configuration under a single Terraform owner.
- Separate lifecycle policies by data purpose and retention requirement.
- Use prefixes and tags to target data precisely.
- Enable versioning when recovery and historical-version management are required.
- Define noncurrent-version expiration explicitly when historical versions should not accumulate indefinitely.
- Configure incomplete multipart upload cleanup to control abandoned-part storage costs.
- Validate lifecycle changes in a non-production environment before applying them to critical buckets.
- Review storage-class minimum durations and retrieval costs.
- Monitor storage usage and lifecycle-related cost changes.
- Include lifecycle configuration in infrastructure code review and change-management processes.
- Keep application-level retention metadata consistent with S3 lifecycle policy.

## Key Takeaways

- The `s3-lifecycle` module manages lifecycle rules for an existing S3 bucket; it does not create the bucket or enable versioning.
- Lifecycle rules support current-version transitions and expiration, noncurrent-version management, and incomplete multipart upload cleanup.
- Prefix and tag filters are essential for applying retention policies to the correct object groups.
- Lifecycle execution is asynchronous, and storage-class transitions must be evaluated against retrieval costs and minimum storage durations.
- Maintain one authoritative Terraform owner for each bucket's complete lifecycle configuration and review expiration changes as destructive operations.