# Useful Admin Commands

## Overview

Beyond creating topics and producing or consuming messages, Kafka administrators frequently perform operational tasks such as checking broker health, verifying cluster metadata, monitoring consumer lag, inspecting configurations, and troubleshooting issues.

Kafka provides numerous command-line utilities for these day-to-day administrative tasks. While each utility has a specific purpose, experienced Kafka engineers often rely on a relatively small set of commands during development and production support.

This chapter collects the most useful Kafka administration commands into a single reference that can be used during everyday operations.

---

# Check Running Docker Containers

Verify that Kafka is running.

```bash
docker ps
```

Example:

```text
CONTAINER ID

NAME

STATUS

PORTS

kafka

Up
```

Always verify the broker is running before troubleshooting Kafka.

---

# View Kafka Logs

Display broker logs.

```bash
docker logs kafka
```

Follow logs continuously.

```bash
docker logs -f kafka
```

Useful for:

- Startup failures
- Connection issues
- Replication problems
- Configuration errors

---

# Enter Kafka Container

Access the Kafka container.

```bash
docker exec -it kafka bash
```

All Kafka CLI commands can now be executed inside the container.

---

# Verify Kafka Connectivity

Check supported API versions.

```bash
kafka-broker-api-versions.sh \
--bootstrap-server localhost:9092
```

If the command succeeds:

```text
Broker Reachable
```

If it fails:

```text
Connection Problem
```

---

# List All Topics

```bash
kafka-topics.sh \
--bootstrap-server localhost:9092 \
--list
```

Useful for confirming topic creation.

---

# Describe Every Topic

```bash
kafka-topics.sh \
--bootstrap-server localhost:9092 \
--describe
```

Displays:

- Partitions
- Leaders
- Replicas
- ISR

---

# Describe One Topic

```bash
kafka-topics.sh \
--bootstrap-server localhost:9092 \
--describe \
--topic orders
```

Useful when troubleshooting a specific topic.

---

# View Consumer Groups

```bash
kafka-consumer-groups.sh \
--bootstrap-server localhost:9092 \
--list
```

Example:

```text
inventory-service

shipping-service

analytics-service
```

---

# Check Consumer Lag

```bash
kafka-consumer-groups.sh \
--bootstrap-server localhost:9092 \
--describe \
--group inventory-service
```

Look for:

```text
LAG
```

Large lag indicates slow consumers.

---

# View Broker Configuration

```bash
kafka-configs.sh \
--bootstrap-server localhost:9092 \
--entity-type brokers \
--entity-name 1 \
--describe
```

Useful for verifying broker settings.

---

# View Topic Configuration

```bash
kafka-configs.sh \
--bootstrap-server localhost:9092 \
--entity-type topics \
--entity-name orders \
--describe
```

Displays:

- Retention
- Compression
- Cleanup Policy
- Message Size

---

# View Cluster ID

```bash
kafka-cluster.sh \
--bootstrap-server localhost:9092 \
cluster-id
```

Every Kafka cluster has a unique identifier.

---

# View Metadata Quorum (KRaft)

```bash
kafka-metadata-quorum.sh \
--bootstrap-server localhost:9092 \
describe --status
```

Useful for monitoring KRaft controller health.

---

# Produce Test Messages

```bash
kafka-console-producer.sh \
--bootstrap-server localhost:9092 \
--topic orders
```

Useful for:

- Testing producers
- Debugging consumers
- Verifying topics

---

# Consume Messages

```bash
kafka-console-consumer.sh \
--bootstrap-server localhost:9092 \
--topic orders \
--from-beginning
```

Useful for verifying producer output.

---

# Display Message Metadata

Show message keys.

```bash
--property print.key=true
```

Show offsets.

```bash
--property print.offset=true
```

Show partitions.

```bash
--property print.partition=true
```

Show timestamps.

```bash
--property print.timestamp=true
```

These options simplify debugging.

---

# Reset Consumer Offsets

Replay messages.

```bash
kafka-consumer-groups.sh \
--bootstrap-server localhost:9092 \
--group inventory-service \
--topic orders \
--reset-offsets \
--to-earliest \
--execute
```

