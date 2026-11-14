# README

## Overview

Amazon S3 versioning and lifecycle troubleshooting covers the diagnostic workflows and corrective procedures for failures related to MFA Delete configuration, versioning and delete marker behavior, and lifecycle transition and expiration issues. It addresses the operational misunderstandings and configuration gaps that cause versioned buckets to behave unexpectedly and lifecycle rules to not execute as intended.

This section provides structured guidance for diagnosing versioning and lifecycle failures: understanding what delete markers are, why lifecycle rules may not transition or expire objects, and what prevents MFA Delete from being enabled through normal API calls.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- MFA Delete Enable Failure](./01-%20MFA%20Delete%20Enable%20Failure.md) | Diagnosing failures when enabling MFA Delete on a versioning-enabled bucket, including credential and request requirements |
| 02 | [02- Versioning and Delete Marker Issues](./02-%20Versioning%20and%20Delete%20Marker%20Issues.md) | Diagnosing unexpected versioning behavior, objects not deleted as expected, and delete marker accumulation |
| 03 | [03- Lifecycle Transition and Expiration Issues](./03-%20Lifecycle%20Transition%20and%20Expiration%20Issues.md) | Resolving lifecycle rules that do not transition or expire objects as configured, including versioned object and noncurrent version rules |

## Why Versioning and Lifecycle Troubleshooting Matters

Versioning and lifecycle failures are often silent: objects appear to be deleted but are not, lifecycle rules appear to be configured but objects remain in the wrong storage class, and storage costs grow unexpectedly. These failures frequently surface only when a cost review or recovery attempt reveals that the system did not behave as expected.

Common causes include:

- Delete operation on a versioned bucket creating a delete marker instead of permanently removing the object, causing the key to appear absent but all versions to remain billed.
- Lifecycle rule configured to expire objects but noncurrent versions accumulating indefinitely because no separate noncurrent version expiration rule was added.
- Lifecycle rule filter not matching the intended objects because the prefix does not account for a trailing slash, tag mismatch, or object size constraint.
- MFA Delete enabled but the IAM role used for object deletion cannot supply an MFA code, blocking all delete operations.
- Lifecycle transitions not occurring because the minimum storage duration for the current storage class has not elapsed.
- Lifecycle rules not applying to objects uploaded before the rule was created, because rules only apply to new object writes.

## Core Troubleshooting Principle

For versioning issues, always verify whether versioning is enabled on the bucket before investigating deletion behavior. A delete on a versioning-enabled bucket without a version ID creates a delete marker — not a permanent deletion. Use `aws s3api list-object-versions` to see all versions and delete markers. For lifecycle failures, confirm the rule is enabled, the filter matches the target objects, and the required minimum storage duration has elapsed.

## Key Takeaways

- A delete operation on a versioning-enabled bucket without specifying a version ID creates a delete marker; the object versions remain and continue to incur storage charges.
- Lifecycle rules that expire current versions do not automatically remove noncurrent versions; a separate `NoncurrentVersionExpiration` action is required.
- MFA Delete, once enabled, blocks all unversioned deletes and version deletions that do not supply a valid MFA code — including automated pipelines that cannot provide one.
