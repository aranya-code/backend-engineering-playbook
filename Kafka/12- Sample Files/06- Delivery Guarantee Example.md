# Delivery Guarantee Example

## Overview

One of Kafka's biggest strengths is that it gives developers control over **how reliably messages are delivered**. Different applications have different reliability requirements. For example, a logging system may tolerate losing a few messages, while a banking system cannot.

Kafka supports three delivery guarantees:

- At Most Once
- At Least Once
- Exactly Once

Each guarantee represents a trade-off between performance, complexity, and reliability.

This chapter explains these delivery guarantees using practical examples and shows when each one should be used.

---

# Delivery Guarantee Overview

```text
Application

↓

Producer

↓

Kafka

↓

Consumer

↓

Business Logic
```

The delivery guarantee determines what happens if failures occur during this flow.

---

# Three Delivery Guarantees

```text
At Most Once

↓

May Lose Messages

----------------

At Least Once

↓

May Duplicate Messages

----------------

Exactly Once

↓

No Loss

No Duplication
```

Each guarantee suits different workloads.

---

# Example 1: At Most Once

Configuration:

```properties
acks=0
```

Consumer:

```properties
enable.auto.commit=true
```

Workflow:

```text
Producer

↓

Send Message

↓

No ACK

↓

Consumer

↓

Auto Commit
```

---

# Failure Scenario

Producer:

```text
Send Message

↓

Network Failure
```

Since no acknowledgement is expected:

```text
Producer

↓

Assumes Success
```

Message may never reach Kafka.

---

# Characteristics

Advantages:

- Lowest latency
- Highest throughput

Disadvantages:

- Messages may be lost
- No retry confirmation

---

# Suitable Applications

Examples:

- Application logs
- Metrics
- Monitoring data
- Temporary telemetry

Losing occasional messages is acceptable.

---

# Example 2: At Least Once

Configuration:

```properties
acks=all

retries>0
```

Consumer:

```text
Manual Commit
```

Workflow:

```text
Producer

↓

Leader

↓

Replication

↓

ACK

↓

Consumer

↓

Process

↓

Commit Offset
```

---

# Failure Scenario

Consumer:

```text
Process Message

↓

Crash

↓

Offset Not Committed
```

Kafka assumes:

```text
Message Not Processed
```

After restart:

```text
Same Message

↓

Processed Again
```

Duplicates occur.

---

# Characteristics

Advantages:

- No message loss
- Reliable processing

Disadvantages:

- Duplicate processing possible

---

# Suitable Applications

Examples:

- Order processing
- Email notifications
- Inventory updates
- Payment requests

Applications should implement idempotent business logic.

---

# Example 3: Exactly Once

Configuration:

```properties
enable.idempotence=true
```

Plus:

```text
Transactions

+

Manual Offset Commit
```

Workflow:

```text
Producer

↓

Transaction

↓

Kafka

↓

Consumer

↓

Transaction Commit
```

---

# Failure Scenario

Producer:

```text
Send

↓

Network Failure

↓

Retry
```

Kafka:

```text
Duplicate?

↓

Ignore Duplicate

↓

One Record Stored
```

Idempotence prevents duplicate writes.

---

# Consumer Side

Consumer:

```text
Read

↓

Process

↓

Commit Transaction

↓

Commit Offset
```

Processing succeeds exactly once.

---

# Characteristics

Advantages:

- No duplicates
- No message loss

Disadvantages:

- More configuration
- Slightly lower throughput
- Greater complexity

---

# Suitable Applications

Examples:

- Banking
- Financial transactions
- Payment systems
- Ledger services
- Stock trading
- Billing systems

---

# Comparison

| Guarantee | Message Loss | Duplicates | Performance |
|------------|-------------|------------|-------------|
| At Most Once | Possible | No | Highest |
| At Least Once | No | Possible | High |
| Exactly Once | No | No | Lower |

---

# Example: Banking System

Requirements:

```text
Transfer ₹1000

↓

Debit

↓

Credit
```

Duplicate processing:

```text
Debit Twice
```

Message loss:

```text
Credit Missing
```

Both are unacceptable.

Solution:

```text
Exactly Once
```

---

# Example: Order Processing

Customer places order.

```text
Order Created

↓

Kafka

↓

Inventory
```

Inventory updates twice.

Not ideal.

However:

Duplicate handling:

```text
Order Already Reserved

↓

Ignore
```

At Least Once is usually sufficient.

---

# Example: Logging

Application writes:

```text
User Logged In
```

If one log is lost:

```text
System Still Works
```

At Most Once is acceptable.

---

# Producer Configuration

### At Most Once

```properties
acks=0

retries=0
```

---

### At Least Once

```properties
acks=all

retries=5
```

---

### Exactly Once

```properties
acks=all

enable.idempotence=true

transactional.id=payment-service
```

---

# Consumer Configuration

### At Most Once

```properties
enable.auto.commit=true
```

---

### At Least Once

```text
Manual Commit

↓

After Processing
```

---

### Exactly Once

```text
Transactional Processing

↓

Commit Offset

↓

Commit Transaction
```

---

# Delivery Flow Comparison

## At Most Once

```text
Producer

↓

Send

↓

Continue
```

---

## At Least Once

```text
Producer

↓

Retry

↓

Consumer

↓

Process

↓

Commit
```

---

## Exactly Once

```text
Producer

↓

Transaction

↓

Consumer

↓

Transaction Commit

↓

Offset Commit
```

---

# Choosing the Right Guarantee

Choose based on business requirements.

| Application | Recommended Guarantee |
|-------------|----------------------|
| Logging | At Most Once |
| Monitoring | At Most Once |
| Notifications | At Least Once |
| Inventory | At Least Once |
| E-commerce Orders | At Least Once |
| Banking | Exactly Once |
| Payments | Exactly Once |
| Financial Ledger | Exactly Once |

---

# Best Practices

- Understand business requirements before choosing a delivery guarantee.
- Use `acks=all` for critical workloads.
- Enable idempotence in production.
- Use manual offset commits for important consumers.
- Design consumers to be idempotent.
- Use transactions only when true Exactly Once semantics are required.
- Monitor retries and duplicate processing.
- Test failure scenarios regularly.
- Document delivery guarantees for every Kafka application.
- Balance reliability against performance.

---

# Common Mistakes

- Assuming Kafka always provides Exactly Once processing.
- Using `acks=0` for critical applications.
- Ignoring duplicate processing.
- Committing offsets before processing.
- Confusing retries with Exactly Once guarantees.
- Using transactions unnecessarily for simple workloads.
- Forgetting that business logic must also be idempotent.
- Choosing a delivery guarantee without considering business impact.

---

# Summary

Kafka supports three delivery guarantees, allowing applications to balance reliability, performance, and complexity according to their needs. At Most Once offers maximum throughput with possible message loss, At Least Once guarantees no message loss but may produce duplicates, and Exactly Once prevents both message loss and duplicate processing through idempotence and transactions. Selecting the appropriate guarantee depends on the application's business requirements, with financial systems typically requiring Exactly Once semantics and less critical workloads often benefiting from simpler delivery models.

---

# Key Takeaways

- Kafka supports At Most Once, At Least Once, and Exactly Once delivery guarantees.
- Each guarantee involves trade-offs between reliability, performance, and complexity.
- At Most Once prioritizes speed but may lose messages.
- At Least Once prevents message loss but may produce duplicates.
- Exactly Once combines idempotence and transactions to avoid both loss and duplication.
- Consumers should commit offsets only after successful processing.
- Idempotent business logic is recommended even when using Exactly Once processing.
- Choose the delivery guarantee based on business requirements rather than technical preference.