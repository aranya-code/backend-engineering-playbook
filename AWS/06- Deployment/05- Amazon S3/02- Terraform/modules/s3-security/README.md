# README

## Overview

The `s3-security` module applies a reusable security and access-control baseline to an existing Amazon S3 bucket.

It centralizes bucket-level security controls, including public access blocking, object ownership enforcement, default encryption, transport security, optional encryption-header enforcement, controlled principal access, CORS, and Requester Pays configuration.

The module is designed to complement a bucket-provisioning module such as `s3-bucket`. It does not create the bucket itself. Instead, it receives the existing bucket name and ARN and manages additional security-related resources.

## Module Structure

```text
modules/
└── s3-security/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── versions.tf
    └── README.md
```

| File | Responsibility |
|---|---|
| `main.tf` | Defines S3 security resources, the bucket policy, and supporting IAM policy document |
| `variables.tf` | Declares module inputs and validation rules |
| `outputs.tf` | Exposes security configuration identifiers and effective module settings |
| `versions.tf` | Defines Terraform and AWS provider version requirements |
| `README.md` | Documents module usage, configuration, and operational considerations |

## Requirements

| Dependency | Requirement |
|---|---|
| Terraform | `>= 1.5.0` |
| AWS provider | `~> 6.0` |
| AWS credentials | Configured through an AWS-supported credential provider |
| Existing S3 bucket | Must exist before this module is applied |
| IAM permissions | Must allow management of the configured S3 security resources |

The calling root module is responsible for configuring the AWS provider and selecting the deployment Region.

The deployment identity must have permissions to manage the bucket's public access block, ownership controls, encryption configuration, bucket policy, CORS configuration, and Requester Pays configuration when enabled.

## Architecture

The module manages security configuration independently of bucket creation.

```mermaid
flowchart TD
    A[Root Terraform Module] --> B[s3-bucket Module]
    A --> C[s3-security Module]

    B --> D[Existing S3 Bucket]
    C --> E[Public Access Block]
    C --> F[Ownership Controls]
    C --> G[Default Encryption]
    C --> H[Bucket Policy]
    C --> I[CORS Configuration]
    C --> J[Requester Pays]

    D --> E
    D --> F
    D --> G
    D --> H
    D --> I
    D --> J
```

The security module references the bucket using:

- `bucket_id`: bucket name or ID used by S3 resources.
- `bucket_arn`: bucket ARN used to construct bucket-level and object-level policy resources.

The bucket must be provisioned before these security resources can be managed.

## Features

| Feature | Implementation |
|---|---|
| Public access protection | Enables all four S3 Block Public Access settings |
| Object ownership | Configures `BucketOwnerEnforced` |
| Default encryption | Supports SSE-S3 and SSE-KMS |
| S3 Bucket Keys | Supports configurable Bucket Keys for SSE-KMS |
| Transport security | Denies requests that do not use secure transport |
| Encryption-header enforcement | Optionally denies uploads that omit required encryption headers |
| KMS key enforcement | Optionally denies uploads that specify an incorrect KMS key |
| Principal access | Grants configured S3 actions to explicitly supplied IAM role or user ARNs |
| CORS | Supports optional browser-based cross-origin access rules |
| Requester Pays | Supports optional Requester Pays configuration |

## Input Variables

The module exposes its configuration through `variables.tf`.

| Variable | Type | Default | Description |
|---|---|---|---|
| `bucket_id` | `string` | Required | Name or ID of the existing S3 bucket |
| `bucket_arn` | `string` | Required | ARN of the existing S3 bucket |
| `kms_key_arn` | `string` | `null` | Customer-managed KMS key ARN; null selects SSE-S3 |
| `bucket_key_enabled` | `bool` | `true` | Enables S3 Bucket Keys when SSE-KMS is configured |
| `enforce_encryption_header` | `bool` | `false` | Enforces encryption headers on object uploads |
| `allowed_principal_arns` | `set(string)` | `[]` | IAM role or user ARNs granted access through the bucket policy |
| `allowed_actions` | `set(string)` | See below | S3 actions granted to configured principals |
| `cors_rules` | `list(object(...))` | `[]` | Optional CORS configuration |
| `request_payer_enabled` | `bool` | `false` | Enables Requester Pays |
| `tags` | `map(string)` | `{}` | Reserved metadata used by the module's `common_tags` local |

