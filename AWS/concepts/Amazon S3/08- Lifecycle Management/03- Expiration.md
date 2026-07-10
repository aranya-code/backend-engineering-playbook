# Expiration

## Why this matters

Expiration removes current objects or creates delete markers in versioned buckets. It cannot override Object Lock retention or legal holds.

## Core model

Lifecycle rules are asynchronous policy evaluation, not an immediate scheduler. Their effects depend on version state, object age, storage-class limits, restore requirements, and retention law.

## Production design checklist

- Use prefixes and tags as a contract, document the retention owner, stage changes on representative data, and review transitions together with restore and legal-hold policies.
- Identify the owner, data classification, caller identity, resource ARN, and recovery objective before enabling the feature.
- Prefer explicit configuration and tests over defaults that are invisible to reviewers.
- Include object key shape, version behavior, and error handling in the application contract whenever this feature affects them.

## Implementation notes

Capture the feature decision in IaC and application configuration. Test allowed and denied requests with the actual workload identity, then add an alert or query that points an on-call engineer to the relevant policy, key, object version, or queue message.

## Operational evidence

Monitor bytes by storage class, transition and expiry activity, noncurrent-version growth, and unexpected retrieval charges.

Build a dashboard, query, or runbook that maps this evidence to an owner and a response. A metric without an investigation path is only a graph.

## Common failure modes

Avoid: Expiring current versions without accounting for delete markers, archived restores, minimum-duration charges, or statutory retention.

## Senior engineer perspective

The feature is successful only when its security boundary, cost model, and failure behavior are understandable by the team on call. Document the decision, automate the baseline, and periodically prove that recovery still works.

## Key takeaways

- Expiration removes current objects or creates delete markers in versioned buckets. It cannot override Object Lock retention or legal holds.
- Use prefixes and tags as a contract, document the retention owner, stage changes on representative data, and review transitions together with restore and legal-hold policies.
- Monitor bytes by storage class, transition and expiry activity, noncurrent-version growth, and unexpected retrieval charges.
