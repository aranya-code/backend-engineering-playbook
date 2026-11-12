# README

## Overview

The `s3-bucket` module is a reusable Terraform child module for provisioning Amazon S3 buckets with consistent security, versioning, encryption, lifecycle management, and optional server access logging.

It centralizes common bucket configuration so application teams can provision S3 resources through a stable module interface instead of duplicating resource definitions across environments.

The module is designed for backend application storage, document repositories, media storage, and other workloads that require private, durable object storage.

## Module Structure

```text
modules/
└── s3-bucket/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    └── versions.tf
```

| File | Responsibility |
|---|---|
| `main.tf` | Defines S3 bucket resources and their configurations |
| `variables.tf` | Declares the module input interface and validation rules |
| `outputs.tf` | Exposes bucket attributes and configuration information |
| `versions.tf` | Defines Terraform and AWS provider version requirements |

## Features

| Feature | Implementation |
|---|---|
| Bucket creation | Creates an S3 bucket using a configurable bucket name |
| Object ownership | Uses `BucketOwnerEnforced` ownership controls |
| Public access protection | Enables all four S3 Block Public Access settings |
| Versioning | Supports enabling or suspending bucket versioning |
| Encryption | Supports SSE-S3 and SSE-KMS |
| S3 Bucket Keys | Supports configurable Bucket Keys for SSE-KMS |
| Lifecycle management | Supports object expiration, noncurrent-version expiration, and incomplete multipart upload cleanup |
| Server access logging | Supports optional logging to a designated target bucket |
| Resource protection | Uses Terraform lifecycle protection against accidental bucket destruction |
| Tagging | Supports common resource tags |

## Requirements

| Dependency | Requirement |
|---|---|
| Terraform | `>= 1.5.0` |
| AWS provider | `~> 6.0` |
| AWS credentials | Configured through an AWS-supported credential provider |
| AWS permissions | Permissions to create and configure S3 buckets and associated resources |

The module does not configure AWS provider credentials or provider aliases. The calling root module is responsible for configuring the AWS provider and selecting the deployment Region.

## Input Variables

The module exposes the following inputs through `variables.tf`.

| Variable | Type | Default | Description |
|---|---|---|---|
| `bucket_name` | `string` | Required | Globally unique S3 bucket name |
| `force_destroy` | `bool` | `false` | Controls whether Terraform may empty a bucket before deletion |
| `versioning_enabled` | `bool` | `true` | Enables or suspends bucket versioning |
| `kms_key_arn` | `string` | `null` | Customer-managed KMS key ARN; null selects SSE-S3 |
| `bucket_key_enabled` | `bool` | `true` | Enables S3 Bucket Keys when SSE-KMS is configured |
| `lifecycle_rules` | `list(object(...))` | `[]` | Configures supported lifecycle actions |
| `logging_target_bucket` | `string` | `null` | Destination bucket for server access logs |
| `logging_target_prefix` | `string` | `"s3-access-logs/"` | Prefix for delivered access logs |
| `tags` | `map(string)` | `{}` | Tags applied to the bucket |

### Lifecycle Rule Attributes

Each lifecycle rule supports:

| Attribute | Type | Description |
|---|---|---|
| `id` | `string` | Unique lifecycle rule identifier |
| `enabled` | `bool` | Whether the rule is enabled |
| `prefix` | `string` | Object key prefix to which the rule applies |
| `expiration_days` | `number` | Number of days before current objects expire |
| `noncurrent_version_expiration_days` | `number` | Number of days before noncurrent versions expire |
| `abort_incomplete_multipart_upload_days` | `number` | Number of days before incomplete multipart uploads are aborted |

At least one supported lifecycle action must be configured in each rule. Rule identifiers must be unique.

## Usage

Reference the module from a root Terraform configuration.

```hcl
module "application_files_bucket" {
  source = "./modules/s3-bucket"

  bucket_name       = "company-prod-application-files-2026"
  versioning_enabled = true

  tags = {
    Project     = "application-platform"
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}
```

The calling root module must configure the AWS provider.

```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "ap-south-1"
}
```

## Encryption Configuration

By default, the module configures SSE-S3 encryption. Supply a KMS key ARN to use SSE-KMS.

