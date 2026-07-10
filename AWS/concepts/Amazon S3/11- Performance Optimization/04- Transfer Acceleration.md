# Transfer Acceleration

## Why this matters

Transfer Acceleration can improve long-distance public uploads through edge locations and AWS backbone routing. Benchmark from real client geographies before paying for it.

## Core model

S3 scales request throughput, but application latency usually comes from client concurrency, payload sizing, network geography, connection reuse, and inefficient full-object reads.

## Production design checklist

- Benchmark with representative objects and error budgets. Parallelize safely, use multipart transfer for large objects, and use caching or range GETs only where the access pattern supports them.
- Identify the owner, data classification, caller identity, resource ARN, and recovery objective before enabling the feature.
- Prefer explicit configuration and tests over defaults that are invisible to reviewers.
- Include object key shape, version behavior, and error handling in the application contract whenever this feature affects them.

## Implementation notes

Capture the feature decision in IaC and application configuration. Test allowed and denied requests with the actual workload identity, then add an alert or query that points an on-call engineer to the relevant policy, key, object version, or queue message.

## Operational evidence

Monitor p50 and p95 request latency, 4xx and 5xx rates, retry volume, bytes per operation, and client connection saturation.

Build a dashboard, query, or runbook that maps this evidence to an owner and a response. A metric without an investigation path is only a graph.

## Common failure modes

Avoid: Inventing random prefixes for a modern bucket without measuring the client, transfer, or downstream bottleneck.

## Senior engineer perspective

The feature is successful only when its security boundary, cost model, and failure behavior are understandable by the team on call. Document the decision, automate the baseline, and periodically prove that recovery still works.

## Key takeaways

- Transfer Acceleration can improve long-distance public uploads through edge locations and AWS backbone routing. Benchmark from real client geographies before paying for it.
- Benchmark with representative objects and error budgets. Parallelize safely, use multipart transfer for large objects, and use caching or range GETs only where the access pattern supports them.
- Monitor p50 and p95 request latency, 4xx and 5xx rates, retry volume, bytes per operation, and client connection saturation.
