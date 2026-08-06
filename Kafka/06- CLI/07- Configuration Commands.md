# Configuration Commands

## Overview

Apache Kafka is highly configurable. Almost every aspect of Kafka—topics, brokers, producers, consumers, quotas, and security—can be customized through configuration properties.

While many configurations are defined in configuration files before starting Kafka, some settings can be viewed and modified dynamically using Kafka CLI commands.

The primary utility used for managing Kafka configurations is **`kafka-configs.sh`**.

This chapter explains how to inspect, modify, and manage Kafka configurations using the command line.

---

# kafka-configs.sh

The configuration management utility is:

```bash
kafka-configs.sh
```

It is used to:

- View configurations
- Add configurations
- Update configurations
- Remove configurations

for various Kafka entities.

---

# Supported Entities

Kafka configurations can be applied to different entities.

Common entities include:

- Topics
- Brokers
- Users
- Clients
- IP Addresses

Each entity type has its own configurable properties.

---

# Command Structure

Most configuration commands follow this format.

```bash
kafka-configs.sh \
--bootstrap-server localhost:9092 \
--entity-type <entity> \
--entity-name <name> \
<operation>
```

Example:

```bash
kafka-configs.sh \
--bootstrap-server localhost:9092 \
--entity-type topics \
--entity-name orders \
--describe
```

---

# Viewing Topic Configuration

Display the current configuration of a topic.

```bash
kafka-configs.sh \
--bootstrap-server localhost:9092 \
--entity-type topics \
--entity-name orders \
--describe
```

Example output:

```text
cleanup.policy=delete

retention.ms=604800000

compression.type=producer
```

---

# Viewing Broker Configuration

Display broker-specific configuration.

```bash
kafka-configs.sh \
--bootstrap-server localhost:9092 \
--entity-type brokers \
--entity-name 1 \
--describe
```

Example:

```text
Broker ID

1

log.retention.hours

168
```

---

# Viewing User Configuration

Kafka supports user-level configuration.

```bash
kafka-configs.sh \
--bootstrap-server localhost:9092 \
--entity-type users \
--entity-name alice \
--describe
```

Useful in secured Kafka clusters.

---

# Altering Topic Configuration

Change topic retention.

```bash
kafka-configs.sh \
--bootstrap-server localhost:9092 \
--entity-type topics \
--entity-name orders \
--alter \
--add-config retention.ms=259200000
```

Example:

```text
Retention

3 Days
```

---

# Adding Multiple Configurations

Multiple settings can be updated simultaneously.

```bash
kafka-configs.sh \
--bootstrap-server localhost:9092 \
--entity-type topics \
--entity-name orders \
--alter \
--add-config retention.ms=259200000,compression.type=gzip
```

Kafka updates both properties.

---

# Removing Configuration

Delete an override.

```bash
kafka-configs.sh \
--bootstrap-server localhost:9092 \
--entity-type topics \
--entity-name orders \
--alter \
--delete-config retention.ms
```

The topic returns to the broker default for that property.

---

# Topic Configuration Workflow

```text
Topic

↓

Current Configuration

↓

Modify

↓

Kafka Applies

↓

Verify
```

Always verify configuration after modification.

---

# Common Topic Configurations

| Configuration | Purpose |
|--------------|---------|
| `retention.ms` | Message retention period |
| `retention.bytes` | Maximum log size |
| `cleanup.policy` | Delete or compact |
| `compression.type` | Compression algorithm |
| `max.message.bytes` | Maximum message size |
| `min.insync.replicas` | Minimum ISR for acknowledgements |

These are among the most frequently modified topic settings.

---

# Broker Configuration Workflow

```text
Broker

↓

Configuration

↓

Dynamic Update

↓

Cluster
```

Some broker settings require a restart.

Others are updated dynamically.

---

# Dynamic vs Static Configuration

Dynamic:

```text
Update

↓

Applied Immediately
```

Static:

```text
Update

↓

Broker Restart Required
```

Always check the Kafka documentation for the specific property.

---

# Configuration Hierarchy

Kafka applies configuration in the following order.

```text
Broker Default

↓

Topic Override

↓

Effective Configuration
```

Topic-level settings take precedence over broker defaults.

---

# Viewing Effective Configuration

Suppose:

Broker:

```text
Retention

7 Days
```

Topic:

```text
Retention

30 Days
```

Effective value:

```text
30 Days
```

The topic-specific configuration overrides the broker setting.

---

# Configuration Example

Suppose:

```text
Orders Topic
```

Current configuration:

```text
Retention

7 Days
```

Command:

```bash
--add-config retention.ms=2592000000
```

Result:

```text
Retention

30 Days
```

---

# Running Inside Docker

Open the Kafka container.

```bash
docker exec -it kafka bash
```

Run configuration commands.

```bash
kafka-configs.sh \
--bootstrap-server localhost:9092 \
--entity-type topics \
--entity-name orders \
--describe
```

---

# Viewing All Topic Overrides

Display customized topic configurations.

```bash
kafka-configs.sh \
--bootstrap-server localhost:9092 \
--entity-type topics \
--describe
```

Useful for auditing cluster configuration.

---

# Common Errors

### Unknown Topic

```text
UnknownTopicOrPartitionException
```

Verify the topic exists.

---

### Invalid Configuration

```text
InvalidConfigurationException
```

Possible causes:

- Typographical error
- Unsupported property
- Invalid value

---

### Authorization Failed

```text
AuthorizationException
```

The current user lacks permission to modify configuration.

---

### Broker Unavailable

```text
Connection refused
```

Verify:

- Broker is running
- Bootstrap server is correct
- Docker networking is correct

---

# Frequently Used Commands

| Command | Purpose |
|----------|---------|
| `--describe` | View configuration |
| `--alter` | Modify configuration |
| `--add-config` | Add configuration |
| `--delete-config` | Remove configuration |
| `--entity-type topics` | Configure topics |
| `--entity-type brokers` | Configure brokers |

---

# Advantages

- Dynamic configuration management.
- No need to edit server files for many settings.
- Supports multiple Kafka entities.
- Simplifies administration.
- Useful for auditing.
- Essential for production operations.

---

# Limitations

- Some settings require broker restarts.
- Administrative privileges may be required.
- Invalid configuration changes can affect cluster performance.

---

# Best Practices

- Prefer topic-level overrides instead of changing broker defaults unnecessarily.
- Verify configuration after every change.
- Test configuration changes in development before production.
- Document every configuration override.
- Keep retention and cleanup policies aligned with business requirements.
- Review Kafka documentation before changing advanced settings.

---

# Common Mistakes

- Changing broker defaults instead of topic-specific settings.
- Forgetting to verify changes.
- Using unsupported configuration properties.
- Applying production changes without testing.
- Ignoring authorization requirements.
- Modifying critical settings during peak traffic.

---

# Summary

The `kafka-configs.sh` utility is Kafka's primary tool for viewing and managing configuration settings. It enables administrators to inspect and modify topic, broker, user, and client configurations without manually editing server configuration files. By understanding configuration hierarchy, dynamic updates, and common configuration properties, engineers can effectively manage Kafka clusters while minimizing operational risk.

---

# Key Takeaways

- `kafka-configs.sh` manages Kafka configuration settings.
- Configurations can be applied to topics, brokers, users, and clients.
- Topic-level configurations override broker defaults.
- Many configuration changes can be applied dynamically.
- Always verify configuration changes after applying them.
- Common settings include retention, cleanup policy, compression, and message size.
- Configuration management is a core Kafka administration skill.
- Test configuration changes before applying them to production.