### SSE-S3

```hcl
module "application_files_bucket" {
  source = "./modules/s3-bucket"

  bucket_name = "company-prod-application-files-2026"

  kms_key_arn = null
}
```

SSE-S3 uses Amazon S3-managed encryption keys and does not require application-level KMS key permissions.

### SSE-KMS

```hcl
module "sensitive_documents_bucket" {
  source = "./modules/s3-bucket"

  bucket_name = "company-prod-sensitive-documents-2026"

  kms_key_arn       = "arn:aws:kms:ap-south-1:123456789012:key/00000000-0000-0000-0000-000000000000"
  bucket_key_enabled = true
}
```

For SSE-KMS, verify that the KMS key:
- Exists in the same Region as the S3 bucket.
- Is enabled and available.
- Has a key policy that permits the required principals.
- Allows the relevant S3 encryption and decryption operations.

The module configures the bucket's default encryption but does not create or manage the KMS key or its key policy.

## Lifecycle Configuration

Lifecycle rules can be supplied to manage object retention and incomplete multipart uploads.

```hcl
module "application_files_bucket" {
  source = "./modules/s3-bucket"

  bucket_name = "company-prod-application-files-2026"

  versioning_enabled = true

  lifecycle_rules = [
    {
      id                                     = "expire-temporary-files"
      enabled                                = true
      prefix                                 = "temporary/"
      expiration_days                       = 30
      noncurrent_version_expiration_days    = 90
      abort_incomplete_multipart_upload_days = 7
    }
  ]
}
```

Review lifecycle policies carefully before applying them to production buckets. Expiration and noncurrent-version cleanup can permanently remove data when versioning and retention requirements are not considered.

## Server Access Logging

The module supports optional server access logging to a separate target bucket.

```hcl
module "application_files_bucket" {
  source = "./modules/s3-bucket"

  bucket_name = "company-prod-application-files-2026"

  logging_target_bucket = "company-prod-s3-access-logs-2026"
  logging_target_prefix = "application-files/"
}
```

The target bucket must already exist and be configured to accept S3 server access logs. The module does not create the logging destination or configure its retention policy.

Use a dedicated logging bucket where possible. Apply appropriate access controls, encryption, and lifecycle policies to the destination.

## Outputs

The module exposes the following outputs through `outputs.tf`.

| Output | Description |
|---|---|
| `bucket_id` | S3 bucket identifier/name |
| `bucket_arn` | Bucket ARN |
| `bucket_region` | Bucket Region |
| `bucket_domain_name` | Regional bucket domain name |
| `bucket_hosted_zone_id` | S3 hosted zone ID |
| `bucket_versioning_enabled` | Configured versioning setting |
| `bucket_kms_key_arn` | Configured KMS key ARN, if supplied |
| `bucket_encryption_algorithm` | Configured encryption algorithm |
| `lifecycle_configuration_id` | Lifecycle configuration identifier, when configured |
| `server_access_logging_enabled` | Whether a logging destination is configured |
| `server_access_logging_target_bucket` | Configured logging destination bucket |

Example output usage:

```hcl
output "application_files_bucket_arn" {
  value = module.application_files_bucket.bucket_arn
}

output "application_files_bucket_name" {
  value = module.application_files_bucket.bucket_id
}
```

## Deployment Workflow

Run Terraform commands from the root module that references this child module.

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

Inspect the planned changes, especially:
- Bucket creation or replacement.
- Versioning changes.
- Encryption configuration changes.
- Lifecycle expiration rules.
- Logging destination changes.
- Resource destruction or replacement.

### Apply

```bash
terraform apply
```

Apply only after reviewing the plan and confirming the intended infrastructure changes.

## Verification

Use the AWS CLI to verify the deployed bucket configuration.

### Check Bucket Region

```bash
aws s3api get-bucket-location \
  --bucket company-prod-application-files-2026
```

### Check Public Access Block

```bash
aws s3api get-public-access-block \
  --bucket company-prod-application-files-2026
```

### Check Object Ownership

```bash
aws s3api get-bucket-ownership-controls \
  --bucket company-prod-application-files-2026
```

