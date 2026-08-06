# Consumer Workflow

## Overview

A Kafka consumer continuously retrieves, processes, and acknowledges messages from a Kafka cluster. Unlike traditional messaging systems where messages are pushed to consumers, Kafka uses a **pull-based architecture**, giving consumers complete control over when and how much data to read.

Although reading a message appears simple from the application's perspective, Kafka performs numerous internal operations, including:

- Connecting to the cluster
- Joining a consumer group
- Receiving partition assignments
- Polling records
- Deserializing messages
- Processing records
- Committing offsets
- Sending heartbeats

Understanding this workflow is essential before learning Poll Loop, Offset Management, and Consumer Rebalancing.

---

# Consumer Workflow at a Glance

Every consumer follows the same lifecycle.

```text
Application

↓

Create Consumer

↓

Connect to Cluster

↓

Join Consumer Group

↓

Receive Partition Assignment

↓

Poll Messages

↓

Deserialize Records

↓

Process Records

↓

Commit Offsets

↓

Repeat
```

This workflow continues until the consumer shuts down.

---

# Step 1: Create the Consumer

The application creates a Kafka Consumer.

```text
Application

↓

Kafka Consumer
```

The consumer is configured with:

- Bootstrap Servers
- Group ID
- Deserializers
- Offset configuration

At this stage, the consumer has not yet connected to Kafka.

---

# Step 2: Connect to the Kafka Cluster

The consumer connects to one of the bootstrap brokers.

```text
Consumer

↓

Bootstrap Broker
```

After connecting, Kafka provides metadata including:

- Brokers
- Topics
- Partitions
- Leaders

The consumer now understands the cluster topology.

---

# Step 3: Join a Consumer Group

If a Group ID is configured:

```text
Consumer

↓

Join Group

↓

Group Coordinator
```

Kafka registers the consumer as part of the group.

Example:

```text
Order Consumers

↓

Consumer A

Consumer B

Consumer C
```

---

# Step 4: Group Coordination

The Group Coordinator performs several tasks.

```text
Register Consumer

↓

Elect Leader (if required)

↓

Assign Partitions

↓

Notify Consumers
```

Every consumer receives its assigned partitions.

---

# Step 5: Partition Assignment

Suppose a topic has four partitions.

```text
Orders Topic

P0

P1

P2

P3
```

Consumer group:

```text
Consumer A

Consumer B
```

Assignment:

```text
Consumer A

↓

P0

P2

----------------

Consumer B

↓

P1

P3
```

Each partition belongs to only one consumer within the group.

---

# Step 6: Initialize Offsets

Before polling begins, Kafka determines where reading should start.

Possible locations:

```text
Committed Offset

↓

Continue Reading
```

or

```text
No Offset

↓

earliest

or

latest
```

The starting position depends on consumer configuration.

---

# Step 7: Enter the Poll Loop

The consumer begins polling.

```text
Consumer

↓

poll()

↓

Broker

↓

Records
```

This is the core of Kafka consumer operation.

The poll loop runs continuously.

---

# Step 8: Fetch Records

The broker reads data from assigned partitions.

```text
Partition

↓

Messages

↓

Consumer
```

Kafka returns a batch of records.

Example:

```text
Offset 100

Offset 101

Offset 102

Offset 103
```

---

# Step 9: Deserialize Records

Kafka stores bytes.

Consumers convert them back into application objects.

```text
Bytes

↓

Deserializer

↓

Application Object
```

Example:

```text
JSON

↓

Python Dictionary
```

Deserialization occurs before processing.

---

# Step 10: Process Messages

The application processes each record.

Example:

```text
Order Created

↓

Validate

↓

Update Database

↓

Send Email
```

Kafka itself does not process business logic.

It simply delivers records.

---

# Step 11: Commit Offsets

After successful processing:

```text
Consumer

↓

Commit Offset
```

Offset:

```text
Current

105

↓

Next Read

106
```

Committing offsets prevents already processed messages from being read again.

