# Django REST Framework

## Why this matters

A REST API should expose upload intent and state, not raw bucket privilege. Use an authenticated endpoint to create a signed request and validate the result asynchronously.

## Core model

Backend services should authorize an S3 operation, record domain state, and delegate bytes when possible. They should not proxy every large object through web workers.

## Production design checklist

- Validate content type and size before signing, bind keys to tenant and object identity, verify completion asynchronously, and persist version and checksum where correctness matters.
- Identify the owner, data classification, caller identity, resource ARN, and recovery objective before enabling the feature.
- Prefer explicit configuration and tests over defaults that are invisible to reviewers.
- Include object key shape, version behavior, and error handling in the application contract whenever this feature affects them.

## Implementation notes

Capture the feature decision in IaC and application configuration. Test allowed and denied requests with the actual workload identity, then add an alert or query that points an on-call engineer to the relevant policy, key, object version, or queue message.

## Operational evidence

Monitor signing failures, upload completion lag, orphan rate, malware-scan status, and per-tenant bytes and requests.

Build a dashboard, query, or runbook that maps this evidence to an owner and a response. A metric without an investigation path is only a graph.

## Common failure modes

Avoid: Trusting an uploaded filename, trusting a client-supplied MIME type, or making a database record visible before object validation completes.

## Senior engineer perspective

The feature is successful only when its security boundary, cost model, and failure behavior are understandable by the team on call. Document the decision, automate the baseline, and periodically prove that recovery still works.

## Key takeaways

- A REST API should expose upload intent and state, not raw bucket privilege. Use an authenticated endpoint to create a signed request and validate the result asynchronously.
- Validate content type and size before signing, bind keys to tenant and object identity, verify completion asynchronously, and persist version and checksum where correctness matters.
- Monitor signing failures, upload completion lag, orphan rate, malware-scan status, and per-tenant bytes and requests.
