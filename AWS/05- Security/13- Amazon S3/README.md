# README

## Overview

Amazon S3 security covers the access control mechanisms, encryption options, key management design, and validation workflows required to protect object data against unauthorized access, accidental public exposure, privilege escalation, and cryptographic failures in production environments.

This section of the Backend Engineering Playbook provides a structured reference for backend engineers, security engineers, and platform teams who design, implement, and audit security controls for S3-backed applications handling sensitive, regulated, or business-critical data.

The focus is on practical security engineering: understanding how S3 evaluates authorization across multiple policy types, selecting and configuring the correct encryption mechanism for each workload, designing KMS key permissions that work correctly at runtime, and validating that security controls are applied as intended after deployment.

## Navigation

| # | Folder | Description |
|---|---|---|
| 01 | [01- Access-control](./01-%20Access-control/) | IAM permissions, bucket policies, Block Public Access, Object Ownership, Access Analyzer, access points, cross-account access, and least privilege design |
| 02 | [02- Encryption](./02-%20Encryption/) | SSE-S3, SSE-KMS, SSE-C, client-side encryption, KMS integration, key permissions, and encryption configuration validation |

## Why S3 Security Matters

Amazon S3 stores application files, user uploads, backups, audit logs, deployment artifacts, and sensitive business data. A single misconfiguration in either the access control or encryption layer can expose that data publicly, grant unintended cross-account access, or prevent legitimate application access entirely.

Common security risks include:

- Buckets exposed publicly through misconfigured bucket policies or ACLs that grant access to `*` without Block Public Access enforcement.
- Application roles with wildcard resource permissions that grant access to every bucket in the account rather than the specific bucket the application owns.
- SSE-KMS objects that cannot be decrypted at runtime because the application role lacks `kms:Decrypt` permission on the KMS key, causing unexpected access failures in production.
- Cross-account object uploads where the uploading account retains object ownership, preventing the bucket owner from reading or managing the objects.
- Encryption configuration changes that do not retroactively apply to existing objects, leaving previously uploaded data unprotected without detection.
- Access Analyzer findings left unreviewed, allowing public or cross-account exposure to persist undetected over time.

Effective S3 security requires coordinating access control and encryption as complementary layers — neither is sufficient alone. A private bucket with unmanaged encryption key permissions is not secure. Encryption without scoped access control does not prevent unauthorized access.

## Documentation Structure

| Area | Primary focus |
|---|---|
| Access control | IAM and bucket policy design, Block Public Access, Object Ownership, and access boundary enforcement |
| Encryption | Encryption mechanism selection, KMS key permission design, and post-deployment validation |

## Core Security Principles

### Defense in Depth Across Both Layers

Access control and encryption address different threat surfaces. Access control determines which principals can reach objects. Encryption protects object data if storage media or access controls are compromised. Both must be configured correctly and validated independently.

### Block Public Access Is the First Safeguard

Enable all four Block Public Access settings at the AWS account level before deploying any bucket. This provides a safety net against bucket policies or ACLs that inadvertently grant public access. Bucket-level overrides should require explicit review and justification.

### KMS Key Permissions Are a Second Authorization Boundary

SSE-KMS introduces a second authorization check beyond S3 permissions: the KMS key policy. An application role that has full S3 permissions but lacks `kms:GenerateDataKey` and `kms:Decrypt` on the key will fail to upload or download encrypted objects. Design IAM policies and KMS key policies together and test both upload and download operations after every deployment.

### Validate Security Configuration After Every Change

Enabling default encryption or modifying access controls does not retroactively affect existing objects or prove that new objects will be handled correctly. Validate bucket configuration, object encryption status, and access control settings after every deployment using Access Analyzer, S3 Inventory, and CLI inspection.

## Key Takeaways

- S3 security requires coordinating IAM identity policies, bucket policies, Block Public Access, Object Ownership, and encryption — omitting any layer creates a gap that the others do not cover.
- Block Public Access at the account level is the most effective safeguard against accidental public bucket exposure and should be the default for every AWS account.
- SSE-KMS introduces a second authorization boundary through KMS key policies; application roles need both S3 and KMS permissions to operate on encrypted objects.
- Security configuration changes do not retroactively protect existing objects; validate encryption status and access configuration after every deployment.
- Access Analyzer findings must be reviewed regularly — unresolved findings represent persistent exposure that preventive controls alone will not catch.