The default `allowed_actions` value is:

```hcl
[
  "s3:GetObject",
  "s3:PutObject",
  "s3:ListBucket"
]
```

### Supported S3 Actions

The module validates `allowed_actions` against this supported set:

| Action | Resource scope | Purpose |
|---|---|---|
| `s3:ListBucket` | Bucket | Lists bucket objects |
| `s3:ListBucketVersions` | Bucket | Lists object versions |
| `s3:GetBucketLocation` | Bucket | Retrieves bucket Region information |
| `s3:GetObject` | Object | Downloads objects |
| `s3:GetObjectVersion` | Object | Retrieves a specific object version |
| `s3:PutObject` | Object | Uploads objects |
| `s3:DeleteObject` | Object | Deletes objects |
| `s3:DeleteObjectVersion` | Object | Deletes a specific object version |

The module constructs bucket-level and object-level resource ARNs based on the configured actions.

It does not support arbitrary S3 actions through `allowed_actions`. Extend the validation and resource-scope mapping deliberately if additional actions are required.

## Usage

Reference the module from a root Terraform configuration after provisioning the bucket.

```hcl
module "application_files_bucket" {
  source = "./modules/s3-bucket"

  bucket_name = "company-prod-application-files-2026"

  versioning_enabled = true

  tags = {
    Project     = "application-platform"
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}

module "application_files_security" {
  source = "./modules/s3-security"

  bucket_id  = module.application_files_bucket.bucket_id
  bucket_arn = module.application_files_bucket.bucket_arn

  allowed_principal_arns = [
    "arn:aws:iam::123456789012:role/application-api-role"
  ]

  allowed_actions = [
    "s3:GetObject",
    "s3:PutObject",
    "s3:ListBucket"
  ]

  depends_on = [
    module.application_files_bucket
  ]
}
```

The explicit dependency ensures that the bucket module completes before the security module is applied.

The root module must configure the AWS provider:

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

## Public Access Protection

The module enables all four S3 Block Public Access settings:

```hcl
block_public_acls       = true
ignore_public_acls      = true
block_public_policy     = true
restrict_public_buckets = true
```

These settings reduce the risk of accidental public exposure through bucket policies or ACL-based access.

The module also configures `BucketOwnerEnforced` object ownership, disabling ACL-based access management for the bucket.

### Production Considerations

- Keep all four public access block settings enabled for private application storage.
- Use IAM policies and bucket policies for access control rather than ACLs.
- Review existing applications before enabling `BucketOwnerEnforced`, particularly if they depend on object ACLs.
- Do not assume that public access blocking replaces least-privilege IAM policies.

## Object Ownership

The module configures:

```hcl
rule {
  object_ownership = "BucketOwnerEnforced"
}
```

This makes the bucket owner responsible for ownership of uploaded objects and disables ACLs.

This is appropriate for most modern application storage architectures.

Applications that explicitly send ACL headers, such as `x-amz-acl`, may need to remove those headers to avoid upload failures.

## Default Encryption

The module configures default bucket encryption.

### SSE-S3

When `kms_key_arn` is `null`, the module uses SSE-S3:

```hcl
kms_key_arn = null
```

The resulting encryption algorithm is `AES256`.

### SSE-KMS

To use a customer-managed KMS key:

```hcl
module "sensitive_documents_security" {
  source = "./modules/s3-security"

  bucket_id  = "company-prod-sensitive-documents-2026"
  bucket_arn = "arn:aws:s3:::company-prod-sensitive-documents-2026"

  kms_key_arn       = "arn:aws:kms:ap-south-1:123456789012:key/00000000-0000-0000-0000-000000000000"
  bucket_key_enabled = true
}
```

S3 Bucket Keys can reduce the number of KMS requests associated with SSE-KMS workloads.

### KMS Permissions

The module configures the bucket's default encryption but does not create or manage the KMS key.

Verify that:

- The KMS key exists in the bucket's Region.
- The key is enabled.
- The key policy permits the required principals.
- Application IAM policies permit the necessary KMS operations.
- Cross-account workloads have compatible S3 and KMS permissions.

S3 authorization and KMS authorization are separate permission checks. An application can have `s3:GetObject` permission and still fail to retrieve an SSE-KMS encrypted object because it lacks the required KMS permissions.

## Transport Security

