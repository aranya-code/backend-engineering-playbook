# README

## Overview

Amazon S3 access control troubleshooting covers the diagnostic workflows and corrective procedures for authorization failures that prevent legitimate requests from succeeding. It addresses `AccessDenied` errors from S3 API calls, IAM identity policy and bucket policy conflicts, and cross-account access failures across centralized storage architectures and multi-account environments.

This section provides structured guidance for diagnosing S3 authorization failures systematically: identifying the principal, the action, the resource, and the applicable policy boundary before making any permission change.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Access Denied and AccessDenied Errors](./01-%20Access%20Denied%20and%20AccessDenied%20Errors.md) | Diagnosing HTTP 403 AccessDenied responses across uploads, downloads, listings, deletions, and bucket configuration operations |
| 02 | [02- IAM and Bucket Policy Permission Failures](./02-%20IAM%20and%20Bucket%20Policy%20Permission%20Failures.md) | Resolving authorization failures caused by policy gaps, explicit denies, incorrect ARNs, conditions, and cross-account requirements |
| 03 | [03- Cross-Account Access Failures](./03-%20Cross-Account%20Access%20Failures.md) | Diagnosing cross-account access failures in centralized storage, shared data platforms, backups, and analytics pipelines |

## Why Access Control Troubleshooting Matters

Access control failures are among the most common and disruptive S3 errors in production. They surface as application errors, deployment failures, data pipeline stalls, and security incidents. Resolving them by granting broad permissions is a security risk; resolving them systematically by identifying the exact policy boundary is the correct approach.

Common causes include:

- Missing IAM action on the identity policy with no matching bucket policy grant to compensate.
- Explicit deny in an SCP, permission boundary, or bucket policy that overrides an allow elsewhere.
- Cross-account access where only one side of the required policy pair — identity policy or bucket policy — is configured.
- Incorrect resource ARN in the policy that does not match the actual bucket or prefix.
- Bucket Owner Enforced mode preventing cross-account callers from accessing objects they uploaded.

## Core Troubleshooting Principle

Never resolve an `AccessDenied` error by attaching `AdministratorAccess` or adding `Action: "*"`. Identify the principal using `aws sts get-caller-identity`, the failing action, the resource ARN, and the applicable policy boundaries. Use `aws iam simulate-principal-policy` and CloudTrail to diagnose the exact cause before making a targeted, minimal permission change.

## Key Takeaways

- `AccessDenied` from S3 can originate from IAM identity policies, bucket policies, SCPs, permission boundaries, Block Public Access, or KMS key policies — each requires a different fix.
- Cross-account access requires both an identity policy grant and a bucket policy grant; configuring only one side is the most common cross-account failure.
- Explicit denies always win; an allow elsewhere in the policy chain does not override an explicit deny.