### Check Versioning

```bash
aws s3api get-bucket-versioning \
  --bucket company-prod-application-files-2026
```

### Check Encryption

```bash
aws s3api get-bucket-encryption \
  --bucket company-prod-application-files-2026
```

### Check Lifecycle Configuration

```bash
aws s3api get-bucket-lifecycle-configuration \
  --bucket company-prod-application-files-2026
```

### Check Server Access Logging

```bash
aws s3api get-bucket-logging \
  --bucket company-prod-application-files-2026
```

A successful Terraform apply confirms that Terraform completed the requested operations. It does not replace application-level verification or validation of the complete bucket security posture.

## Security Considerations

- Keep buckets private unless public access is an explicit, reviewed requirement.
- Retain all four Block Public Access settings.
- Use IAM roles and temporary credentials instead of long-lived access keys.
- Grant application workloads only the S3 permissions they require.
- Use SSE-KMS when customer-managed key control or key-level auditability is required.
- Ensure KMS key policies and IAM policies both permit required operations.
- Keep logging destinations separate from application data buckets.
- Apply retention and lifecycle policies according to business and regulatory requirements.
- Avoid exposing bucket names, object keys, or presigned URLs unnecessarily.
- Use separate buckets or carefully designed prefixes and IAM conditions for tenant isolation.

## Production Considerations

### Bucket Naming

S3 bucket names are globally unique within an AWS partition. Include meaningful environment and workload identifiers, but avoid sensitive information in bucket names.

### Resource Protection

The module uses Terraform `prevent_destroy` protection for the bucket. This helps prevent accidental deletion through Terraform plans and applies.

This protection also means that ordinary Terraform destruction will be blocked until the lifecycle protection is deliberately changed. The `force_destroy` setting does not override Terraform's `prevent_destroy` lifecycle rule.

### Versioning

Versioning is enabled by default. Versioning increases recovery options but can increase storage costs because previous object versions remain stored.

Define noncurrent-version retention policies when historical versions do not need to be retained indefinitely.

### Encryption

The module configures default bucket encryption. Applications should still follow a consistent encryption policy when uploading objects, particularly when using SSE-KMS with specific keys or encryption contexts.

### Lifecycle Management

Lifecycle policies should be tested against representative object keys and retention requirements. Review the interaction between current versions, noncurrent versions, delete markers, and incomplete multipart uploads.

### Logging

Server access logging delivery is not immediate. Do not use it as the sole mechanism for real-time security monitoring or request-level alerting.

### Multi-Environment Deployment

Use separate bucket names and Terraform state boundaries for development, staging, and production. Avoid sharing production state with non-production deployment workflows.

## Common Mistakes

| Mistake | Impact | Prevention |
|---|---|---|
| Reusing a bucket name | Bucket creation fails because names are globally unique | Use globally unique naming conventions |
| Assuming `force_destroy` bypasses `prevent_destroy` | Terraform destruction remains blocked | Review and deliberately change lifecycle protection before approved deletion |
| Using a KMS key from another Region | Encryption configuration fails | Use a compatible KMS key in the bucket Region |
| Omitting KMS permissions | Application uploads or downloads fail | Validate IAM permissions and KMS key policy |
| Configuring a nonexistent logging destination | Logging configuration fails | Provision and validate the target bucket first |
| Expiring noncurrent versions too early | Historical data becomes unrecoverable | Align lifecycle rules with retention requirements |
| Assuming bucket encryption grants access | Applications receive authorization errors | Configure S3 and KMS permissions independently |
| Sharing one bucket across unrelated workloads | Access control and lifecycle policies become difficult to manage | Separate buckets by workload and security boundary where appropriate |

## Key Takeaways

- The module provides a reusable S3 bucket baseline with private access, ownership controls, versioning, and default encryption.
- SSE-S3 is the default encryption mode; SSE-KMS requires a compatible KMS key and appropriate permissions.
- Lifecycle rules and server access logging are optional and must be aligned with retention and operational requirements.
- Terraform `prevent_destroy` protects the bucket from accidental deletion and is not overridden by `force_destroy`.
- Validate deployed bucket settings and application access independently after every infrastructure change.