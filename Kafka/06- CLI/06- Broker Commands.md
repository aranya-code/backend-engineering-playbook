# Broker Commands

## Overview

Kafka Brokers are the core servers of a Kafka cluster. They are responsible for storing topic partitions, serving producers and consumers, replicating data, electing partition leaders, and maintaining cluster metadata.

Although brokers are usually managed automatically, Kafka provides several CLI tools that allow administrators to inspect broker health, discover cluster metadata, verify API compatibility, and troubleshoot broker-related issues.

This chapter introduces the most useful broker-related CLI commands that every Kafka administrator should know.

---

# Broker Administration

Unlike topic or consumer commands, there is no single broker management utility.

Broker administration is performed using several CLI tools.

Common utilities include:

- kafka-broker-api-versions.sh
- kafka-metadata-quorum.sh
- kafka-cluster.sh
- kafka-configs.sh

Each provides different information about the cluster.

---

# Broker Architecture

```text
             Kafka Cluster

      ┌──────────┬──────────┬──────────┐
      ▼          ▼          ▼

 Broker 1    Broker 2    Broker 3

      │          │          │

      └──────────┼──────────┘

           Cluster Metadata
```

Every broker participates in the cluster.

---

# kafka-broker-api-versions.sh

This command displays the Kafka protocol versions supported by brokers.

Basic syntax:

```bash
kafka-broker-api-versions.sh \
--bootstrap-server localhost:9092
```

Example output:

```text
Broker 1

Produce API

Fetch API

Metadata API
```

Useful for:

- Version verification
- Client compatibility
- Upgrade planning

---

# Why API Versions Matter

Suppose:

```text
Client

Kafka 4.x

↓

Broker

Kafka 3.x
```

Some newer client features may not be supported.

Checking API versions helps identify compatibility issues.

---

# kafka-cluster.sh

Display cluster information.

Example:

```bash
kafka-cluster.sh \
--bootstrap-server localhost:9092 \
cluster-id
```

Example output:

```text
Cluster ID

qj8Fs8TgTqKjL2...
```

Every Kafka cluster has a unique Cluster ID.

---

# Listing Brokers

Cluster information may also include:

```text
Broker 1

Broker 2

Broker 3
```

Useful for confirming broker registration.

---

# kafka-metadata-quorum.sh

Modern Kafka (KRaft mode) stores metadata inside Kafka itself.

Display quorum status:

```bash
kafka-metadata-quorum.sh \
--bootstrap-server localhost:9092 \
describe --status
```

Example:

```text
Leader

Broker 1

Followers

Broker 2

Broker 3
```

Useful for monitoring KRaft clusters.

---

# Metadata Quorum

In KRaft mode:

```text
Controller

↓

Metadata Log

↓

Broker Synchronization
```

The quorum replaces ZooKeeper.

---

# Broker Configuration

Broker configuration can be inspected using:

```bash
kafka-configs.sh \
--bootstrap-server localhost:9092 \
--entity-type brokers \
--entity-name 1 \
--describe
```

Example output:

```text
Broker ID

1

Retention

Compression

Log Cleaner
```

---

# Dynamic Broker Configuration

Some broker properties can be updated without restarting Kafka.

Example:

```bash
kafka-configs.sh \
--bootstrap-server localhost:9092 \
--entity-type brokers \
--entity-name 1 \
--alter
```

The available properties depend on the Kafka version.

---

# Broker IDs

Every broker has a unique identifier.

Example:

```text
Broker

↓

ID = 1

ID = 2

ID = 3
```

Broker IDs are used for:

- Replication
- Leader Election
- Metadata
- Partition Assignment

---

# Viewing Broker Logs

When Kafka runs in Docker:

```bash
docker logs kafka
```

Follow logs:

```bash
docker logs -f kafka
```

Logs help diagnose:

- Startup failures
- Replication issues
- Configuration errors

---

# Viewing Running Containers

If Kafka runs in Docker:

```bash
docker ps
```

Example:

```text
kafka

Running

9092
```

Verify the broker is online before executing Kafka CLI commands.

---

# Broker Health Workflow

```text
Check Container

↓

Check Broker

↓

Check Metadata

↓

Check API Versions

↓

Inspect Logs
```

This is a common troubleshooting sequence.

---

# Broker Information

Broker metadata typically includes:

- Broker ID
- Host
- Port
- Rack (if configured)
- Leader Partitions
- Replica Partitions

This information helps verify cluster health.

---

# Running Inside Docker

Open the Kafka container.

```bash
docker exec -it kafka bash
```

Execute broker commands.

Example:

```bash
kafka-broker-api-versions.sh \
--bootstrap-server localhost:9092
```

---

# Broker Failure Example

Suppose:

```text
Broker 2

↓

Offline
```

Possible symptoms:

- Leader election
- Increased ISR changes
- Replica synchronization
- Client reconnections

Broker commands help identify these issues.

---

# Common Errors

### Broker Not Available

```text
Broker may not be available.
```

Possible causes:

- Broker stopped
- Wrong hostname
- Firewall
- Port mismatch

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

### Unknown Cluster

Possible causes:

- Wrong bootstrap server
- Incorrect listener configuration
- Cluster unavailable

---

# Frequently Used Broker Commands

| Command | Purpose |
|----------|---------|
| `kafka-broker-api-versions.sh` | Show supported API versions |
| `kafka-cluster.sh cluster-id` | Display Cluster ID |
| `kafka-metadata-quorum.sh describe --status` | View KRaft metadata quorum |
| `kafka-configs.sh --entity-type brokers` | Display broker configuration |
| `docker logs kafka` | View broker logs |
| `docker ps` | Verify broker container |

---

# Advantages

- Inspect broker health.
- Verify cluster metadata.
- Check protocol compatibility.
- Troubleshoot startup issues.
- View broker configuration.
- Essential during upgrades.

---

# Limitations

- Some commands require administrative privileges.
- Available commands vary by Kafka version.
- Older ZooKeeper-based clusters support different utilities.

---

# Best Practices

- Verify broker status before troubleshooting applications.
- Monitor broker logs regularly.
- Check API versions before upgrades.
- Use KRaft metadata commands for modern Kafka deployments.
- Keep broker configurations documented.
- Use Docker logs during local development.

---

# Common Mistakes

- Connecting to the wrong bootstrap server.
- Ignoring broker logs.
- Assuming every broker supports the same API version.
- Forgetting that KRaft replaces ZooKeeper in modern Kafka.
- Editing broker configurations without understanding their impact.
- Troubleshooting producers before verifying broker health.

---

# Summary

Broker commands provide administrators with the tools needed to inspect Kafka clusters, verify broker health, view metadata, check protocol compatibility, and troubleshoot infrastructure issues. While most day-to-day development focuses on topics and consumers, understanding broker administration is essential for maintaining reliable Kafka deployments and supporting production systems.

---

# Key Takeaways

- Broker commands help inspect and troubleshoot Kafka infrastructure.
- `kafka-broker-api-versions.sh` displays supported protocol versions.
- `kafka-cluster.sh` provides cluster-level information.
- `kafka-metadata-quorum.sh` is used to inspect KRaft metadata.
- `kafka-configs.sh` manages broker configurations.
- Broker logs are one of the most valuable troubleshooting resources.
- Verify broker health before investigating application-level issues.
- Modern Kafka clusters rely on KRaft rather than ZooKeeper for metadata management.