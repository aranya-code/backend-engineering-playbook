# Producer Acknowledgements

## Overview

When a Kafka producer sends a message, an important question arises:

> **How does the producer know whether the message was successfully stored?**

The answer is through **Acknowledgements (ACKs)**.

An acknowledgement is a response sent by the Kafka broker back to the producer indicating whether the message has been successfully written.

The acknowledgement strategy directly affects:

- Reliability
- Durability
- Throughput
- Latency
- Fault tolerance

Choosing the correct acknowledgement level is one of the most important configuration decisions when building Kafka applications.

---

# What is an Acknowledgement?

An acknowledgement (ACK) is a confirmation sent from the Kafka broker to the producer.

Example:

```text
Producer

↓

Send Message

↓

Broker

↓

ACK
```

The ACK tells the producer whether the write operation succeeded.

---

# Why Are ACKs Needed?

Imagine the producer sends an order.

```text
Order Created
```

Without acknowledgements:

```text
Producer

↓

Send

↓

???

Did Kafka receive it?
```

The producer has no idea whether:

- The broker stored the message.
- The network failed.
- The broker crashed.
- The message was lost.

Acknowledgements eliminate this uncertainty.

---

# Producer Write Workflow

The complete workflow is:

```text
Producer

↓

Send Message

↓

Leader Broker

↓

Write Message

↓

Replicate (Optional)

↓

ACK

↓

Producer
```

The point at which Kafka sends the acknowledgement depends on the configured ACK level.

---

# ACK Configuration

Kafka provides three acknowledgement modes.

```properties
acks=0

acks=1

acks=all
```

Each offers a different balance between performance and reliability.

---

# ACK = 0

## What Happens?

The producer sends the message and immediately continues.

```text
Producer

↓

Send Message

↓

Continue
```

No acknowledgement is expected.

---

# Workflow

```text
Producer

↓

Broker

(No ACK)
```

The producer never knows whether the broker actually received the message.

---

# Advantages

- Lowest latency
- Maximum throughput
- Minimal network overhead

---

# Disadvantages

Messages can be lost.

Example:

```text
Producer

↓

Send

↓

Network Failure

↓

Message Lost
```

The producer never detects the failure.

---

# Suitable Use Cases

ACK=0 is appropriate when occasional message loss is acceptable.

Examples:

- Application logs
- Metrics
- Monitoring
- Temporary analytics

Not suitable for business-critical systems.

---

# ACK = 1

## What Happens?

The producer waits until the **Leader Broker** stores the message.

```text
Producer

↓

Leader

↓

ACK
```

Followers may not have replicated the message yet.

---

# Workflow

```text
Producer

↓

Leader

↓

Write Message

↓

ACK
```

Replication continues after the acknowledgement.

---

# Failure Scenario

Suppose:

```text
Leader

↓

ACK

↓

Leader Crash

↓

Followers Not Updated
```

The message may still be lost because replication was incomplete.

---

# Advantages

- Good performance
- Low latency
- Reasonable reliability

---

# Disadvantages

Messages may be lost if the leader fails before replication completes.

---

# Suitable Use Cases

ACK=1 is commonly used for:

- Notifications
- Recommendation systems
- Search indexing
- General event processing

where limited data loss is acceptable.

---

# ACK = all

Sometimes written as:

```properties
acks=-1
```

Both configurations are equivalent.

---

# What Happens?

The producer waits until **all In-Sync Replicas (ISR)** acknowledge the message.

```text
Producer

↓

Leader

↓

Followers

↓

ACK
```

Only after every ISR replica confirms does Kafka respond.

---

# Workflow

```text
Producer

↓

Leader

↓

Write Message

↓

Replicate

↓

ISR Confirmation

↓

ACK
```

---

# Failure Scenario

Suppose:

```text
Leader

↓

Follower 1

↓

Follower 2

↓

ACK

↓

Leader Crash
```

Because followers already contain the message:

```text
Follower

↓

New Leader
```

No message is lost.

---

# Advantages

- Highest durability
- Highest reliability
- Excellent fault tolerance

---

# Disadvantages

- Slightly higher latency
- More network traffic
- Slightly lower throughput

The reliability benefits usually outweigh these costs.

---

# ACK Comparison

