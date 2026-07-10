# Versioning

## Why this matters

Enable versioning before critical data, recover ordinary deletes by removing a delete marker, lifecycle noncurrent versions, and use Object Lock when WORM retention is required.

## Core model

A cheat sheet should accelerate a safe decision, not replace a review. Keep commands parameterized, include guardrails, and link to the full chapter for trade-offs.

## Production design checklist

- Use placeholders for account IDs and bucket names, inspect before mutating, and verify after every policy or lifecycle change.
- Identify the owner, data classification, caller identity, resource ARN, and recovery objective before enabling the feature.
- Prefer explicit configuration and tests over defaults that are invisible to reviewers.
- Include object key shape, version behavior, and error handling in the application contract whenever this feature affects them.

## Implementation notes

Treat this as an on-call prompt, not a substitute for review. Parameterize account, region, bucket, key, and prefix; show the inspection action before the mutation; verify the resulting state afterward.

## Operational evidence

Review cheat sheets after SDK, policy, or platform changes and validate examples in a sandbox account.

Build a dashboard, query, or runbook that maps this evidence to an owner and a response. A metric without an investigation path is only a graph.

## Common failure modes

Avoid: Copying commands into production without checking region, identity, encryption requirements, or the target prefix.

## Senior engineer perspective

The feature is successful only when its security boundary, cost model, and failure behavior are understandable by the team on call. Document the decision, automate the baseline, and periodically prove that recovery still works.

## Key takeaways

- Enable versioning before critical data, recover ordinary deletes by removing a delete marker, lifecycle noncurrent versions, and use Object Lock when WORM retention is required.
- Use placeholders for account IDs and bucket names, inspect before mutating, and verify after every policy or lifecycle change.
- Review cheat sheets after SDK, policy, or platform changes and validate examples in a sandbox account.
