# Resilience Patterns — Retries, Backoff, and Jitter

## Exponential Backoff

A retry mechanism where the wait time between attempts doubles after each failure.

```text
Retry 1 -> 1 sec
Retry 2 -> 2 sec
Retry 3 -> 4 sec
Retry 4 -> 8 sec
Retry 5 -> 16 sec
```

## Why AWS Services Lean on This Heavily

- Absorbs transient throttling (`ThrottlingException`, `RequestLimitExceeded`, HTTP 429) without hammering an already-struggling service
- Prevents a "retry storm" — many clients failing and retrying in lockstep, which can turn a brief blip into a sustained outage
- Reduces load on the downstream service exactly when it's least able to handle load

## The Problem Plain Exponential Backoff Doesn't Solve: Thundering Herd

If every client backs off on the exact same schedule (1s, 2s, 4s...), they all retry at the exact same moments — synchronized waves of load hitting the recovering service in lockstep, which can itself cause repeated failure.

## Jitter

Adding randomness to the backoff delay so retries spread out over time instead of arriving in synchronized waves.

```text
Base delay: 4 sec
With jitter: random value between 0–4 sec (or 2–6 sec, depending on jitter strategy)
```

**Common jitter strategies:**
- **Full jitter** — random delay between 0 and the full computed backoff value
- **Equal jitter** — half the computed delay, plus a random amount up to the other half
- **Decorrelated jitter** — each delay is randomized based on the previous delay, not just the fixed exponential schedule

AWS SDKs implement exponential backoff with jitter by default for retryable errors — this is why it's worth understanding even if you never write retry logic by hand.

## Idempotency — The Prerequisite for Safe Retries

Retrying is only safe if the operation is **idempotent** — running it twice has the same effect as running it once. A payment charge API that isn't idempotent, retried after a timeout (where the first request may have actually succeeded server-side), can double-charge a customer. AWS services that support retries safely typically expose an idempotency token (e.g., DynamoDB conditional writes, SQS deduplication IDs for FIFO queues) specifically to make retries safe.

## Senior-Level Considerations

- Not all errors should be retried — a 400 Bad Request won't succeed on retry no matter how long you wait; only retry on errors that represent a plausibly transient condition (throttling, timeouts, 5xx)
- Set a maximum retry count and a maximum total time budget — unbounded retries just delay failure, they don't prevent it, and can make a caller hang far longer than the caller's own timeout expectations
- Backoff and jitter reduce the *chance* of overwhelming a downstream service; they are not a substitute for the downstream service having its own capacity and throttling controls
