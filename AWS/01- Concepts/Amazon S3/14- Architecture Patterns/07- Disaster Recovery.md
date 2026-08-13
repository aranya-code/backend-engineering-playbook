# Disaster Recovery

## Why this matters

S3 DR combines versioning, replication, Object Lock, separate accounts, and restoration automation. Document DNS and application failover, replica writes, and a test cadence that proves RTO/RPO.

## Core model

S3 is a durable object boundary, not a database or a POSIX filesystem. Patterns succeed when ownership, authorization, immutability, event delivery, and recovery are explicit.

## Production design checklist

- Keep application metadata in a database, use server-derived keys, issue short-lived delegated access, and define a repair or replay procedure.
- Identify the owner, data classification, caller identity, resource ARN, and recovery objective before enabling the feature.
- Prefer explicit configuration and tests over defaults that are invisible to reviewers.
- Include object key shape, version behavior, and error handling in the application contract whenever this feature affects them.

## Implementation notes

Capture the feature decision in IaC and application configuration. Test allowed and denied requests with the actual workload identity, then add an alert or query that points an on-call engineer to the relevant policy, key, object version, or queue message.

## Operational evidence

Monitor object-to-record reconciliation, orphaned uploads, event lag, cache hit ratio, and backup restore tests.

Build a dashboard, query, or runbook that maps this evidence to an owner and a response. A metric without an investigation path is only a graph.

## Common failure modes

Avoid: Letting clients choose arbitrary keys or treating object listing as an authoritative transaction log.

## Senior engineer perspective

The feature is successful only when its security boundary, cost model, and failure behavior are understandable by the team on call. Document the decision, automate the baseline, and periodically prove that recovery still works.

## Key takeaways

- S3 DR combines versioning, replication, Object Lock, separate accounts, and restoration automation. Document DNS and application failover, replica writes, and a test cadence that proves RTO/RPO.
- Keep application metadata in a database, use server-derived keys, issue short-lived delegated access, and define a repair or replay procedure.
- Monitor object-to-record reconciliation, orphaned uploads, event lag, cache hit ratio, and backup restore tests.
