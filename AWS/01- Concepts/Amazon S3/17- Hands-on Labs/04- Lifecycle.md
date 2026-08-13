# Lab 04 Lifecycle

## Why this matters

Scope rules by prefix or tag, calculate retrieval and minimum-duration costs, handle current and noncurrent versions separately, account for Object Lock, and validate before broad rollout.

## Core model

A useful lab is an executable design review: state the objective, provision least privilege, verify behavior with commands, demonstrate a failure case, and remove resources.

## Production design checklist

- Work in a disposable account or prefix, use unique names, capture expected outputs, and include an explicit cleanup checklist.
- Identify the owner, data classification, caller identity, resource ARN, and recovery objective before enabling the feature.
- Prefer explicit configuration and tests over defaults that are invisible to reviewers.
- Include object key shape, version behavior, and error handling in the application contract whenever this feature affects them.

## Implementation notes

Run in a disposable account or prefix with a unique name. Validate one expected success and one expected deny or recovery path, capture evidence, then remove every bucket, queue, distribution, key, and log resource.

## Operational evidence

Record validation evidence, expected denial behavior, time to clean up, and every cost-bearing resource created.

Build a dashboard, query, or runbook that maps this evidence to an owner and a response. A metric without an investigation path is only a graph.

## Common failure modes

Avoid: Completing only the happy path without proving the security boundary or recovery behavior.

## Senior engineer perspective

The feature is successful only when its security boundary, cost model, and failure behavior are understandable by the team on call. Document the decision, automate the baseline, and periodically prove that recovery still works.

## Key takeaways

- Scope rules by prefix or tag, calculate retrieval and minimum-duration costs, handle current and noncurrent versions separately, account for Object Lock, and validate before broad rollout.
- Work in a disposable account or prefix, use unique names, capture expected outputs, and include an explicit cleanup checklist.
- Record validation evidence, expected denial behavior, time to clean up, and every cost-bearing resource created.
