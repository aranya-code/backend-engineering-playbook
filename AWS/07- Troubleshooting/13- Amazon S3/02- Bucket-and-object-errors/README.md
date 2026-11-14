# README

## Overview

Amazon S3 bucket and object error troubleshooting covers the diagnostic workflows and corrective procedures for errors that occur when requests cannot resolve the specified bucket or object. It addresses `NoSuchBucket`, `NoSuchKey`, incorrect bucket name and region configuration errors, and AWS CLI profile and account mismatches that cause operations to target unintended resources.

This section provides structured guidance for diagnosing resource resolution failures: confirming the correct bucket name, region, account, and credential context before investigating application or infrastructure configuration.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- NoSuchBucket Error](./01-%20NoSuchBucket%20Error.md) | Diagnosing requests that fail because the bucket name cannot be resolved — incorrect names, deleted buckets, or wrong account and environment |
| 02 | [02- NoSuchKey Error](./02-%20NoSuchKey%20Error.md) | Diagnosing object retrieval, copy, and presigned URL failures caused by missing or incorrectly referenced object keys |
| 03 | [03- Incorrect Bucket Name and Region](./03-%20Incorrect%20Bucket%20Name%20and%20Region.md) | Resolving failures caused by sending requests to the wrong bucket, account, region, or endpoint |
| 04 | [04- AWS CLI Profile and Account Mismatch](./04-%20AWS%20CLI%20Profile%20and%20Account%20Mismatch.md) | Diagnosing CLI operations that use unexpected credentials, profiles, roles, or regions and affect unintended resources |

## Why Bucket and Object Error Troubleshooting Matters

Bucket and object errors frequently appear as application failures, deployment errors, and data pipeline interruptions. They share similar symptoms — 404 or 403 responses — but have distinct root causes. Misidentifying the cause leads to incorrect fixes: recreating a bucket that still exists in a different region, or uploading to a key path that differs from the retrieval path.

Common causes include:

- Application configuration pointing to a bucket name that differs between environments.
- Object key constructed differently during upload and retrieval due to inconsistent path normalization.
- CLI operations executed with the wrong profile, region, or assumed role because environment variables override the default configuration.
- Bucket deleted and not recreated, or created in a different region than expected.
- Presigned URL referencing a key that has been deleted, moved, or never uploaded.

## Core Troubleshooting Principle

Before investigating application code, verify the credential context using `aws sts get-caller-identity`, the target region with `aws configure list`, and that the bucket exists in the expected account and region with `aws s3api head-bucket`. Most bucket and object resolution failures are configuration or deployment issues, not code defects.

## Key Takeaways

- `NoSuchBucket` and `NoSuchKey` errors require confirming the bucket name, region, account, and key path before investigating application logic.
- AWS CLI profile and region mismatches are a common source of operations that silently target the wrong environment.
- Object key construction must be consistent between upload and retrieval; small differences in path normalization, encoding, or prefix construction produce `NoSuchKey` errors.