| ACK Mode | Waits For | Message Loss | Latency | Throughput |
|----------|-----------|--------------|---------|------------|
| 0 | Nobody | High | Lowest | Highest |
| 1 | Leader | Possible | Low | High |
| all | All ISR Replicas | Very Low | Highest | Lower |

---

# ACK Timeline

## ACK = 0

```text
Producer

↓

Send

↓

Continue
```

---

## ACK = 1

```text
Producer

↓

Leader

↓

Write

↓

ACK
```

---

## ACK = all

```text
Producer

↓

Leader

↓

Followers

↓

ISR

↓

ACK
```

---

# ACKs and Replication

ACKs work closely with Kafka replication.

Example:

```text
Producer

↓

Leader

↓

Follower 1

↓

Follower 2
```

ACK=all waits for every replica in the ISR.

Without replication:

```text
Replication Factor = 1
```

ACK=all behaves similarly to ACK=1 because only the leader exists.

---

# ACKs and ISR

Kafka only waits for replicas inside the ISR.

Example:

```text
Leader

Broker 1

----------------

Follower

Broker 2

(In ISR)

----------------

Follower

Broker 3

(Not in ISR)
```

Kafka waits only for:

```text
Broker 1

Broker 2
```

Broker 3 does not delay the acknowledgement.

---

# ACKs and Retries

Suppose:

```text
Producer

↓

Send

↓

Timeout

↓

Retry
```

Retries occur if:

- ACK never arrives
- Network timeout
- Temporary broker failure

Modern Kafka producers use idempotence to prevent duplicate writes during retries.

---

# ACKs and Idempotent Producers

Recommended configuration:

```properties
acks=all

enable.idempotence=true
```

Benefits:

- No duplicate writes
- High durability
- Reliable retries

This combination is recommended for production systems.

---

# ACKs and Performance

Performance generally follows this pattern:

```text
ACK=0

↓

Fastest

-------------------

ACK=1

↓

Balanced

-------------------

ACK=all

↓

Most Reliable
```

Choosing the correct mode depends on business requirements.

---

# Real-World Examples

### Log Collection

```text
Performance

>

Reliability
```

Recommended:

```properties
acks=0
```

---

### Order Processing

```text
Performance

≈

Reliability
```

Recommended:

```properties
acks=1
```

or

```properties
acks=all
```

depending on business requirements.

---

### Banking

```text
Reliability

>

Performance
```

Recommended:

```properties
acks=all
```

Always prioritize durability.

---

# Recommended Production Configuration

```properties
acks=all

enable.idempotence=true

retries=Integer.MAX_VALUE
```

This provides:

- High durability
- Automatic retries
- Duplicate protection

This is the recommended configuration for most production workloads.

---

# Best Practices

- Use `acks=all` for production applications handling important business data.
- Combine acknowledgements with idempotent producers.
- Configure retries appropriately.
- Monitor producer latency after changing ACK settings.
- Understand the trade-off between throughput and durability.
- Ensure an appropriate replication factor for reliable acknowledgements.

---

# Common Mistakes

- Using `acks=0` for financial or business-critical events.
- Assuming `acks=1` guarantees no message loss.
- Forgetting that `acks=all` depends on the ISR.
- Ignoring the impact of replication on acknowledgement behavior.
- Using `acks=all` without enabling retries or idempotence.

---

# Summary

Producer acknowledgements determine when Kafka confirms that a message has been successfully written. With `acks=0`, the producer prioritizes speed by not waiting for confirmation. With `acks=1`, the producer waits for the leader broker to store the message. With `acks=all`, the producer waits until every in-sync replica has acknowledged the write, providing the highest level of durability. Selecting the appropriate acknowledgement strategy requires balancing performance, latency, and reliability based on the application's business requirements.

---

# Key Takeaways

- Acknowledgements confirm whether Kafka successfully received a message.
- Kafka supports three acknowledgement modes: `acks=0`, `acks=1`, and `acks=all`.
- `acks=0` provides maximum throughput but the lowest reliability.
- `acks=1` waits only for the leader broker and may still lose messages if the leader fails before replication.
- `acks=all` waits for all in-sync replicas and provides the highest durability.
- Acknowledgements work closely with replication and the ISR.
- Combining `acks=all`, retries, and idempotent producers provides a reliable production configuration.
- Choosing the correct acknowledgement level is a trade-off between performance and fault tolerance.