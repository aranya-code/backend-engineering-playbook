# Topic Commands

## Overview

Topics are the fundamental building blocks of Apache Kafka. Every message produced to Kafka is written to a topic, and every consumer reads messages from one or more topics.

The Kafka CLI provides a dedicated utility called **`kafka-topics.sh`** for managing topics. Using this tool, administrators can:

- Create topics
- List topics
- Describe topics
- Delete topics
- Increase partitions
- Modify configurations

Understanding these commands is essential for Kafka administration and everyday development.

---

# kafka-topics.sh

The primary topic management utility is:

```bash
kafka-topics.sh
```

Most commands require:

```bash
--bootstrap-server
```

Example:

```bash
kafka-topics.sh --bootstrap-server localhost:9092
```

---

# Command Structure

Most topic commands follow this pattern:

```bash
kafka-topics.sh \
--bootstrap-server localhost:9092 \
<operation> \
<options>
```

Example:

```bash
kafka-topics.sh \
--bootstrap-server localhost:9092 \
--list
```

---

# Listing Topics

Display every topic in the cluster.

```bash
kafka-topics.sh \
--bootstrap-server localhost:9092 \
--list
```

Example output:

```text
orders

payments

inventory

customers
```

Useful for:

- Verifying topic creation
- Cluster inspection
- Troubleshooting

---

# Creating a Topic

Create a topic with three partitions.

```bash
kafka-topics.sh \
--bootstrap-server localhost:9092 \
--create \
--topic orders \
--partitions 3 \
--replication-factor 1
```

Example output:

```text
Created topic orders.
```

---

# Understanding Create Parameters

| Parameter | Description |
|-----------|-------------|
| `--topic` | Topic name |
| `--partitions` | Number of partitions |
| `--replication-factor` | Number of replicas |

---

# Example Architecture

```text
orders

↓

3 Partitions

↓

Replication Factor = 1
```

Result:

```text
P0

P1

P2
```

---

# Creating Multiple Topics

Create another topic.

```bash
kafka-topics.sh \
--bootstrap-server localhost:9092 \
--create \
--topic payments \
--partitions 6 \
--replication-factor 1
```

Repeat as needed for additional topics.

---

# Describing a Topic

Display metadata about a topic.

```bash
kafka-topics.sh \
--bootstrap-server localhost:9092 \
--describe \
--topic orders
```

Example:

```text
Topic: orders

PartitionCount: 3

ReplicationFactor: 1
```

The output also includes:

- Leaders
- Replicas
- ISR
- Partition IDs

---

# Sample Describe Output

```text
Topic: orders

Partition: 0

Leader: 1

Replicas: 1

ISR: 1
```

This information is useful for debugging cluster health.

---

# Describing All Topics

```bash
kafka-topics.sh \
--bootstrap-server localhost:9092 \
--describe
```

Kafka displays metadata for every topic.

Useful for:

- Cluster audits
- Capacity planning
- Troubleshooting

---

# Checking if a Topic Exists

List topics and search.

Linux/macOS:

```bash
kafka-topics.sh \
--bootstrap-server localhost:9092 \
--list | grep orders
```

Windows PowerShell:

```powershell
kafka-topics.sh --bootstrap-server localhost:9092 --list | Select-String orders
```

---

# Increasing Partitions

Kafka allows partition counts to increase.

```bash
kafka-topics.sh \
--bootstrap-server localhost:9092 \
--alter \
--topic orders \
--partitions 6
```

Before:

```text
P0

P1

P2
```

After:

```text
P0

P1

P2

P3

P4

P5
```

---

# Important Note About Partitions

Increasing partitions:

✅ Supported

Reducing partitions:

❌ Not Supported

Kafka cannot safely decrease partition counts because doing so could result in data loss and ordering issues.

---

# Deleting a Topic

Delete a topic.

```bash
kafka-topics.sh \
--bootstrap-server localhost:9092 \
--delete \
--topic orders
```

Example:

```text
Topic orders marked for deletion.
```

Depending on broker configuration, deletion may take some time.

---

# Listing Internal Topics

Internal topics begin with:

```text
__
```

Example:

```text
__consumer_offsets
```

Display them:

```bash
kafka-topics.sh \
--bootstrap-server localhost:9092 \
--list \
--exclude-internal
```

To include internal topics:

```bash
kafka-topics.sh \
--bootstrap-server localhost:9092 \
--list
```

---

# Topic Configuration

Describe topic configuration.

```bash
kafka-configs.sh \
--bootstrap-server localhost:9092 \
--entity-type topics \
--entity-name orders \
--describe
```

Configuration management is covered later in this section.

---

# Topic Lifecycle

```text
Create Topic

↓

Produce Messages

↓

Consume Messages

↓

Monitor

↓

Delete Topic
```

Every Kafka topic follows this lifecycle.

---

# Running Inside Docker

Enter the Kafka container.

```bash
docker exec -it kafka bash
```

Execute topic commands.

```bash
kafka-topics.sh \
--bootstrap-server localhost:9092 \
--list
```

No Kafka installation is required on the host machine.

---

# Typical Development Workflow

```text
Create Topic

↓

List Topics

↓

Describe Topic

↓

Produce Messages

↓

Consume Messages

↓

Delete Topic
```

These are the commands developers use most frequently.

---

# Common Errors

### Topic Already Exists

```text
TopicExistsException
```

Solution:

Use another topic name or verify existing topics.

---

### Unknown Topic

```text
UnknownTopicOrPartitionException
```

Solution:

Create the topic or verify the topic name.

---

### Connection Error

```text
Connection refused
```

Verify:

- Kafka is running
- Bootstrap server is correct
- Port mapping is correct

---

### Replication Factor Too Large

Example:

```text
Replication Factor: 3

Available Brokers: 1
```

Kafka cannot create the topic.

Replication factor cannot exceed the number of brokers.

---

# Useful Topic Commands

| Command | Purpose |
|----------|---------|
| `--list` | List topics |
| `--create` | Create topic |
| `--describe` | Show topic details |
| `--delete` | Delete topic |
| `--alter` | Modify partitions |
| `--help` | Display help |

---

# Best Practices

- Use meaningful topic names.
- Plan partition counts before production.
- Verify topic configuration after creation.
- Avoid unnecessary topic deletion.
- Use explicit replication factors.
- Monitor partition distribution.
- Prefer topic-specific configurations over broker defaults.

---

# Common Mistakes

- Creating topics with too few partitions.
- Setting replication factors higher than available brokers.
- Assuming partitions can be reduced later.
- Deleting production topics accidentally.
- Ignoring describe output.
- Creating generic topic names like `data` or `events`.

---

# Summary

The `kafka-topics.sh` utility is the primary command-line tool for managing Kafka topics. It enables developers and administrators to create, inspect, modify, and delete topics while providing detailed metadata about partitions, leaders, replicas, and configurations. Mastering these commands is essential for Kafka administration, application development, and production troubleshooting.

---

# Key Takeaways

- `kafka-topics.sh` manages Kafka topics from the command line.
- The `--bootstrap-server` option connects the CLI to the Kafka cluster.
- Topics can be created, listed, described, altered, and deleted.
- Partition counts can be increased but not decreased.
- The replication factor cannot exceed the number of brokers.
- Topic metadata includes partitions, leaders, replicas, and ISR.
- Topic commands are among the most frequently used Kafka administrative operations.
- Understanding topic management is fundamental to working effectively with Kafka.