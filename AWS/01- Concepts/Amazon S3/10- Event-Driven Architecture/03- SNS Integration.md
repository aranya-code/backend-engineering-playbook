# SNS Integration

## Why this matters

SNS fans an S3 event to independent subscribers. Use filter policies and durable subscriptions when individual consumers have separate retry or ownership needs.

## Core model

S3 notifications describe object activity, not exactly-once business events. Consumers must tolerate duplicates, reordering, retries, and objects that are no longer readable when processed.

## Production design checklist

- Route work through a durable queue when back-pressure matters, make processing idempotent on bucket, key, version ID, and event type, and isolate poison messages.
- Identify the owner, data classification, caller identity, resource ARN, and recovery objective before enabling the feature.
- Prefer explicit configuration and tests over defaults that are invisible to reviewers.
- Include object key shape, version behavior, and error handling in the application contract whenever this feature affects them.

## Implementation notes

Capture the feature decision in IaC and application configuration. Test allowed and denied requests with the actual workload identity, then add an alert or query that points an on-call engineer to the relevant policy, key, object version, or queue message.

## Operational evidence

Monitor queue age, DLQ depth, consumer errors, duplicate suppressions, and end-to-end processing latency.

Build a dashboard, query, or runbook that maps this evidence to an owner and a response. A metric without an investigation path is only a graph.

## Common failure modes

Avoid: Writing derived output into the same watched prefix and creating a recursive event loop.

## Senior engineer perspective

The feature is successful only when its security boundary, cost model, and failure behavior are understandable by the team on call. Document the decision, automate the baseline, and periodically prove that recovery still works.

## Key takeaways

- SNS fans an S3 event to independent subscribers. Use filter policies and durable subscriptions when individual consumers have separate retry or ownership needs.
- Route work through a durable queue when back-pressure matters, make processing idempotent on bucket, key, version ID, and event type, and isolate poison messages.
- Monitor queue age, DLQ depth, consumer errors, duplicate suppressions, and end-to-end processing latency.