The module creates a bucket policy statement named `DenyInsecureTransport`.

It denies S3 actions against the bucket and its objects when:

```text
aws:SecureTransport = false
```

This requires clients to use HTTPS rather than insecure HTTP transport.

Applications should use AWS SDKs and HTTPS endpoints. Avoid disabling certificate verification or bypassing TLS validation in application code.

## Encryption Header Enforcement

By default, `enforce_encryption_header` is `false`.

When enabled, the module adds bucket policy statements that enforce encryption headers on object uploads.

For SSE-S3, the policy denies uploads that omit the encryption header.

For SSE-KMS, the policy additionally requires:

- The encryption algorithm to be `aws:kms`.
- The specified KMS key identifier to match `kms_key_arn`.

Example:

```hcl
module "application_files_security" {
  source = "./modules/s3-security"

  bucket_id  = "company-prod-application-files-2026"
  bucket_arn = "arn:aws:s3:::company-prod-application-files-2026"

  kms_key_arn                = "arn:aws:kms:ap-south-1:123456789012:key/00000000-0000-0000-0000-000000000000"
  enforce_encryption_header = true
}
```

### Important Operational Consideration

S3 default bucket encryption already encrypts new objects when an upload does not specify an encryption header.

Therefore, encryption-header enforcement is a stricter client contract, not a prerequisite for default encryption.

Before enabling it, verify that every upload path supplies the required headers, including:

- Backend API uploads.
- Presigned URL uploads.
- Multipart upload workflows.
- Batch processing jobs.
- Third-party integrations.

A client that relies on bucket default encryption but omits the encryption headers will be denied when this enforcement is enabled.

## Principal Access

The module can add explicit bucket policy statements for configured IAM principals.

Example:

```hcl
module "application_files_security" {
  source = "./modules/s3-security"

  bucket_id  = "company-prod-application-files-2026"
  bucket_arn = "arn:aws:s3:::company-prod-application-files-2026"

  allowed_principal_arns = [
    "arn:aws:iam::123456789012:role/application-api-role",
    "arn:aws:iam::123456789012:role/document-processing-role"
  ]

  allowed_actions = [
    "s3:GetObject",
    "s3:PutObject",
    "s3:ListBucket"
  ]
}
```

The module generates a separate allow statement for each configured principal.

### Resource Scope

The module maps actions to their corresponding resource types:

- Bucket-level actions are granted against the bucket ARN.
- Object-level actions are granted against the bucket's object ARN pattern.

This distinction matters because S3 bucket operations and object operations use different resource scopes.

### IAM and Bucket Policy Interaction

The generated bucket policy does not replace identity-based IAM policies.

A successful request may depend on multiple authorization layers:

- The principal's identity-based IAM permissions.
- The bucket's resource-based policy.
- Any applicable organization-level or account-level controls.
- KMS permissions when the object uses SSE-KMS.

Explicit denies take precedence over allows.

The module's insecure-transport and optional encryption-enforcement statements apply regardless of the configured principal allow statements.

### Important Bucket Policy Ownership Consideration

The `aws_s3_bucket_policy` resource manages the bucket's complete policy document.

Do not manage the same bucket policy independently from another Terraform module or resource. Multiple Terraform resources attempting to own the same bucket policy can overwrite each other's configuration or create persistent drift.

If the bucket already has a policy, consolidate all required statements into one authoritative policy configuration before applying this module.

## CORS Configuration

CORS is optional. When `cors_rules` is empty, the module does not create an S3 CORS configuration resource.

Example:

```hcl
module "application_files_security" {
  source = "./modules/s3-security"

  bucket_id  = "company-prod-application-files-2026"
  bucket_arn = "arn:aws:s3:::company-prod-application-files-2026"

  cors_rules = [
    {
      id              = "application-upload-download"
      allowed_origins = ["https://app.example.com"]
      allowed_methods = ["GET", "PUT", "HEAD"]
      allowed_headers = ["Content-Type", "Authorization"]
      expose_headers  = ["ETag"]
      max_age_seconds = 3600
    }
  ]
}
```

Supported rule attributes:

| Attribute | Type | Default | Description |
|---|---|---|---|
| `id` | `string` | `null` | Optional rule identifier |
| `allowed_headers` | `list(string)` | `["*"]` | Allowed request headers |
| `allowed_methods` | `list(string)` | Required | Permitted HTTP methods |
| `allowed_origins` | `list(string)` | Required | Permitted browser origins |
| `expose_headers` | `list(string)` | `[]` | Response headers exposed to browsers |
| `max_age_seconds` | `number` | `3000` | Browser preflight cache duration |

