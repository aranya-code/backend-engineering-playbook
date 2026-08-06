# Poll Loop

## Overview

The **Poll Loop** is the heart of every Kafka Consumer.

Unlike traditional messaging systems that push messages to consumers, Kafka follows a **pull-based model**. Consumers repeatedly request new messages from Kafka by calling the `poll()` method.

Every consumer application, regardless of language or framework, continuously performs the following cycle:

- Poll messages
- Process messages
- Commit offsets
- Poll again

Without the poll loop, a Kafka consumer cannot receive messages, maintain membership in a consumer group, or participate in rebalancing.

---

# What is the Poll Loop?

The Poll Loop is a continuous cycle in which the consumer repeatedly asks Kafka for new records.

```text
Consumer

↓

poll()

↓

Kafka Broker

↓

Records

↓

Process Records

↓

poll()

↓

Repeat
```

This loop continues until the application shuts down.

---

# Why Kafka Uses Polling

Kafka follows a **Pull Model** instead of a Push Model.

Push Model:

```text
Broker

↓

Consumer
```

Problems:

- Consumer overload
- No flow control
- Difficult backpressure handling
- Unpredictable memory usage

Pull Model:

```text
Consumer

↓

Broker
```

Advantages:

- Consumer controls reading speed.
- Better backpressure management.
- Predictable resource utilization.
- Efficient batching.

---

# Poll Loop Lifecycle

A consumer repeatedly performs the following workflow.

```text
Poll

↓

Receive Records

↓

Deserialize

↓

Business Logic

↓

Commit Offset

↓

Poll Again
```

This cycle continues throughout the application's lifetime.

---

# Basic Poll Loop

The simplified workflow looks like this:

```text
while Running

↓

poll()

↓

Process Messages

↓

Commit Offset
```

Although simple, this loop drives the entire Kafka consumer architecture.

---

# What Happens During poll()

When the consumer calls:

```text
poll()
```

Kafka performs multiple operations internally.

```text
Consumer

↓

Send Fetch Request

↓

Broker Reads Partition

↓

Broker Creates Response

↓

Return Records
```

The application only sees the returned records.

---

# Internal Poll Workflow

```text
poll()

↓

Heartbeat

↓

Check Rebalance

↓

Fetch Records

↓

Deserialize

↓

Return Records
```

The `poll()` method does much more than simply retrieving messages.

---

# Fetch Request

The consumer sends a fetch request to the leader broker.

```text
Consumer

↓

Fetch Request

↓

Leader Broker
```

The request includes:

- Assigned partitions
- Current offsets
- Maximum bytes
- Wait timeout

---

# Broker Response

The broker searches the requested partitions.

```text
Partition

↓

Offset 150

↓

Offset 151

↓

Offset 152
```

The matching records are returned to the consumer.

---

# Poll Returns a Batch

Kafka always returns a batch of records.

Example:

```text
Batch

↓

Record 150

Record 151

Record 152

Record 153
```

Even if only one record exists, Kafka still returns a batch.

---

# Empty Poll

Sometimes no new records exist.

```text
Consumer

↓

poll()

↓

Empty Batch
```

This is completely normal.

The consumer immediately polls again.

---

# Continuous Polling

The consumer never stops polling.

```text
poll()

↓

Records

↓

Process

↓

poll()

↓

Records

↓

Process

↓

poll()
```

This continuous cycle allows Kafka to stream data in real time.

---

# Poll Interval

Consumers should call `poll()` regularly.

If the consumer waits too long:

```text
No Poll

↓

Heartbeat Lost

↓

Consumer Removed

↓

Rebalance
```

Kafka assumes the consumer has failed.

---

# max.poll.interval.ms

Kafka allows a maximum processing interval between two poll calls.

Example:

```properties
max.poll.interval.ms=300000
```

Equivalent:

```text
5 Minutes
```

If exceeded:

```text
Consumer

↓

Removed From Group

↓

Rebalance
```

---

# Poll Timeout

The consumer specifies how long Kafka should wait for records.

Example:

```text
poll(1 second)
```

Possible outcomes:

```text
Records Available

↓

Return Immediately
```

or

```text
No Records

↓

Wait

↓

Return Empty Batch
```

---

# Fetch Batching

Suppose multiple messages exist.

```text
Offset 100

Offset 101

Offset 102

Offset 103

Offset 104
```

Kafka returns all available records up to configured limits.

This reduces network requests.

---

# Processing After Poll

Once records are received:

```text
Poll

↓

Deserialize

↓

Business Logic

↓

Commit Offset
```

Kafka does not process records automatically.

Applications implement the processing logic.

---

# Poll and Offset Progress

Suppose the consumer has committed:

```text
Offset

200
```

Next poll:

```text
Offset

201

↓

202

↓

203
```

The consumer resumes from the next unread record.

---

# Poll and Heartbeats

Calling `poll()` also helps maintain consumer group membership.

```text
poll()

↓

Heartbeat

↓

Group Coordinator
```

Without regular polling:

```text
Heartbeat Missing

↓

Consumer Dead

↓

Rebalance
```

---

# Poll and Rebalancing

When group membership changes:

```text
Consumer Added

↓

Rebalance

↓

New Partition Assignment

↓

poll()
```

The next poll reflects the updated assignments.

---

# Slow Processing Problem

Suppose processing takes a long time.

```text
poll()

↓

10 Minutes Processing

↓

Next Poll
```

Kafka detects:

```text
No Poll

↓

Consumer Timeout

↓

Rebalance
```

This is one of the most common production issues.

---

# Solution for Slow Processing

Instead of blocking the poll loop:

```text
poll()

↓

Receive Batch

↓

Worker Threads

↓

Continue Polling
```

The consumer continues sending heartbeats while worker threads process messages.

---

# Poll Loop Architecture

```text
                  Kafka Cluster
                        │
                        ▼
                 poll()
                        │
                        ▼
               Receive Records
                        │
                        ▼
              Deserialize Records
                        │
                        ▼
             Business Processing
                        │
                        ▼
               Commit Offsets
                        │
                        ▼
                  poll() Again
```

---

# Real-World Example

An inventory service consumes order events.

```text
Orders Topic

↓

poll()

↓

Order Created

↓

Reserve Inventory

↓

Commit Offset

↓

poll()
```

This loop may execute thousands of times every second.

---

# Performance Considerations

Efficient poll loops should:

- Poll frequently.
- Process batches efficiently.
- Avoid long blocking operations.
- Commit offsets after successful processing.
- Monitor consumer lag.

A healthy poll loop keeps consumers responsive and minimizes unnecessary rebalancing.

---

# Best Practices

- Keep the poll loop running continuously.
- Process records quickly.
- Offload long-running work to worker threads when appropriate.
- Commit offsets only after successful processing.
- Monitor `max.poll.interval.ms`.
- Handle empty polls correctly.
- Avoid blocking the polling thread.

---

# Common Mistakes

- Calling `poll()` only once.
- Performing heavy processing inside the polling thread.
- Ignoring empty poll responses.
- Allowing processing time to exceed `max.poll.interval.ms`.
- Confusing polling frequency with message processing speed.
- Assuming Kafka pushes messages automatically.

---

# Summary

The Poll Loop is the core execution cycle of every Kafka consumer. By repeatedly calling `poll()`, consumers fetch batches of records, maintain group membership, receive heartbeat updates, participate in rebalancing, and process incoming events. A well-designed poll loop balances frequent polling with efficient message processing, ensuring high throughput, low latency, and stable consumer group operation.

---

# Key Takeaways

- The Poll Loop is the central mechanism of Kafka consumers.
- Kafka uses a pull-based model where consumers request records using `poll()`.
- Each `poll()` call may fetch records, send heartbeats, and participate in rebalancing.
- Kafka returns batches of records rather than individual messages.
- Consumers must call `poll()` regularly to remain active in the consumer group.
- Long-running processing can trigger unnecessary rebalancing if polling is delayed.
- Worker threads can help keep the poll loop responsive while processing messages.
- Efficient poll loop design is essential for scalable and reliable Kafka consumer applications.