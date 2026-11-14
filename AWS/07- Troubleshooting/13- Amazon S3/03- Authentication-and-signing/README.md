# README

## Overview

Amazon S3 authentication and signing troubleshooting covers the diagnostic workflows and corrective procedures for request signing failures, AWS Signature Version 4 validation errors, and credential configuration problems that prevent S3 API requests from authenticating successfully. It addresses `SignatureDoesNotMatch` errors, SigV4 signing mechanics, and misconfigured or expired credentials.

This section provides structured guidance for diagnosing authentication failures: identifying whether the issue originates from credential selection, clock skew, incorrect region configuration, request canonicalization, or SDK and client configuration.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- SignatureDoesNotMatch Error](./01-%20SignatureDoesNotMatch%20Error.md) | Diagnosing HTTP 403 responses caused by a calculated signature that does not match the client-supplied signature |
| 02 | [02- AWS Signature Version 4 Validation](./02-%20AWS%20Signature%20Version%204%20Validation.md) | Understanding SigV4 signing mechanics, canonical request construction, and common validation failure causes |
| 03 | [03- Credential and Request Configuration Issues](./03-%20Credential%20and%20Request%20Configuration%20Issues.md) | Diagnosing authentication failures from incorrect credentials, unexpected provider selection, expired tokens, or region mismatches |

## Why Authentication and Signing Troubleshooting Matters

Authentication failures block all S3 operations regardless of whether the identity would otherwise be authorized. They can originate from the credential provider chain, clock skew, region configuration, SDK version, or incorrect request construction — and all produce similar HTTP 403 responses that are easy to confuse with authorization failures.

Common causes include:

- System clock skew exceeding five minutes, causing the request timestamp to fall outside the SigV4 validity window.
- Credential provider chain resolving to an unexpected identity — environment variable credentials taking precedence over the intended IAM role.
- SDK or client configured with a different region than the bucket's region, causing the signing region to mismatch.
- Presigned URL signed for one region or endpoint and used against another.
- Expired temporary credentials from an assumed role or federated session used after the session duration has elapsed.
- Request body modified after signing, invalidating the payload hash included in the signature.

## Core Troubleshooting Principle

Distinguish authentication failures (`SignatureDoesNotMatch`) from authorization failures (`AccessDenied`) before investigating. Authentication failures indicate the request was not correctly signed; authorization failures indicate the request was signed but the identity lacks permission. Use `aws sts get-caller-identity` to confirm the active credential identity and `aws configure list` to confirm the active region before investigating signing configuration.

## Key Takeaways

- `SignatureDoesNotMatch` is an authentication failure, not an authorization failure — confirm credential identity and region configuration before investigating IAM policies.
- System clock skew over five minutes is the most common cause of unexpected `SignatureDoesNotMatch` errors in automated workloads and containers.
- The credential provider chain resolves credentials in a defined order; environment variables and instance metadata may override the intended identity silently.
