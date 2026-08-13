# SSE-KMS

## Why this matters

SSE-KMS ties reads and writes to both S3 and KMS authorization. It improves governance but adds KMS availability, quota, policy, and request-cost considerations.

## Core model

Encryption at rest is a default baseline in S3, but the key choice determines authorization, audit events, quotas, cross-account sharing behavior, and incident blast radius.

## Production design checklist

- Classify data, choose SSE-S3 or SSE-KMS deliberately, constrain encryption headers in policy, and test the KMS path with the same role that writes production data.
- Identify the owner, data classification, caller identity, resource ARN, and recovery objective before enabling the feature.
- Prefer explicit configuration and tests over defaults that are invisible to reviewers.
- Include object key shape, version behavior, and error handling in the application contract whenever this feature affects them.

## Implementation notes

Capture the feature decision in IaC and application configuration. Test allowed and denied requests with the actual workload identity, then add an alert or query that points an on-call engineer to the relevant policy, key, object version, or queue message.

## Operational evidence

Monitor KMS access-denied and throttling errors, encryption type in inventory, and keys scheduled for deletion.

Build a dashboard, query, or runbook that maps this evidence to an owner and a response. A metric without an investigation path is only a graph.

## Common failure modes

Avoid: Treating SSE-S3 and SSE-KMS as interchangeable, or granting broad KMS permissions to compensate for a broken S3 policy.

## Senior engineer perspective

The feature is successful only when its security boundary, cost model, and failure behavior are understandable by the team on call. Document the decision, automate the baseline, and periodically prove that recovery still works.

## Key takeaways

- SSE-KMS ties reads and writes to both S3 and KMS authorization. It improves governance but adds KMS availability, quota, policy, and request-cost considerations.
- Classify data, choose SSE-S3 or SSE-KMS deliberately, constrain encryption headers in policy, and test the KMS path with the same role that writes production data.
- Monitor KMS access-denied and throttling errors, encryption type in inventory, and keys scheduled for deletion.
