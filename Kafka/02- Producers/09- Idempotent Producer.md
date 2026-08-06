# Idempotent Producer

## Overview

In distributed systems, temporary failures are inevitable. A producer may successfully send a message to Kafka, but fail to receive the acknowledgement because of a network interruption or broker restart. In such situations, the producer retries sending the message.

Without additional protection, the broker may store the same message multiple times, resulting in duplicate events.

To solve this problem, Kafka introduced the **Idempotent Producer**, which guarantees that a producer writes a message **only once**, even if it is retried multiple times.

Idempotence is one of Kafka's most important reliability features and is enabled by default in modern Kafka clients.

---

# What is Idempotence?

Idempotence means:

> Performing the same operation multiple times produces the same result as performing it once.

In Kafka:

```text
Producer

↓

Send Message

↓

Retry

↓

Retry

↓

Retry

↓

Broker Stores

ONE Message
```

Regardless of how many retries occur, only one copy of the message is stored.

---

# Why is Idempotence Needed?

Suppose an order service publishes an event.

```text
Order Created
```

The producer sends the message.

```text
Producer

↓

Broker
```

The broker stores it successfully.

```text
Broker

↓

Message Stored
```

However, the acknowledgement never reaches the producer.

```text
ACK

↓

Network Failure
```

The producer assumes the message was never stored.

```text
Producer

↓

Retry
```

Without idempotence:

```text
Broker

↓

Store Again

↓

Duplicate Message
```

---

# Duplicate Message Problem

Without idempotence:

```text
Attempt 1

↓

Store Message

↓

ACK Lost

↓

Attempt 2

↓

Store Message Again
```

Topic:

```text
Offset 10

Order Created

--------------------

Offset 11

Order Created
```

The same event exists twice.

---

# Idempotent Producer Solution

With idempotence enabled:

```text
Attempt 1

↓

Store Message

↓

ACK Lost

↓

Retry

↓

Duplicate Detected

↓

Ignore Retry
```

Topic:

```text
Offset 10

Order Created
```

Only one message exists.

---

# How Kafka Detects Duplicates

Kafka assigns every producer a unique identifier.

```text
Producer

↓

Producer ID (PID)
```

Every message also receives a sequence number.

```text
Producer

↓

Message 1

Sequence 0

--------------------

Message 2

Sequence 1

--------------------

Message 3

Sequence 2
```

The broker keeps track of the latest sequence number for each producer.

---

# Producer ID (PID)

When a producer starts:

```text
Producer

↓

Kafka

↓

Assign PID
```

Example:

```text
Producer

↓

PID = 78231
```

This identifier remains associated with the producer session.

---

# Sequence Numbers

Every partition maintains an independent sequence.

Example:

```text
Partition 0

Sequence

0

1

2

3

4
```

The broker expects sequence numbers to arrive in order.

---

# Duplicate Detection

Suppose the broker already stored:

```text
Producer ID

78231

Sequence

5
```

A retry arrives.

```text
Producer ID

78231

Sequence

5
```

Kafka immediately recognizes:

```text
Already Stored

↓

Ignore
```

No duplicate is written.

---

# Idempotent Producer Workflow

```text
Producer

↓

Assign PID

↓

Assign Sequence Number

↓

Send Message

↓

Broker Stores

↓

ACK Lost

↓

Retry

↓

Broker Detects Duplicate

↓

Ignore Retry
```

The producer receives success without duplicate writes.

---

# Ordering with Idempotence

Idempotence also helps preserve message ordering during retries.

Example:

```text
Message A

↓

Retry

--------------------

Message B

↓

Success
```

Without idempotence:

```text
Message B

↓

Message A
```

Ordering may change.

With idempotence:

```text
Message A

↓

Message B
```

Ordering is preserved.

---

# Configuration

Enable idempotence:

```properties
enable.idempotence=true
```

In modern Kafka clients:

```text
Enabled by Default
```

unless conflicting configurations are provided.

---

# Additional Producer Settings

When idempotence is enabled, Kafka automatically enforces compatible settings.

Typical configuration:

```properties
acks=all

enable.idempotence=true

retries=Integer.MAX_VALUE
```

These settings work together to provide reliable message delivery.

---

# Idempotence and Retries

Retries become much safer.

Without idempotence:

```text
Retry

↓

Duplicate Event
```

With idempotence:

```text
Retry

↓

Duplicate Ignored
```

Applications can safely retry temporary failures.

---

# Idempotence and Acknowledgements

Kafka recommends:

```properties
acks=all
```

Reason:

```text
Leader

↓

Followers

↓

ACK
```

Waiting for all in-sync replicas provides maximum durability.

---

# Idempotence and Transactions

Idempotence guarantees:

```text
Exactly Once

Per Partition
```

Transactions extend this guarantee across:

- Multiple partitions
- Multiple topics

Transactions build upon idempotent producers.

---

# Limitations

Idempotence guarantees:

- No duplicate writes from retries.
- Ordering preservation.
- Reliable producer retries.

It does **not** provide:

- Atomic writes across multiple partitions.
- Exactly-once processing between producer and consumer.
- Distributed transactions.

These require Kafka Transactions.

---

# Failure Example

Suppose:

```text
Producer

↓

Send

↓

Broker Stores

↓

Broker Restarts

↓

Retry
```

Because the producer uses:

```text
PID

+

Sequence Number
```

Kafka still prevents duplicate writes after recovery.

---

# Performance Impact

Idempotence introduces only minimal overhead.

Benefits:

- Duplicate protection
- Reliable retries
- Ordering preservation

Modern Kafka clusters use idempotence without noticeable performance degradation.

---

# Real-World Example

Payment service:

```text
Payment Received

↓

Kafka
```

Network failure:

```text
ACK Lost

↓

Retry
```

Without idempotence:

```text
Payment Received

Payment Received
```

Duplicate payment event.

With idempotence:

```text
Payment Received
```

Exactly one event is stored.

---

# Advantages

- Eliminates duplicate writes
- Safe automatic retries
- Preserves ordering
- Improves fault tolerance
- Minimal performance overhead
- Enabled by default in modern Kafka clients

---

# Limitations

- Works only for a single producer session.
- Guarantees apply per partition.
- Does not replace transactions.
- Requires compatible producer configuration.

---

# Best Practices

- Keep idempotence enabled in production.
- Use `acks=all`.
- Allow producer retries.
- Avoid overriding compatible producer settings.
- Use transactions when writing to multiple partitions or topics atomically.
- Monitor producer errors and retry metrics.

---

# Common Mistakes

- Disabling idempotence unnecessarily.
- Assuming retries alone prevent duplicates.
- Confusing idempotence with transactions.
- Believing idempotence provides end-to-end exactly-once processing.
- Ignoring acknowledgement settings.

---

# Summary

The Idempotent Producer ensures that Kafka stores each message only once, even if the producer retries sending it because of temporary failures. Kafka achieves this by assigning every producer a unique Producer ID (PID) and tracking sequence numbers for every partition. When a duplicate retry arrives, the broker detects the repeated sequence number and ignores it. Idempotence provides reliable retries, prevents duplicate writes, and preserves message ordering, making it a fundamental feature for modern Kafka production systems.

---

# Key Takeaways

- Idempotence prevents duplicate message writes during retries.
- Kafka assigns every producer a unique Producer ID (PID).
- Sequence numbers allow brokers to detect duplicate requests.
- Idempotence preserves ordering during retries.
- Modern Kafka clients enable idempotence by default.
- `acks=all` and retries complement idempotent producers.
- Idempotence guarantees exactly-once writes per partition.
- Transactions build on idempotence to support atomic writes across multiple partitions and topics.