Always preview offset resets before using `--execute`.

---

# Check Docker Resource Usage

```bash
docker stats
```

Displays:

- CPU
- Memory
- Network
- Disk I/O

Useful when running multiple Kafka containers.

---

# Inspect Docker Container

```bash
docker inspect kafka
```

Displays:

- Networks
- Environment Variables
- Volumes
- Port Mappings

---

# Stop Kafka

```bash
docker stop kafka
```

---

# Start Kafka

```bash
docker start kafka
```

---

# Restart Kafka

```bash
docker restart kafka
```

Useful after configuration changes.

---

# Docker Compose Commands

Start environment.

```bash
docker compose up -d
```

Stop environment.

```bash
docker compose down
```

Restart.

```bash
docker compose restart
```

View logs.

```bash
docker compose logs -f
```

---

# Frequently Used Kafka Commands

| Task | Command |
|------|---------|
| List Topics | `kafka-topics.sh --list` |
| Create Topic | `kafka-topics.sh --create` |
| Describe Topic | `kafka-topics.sh --describe` |
| Produce Messages | `kafka-console-producer.sh` |
| Consume Messages | `kafka-console-consumer.sh` |
| List Consumer Groups | `kafka-consumer-groups.sh --list` |
| Check Consumer Lag | `kafka-consumer-groups.sh --describe` |
| View Topic Configuration | `kafka-configs.sh --describe` |
| View Broker APIs | `kafka-broker-api-versions.sh` |
| View Cluster ID | `kafka-cluster.sh cluster-id` |

---

# Common Troubleshooting Workflow

```text
Application Error
        │
        ▼
Is Kafka Running?
        │
        ▼
Check Docker Logs
        │
        ▼
Check Topics
        │
        ▼
Check Consumer Groups
        │
        ▼
Check Consumer Lag
        │
        ▼
Inspect Broker Configuration
        │
        ▼
Verify Producer & Consumer
```

Following this sequence helps isolate most Kafka issues.

---

# Useful Docker Commands

| Command | Purpose |
|----------|---------|
| `docker ps` | Running containers |
| `docker logs kafka` | Broker logs |
| `docker exec -it kafka bash` | Enter container |
| `docker inspect kafka` | Container details |
| `docker stats` | Resource usage |
| `docker restart kafka` | Restart broker |

---

# Advantages

- Quick operational reference.
- Covers the most frequently used commands.
- Useful for production support.
- Simplifies troubleshooting.
- Reduces time spent searching documentation.

---

# Best Practices

- Verify broker availability before troubleshooting applications.
- Check broker logs whenever errors occur.
- Monitor consumer lag regularly.
- Use Docker Compose for local environments.
- Preview offset resets before executing them.
- Document commonly used commands for your team.
- Keep CLI commands aligned with your Kafka version.

---

# Common Mistakes

- Troubleshooting applications before verifying broker health.
- Ignoring broker logs.
- Forgetting the bootstrap server.
- Resetting offsets without understanding the consequences.
- Using outdated CLI syntax from older Kafka versions.
- Running administrative commands against the wrong cluster.

---

# Summary

Kafka administration relies heavily on a small set of CLI commands for monitoring, troubleshooting, and cluster management. By mastering commands for topics, producers, consumers, consumer groups, brokers, configurations, and Docker, administrators can quickly diagnose issues, verify cluster health, and maintain reliable Kafka deployments. Keeping these commands readily available significantly improves productivity during both development and production operations.

---

# Key Takeaways

- Kafka provides powerful CLI tools for day-to-day administration.
- Topic, producer, consumer, and Consumer Group commands are used most frequently.
- Docker commands are essential when Kafka runs in containers.
- Consumer lag is one of the most important operational metrics.
- Broker logs are invaluable during troubleshooting.
- Administrative commands should be part of every Kafka engineer's toolkit.
- Combining Kafka CLI with Docker commands provides complete visibility into local Kafka environments.
- Maintaining a quick-reference collection of commands speeds up debugging and production support.