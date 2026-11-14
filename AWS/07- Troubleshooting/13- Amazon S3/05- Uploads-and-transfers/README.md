# README

## Overview

Amazon S3 upload and transfer troubleshooting covers the diagnostic workflows and corrective procedures for failures during object uploads, downloads, multipart upload workflows, and synchronization and copy operations. It addresses multipart upload failures and incomplete part accumulation, single-object upload and download errors, and the silent data modification and permission-related issues that arise during `aws s3 sync` and `aws s3 cp` operations.

This section provides structured guidance for diagnosing transfer failures across their multiple root causes: authorization, encryption, network interruption, request size, metadata handling, and incorrect path or prefix configuration.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Multipart Upload Failures](./01-%20Multipart%20Upload%20Failures.md) | Diagnosing incomplete multipart uploads, failed part uploads, assembly errors, and abandoned upload cost accumulation |
| 02 | [02- Upload and Download Failures](./02-%20Upload%20and%20Download%20Failures.md) | Resolving upload and download failures caused by authorization, encryption, signing, network, or transfer limit issues |
| 03 | [03- S3 Sync and Copy Issues](./03-%20S3%20Sync%20and%20Copy%20Issues.md) | Diagnosing incorrect sync behavior, unexpected deletions, path mismatches, metadata loss, and permission failures in sync and copy operations |

## Why Upload and Transfer Troubleshooting Matters

Transfer failures disrupt data ingestion pipelines, deployment workflows, backup jobs, and application uploads. They are often intermittent, hard to reproduce in development, and can silently accumulate incomplete multipart upload parts that generate ongoing storage charges. Sync and copy operations that behave unexpectedly can overwrite or delete production data without error.

Common causes include:

- Multipart upload initiated but never completed or aborted, leaving parts stored and billed indefinitely with no lifecycle rule to clean them up.
- Upload failing after the presigned URL expiry window without the client detecting and retrying.
- `aws s3 sync` deleting objects at the destination that do not exist at the source because `--delete` was included without reviewing the scope first.
- Copy operation dropping user-defined metadata because `COPY` directive was used instead of `REPLACE`.
- Network interruption mid-transfer not retried because the SDK retry configuration was not set correctly.
- Encryption mismatch between what the bucket policy requires and what the upload request specifies, causing every upload to fail.

## Core Troubleshooting Principle

For upload failures, confirm authorization, encryption configuration, and request size before investigating network or SDK issues. For sync and copy operations, always use `--dryrun` to preview the planned changes before executing against production data. For multipart upload failures, check for incomplete uploads using `aws s3api list-multipart-uploads` and ensure a lifecycle rule is configured to abort them automatically.

## Key Takeaways

- Incomplete multipart uploads accumulate storage charges indefinitely without a lifecycle abort rule; always check for abandoned parts when investigating unexpected S3 costs.
- `aws s3 sync --delete` removes objects at the destination not present at the source; always run with `--dryrun` before executing against production buckets.
- Copy operations must specify `--metadata-directive REPLACE` to update user-defined metadata; `COPY` preserves the original metadata regardless of what is specified in the command.
