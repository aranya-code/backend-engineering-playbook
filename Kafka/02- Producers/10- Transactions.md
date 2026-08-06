# Transactions

## Overview

In many business applications, writing a single message is not enough. A producer may need to write multiple messages across different topics or partitions as part of a single business operation.

Consider an order processing system.

When an order is placed, the application may need to publish:

- Order Created
- Inventory Reserved
- Payment Initiated

If one of these messages is written successfully while another fails, the system enters an inconsistent state.

Apache Kafka solves this problem using **Transactions**.

Transactions allow a producer to group multiple write operations into a single **atomic unit of work**.

Either:

- Every message is committed.

or

- Every message is discarded.

There is no partial success.

---

# What is a Transaction?

A transaction is a collection of producer operations that succeed or fail together.

Instead of:

```text
Message A

Success

------------------

Message B

Failed

------------------

Message C

Success
```

Kafka guarantees:

```text
Message A

Committed

↓

Message B

Committed

↓

Message C

Committed
```

or

```text
Message A

Discarded

↓

Message B

Discarded

↓

Message C

Discarded
```

---

# Why are Transactions Needed?

Consider an e-commerce application.

When a customer places an order:

```text
Create Order

↓

Reserve Inventory

↓

Start Payment
```

Each operation produces an event.

Without transactions:

```text
Order Created

✓

----------------

Inventory Reserved

✗

----------------

Payment Started

✓
```

The system becomes inconsistent.

---

# Real-World Example

Suppose an order service sends three messages.

```text
Orders Topic

↓

Order Created

----------------

Inventory Topic

↓

Inventory Reserved

----------------

Payments Topic

↓

Payment Started
```

If the producer crashes after sending the second message:

```text
Orders

✓

Inventory

✓

Payments

✗
```

The order exists, inventory is reserved, but payment never starts.

---

# Transaction Solution

With transactions:

```text
Begin Transaction

↓

Send Order Event

↓

Send Inventory Event

↓

Send Payment Event

↓

Commit Transaction
```

If any step fails:

```text
Abort Transaction
```

Kafka discards every message.

---

# Transaction Workflow

```text
Producer

↓

Begin Transaction

↓

Send Message

↓

Send Message

↓

Send Message

↓

Commit

↓

Visible to Consumers
```

Messages become visible only after the transaction commits.

---

# Atomicity

Transactions provide **Atomicity**.

Atomicity means:

```text
All

or

Nothing
```

Never:

```text
Half Completed
```

This is the "A" in the ACID properties.

---

# Transaction Coordinator

Kafka uses a special internal component called the **Transaction Coordinator**.

Architecture:

```text
Producer

↓

Transaction Coordinator

↓

Kafka Brokers
```

The Transaction Coordinator manages:

- Transaction state
- Commit
- Abort
- Recovery

---

# Transaction Lifecycle

A transaction follows these stages.

```text
Initialize

↓

Begin

↓

Send Messages

↓

Commit

or

Abort

↓

Complete
```

---

# Step 1: Initialize Transactions

Before sending transactional messages, the producer initializes transaction support.

```text
Producer

↓

Initialize Transactions
```

Kafka assigns a unique transaction identity.

---

# Step 2: Begin Transaction

```text
Producer

↓

Begin Transaction
```

All subsequent messages belong to this transaction.

---

# Step 3: Send Messages

Example:

```text
Orders Topic

↓

Order Created

-------------------

Inventory Topic

↓

Inventory Reserved

-------------------

Payments Topic

↓

Payment Started
```

These messages remain invisible to consumers.

---

# Step 4: Commit Transaction

If everything succeeds:

```text
Commit Transaction
```

Kafka marks every message as committed.

Consumers can now read them.

```text
Committed

↓

Visible
```

---

# Step 5: Abort Transaction

Suppose payment fails.

```text
Producer

↓

Abort Transaction
```

Kafka discards every message.

```text
Order Created

Discard

-------------------

Inventory Reserved

Discard

-------------------

Payment Started

Discard
```

No partial data exists.

---

# Transaction Visibility

Before commit:

```text
Producer

↓

Messages

↓

Hidden
```

After commit:

```text
Messages

↓

Visible

↓

Consumers
```

