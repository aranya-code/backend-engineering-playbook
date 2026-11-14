# README

## Overview

Amazon S3 troubleshooting covers the diagnostic workflows and corrective procedures for the failures that occur most frequently in production S3-backed systems. It addresses access control errors, bucket and object resolution failures, authentication and signing issues, encryption and KMS authorization failures, upload and transfer problems, versioning and lifecycle behavior, and replication configuration failures.

This section of the Backend Engineering Playbook provides a structured reference for backend engineers, platform engineers, and operations teams who need to diagnose and resolve S3 failures systematically in production environments.

The focus is on practical failure diagnosis: identifying the correct layer to investigate first, using the right diagnostic commands, and making targeted minimal fixes rather than broadening permissions or disabling controls to work around the symptom.

## Navigation

| # | Folder | Description |
|---|---|---|
| 01 | [01- Access-control](./01-%20Access-control/) | Diagnosing AccessDenied errors, IAM and bucket policy permission failures, and cross-account access failures |
| 02 | [02- Bucket-and-object-errors](./02-%20Bucket-and-object-errors/) | Resolving NoSuchBucket, NoSuchKey, incorrect region configuration, and AWS CLI profile and account mismatches |
| 03 | [03- Authentication-and-signing](./03-%20Authentication-and-signing/) | Diagnosing SignatureDoesNotMatch errors, SigV4 validation failures, and credential and request configuration issues |
| 04 | [04- Encryption-and-kms](./04-%20Encryption-and-kms/) | Resolving KMS access errors, SSE-KMS AccessDenied failures, and encryption configuration mismatches |
| 05 | [05- Uploads-and-transfers](./05-%20Uploads-and-transfers/) | Diagnosing multipart upload failures, upload and download errors, and S3 sync and copy issues |
| 06 | [06- Versioning-and-lifecycle](./06-%20Versioning-and-lifecycle/) | Resolving MFA Delete configuration failures, versioning and delete marker behavior, and lifecycle rule issues |
| 07 | [07- Replication](./07-%20Replication/) | Diagnosing Cross-Region and Same-Region Replication failures, permission gaps, and replication status inspection |

## Why S3 Troubleshooting Matters

S3 failures span multiple independent layers — IAM, KMS, bucket configuration, request signing, object versioning, lifecycle rules, and replication — and similar symptoms can have very different root causes. An `AccessDenied` response may originate from an IAM policy, a bucket policy, a KMS key policy, an SCP, or Block Public Access. A missing object may be a key mismatch, a versioning delete marker, or a replication that never occurred.

Diagnosing failures incorrectly leads to the wrong fix: broadening permissions when the issue is a signing error, recreating a bucket that exists in a different region, or disabling encryption to work around a KMS key policy gap. Each wrong fix introduces new risk while leaving the original problem unresolved.

Common production failure patterns include:

- `AccessDenied` on SSE-KMS objects where the application has S3 permissions but the IAM role is not in the KMS key policy.
- `NoSuchKey` caused by inconsistent object key construction between the upload and retrieval code paths.
- `SignatureDoesNotMatch` from a container with clock skew that exceeds the SigV4 five-minute validity window.
- Objects apparently deleted but still accumulating storage charges because versioning created delete markers instead of permanent deletions.
- Replication silently failing because objects were uploaded before the replication rule was enabled.
- Lifecycle rules configured but not executing because the filter prefix does not match the actual object key structure.

## Documentation Structure

| Area | Primary focus |
|---|---|
| Access control | IAM policy gaps, bucket policy conflicts, explicit denies, and cross-account authorization |
| Bucket and object errors | Resource resolution failures, region mismatches, and incorrect credential context |
| Authentication and signing | SigV4 signing failures, clock skew, credential provider chain, and region configuration |
| Encryption and KMS | Dual authorization failures, KMS key policy gaps, and encryption configuration conflicts |
| Uploads and transfers | Multipart failures, transfer errors, sync behavior, and metadata handling |
| Versioning and lifecycle | Delete marker behavior, lifecycle rule matching, and MFA Delete operational impact |
| Replication | Configuration gaps, IAM role permissions, destination policy requirements, and object eligibility |

## Core Troubleshooting Principles

### Identify the Layer Before Investigating

S3 errors from different layers produce similar HTTP responses. Before investigating permissions, confirm whether the failure is an authentication error (`SignatureDoesNotMatch`), an authorization error (`AccessDenied`), or a resource resolution error (`NoSuchBucket`, `NoSuchKey`). Each requires a different diagnostic path.

### Confirm Identity and Context First

Before investigating any S3 failure, run `aws sts get-caller-identity` to confirm the active credential identity and `aws configure list` to confirm the active region. Most bucket and object resolution errors and many access failures originate from the wrong credential context or region rather than a misconfigured policy.

### Never Fix AccessDenied with Broad Permissions

Identify the specific principal, action, resource, and policy boundary causing the denial before making any permission change. Use `aws iam simulate-principal-policy`, CloudTrail, and the IAM policy simulator to diagnose the exact cause. A broad permission grant fixes the symptom while creating unnecessary security risk and making the underlying configuration harder to audit.

### Check Both Layers for SSE-KMS Failures

SSE-KMS `AccessDenied` errors require checking the S3 IAM permissions and the KMS key policy independently. Having `s3:GetObject` does not grant the right to decrypt an SSE-KMS object. The application IAM role must also be authorized in the KMS key policy with `kms:Decrypt`.

### Use Diagnostic Commands Before Changing Configuration

Use `aws s3api head-bucket`, `aws s3api head-object`, `aws s3api list-object-versions`, `aws s3api list-multipart-uploads`, and `aws s3api get-bucket-replication` to inspect the current state before making changes. Many failures are explained by observable state that does not require changing any configuration to understand.

## Key Takeaways

- S3 failures span multiple independent layers; diagnosing the wrong layer produces the wrong fix and introduces additional risk.
- Confirm credential identity and region context before investigating any S3 failure — most resource resolution errors are credential or configuration issues, not policy defects.
- SSE-KMS errors require checking both S3 IAM permissions and KMS key policy independently; a grant at one layer does not imply a grant at the other.
- Never resolve `AccessDenied` by granting broad permissions; identify the exact principal, action, resource, and policy boundary, then make a targeted minimal change.
- Many versioning, lifecycle, and replication failures are silent and only discovered during cost reviews or recovery tests — establish monitoring and periodic audits rather than relying on application errors to surface them.
