# Senior

## Why this matters

Practice decisions under constraints: multi-tenant authorization, ransomware recovery, cross-account sharing, high-volume ingest, data residency, event idempotency, and cost anomalies.

## Core model

Strong answers start with the S3 primitive, then name the trade-off, failure mode, and operational control. A senior answer makes its decision conditional on requirements.

## Production design checklist

- State assumptions, distinguish durability from availability, call out policy and KMS boundaries, and include a recovery or observability mechanism.
- Identify the owner, data classification, caller identity, resource ARN, and recovery objective before enabling the feature.
- Prefer explicit configuration and tests over defaults that are invisible to reviewers.
- Include object key shape, version behavior, and error handling in the application contract whenever this feature affects them.

## Implementation notes

Use this answer pattern: clarify classification, scale, access pattern, RPO/RTO, and tenancy; select the smallest feature set; separate S3 authorization from KMS authorization; name a failure mode, a signal, and a cost trade-off.

## Operational evidence

Use a design rubric: data classification, access path, consistency, RPO/RTO, scale, cost, and operability.

Build a dashboard, query, or runbook that maps this evidence to an owner and a response. A metric without an investigation path is only a graph.

## Common failure modes

Avoid: Giving feature lists without explaining why a feature is selected or how it fails in production.

## Senior engineer perspective

The feature is successful only when its security boundary, cost model, and failure behavior are understandable by the team on call. Document the decision, automate the baseline, and periodically prove that recovery still works.

## Key takeaways

- Practice decisions under constraints: multi-tenant authorization, ransomware recovery, cross-account sharing, high-volume ingest, data residency, event idempotency, and cost anomalies.
- State assumptions, distinguish durability from availability, call out policy and KMS boundaries, and include a recovery or observability mechanism.
- Use a design rubric: data classification, access path, consistency, RPO/RTO, scale, cost, and operability.
