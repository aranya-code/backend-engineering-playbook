# Consumer Commands

## Overview

After messages are produced to Kafka topics, they must be consumed by applications. While production consumers are typically implemented using programming languages such as Java or Python, Kafka provides a command-line consumer utility for testing, debugging, and development.

The **`kafka-console-consumer.sh`** utility allows developers to:

- Read messages from topics
- Verify producers
- Replay historical messages
- Inspect message keys
- Read specific partitions
- Debug Consumer Groups

It is one of the most commonly used Kafka CLI tools during development.

---

# kafka-console-consumer.sh

The Kafka console consumer utility is:

```bash
kafka-console-consumer.sh
```

It connects to Kafka and continuously reads messages from a topic.

---

# Basic Command

Consume messages from a topic.

```bash
kafka-console-consumer.sh \
--bootstrap-server localhost:9092 \
--topic orders
```

The consumer starts waiting for new messages.

---

# Consumer Workflow

```text
Kafka Topic

↓

Consumer

↓

Terminal
```

Every new message appears in the terminal.

---

# Reading New Messages

Suppose the producer sends:

```text
Order Created

Order Updated

Order Packed
```

Consumer output:

```text
Order Created

Order Updated

Order Packed
```

The consumer continues waiting for additional records.

---

# Stopping the Consumer

Press:

```text
Ctrl + C
```

The consumer exits gracefully.

---

# Reading From the Beginning

By default, Kafka reads only new messages.

To replay existing messages:

```bash
kafka-console-consumer.sh \
--bootstrap-server localhost:9092 \
--topic orders \
--from-beginning
```

Kafka starts from the earliest available offset.

---

# Consumer Timeline

Without:

```text
--from-beginning
```

```text
Start Consumer

↓

Read New Messages
```

---

With:

```text
--from-beginning
```

```text
Start Consumer

↓

Read All Available Messages

↓

Wait For New Messages
```

---

# Displaying Message Keys

Show keys with values.

```bash
kafka-console-consumer.sh \
--bootstrap-server localhost:9092 \
--topic orders \
--property print.key=true
```

Example output:

```text
101    Order Created

102    Order Created

101    Order Updated
```

---

# Displaying Offsets

Display message offsets.

```bash
kafka-console-consumer.sh \
--bootstrap-server localhost:9092 \
--topic orders \
--property print.offset=true
```

Example:

```text
Offset:0

Order Created

----------------

Offset:1

Order Updated
```

Useful for debugging replay scenarios.

---

# Displaying Partitions

Show partition information.

```bash
kafka-console-consumer.sh \
--bootstrap-server localhost:9092 \
--topic orders \
--property print.partition=true
```

Example:

```text
Partition:0

Order Created

----------------

Partition:1

Order Updated
```

---

# Displaying Timestamps

```bash
kafka-console-consumer.sh \
--bootstrap-server localhost:9092 \
--topic orders \
--property print.timestamp=true
```

Example:

```text
CreateTime

2026-08-06

Order Created
```

---

# Reading a Specific Partition

Consume only one partition.

```bash
kafka-console-consumer.sh \
--bootstrap-server localhost:9092 \
--topic orders \
--partition 1
```

Only messages from Partition 1 are displayed.

---

# Reading From a Specific Offset

Replay messages starting at Offset 50.

```bash
kafka-console-consumer.sh \
--bootstrap-server localhost:9092 \
--topic orders \
--partition 0 \
--offset 50
```

Kafka begins reading from Offset 50.

---

# Reading Only One Message

Consume a fixed number of records.

```bash
kafka-console-consumer.sh \
--bootstrap-server localhost:9092 \
--topic orders \
--max-messages 1
```

Consumer exits automatically after reading one record.

---

# Reading Ten Messages

```bash
kafka-console-consumer.sh \
--bootstrap-server localhost:9092 \
--topic orders \
--max-messages 10
```

Useful for testing.

---

