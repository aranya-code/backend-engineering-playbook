# README

## Overview

Amazon S3 encryption and KMS troubleshooting covers the diagnostic workflows and corrective procedures for errors that arise from KMS key authorization failures, SSE-KMS access denied responses, and encryption configuration mismatches between bucket defaults, application requests, and deployed object metadata. It addresses the dual authorization requirement introduced by SSE-KMS and the configuration drift that produces unexpected encryption behavior.

This section provides structured guidance for diagnosing encryption failures at both the S3 authorization layer and the KMS key policy layer — two independent boundaries that must both permit the operation for SSE-KMS requests to succeed.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- KMS Access and Encryption Errors](./01-%20KMS%20Access%20and%20Encryption%20Errors.md) | Diagnosing KMS authorization failures, key policy gaps, and encryption errors across SSE-S3, SSE-KMS, and SSE-C |
| 02 | [02- Access Denied During SSE-KMS Operations](./02-%20Access%20Denied%20During%20SSE-KMS%20Operations.md) | Resolving AccessDenied errors where the principal has S3 permissions but lacks KMS key authorization for the encrypted object |
| 03 | [03- Encryption Configuration Mismatches](./03-%20Encryption%20Configuration%20Mismatches.md) | Diagnosing failures caused by conflicting encryption settings between bucket defaults, application headers, object metadata, and key policies |

## Why Encryption and KMS Troubleshooting Matters

SSE-KMS introduces a second authorization boundary that is independent of S3 permissions. An application that has `s3:GetObject` on a bucket will still receive `AccessDenied` if its IAM role lacks `kms:Decrypt` on the key protecting the object. This is one of the most commonly misdiagnosed S3 errors in production because the `AccessDenied` response does not indicate which authorization layer failed.

Common causes include:

- Application IAM role has S3 permissions but is not listed as an authorized principal in the KMS key policy.
- Bucket default encryption uses a KMS key the application role cannot access, causing all new uploads to be stored with a key the same role cannot later decrypt.
- Encryption enforcement bucket policy requires SSE-KMS but the application sends an SSE-S3 header or no encryption header.
- KMS key rotated or deleted after objects were encrypted, making existing encrypted objects permanently inaccessible.
- SSE-C request missing the required encryption key header, or providing a key that does not match the one used during upload.

## Core Troubleshooting Principle

When `AccessDenied` occurs on an SSE-KMS encrypted object, check both layers independently: confirm the S3 permissions first with `aws iam simulate-principal-policy`, then check the KMS key policy with `aws kms get-key-policy` to confirm the application role is an authorized principal for `kms:Decrypt` and `kms:GenerateDataKey`. Never diagnose a KMS access failure by broadening S3 permissions.

## Key Takeaways

- SSE-KMS `AccessDenied` errors require checking both the S3 IAM permissions and the KMS key policy — the S3 layer and the KMS layer are independent authorization boundaries.
- Bucket default encryption with a KMS key that the application role cannot access causes all subsequent uploads to be stored as unreadable by the same application.
- Encryption configuration mismatches between bucket policy enforcement conditions and application-supplied headers are a common cause of upload failures after security controls are tightened.
