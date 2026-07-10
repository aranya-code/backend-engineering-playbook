# SRR

## Why this matters

Same-Region Replication supports aggregation, account isolation, log fan-out, and production-to-analytics separation without cross-region transfer.

## Core model

Replication asynchronously copies eligible object versions under a replication role. It does not define application failover, conflict resolution, historical backfill, or a database transaction.

## Production design checklist

- Write an RPO, ownership, encryption, delete-marker, and destination-access decision before enabling a rule. Test the recovery path, not just replication status.
- Identify the owner, data classification, caller identity, resource ARN, and recovery objective before enabling the feature.
- Prefer explicit configuration and tests over defaults that are invisible to reviewers.
- Include object key shape, version behavior, and error handling in the application contract whenever this feature affects them.

## Implementation notes

Capture the feature decision in IaC and application configuration. Test allowed and denied requests with the actual workload identity, then add an alert or query that points an on-call engineer to the relevant policy, key, object version, or queue message.

## Operational evidence

Monitor pending bytes and operations, replication latency, failed operations, and destination KMS failures.

Build a dashboard, query, or runbook that maps this evidence to an owner and a response. A metric without an investigation path is only a graph.

## Common failure modes

Avoid: Expecting replication to repair old data automatically or treating a replica bucket as writable without a conflict model.

## Senior engineer perspective

The feature is successful only when its security boundary, cost model, and failure behavior are understandable by the team on call. Document the decision, automate the baseline, and periodically prove that recovery still works.

## Key takeaways

- Same-Region Replication supports aggregation, account isolation, log fan-out, and production-to-analytics separation without cross-region transfer.
- Write an RPO, ownership, encryption, delete-marker, and destination-access decision before enabling a rule. Test the recovery path, not just replication status.
- Monitor pending bytes and operations, replication latency, failed operations, and destination KMS failures.
