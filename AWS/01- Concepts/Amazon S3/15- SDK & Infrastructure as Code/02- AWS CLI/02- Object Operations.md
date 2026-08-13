# Object Operations

## Why this matters

Use head-object for a precise metadata or existence check; list operations are not an authorization or transaction primitive. Prefer version-aware actions for recovery-sensitive data.

## Core model

SDK calls and infrastructure definitions are production interfaces. Pin their behavior with retries, timeouts, idempotency, policy tests, and drift detection.

## Production design checklist

- Use a reusable bucket baseline, explicit encryption and public-access controls, least-privilege roles, and integration tests in a non-production account.
- Identify the owner, data classification, caller identity, resource ARN, and recovery objective before enabling the feature.
- Prefer explicit configuration and tests over defaults that are invisible to reviewers.
- Include object key shape, version behavior, and error handling in the application contract whenever this feature affects them.

## Implementation notes

Use aws s3api for exact configuration and aws s3 for high-level copy or sync. Confirm identity with aws sts get-caller-identity, use --region deliberately, inspect before mutation, and run sync with --dryrun before --delete.

## Operational evidence

Monitor deployment drift, failed API calls by error code, aborted multipart uploads, and policy-analysis findings.

Build a dashboard, query, or runbook that maps this evidence to an owner and a response. A metric without an investigation path is only a graph.

## Common failure modes

Avoid: Relying on console-only settings or using an SDK default as an undocumented security policy.

## Senior engineer perspective

The feature is successful only when its security boundary, cost model, and failure behavior are understandable by the team on call. Document the decision, automate the baseline, and periodically prove that recovery still works.

## Key takeaways

- Use head-object for a precise metadata or existence check; list operations are not an authorization or transaction primitive. Prefer version-aware actions for recovery-sensitive data.
- Use a reusable bucket baseline, explicit encryption and public-access controls, least-privilege roles, and integration tests in a non-production account.
- Monitor deployment drift, failed API calls by error code, aborted multipart uploads, and policy-analysis findings.