Consumers never see incomplete transactions.

---

# Transactions Across Partitions

Transactions work across multiple partitions.

Example:

```text
Orders

Partition 0

----------------

Payments

Partition 2

----------------

Inventory

Partition 1
```

Kafka commits all partitions together.

---

# Transactions Across Topics

Transactions also support multiple topics.

```text
Orders Topic

↓

Payments Topic

↓

Inventory Topic

↓

Notifications Topic
```

All topics commit together.

---

# Idempotence vs Transactions

These concepts solve different problems.

| Idempotence | Transactions |
|--------------|--------------|
| Prevents duplicate writes | Groups multiple writes atomically |
| Single partition guarantee | Multiple partitions and topics |
| Handles retries | Handles business consistency |
| Enabled by default | Requires configuration |

Transactions build on top of idempotent producers.

---

# Transaction Configuration

Enable transactions by specifying a transaction ID.

Example:

```properties
transactional.id=order-service-1
```

The producer initializes transactions before sending messages.

---

# Transaction Timeline

```text
Producer

↓

Begin Transaction

↓

Message A

↓

Message B

↓

Message C

↓

Commit

↓

Consumer Reads
```

If failure occurs:

```text
Producer

↓

Begin

↓

Message A

↓

Failure

↓

Abort

↓

Nothing Stored
```

---

# Transactions and Exactly Once Semantics

Transactions are a key building block for **Exactly Once Semantics (EOS)**.

Kafka combines:

- Idempotent Producer
- Transactions
- Offset Management

to ensure:

```text
Process Once

↓

Store Once

↓

Commit Once
```

This is essential for stream processing applications.

---

# Consumer Isolation Levels

Consumers control whether they read transactional messages.

Default production setting:

```properties
isolation.level=read_committed
```

Behavior:

```text
Committed Messages

↓

Visible
```

Aborted transactions remain hidden.

Alternative:

```properties
isolation.level=read_uncommitted
```

Behavior:

```text
Committed

+

Aborted

↓

Visible
```

This mode is primarily useful for debugging and testing.

---

# Common Use Cases

Transactions are commonly used for:

- Banking systems
- Payment processing
- Order processing
- Inventory management
- Financial ledgers
- Event sourcing
- Kafka Streams applications

These systems require strong consistency.

---

# Performance Considerations

Transactions provide excellent reliability.

Trade-offs:

- Additional coordination
- Slightly higher latency
- Increased metadata management

For most business applications, the consistency benefits outweigh the performance cost.

---

# Advantages

- Atomic writes
- Multi-topic support
- Multi-partition support
- Exactly-once semantics
- Strong consistency
- Safe failure recovery

---

# Limitations

- Higher latency than normal producers
- Additional configuration
- Slightly more operational complexity
- Not necessary for every application

Simple event publishing often works well without transactions.

---

# Best Practices

- Use transactions for business-critical workflows.
- Enable idempotent producers.
- Configure a unique `transactional.id`.
- Use `acks=all`.
- Configure consumers with `read_committed`.
- Keep transactions short to reduce resource usage.
- Monitor transaction failures in production.

---

# Common Mistakes

- Confusing idempotence with transactions.
- Using transactions for simple logging workloads.
- Forgetting to configure `transactional.id`.
- Using `read_uncommitted` in production consumers.
- Keeping transactions open for long periods.

---

# Summary

Kafka Transactions allow producers to group multiple write operations into a single atomic unit of work. Messages remain invisible until the transaction is successfully committed, ensuring that consumers never observe partial results. Transactions extend the guarantees provided by idempotent producers by supporting atomic writes across multiple partitions and topics, making them essential for financial systems, order processing, inventory management, and other business-critical applications requiring exactly-once semantics.

---

# Key Takeaways

- Transactions group multiple producer operations into one atomic unit.
- Either all messages are committed or all are aborted.
- Messages remain invisible until the transaction commits.
- Kafka uses a Transaction Coordinator to manage transaction state.
- Transactions support multiple topics and partitions.
- Transactions build upon idempotent producers.
- Consumers should use `read_committed` to avoid reading aborted transactions.
- Transactions are fundamental for implementing exactly-once semantics in Kafka.