---

# Step 12: Send Heartbeats

While polling, the consumer periodically sends heartbeats.

```text
Consumer

↓

Heartbeat

↓

Group Coordinator
```

Heartbeats tell Kafka:

```text
Consumer

↓

Alive
```

Without heartbeats:

```text
Consumer

↓

Dead

↓

Rebalance
```

---

# Step 13: Repeat

The workflow continues.

```text
Poll

↓

Process

↓

Commit

↓

Heartbeat

↓

Poll Again
```

Consumers continue until they are stopped.

---

# Complete Consumer Workflow

```text
Application
      │
      ▼
Create Consumer
      │
      ▼
Connect to Cluster
      │
      ▼
Join Consumer Group
      │
      ▼
Receive Partition Assignment
      │
      ▼
Initialize Offsets
      │
      ▼
Poll Messages
      │
      ▼
Deserialize
      │
      ▼
Process Records
      │
      ▼
Commit Offsets
      │
      ▼
Heartbeat
      │
      ▼
Repeat
```

---

# Consumer Shutdown

When shutting down:

```text
Consumer

↓

Finish Processing

↓

Commit Offsets

↓

Leave Group

↓

Close Connection
```

A graceful shutdown prevents unnecessary rebalancing and duplicate processing.

---

# Failure During Processing

Suppose processing fails.

```text
Poll

↓

Process

↓

Exception
```

Possible outcomes:

- Retry processing
- Skip the message
- Send to Dead Letter Topic
- Stop the consumer

The chosen strategy depends on the application's requirements.

---

# Consumer Restart

Suppose the application crashes.

```text
Consumer

↓

Crash
```

After restarting:

```text
Read Last Committed Offset

↓

Resume Processing
```

This allows Kafka consumers to recover from failures without starting from the beginning.

---

# Consumer Workflow vs Producer Workflow

| Producer | Consumer |
|----------|----------|
| Serialize | Deserialize |
| Choose Partition | Read Assigned Partition |
| Batch Messages | Poll Message Batch |
| Send to Broker | Fetch from Broker |
| Receive ACK | Commit Offset |

Together they complete Kafka's event streaming pipeline.

---

# Real-World Example

An order processing system.

```text
Orders Topic

↓

Consumer

↓

Poll

↓

Deserialize

↓

Create Invoice

↓

Update Inventory

↓

Commit Offset

↓

Poll Again
```

Thousands of such workflows may execute simultaneously across multiple consumer instances.

---

# Best Practices

- Keep the poll loop running continuously.
- Process records efficiently to avoid poll timeouts.
- Commit offsets only after successful processing.
- Handle processing failures gracefully.
- Shut down consumers cleanly.
- Monitor consumer lag and rebalance events.
- Keep business logic separate from Kafka infrastructure code.

---

# Common Mistakes

- Assuming Kafka pushes messages automatically.
- Performing long-running work without polling.
- Committing offsets before processing completes.
- Ignoring heartbeat requirements.
- Blocking the poll loop for extended periods.
- Failing to handle consumer shutdown properly.

---

# Summary

A Kafka consumer follows a continuous workflow of connecting to the cluster, joining a consumer group, receiving partition assignments, polling records, deserializing messages, processing business logic, committing offsets, and sending heartbeats. This cycle repeats for the lifetime of the consumer, allowing Kafka to provide scalable, fault-tolerant, and reliable message consumption. Understanding this workflow provides the foundation for mastering poll loops, offset management, consumer rebalancing, and delivery semantics.

---

# Key Takeaways

- Kafka consumers operate using a pull-based workflow.
- Consumers connect to the cluster and join a consumer group before reading messages.
- The Group Coordinator assigns partitions to consumers.
- Messages are fetched in batches using the poll mechanism.
- Records are deserialized before application processing.
- Offsets are committed after successful processing.
- Heartbeats maintain consumer membership within the group.
- The poll-process-commit cycle continues throughout the consumer's lifetime.