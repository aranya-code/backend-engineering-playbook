# Retries

## Overview

Distributed systems are inherently unreliable. Networks become unavailable, brokers restart, leaders change, and temporary failures occur during normal operations.

If a producer gave up after the first failure, many messages would be permanently lost.

To solve this problem, Kafka producers automatically **retry failed requests** whenever the failure is considered temporary.

Retries improve:

- Reliability
- Fault tolerance
- Availability
- Producer resilience

However, retries must be configured carefully because they can introduce duplicate messages or affect message ordering if not combined with other Kafka features such as **Idempotent Producers**.

---

# What are Retries?

Retries allow a producer to resend a message after a temporary failure.

Instead of:

```text
Send Message

↓

Failure

↓

Give Up
```

Kafka performs:

```text
Send Message

↓

Failure

↓

Retry

↓

Success
```

Most transient failures are automatically recovered without application intervention.

---

# Why are Retries Needed?

Suppose a producer sends an order.

```text
Order Created
```

During transmission:

```text
Producer

↓

Network Timeout

↓

Broker Never Receives Message
```

Without retries:

```text
Message Lost
```

With retries:

```text
Timeout

↓

Retry

↓

Broker Receives Message
```

The application continues normally.

---

# Retry Workflow

```text
Producer

↓

Send Message

↓

Failure?

↓

Yes

↓

Wait

↓

Retry

↓

Success

↓

ACK
```

If all retry attempts fail, the producer reports an exception.

---

# Common Reasons for Retries

Kafka automatically retries during temporary failures such as:

- Network interruptions
- Leader broker changes
- Temporary broker unavailability
- Request timeout
- Connection reset
- Metadata refresh
- ISR synchronization delays

Retries are intended for **recoverable** failures.

---

# Retry Configuration

The producer configuration:

```properties
retries=10
```

allows the producer to retry a failed request ten times.

Example:

```text
Attempt 1

↓

Failure

↓

Attempt 2

↓

Failure

↓

Attempt 3

↓

Success
```

---

# Unlimited Retries

Modern Kafka producers often use:

```properties
retries=Integer.MAX_VALUE
```

This allows retries until the overall delivery timeout expires.

The producer does **not** retry forever.

The maximum retry duration is controlled by:

```properties
delivery.timeout.ms
```

---

# Retry Backoff

Kafka waits briefly before retrying.

Example:

```text
Failure

↓

Wait

100 ms

↓

Retry
```

Configuration:

```properties
retry.backoff.ms=100
```

This prevents overwhelming a broker that is recovering from a failure.

---

# Example Timeline

```text
Time

0 ms

↓

Send

↓

Failure

↓

100 ms

↓

Retry

↓

Failure

↓

200 ms

↓

Retry

↓

Success
```

The producer eventually receives an acknowledgement.

---

# Retryable vs Non-Retryable Errors

Kafka distinguishes between temporary and permanent failures.

### Retryable

Examples:

- Leader not available
- Network timeout
- Broker temporarily unavailable
- Connection failure

Kafka retries automatically.

---

### Non-Retryable

Examples:

- Invalid topic
- Message too large
- Authentication failure
- Authorization failure
- Serialization error

Retries will not solve these problems.

The producer immediately reports an exception.

---

# Retries and Leader Election

Suppose:

```text
Producer

↓

Leader Broker

↓

Leader Crashes
```

Kafka performs:

```text
Leader Election

↓

New Leader

↓

Retry

↓

Success
```

Applications usually do not notice this transition.

---

# Retries and Metadata Refresh

Sometimes retries occur because metadata becomes outdated.

Example:

```text
Producer

↓

Old Leader

↓

Failure

↓

Refresh Metadata

↓

New Leader

↓

Retry
```

Kafka automatically refreshes metadata before retrying.

---

# Retries and Acknowledgements

Retries work together with acknowledgements.

Suppose:

```text
Producer

↓

Send

↓

ACK Never Arrives
```

Kafka assumes the request failed.

```text
Retry
```

However:

```text
Broker Actually Stored Message
```

This creates the possibility of duplicate messages.

---

# Duplicate Messages

Without idempotence:

```text
Send

↓

Broker Stores Message

↓

ACK Lost

↓

Retry

↓

Broker Stores Message Again
```

Result:

```text
Duplicate Message
```

The same event appears twice.

---

# Retries with Idempotent Producers

Modern Kafka solves duplicate writes using idempotence.

Configuration:

```properties
enable.idempotence=true
```

Workflow:

```text
Send

↓

ACK Lost

↓

Retry

↓

Broker Detects Duplicate

↓

Ignore Duplicate
```

Only one copy is stored.

---

# Retries and Message Ordering

Retries may affect ordering if multiple requests are in flight.

Example:

```text
Message A

↓

Failure

↓

Retry

---------------------

Message B

↓

Success
```

Without protection:

```text
Message B

↓

Message A
```

Ordering changes.

Modern Kafka prevents this by combining:

```properties
enable.idempotence=true

max.in.flight.requests.per.connection=5
```

Ordering remains preserved.

---

# Delivery Timeout

Retries continue only until:

```properties
delivery.timeout.ms
```

expires.

Example:

```properties
delivery.timeout.ms=120000
```

Equivalent to:

```text
120 Seconds
```

After this period:

```text
Producer

↓

Exception
```

---

# Retry Configuration Example

Reliable production configuration:

```properties
acks=all

enable.idempotence=true

retries=Integer.MAX_VALUE

retry.backoff.ms=100

delivery.timeout.ms=120000
```

This combination provides:

- High reliability
- Automatic recovery
- Duplicate protection

---

# Retry Flow Diagram

```text
Producer

↓

Send Request

↓

Temporary Failure?

↓

Yes

↓

Wait

↓

Retry

↓

Success?

↓

Yes

↓

ACK

↓

Complete
```

If all retries fail:

```text
Exception
```

---

# Performance Impact

Retries improve reliability but may increase:

- Latency
- Network traffic
- Broker load

Fortunately, retries occur only during failures.

Under normal operation:

```text
No Retry

↓

Minimal Performance Impact
```

---

# Best Practices

- Enable retries in production.
- Use idempotent producers.
- Configure `acks=all`.
- Set an appropriate retry backoff.
- Monitor retry metrics.
- Investigate frequent retries.
- Tune delivery timeout according to application requirements.

---

# Common Mistakes

- Disabling retries in production.
- Assuming retries guarantee no duplicates.
- Forgetting to enable idempotence.
- Treating non-retryable errors as temporary failures.
- Ignoring excessive retry rates.

---

# Summary

Retries allow Kafka producers to automatically recover from temporary failures by resending failed requests. They are an essential mechanism for building reliable distributed systems because they handle transient network problems, broker failures, and leader elections without requiring application intervention. When combined with acknowledgements, idempotent producers, and appropriate timeout settings, retries provide highly reliable message delivery while preventing duplicate writes and preserving message ordering.

---

# Key Takeaways

- Retries automatically resend messages after temporary failures.
- They improve reliability and fault tolerance.
- Kafka retries only recoverable errors.
- Retry behavior is controlled using producer configuration.
- Retries work closely with acknowledgements and leader elections.
- Without idempotence, retries may produce duplicate messages.
- Idempotent producers eliminate duplicate writes during retries.
- A production-ready Kafka producer should combine retries, `acks=all`, and idempotence for maximum reliability.