# Producer Questions

## Overview

Kafka Producers are responsible for publishing messages to Kafka topics. Since producers are the entry point for data into a Kafka cluster, interviewers frequently ask questions about how producers work, message routing, acknowledgements, retries, batching, compression, idempotence, and transactions.

This chapter covers the most frequently asked Kafka Producer interview questions with concise, production-oriented answers.

---

# What is a Kafka Producer?

**Question**

> What is a Kafka Producer?

**Answer**

A Kafka Producer is an application or client that publishes messages to Kafka topics.

Example:

```text
Order Service

↓

Kafka Producer

↓

orders.created
```

The producer sends events to Kafka brokers for storage.

---

# How Does a Producer Send a Message?

**Question**

> Explain the Producer workflow.

**Answer**

Producer workflow:

```text
Application

↓

Producer

↓

Serializer

↓

Partition Selection

↓

Broker

↓

Acknowledgement
```

The producer serializes the message, selects a partition, sends the record to the broker, and waits for an acknowledgement based on the configured `acks` value.

---

# How Does a Producer Choose a Partition?

**Question**

> How is the target partition selected?

**Answer**

Kafka uses the following strategy:

- If a key is provided, Kafka hashes the key and selects a partition.
- If no key is provided, Kafka's partitioner distributes records across available partitions.

Example:

```text
Order ID

↓

Hash

↓

Partition 2
```

---

# Why Do We Use Message Keys?

**Question**

> Why should we use message keys?

**Answer**

Message keys ensure related events always go to the same partition.

Example:

```text
Order 101

↓

Created

↓

Paid

↓

Shipped
```

All events remain ordered because they are written to the same partition.

---

# What Happens If No Key Is Provided?

**Question**

> What happens when a producer sends a message without a key?

**Answer**

Kafka distributes messages automatically using its partitioning strategy.

Benefits:

- Better load balancing
- Even partition distribution

Limitation:

- Ordering between related messages is not guaranteed.

---

# What is `acks`?

**Question**

> What does the `acks` configuration control?

**Answer**

`acks` determines when the producer considers a message successfully written.

Options:

```properties
acks=0
```

No acknowledgement.

---

```properties
acks=1
```

Leader acknowledgement only.

---

```properties
acks=all
```

Leader and required replicas acknowledge the write.

`acks=all` provides the highest durability.

---

# Which `acks` Value Is Best?

**Question**

> Which acknowledgement mode should be used in production?

**Answer**

For critical applications:

```properties
acks=all
```

Reasons:

- Highest durability
- Better fault tolerance
- Reduced risk of message loss

---

# What Happens If a Broker Fails During a Write?

**Question**

> What happens if the leader broker fails while producing messages?

**Answer**

Kafka elects a new leader from the In-Sync Replicas (ISR).

The producer retries the request if retries are enabled.

Proper configuration minimizes the chance of data loss.

---

# What Are Producer Retries?

**Question**

> Why do producers retry failed requests?

**Answer**

Retries help recover from temporary failures such as:

- Network issues
- Broker restarts
- Leader elections

Configuration:

```properties
retries=5
```

Retries improve reliability but should be combined with idempotence.

---

# Why Enable Idempotence?

**Question**

> What is an Idempotent Producer?

**Answer**

An Idempotent Producer prevents duplicate messages during retries.

Configuration:

```properties
enable.idempotence=true
```

Benefits:

- Safe retries
- Duplicate prevention
- Improved reliability

Recommended for almost all production workloads.

---

# What is Producer Batching?

**Question**

> Why does Kafka batch messages?

**Answer**

Instead of sending one message at a time:

```text
1 Message

↓

Network Request
```

Kafka batches records:

```text
100 Messages

↓

Single Network Request
```

Benefits:

- Higher throughput
- Lower network overhead
- Better performance

---

# What is `linger.ms`?

**Question**

> What is the purpose of `linger.ms`?

**Answer**

`linger.ms` specifies how long the producer waits before sending a batch.

Example:

```properties
linger.ms=5
```

The producer waits up to five milliseconds to collect additional records.

Higher values:

- Larger batches
- Higher throughput
- Slightly increased latency

---

# What is `batch.size`?

**Question**

> What does `batch.size` control?

**Answer**