The module validates supported HTTP methods, non-empty origins and headers, unique optional rule IDs, and a maximum age between zero and 86400 seconds.

### Production Considerations

- Avoid wildcard origins for authenticated application workflows.
- Allow only the HTTP methods required by the frontend.
- Restrict allowed headers to those actually used by the application.
- Remember that CORS is a browser-enforced cross-origin policy, not an authorization mechanism.
- IAM and bucket policies must still authorize the underlying S3 request.

## Requester Pays

Requester Pays is disabled by default.

Enable it when the bucket owner wants eligible requesters to pay applicable request and data transfer charges.

```hcl
module "shared_dataset_security" {
  source = "./modules/s3-security"

  bucket_id  = "company-shared-dataset-2026"
  bucket_arn = "arn:aws:s3:::company-shared-dataset-2026"

  request_payer_enabled = true
}
```

Clients accessing a Requester Pays bucket must use the appropriate request-payer setting, such as the AWS CLI `--request-payer requester` option.

Requester Pays is generally unsuitable for ordinary application-facing buckets where the application expects transparent access without requester billing requirements.

## Outputs

The module exposes the following outputs through `outputs.tf`.

| Output | Description |
|---|---|
| `public_access_block_id` | Public access block configuration identifier |
| `ownership_controls_id` | Object ownership configuration identifier |
| `server_side_encryption_configuration_id` | Default encryption configuration identifier |
| `bucket_policy_id` | Managed bucket policy identifier |
| `bucket_policy_json` | Rendered bucket policy JSON |
| `cors_configuration_id` | CORS configuration identifier, or `null` |
| `request_payment_configuration_id` | Requester Pays configuration identifier, or `null` |
| `encryption_algorithm` | Configured encryption algorithm |
| `kms_key_arn` | Configured KMS key ARN, or `null` |
| `bucket_key_enabled` | Whether S3 Bucket Keys are enabled |
| `public_access_block_enabled` | Indicates that all four public access block settings are enabled |
| `object_ownership` | Configured object ownership mode |
| `allowed_principal_arns` | Configured IAM principal ARNs |
| `allowed_actions` | Configured S3 actions |
| `cors_enabled` | Whether CORS rules are configured |
| `request_payer_enabled` | Whether Requester Pays is enabled |

The rendered bucket policy output is marked sensitive in Terraform to avoid displaying the full policy in ordinary output contexts.

## Deployment Workflow

Run Terraform commands from the root module that references `s3-security`.

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

Review changes carefully, especially:

- Public access block configuration.
- Object ownership changes.
- Encryption algorithm and KMS key changes.
- Bucket policy additions or replacement.
- Principal permissions.
- CORS rules.
- Requester Pays configuration.

### Apply

```bash
terraform apply
```

Apply only after reviewing the plan and confirming that the bucket's existing access patterns remain compatible with the proposed configuration.

## Verification

Use the AWS CLI to inspect the deployed configuration.

Set the bucket name:

```bash
BUCKET_NAME="company-prod-application-files-2026"
```

### Verify Public Access Block

```bash
aws s3api get-public-access-block \
  --bucket "$BUCKET_NAME"
```

All four settings should be enabled.

### Verify Object Ownership

```bash
aws s3api get-bucket-ownership-controls \
  --bucket "$BUCKET_NAME"
```

Expected ownership mode:

```json
{
  "Rules": [
    {
      "ObjectOwnership": "BucketOwnerEnforced"
    }
  ]
}
```

### Verify Default Encryption

```bash
aws s3api get-bucket-encryption \
  --bucket "$BUCKET_NAME"
```

Check the configured algorithm and KMS key, if applicable.

### Verify Bucket Policy

```bash
aws s3api get-bucket-policy \
  --bucket "$BUCKET_NAME" \
  --query Policy \
  --output text
```

Inspect the policy for:

- Insecure transport denial.
- Optional encryption enforcement.
- Configured principal allow statements.
- Correct bucket and object resource ARNs.

### Verify CORS

```bash
aws s3api get-bucket-cors \
  --bucket "$BUCKET_NAME"
```

