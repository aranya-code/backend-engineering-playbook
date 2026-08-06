# Consumer Group Commands

## Overview

Consumer Groups are one of Kafka's most powerful features. They allow multiple consumers to work together to process messages in parallel while ensuring that each partition is consumed by only one consumer within the group.

Kafka provides the **`kafka-consumer-groups.sh`** command-line utility for inspecting and managing Consumer Groups. This tool is essential for monitoring consumer health, checking lag, resetting offsets, and troubleshooting production systems.

As a Kafka administrator or backend engineer, `kafka-consumer-groups.sh` is one of the most frequently used CLI utilities.

---

# kafka-consumer-groups.sh

The Consumer Group management utility is:

```bash
kafka-consumer-groups.sh
```

It allows administrators to:

- List Consumer Groups
- Describe Consumer Groups
- Monitor consumer lag
- View partition assignments
- Reset offsets
- Delete Consumer Groups (when applicable)

---

# Command Structure

Most commands follow this format:

```bash
kafka-consumer-groups.sh \
--bootstrap-server localhost:9092 \
<operation>
```

Example:

```bash
kafka-consumer-groups.sh \
--bootstrap-server localhost:9092 \
--list
```

---

# Listing Consumer Groups

Display all Consumer Groups.

```bash
kafka-consumer-groups.sh \
--bootstrap-server localhost:9092 \
--list
```

Example output:

```text
inventory-service

shipping-service

analytics-service
```

Useful for:

- Cluster inspection
- Debugging
- Administration

---

# Describing a Consumer Group

Display detailed information.

```bash
kafka-consumer-groups.sh \
--bootstrap-server localhost:9092 \
--describe \
--group inventory-service
```

Example:

```text
GROUP

inventory-service

TOPIC

orders

PARTITION

0

CURRENT-OFFSET

152

LOG-END-OFFSET

160

LAG

8
```

---

# Understanding the Output

| Column | Description |
|----------|-------------|
| GROUP | Consumer Group name |
| TOPIC | Kafka topic |
| PARTITION | Assigned partition |
| CURRENT-OFFSET | Last committed offset |
| LOG-END-OFFSET | Latest available offset |
| LAG | Messages remaining |
| CONSUMER-ID | Consumer instance |
| HOST | Consumer host |
| CLIENT-ID | Kafka client ID |

These values are essential for monitoring consumer performance.

---

# Consumer Lag

Lag represents the number of messages waiting to be processed.

Formula:

```text
Lag

=

Log End Offset

-

Current Offset
```

Example:

```text
Current Offset

150

Latest Offset

165

Lag

15
```

---

# Why Lag Matters

Small Lag:

```text
Consumer

↓

Keeping Up
```

Large Lag:

```text
Producer

↓

Consumer Falling Behind
```

High lag usually indicates:

- Slow consumers
- Heavy workload
- Consumer failures

---

# Viewing Active Consumers

Describe output also shows active consumers.

Example:

```text
Consumer ID

Host

Client ID
```

Useful for verifying:

- Consumer availability
- Group membership
- Partition ownership

---

# Viewing Partition Assignments

Example:

```text
Partition 0

↓

Consumer A

----------------

Partition 1

↓

Consumer B

----------------

Partition 2

↓

Consumer C
```

Helps verify load balancing.

---

# Viewing Empty Groups

Suppose all consumers stop.

```text
Consumer Group

↓

No Active Members
```

The group still exists if offsets have been committed.

---

# Resetting Offsets

Kafka allows offsets to be reset.

Example:

```bash
kafka-consumer-groups.sh \
--bootstrap-server localhost:9092 \
--group inventory-service \
--topic orders \
--reset-offsets \
--to-earliest \
--execute
```

The consumer will replay messages from the beginning.

---

# Preview Offset Reset

Before executing:

```bash
kafka-consumer-groups.sh \
--bootstrap-server localhost:9092 \
--group inventory-service \
--topic orders \
--reset-offsets \
--to-earliest
```

Without:

```text
--execute
```

Kafka displays the proposed changes without applying them.

This is a safer approach.

---

# Reset to Latest

Skip historical records.

```bash
kafka-consumer-groups.sh \
--bootstrap-server localhost:9092 \
--group inventory-service \
--reset-offsets \
--to-latest \
--execute
```

