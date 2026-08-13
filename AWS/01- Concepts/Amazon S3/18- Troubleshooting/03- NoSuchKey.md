# NoSuchKey

## Why this matters

NoSuchKey is an exact-key mismatch, not a directory lookup failure. Check encoding, case, prefix, version state, and whether the writer completed before publishing a reference.

## Core model

S3 failures are usually deterministic once request identity, action, resource ARN, region, encryption headers, endpoint, and explicit denies are inspected together.

## Production design checklist

- Capture request IDs, reproduce with the intended role, use policy simulation and CloudTrail, and change one dimension at a time. Do not broaden permissions as a first response.
- Identify the owner, data classification, caller identity, resource ARN, and recovery objective before enabling the feature.
- Prefer explicit configuration and tests over defaults that are invisible to reviewers.
- Include object key shape, version behavior, and error handling in the application contract whenever this feature affects them.

## Implementation notes

Capture the feature decision in IaC and application configuration. Test allowed and denied requests with the actual workload identity, then add an alert or query that points an on-call engineer to the relevant policy, key, object version, or queue message.

## Operational evidence

Monitor recurring error codes, retry exhaustion, failed deployment changes, and time to identify the denying policy or KMS key.

Build a dashboard, query, or runbook that maps this evidence to an owner and a response. A metric without an investigation path is only a graph.

## Common failure modes

Avoid: Fixing AccessDenied with AdministratorAccess and leaving the original policy defect unresolved.

## Senior engineer perspective

The feature is successful only when its security boundary, cost model, and failure behavior are understandable by the team on call. Document the decision, automate the baseline, and periodically prove that recovery still works.

## Key takeaways

- NoSuchKey is an exact-key mismatch, not a directory lookup failure. Check encoding, case, prefix, version state, and whether the writer completed before publishing a reference.
- Capture request IDs, reproduce with the intended role, use policy simulation and CloudTrail, and change one dimension at a time. Do not broaden permissions as a first response.
- Monitor recurring error codes, retry exhaustion, failed deployment changes, and time to identify the denying policy or KMS key.
