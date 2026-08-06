# Producer Commands

## Overview

Kafka Producers publish messages to Kafka topics. While producers are typically implemented using programming languages such as Java or Python, Kafka also provides a command-line producer utility for testing and development.

The **`kafka-console-producer.sh`** command allows developers to:

- Publish messages
- Test topics
- Verify consumer applications
- Simulate events
- Debug Kafka clusters

The console producer is one of the most frequently used Kafka CLI tools during development.

---

# kafka-console-producer.sh

The Kafka console producer utility is:

```bash
kafka-console-producer.sh
```

It connects to a Kafka broker and sends messages to a topic.

---

# Basic Command

The minimum required command is:

```bash
kafka-console-producer.sh \
--bootstrap-server localhost:9092 \
--topic orders
```

After running the command:

```text
>
```

Kafka waits for input.

---

# Producing Messages

Example:

```text
Order Created

Order Updated

Order Cancelled
```

Press **Enter** after each line.

Each line becomes one Kafka message.

---

# Producer Workflow

```text
User Input

↓

Console Producer

↓

Kafka Broker

↓

Topic

↓

Partition
```

Messages are immediately sent to Kafka.

---

# Producing JSON Messages

The producer accepts any text.

Example:

```json
{
  "orderId": 101,
  "customer": "Alice",
  "status": "CREATED"
}
```

JSON is commonly used when testing APIs and consumers.

---

# Producing Multiple Messages

Simply continue typing.

```text
Message One

Message Two

Message Three

Message Four
```

Every line becomes a separate Kafka record.

---

# Ending the Producer

Press:

```text
Ctrl + C
```

The producer exits gracefully.

---

# Sending Messages with Keys

Kafka can send keyed messages.

Enable key parsing:

```bash
kafka-console-producer.sh \
--bootstrap-server localhost:9092 \
--topic orders \
--property parse.key=true \
--property key.separator=:
```

Input:

```text
101:Order Created

102:Order Created

101:Order Updated
```

---

# Key Parsing

Example:

```text
101:Order Created
```

Kafka interprets:

```text
Key

↓

101

----------------

Value

↓

Order Created
```

The key determines the target partition.

---

# Why Use Keys?

Without keys:

```text
Producer

↓

Random Partition
```

With keys:

```text
Order ID

↓

Hash

↓

Partition
```

All records with the same key go to the same partition.

---

# Producing to Different Topics

Example:

```bash
kafka-console-producer.sh \
--bootstrap-server localhost:9092 \
--topic payments
```

Now every message is written to the **payments** topic.

---

# Running Inside Docker

Open the Kafka container.

```bash
docker exec -it kafka bash
```

Run the producer.

```bash
kafka-console-producer.sh \
--bootstrap-server localhost:9092 \
--topic orders
```

---

# Producing Large Messages

Example:

```text
Very Large JSON

↓

Producer

↓

Kafka
```

Message size is limited by broker and producer configuration.

The default maximum message size is typically **1 MB**.

---

# Producer Properties

Useful properties include:

| Property | Purpose |
|-----------|---------|
| `parse.key` | Enable message keys |
| `key.separator` | Separate key and value |
| `acks` | Acknowledgement mode |
| `compression.type` | Message compression |

Most production applications configure these through client libraries rather than the console producer.

---

# Producer Example

Suppose:

```text
Orders Topic
```

Messages entered:

```text
Order Created

Order Updated

Order Packed
```

Kafka stores:

```text
Offset

0

↓

1

↓

2
```

The consumer can now read these records.

---

# Producing Events

Instead of arbitrary text:

```text
Hello

World
```

Prefer realistic business events.

Example:

```json
{
  "event": "OrderCreated",
  "orderId": 105,
  "customer": "Alice"
}
```

This better simulates production systems.

---

# Common Workflow

```text
Create Topic

↓

Start Producer

↓

Enter Messages

↓

Start Consumer

↓

Verify Output
```

This is the most common workflow when learning Kafka.

---

# Common Errors

### Unknown Topic

```text
UnknownTopicOrPartitionException
```

Solution:

Create the topic first.

---

### Connection Refused

```text
Connection refused
```

Verify:

- Kafka is running
- Bootstrap server is correct
- Port mapping is correct

---

### Timeout

```text
TimeoutException
```

Possible causes:

- Broker unavailable
- Incorrect hostname
- Network issue

---

### Invalid Key Separator

Suppose:

```text
101-Order Created
```

Configuration:

```text
key.separator=:
```

Kafka cannot split the key correctly.

Ensure the separator matches the input format.

---

# Typical Development Usage

Developers commonly use the console producer for:

- Testing new topics
- Verifying consumers
- Sending sample JSON
- Debugging applications
- Learning Kafka

It is not intended for high-throughput production workloads.

---

# Advantages

- Simple to use.
- No programming required.
- Excellent for testing.
- Works with any Kafka topic.
- Supports keyed messages.
- Ideal for debugging.

---

# Limitations

- Manual message entry.
- Not suitable for large-scale publishing.
- Limited producer configuration.
- No batching or application logic.

---

# Best Practices

- Test consumers using realistic business events.
- Use JSON when simulating APIs.
- Test keyed messages to verify partitioning.
- Verify topics before producing.
- Use Docker containers for consistent environments.
- Stop the producer cleanly using **Ctrl + C**.

---

# Common Mistakes

- Producing to a topic that does not exist.
- Forgetting the bootstrap server.
- Using the wrong key separator.
- Assuming the console producer behaves like a production application.
- Sending malformed JSON.
- Ignoring broker connection errors.

---

# Summary

The `kafka-console-producer.sh` utility provides a simple way to publish messages directly to Kafka topics without writing application code. It is widely used for testing, debugging, and learning Kafka. By supporting plain text, JSON, and keyed messages, the console producer helps developers verify producer behavior, consumer applications, and topic configurations before implementing production-grade Kafka producers.

---

# Key Takeaways

- `kafka-console-producer.sh` publishes messages to Kafka topics.
- Every line entered becomes a separate Kafka record.
- Message keys can be enabled using `parse.key=true`.
- Keys determine partition assignment.
- JSON messages are commonly used for testing.
- The console producer is ideal for development and debugging.
- It complements application-based producers rather than replacing them.
- Mastering the console producer simplifies Kafka testing and troubleshooting.