This command returns an error when no CORS configuration exists. That is expected when `cors_rules` is empty.

### Verify Requester Pays

```bash
aws s3api get-bucket-request-payment \
  --bucket "$BUCKET_NAME"
```

Check whether the payer is configured as `BucketOwner` or `Requester`.

## Security Considerations

- Use IAM roles and temporary credentials rather than long-lived access keys.
- Grant only the S3 actions required by each application workload.
- Keep all four Block Public Access settings enabled for private buckets.
- Use `BucketOwnerEnforced` unless an explicit ACL-based requirement exists.
- Require HTTPS for all S3 requests.
- Use SSE-KMS when customer-managed key control is required.
- Keep KMS key policies and IAM permissions aligned with application access requirements.
- Restrict CORS origins and methods.
- Avoid wildcard principal permissions.
- Review existing bucket policies before allowing this module to manage the complete policy.
- Do not treat CORS as an access-control mechanism.
- Do not enable encryption-header enforcement until all upload clients support the required headers.

## Common Mistakes

| Mistake | Impact | Prevention |
|---|---|---|
| Applying the module before creating the bucket | Security resources cannot reference the bucket | Establish an explicit dependency on the bucket module |
| Managing the bucket policy from multiple Terraform resources | Policy statements can overwrite each other | Maintain one authoritative bucket policy resource |
| Enabling `BucketOwnerEnforced` without checking clients | ACL-dependent uploads can fail | Remove ACL headers and migrate ACL-dependent workflows |
| Enabling encryption-header enforcement without updating clients | Upload requests can be denied | Update and test every upload path first |
| Assuming default encryption requires client headers | Unnecessary upload failures | Use default encryption unless strict header enforcement is required |
| Omitting KMS permissions | Encrypted object access fails | Validate both S3 and KMS authorization |
| Allowing wildcard CORS origins | Unnecessary browser access exposure | Restrict origins, methods, and headers |
| Treating CORS as authorization | Unauthorized access assumptions | Enforce IAM and bucket policy permissions independently |
| Enabling Requester Pays without client changes | Requests can fail | Configure clients to identify themselves as requesters |
| Granting bucket-level actions on object ARNs | IAM authorization fails | Match each action to its correct resource scope |

## Production Considerations

### Terraform Resource Ownership

Assign one Terraform module or configuration as the authoritative owner of each bucket-level setting.

For example, the bucket module may own bucket creation, versioning, and lifecycle configuration, while this security module owns public access blocking, ownership controls, encryption, and the bucket policy.

Avoid managing the same S3 configuration from multiple modules.

### Existing Bucket Migration

When adopting this module for an existing bucket:

1. Inspect the current bucket policy.
2. Review ACL usage and object ownership.
3. Inspect default encryption and KMS dependencies.
4. Review existing CORS configuration.
5. Identify applications that upload objects directly.
6. Review existing Requester Pays behavior.
7. Consolidate Terraform ownership before applying changes.

Changes to ownership controls, encryption, and bucket policies can affect existing applications even when no objects are modified.

### Application Compatibility

For backend applications using Boto3, Django, FastAPI, or Celery:

- Use IAM roles for runtime credentials.
- Configure the expected encryption behavior in the upload service.
- Avoid setting ACLs when `BucketOwnerEnforced` is active.
- Test presigned URL uploads against the configured CORS and encryption policies.
- Handle `AccessDenied` separately from KMS authorization failures.
- Include integration tests for upload, download, and deletion workflows.

### Policy Size and Complexity

Bucket policies have service-defined size limits. As the number of principals and statements grows, review the rendered policy and consider whether access points, IAM identity policies, or a different authorization design would be more maintainable.

### Change Management

Security configuration changes should be reviewed through Terraform plans and deployed through controlled environments.

Do not make manual console changes to settings that Terraform owns unless the change is part of a documented emergency procedure followed by state reconciliation.

## Key Takeaways

- The `s3-security` module secures an existing bucket; it does not create the bucket.
- Public access blocking, `BucketOwnerEnforced`, default encryption, and HTTPS enforcement establish the core security baseline.
- S3 bucket policies and KMS key policies enforce separate authorization layers.
- Encryption-header enforcement is stricter than default encryption and requires compatible upload clients.
- Maintain one authoritative Terraform owner for the bucket policy and each bucket-level configuration.