`batch.size` determines the maximum size of a producer batch.

Larger batches:

- Improve throughput
- Reduce network calls

Excessively large batches may increase memory usage and latency.

---

# Why Use Compression?

**Question**

> Why should producers compress messages?

**Answer**

Compression reduces:

- Network traffic
- Disk usage
- Storage cost

Common algorithms:

- zstd
- lz4
- snappy
- gzip

Modern Kafka deployments commonly prefer **zstd** or **lz4**.

---

# What is `delivery.timeout.ms`?

**Question**

> What happens if a producer cannot deliver a message?

**Answer**

The producer retries until:

```properties
delivery.timeout.ms
```

expires.

If delivery still fails:

```text
TimeoutException
```

is returned.

---

# What Happens If the Topic Does Not Exist?

**Question**

> What happens if a producer sends data to a non-existent topic?

**Answer**

Possible outcomes:

- Topic is created automatically (if enabled).
- The producer receives:

```text
UnknownTopicOrPartitionException
```

Many production environments disable automatic topic creation.

---

# What is a Producer Transaction?

**Question**

> Why do Kafka producers support transactions?

**Answer**

Transactions allow multiple writes to succeed or fail together.

Example:

```text
Write Record A

↓

Write Record B

↓

Commit

OR

Rollback
```

Transactions support Exactly Once Processing.

---

# How Does a Producer Handle Failures?

**Question**

> How should producers recover from failures?

**Answer**

Recommended practices:

- Enable retries
- Enable idempotence
- Use `acks=all`
- Log failures
- Monitor retry rates
- Handle exceptions gracefully

---

# Producer Best Practices

**Question**

> What are the best practices for Kafka producers?

**Answer**

- Use `acks=all`.
- Enable idempotence.
- Use meaningful message keys.
- Batch messages.
- Enable compression.
- Keep messages reasonably small.
- Monitor latency and retries.
- Handle failures gracefully.
- Secure producers using SSL/TLS and SASL.
- Test retry and recovery scenarios.

---

# Scenario-Based Questions

### Question

> A producer is creating duplicate messages. What could be the reason?

**Answer**

Possible causes:

- Retries without idempotence
- Application retries
- Duplicate business logic

Enable:

```properties
enable.idempotence=true
```

---

### Question

> Producer latency suddenly increases. How would you investigate?

**Answer**

Check:

- Broker health
- Network latency
- Disk performance
- Producer batch settings
- Compression
- Request latency
- CPU utilization

---

### Question

> Why is `acks=0` rarely used in production?

**Answer**

Because the producer never verifies whether the broker actually received the message.

This provides maximum performance but the lowest reliability.

---

### Question

> When should you use a message key?

**Answer**

Whenever ordering must be preserved for related events.

Examples:

- Order ID
- Customer ID
- Account ID

---

### Question

> Why shouldn't large files be sent through Kafka?

**Answer**

Large messages:

- Increase latency
- Consume more memory
- Reduce throughput
- Increase disk usage

Instead, store files externally and publish references through Kafka.

---

# Frequently Asked Interview Questions

- What is a Kafka Producer?
- How does a Producer work?
- How does Kafka choose a partition?
- What is a message key?
- What is `acks`?
- What is `acks=all`?
- Why do producers retry requests?
- What is an Idempotent Producer?
- What is batching?
- What is `linger.ms`?
- What is `batch.size`?
- Why use compression?
- What is `delivery.timeout.ms`?
- What are producer transactions?
- What are Kafka producer best practices?

---

# Summary

Kafka Producers are responsible for reliably publishing messages into Kafka topics. Interview questions typically focus on acknowledgements, partitioning, batching, retries, compression, idempotence, and transactions because these features directly impact performance and reliability. A solid understanding of producer configuration and failure handling demonstrates the ability to build resilient, production-ready Kafka applications.

---

# Key Takeaways

- Producers publish messages to Kafka topics.
- Message keys determine partition selection and preserve ordering.
- `acks=all` provides the strongest delivery guarantee.
- Idempotent producers prevent duplicate messages during retries.
- Batching and compression improve throughput.
- Transactions support Exactly Once Processing.
- Monitor producer latency, retries, and failures in production.
- Proper producer configuration is essential for reliable Kafka deployments.