# Using a Consumer Group

Join a Consumer Group.

```bash
kafka-console-consumer.sh \
--bootstrap-server localhost:9092 \
--topic orders \
--group inventory-service
```

Kafka now tracks offsets for this Consumer Group.

---

# Consumer Group Workflow

```text
Topic

↓

Consumer Group

↓

Offset Stored

↓

Next Read Continues
```

Without a group, offsets are not committed in the same way as a managed consumer application.

---

# Running Inside Docker

Open the Kafka container.

```bash
docker exec -it kafka bash
```

Run the consumer.

```bash
kafka-console-consumer.sh \
--bootstrap-server localhost:9092 \
--topic orders
```

---

# Consuming JSON Messages

Suppose producer sends:

```json
{
  "orderId":101,
  "status":"CREATED"
}
```

Consumer output:

```json
{
  "orderId":101,
  "status":"CREATED"
}
```

Kafka does not modify the payload.

---

# Typical Development Workflow

```text
Create Topic

↓

Start Consumer

↓

Start Producer

↓

Verify Messages

↓

Stop Consumer
```

This is the most common Kafka development workflow.

---

# Common Errors

### Unknown Topic

```text
UnknownTopicOrPartitionException
```

Solution:

Verify the topic exists.

---

### Connection Refused

```text
Connection refused
```

Verify:

- Kafka is running
- Bootstrap server is correct
- Docker networking is correct

---

### No Messages Displayed

Possible causes:

- Topic is empty
- Reading only new messages
- Wrong Consumer Group
- Wrong topic

Try:

```text
--from-beginning
```

---

### Offset Out of Range

```text
OffsetOutOfRangeException
```

Requested offset no longer exists because of retention.

---

# Frequently Used Consumer Options

| Option | Purpose |
|---------|---------|
| `--topic` | Topic name |
| `--from-beginning` | Read historical messages |
| `--group` | Consumer Group |
| `--partition` | Read one partition |
| `--offset` | Start from a specific offset |
| `--max-messages` | Stop after N records |
| `print.key=true` | Display keys |
| `print.offset=true` | Display offsets |
| `print.partition=true` | Display partition |
| `print.timestamp=true` | Display timestamps |

---

# Advantages

- No programming required.
- Excellent for debugging.
- Supports replay.
- Supports Consumer Groups.
- Displays metadata.
- Ideal for learning Kafka.

---

# Limitations

- Manual consumption.
- Not suitable for production workloads.
- Limited processing capabilities.
- No business logic.

---

# Best Practices

- Use `--from-beginning` when replaying historical data.
- Verify offsets during debugging.
- Use Consumer Groups to simulate production behavior.
- Inspect partitions when troubleshooting ordering issues.
- Display keys when testing partitioning.
- Stop consumers cleanly using **Ctrl + C**.

---

# Common Mistakes

- Forgetting `--from-beginning` when expecting historical messages.
- Using the wrong Consumer Group.
- Reading the wrong partition.
- Assuming the consumer automatically replays old messages.
- Ignoring offset information while debugging.
- Connecting to the wrong Kafka cluster.

---

# Summary

The `kafka-console-consumer.sh` utility provides a simple way to read messages directly from Kafka topics without writing application code. It supports replaying historical messages, displaying keys, partitions, offsets, timestamps, and joining Consumer Groups, making it an essential tool for testing, debugging, and learning Kafka. Mastering the console consumer greatly simplifies the development and troubleshooting of Kafka-based applications.

---

# Key Takeaways

- `kafka-console-consumer.sh` reads messages from Kafka topics.
- `--from-beginning` replays existing messages.
- Consumers can display keys, offsets, partitions, and timestamps.
- Specific partitions and offsets can be consumed.
- Consumer Groups allow offset tracking.
- The console consumer is ideal for development and debugging.
- It complements application-based consumers rather than replacing them.
- Understanding consumer CLI commands is essential for effective Kafka troubleshooting.