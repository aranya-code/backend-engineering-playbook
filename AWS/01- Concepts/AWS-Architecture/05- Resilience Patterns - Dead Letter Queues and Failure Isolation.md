# Resilience Patterns — Dead Letter Queues and Failure Isolation

## The Problem: Poison Messages

In an asynchronous, queue-based system, what happens to a message that fails processing every single time — not due to a transient issue, but because the message itself is malformed, or triggers a bug? Without a safeguard, it can be retried indefinitely, blocking the queue or endlessly consuming compute, while the "healthy" messages behind it wait.

## Dead Letter Queues (DLQ)

A separate queue that receives messages after they've failed processing a configured maximum number of times. The main queue keeps moving; failed messages are isolated for later inspection instead of blocking or looping forever.

```text
Main Queue → Consumer fails 3x → Message moved to DLQ
```

## Why This Is an Architectural Decision, Not Just Configuration

Enabling a DLQ is one line of configuration on an SQS queue or Lambda event source mapping. The architectural decision is everything *around* that: who monitors the DLQ, what the alerting threshold is, whether failed messages are replayed automatically or require human review, and how long they're retained before being considered unrecoverable. A DLQ nobody watches is just a slower way to silently lose data.

## Failure Isolation Beyond DLQs

- **Per-message failure isolation** — one bad message shouldn't block the rest of the queue (DLQs solve this directly)
- **Per-tenant failure isolation** — in multi-tenant systems, one tenant's unusual load or malformed data shouldn't degrade service for other tenants (often solved with per-tenant queues, rate limits, or partitioning)
- **Cell-based architecture** — partitioning an entire system into independent "cells," each serving a subset of customers/traffic, so a failure in one cell's infrastructure doesn't affect the others — a pattern AWS itself uses internally for some of its largest services

## Senior-Level Considerations

- Alert on DLQ depth, not just on the main queue's health — a growing DLQ is a real signal of a bug or bad data upstream, and it's easy to miss if monitoring only covers the "happy path" queue
- Decide *before* an incident whether failed messages will be automatically replayed after a fix, or require manual review — doing this mid-incident under pressure is worse than deciding it in a design doc ahead of time
- Cell-based architecture trades operational complexity (more infrastructure to manage) for blast-radius containment — appropriate at a scale where "the whole system going down together" is a much bigger risk than the added complexity