Consumer resumes from the latest offset.

---

# Reset to a Specific Offset

Replay from Offset 250.

```bash
kafka-consumer-groups.sh \
--bootstrap-server localhost:9092 \
--group inventory-service \
--topic orders \
--reset-offsets \
--to-offset 250 \
--execute
```

---

# Shift Offsets

Move offsets forward.

```bash
kafka-consumer-groups.sh \
--bootstrap-server localhost:9092 \
--group inventory-service \
--topic orders \
--reset-offsets \
--shift-by 100 \
--execute
```

Or backward:

```text
--shift-by -100
```

Useful during testing.

---

# Reset to a Date

Replay records after a timestamp.

```bash
kafka-consumer-groups.sh \
--bootstrap-server localhost:9092 \
--group inventory-service \
--reset-offsets \
--to-datetime 2026-08-01T00:00:00.000
```

Kafka locates the corresponding offsets.

---

# Consumer Group Workflow

```text
Consumer

↓

Commit Offset

↓

Kafka Stores Offset

↓

Consumer Restarts

↓

Continue From Last Offset
```

Consumer Groups provide reliable progress tracking.

---

# Running Inside Docker

Open the Kafka container.

```bash
docker exec -it kafka bash
```

Execute:

```bash
kafka-consumer-groups.sh \
--bootstrap-server localhost:9092 \
--list
```

---

# Typical Monitoring Workflow

```text
List Groups

↓

Describe Group

↓

Check Lag

↓

Investigate Slow Consumers

↓

Reset Offsets (If Needed)
```

This workflow is commonly used during production support.

---

# Common Errors

### Group Does Not Exist

```text
Consumer group does not exist.
```

Possible reasons:

- No committed offsets
- Incorrect group name

---

### No Active Members

Output:

```text
No Active Members
```

Consumers are offline.

---

### Offset Reset Failed

Common cause:

```text
Consumer Still Running
```

Stop all consumers before resetting offsets.

---

### Connection Refused

Verify:

- Kafka broker is running
- Bootstrap server is correct
- Network configuration is correct

---

# Frequently Used Commands

| Command | Purpose |
|----------|---------|
| `--list` | List Consumer Groups |
| `--describe` | View Consumer Group details |
| `--reset-offsets` | Reset offsets |
| `--to-earliest` | Replay from beginning |
| `--to-latest` | Skip historical data |
| `--to-offset` | Reset to a specific offset |
| `--shift-by` | Shift offsets |
| `--execute` | Apply changes |

---

# Advantages

- Monitor consumer health.
- Measure consumer lag.
- View partition assignments.
- Reset offsets safely.
- Debug Consumer Groups.
- Essential for production support.

---

# Limitations

- Offset resets require care.
- Some operations require consumers to be stopped.
- Administrative privileges may be required on secured clusters.

---

# Best Practices

- Monitor consumer lag regularly.
- Preview offset resets before executing them.
- Stop consumers before resetting offsets.
- Use Consumer Groups for scalable processing.
- Investigate increasing lag immediately.
- Automate lag monitoring in production.

---

# Common Mistakes

- Resetting offsets while consumers are running.
- Ignoring consumer lag.
- Using the wrong Consumer Group.
- Executing offset resets without previewing them.
- Confusing committed offsets with latest offsets.
- Forgetting that lag is calculated per partition.

---

# Summary

The `kafka-consumer-groups.sh` utility is the primary command-line tool for monitoring and managing Kafka Consumer Groups. It enables administrators to inspect consumer membership, monitor lag, view partition assignments, and safely reset offsets when necessary. Because Consumer Groups are fundamental to Kafka's scalability and reliability, mastering these commands is essential for development, troubleshooting, and production operations.

---

# Key Takeaways

- `kafka-consumer-groups.sh` manages and monitors Consumer Groups.
- Consumer lag is the difference between the latest offset and the committed offset.
- The `--describe` command provides detailed group information.
- Offset resets support replay, recovery, and testing scenarios.
- Always preview offset resets before executing them.
- Consumer Groups enable scalable, fault-tolerant message processing.
- Monitoring consumer lag is a critical production responsibility.
- Consumer Group commands are among the most frequently used Kafka administrative tools.