# Kafka CLI Overview

## Overview

Apache Kafka provides a comprehensive set of Command Line Interface (CLI) tools for managing, monitoring, and troubleshooting Kafka clusters. These tools allow developers and administrators to create topics, produce messages, consume records, inspect consumer groups, manage broker configurations, and perform various administrative operations.

Although graphical tools such as Kafka UI simplify many tasks, the Kafka CLI remains the most powerful and widely used interface for automation, scripting, debugging, and production administration.

Every Kafka engineer should be comfortable using the Kafka CLI before working with higher-level libraries and frameworks.

---

# Why Learn the Kafka CLI?

The Kafka CLI allows you to:

- Create and delete topics
- Produce messages
- Consume messages
- Monitor Consumer Groups
- View broker metadata
- Inspect offsets
- Modify configurations
- Troubleshoot production issues

Many production incidents are investigated using CLI commands.

---

# Why CLI Still Matters

Graphical interfaces are useful for visualization, but they cannot replace the flexibility of command-line tools.

Example:

```text
Kafka UI

↓

Visual Inspection

--------------------

Kafka CLI

↓

Automation

↓

Debugging

↓

Administration

↓

Scripting
```

Most DevOps pipelines and automation scripts rely on CLI commands.

---

# Kafka CLI Architecture

```text
Terminal

↓

Kafka CLI

↓

Kafka Broker

↓

Kafka Cluster
```

The CLI communicates directly with Kafka brokers.

---

# Where CLI Tools Come From

Kafka CLI tools are included with every Kafka distribution.

Common installation methods:

- Apache Kafka
- Docker Container
- Confluent Platform
- Package Managers

When running Kafka in Docker, CLI tools are already available inside the Kafka container.

---

# Running CLI Commands

If Kafka is installed locally:

```bash
kafka-topics.sh --help
```

If Kafka runs inside Docker:

```bash
docker exec -it kafka bash
```

Then execute CLI commands from inside the container.

---

# CLI Tool Categories

Kafka provides several command-line utilities.

```text
Topic Management

↓

Producer

↓

Consumer

↓

Consumer Groups

↓

Broker Administration

↓

Configuration

↓

Metadata
```

Each tool focuses on a specific administrative task.

---

# Common Kafka CLI Tools

| Tool | Purpose |
|------|---------|
| `kafka-topics.sh` | Topic management |
| `kafka-console-producer.sh` | Produce messages |
| `kafka-console-consumer.sh` | Consume messages |
| `kafka-consumer-groups.sh` | Manage Consumer Groups |
| `kafka-configs.sh` | Configure Kafka resources |
| `kafka-broker-api-versions.sh` | Broker API information |
| `kafka-metadata-quorum.sh` | KRaft metadata management |
| `kafka-features.sh` | Feature management |

These are the tools most frequently used in development and production.

---

# Typical CLI Workflow

A common development workflow:

```text
Create Topic

↓

Produce Messages

↓

Consume Messages

↓

Check Consumer Group

↓

Inspect Topic
```

Almost every Kafka tutorial follows this sequence.

---

# Connecting to Kafka

Most CLI tools require a broker address.

Example:

```bash
--bootstrap-server localhost:9092
```

Or:

```bash
--bootstrap-server kafka:9092
```

inside Docker.

The bootstrap server is the initial contact point for the Kafka cluster.

---

# Getting Help

Every Kafka CLI tool supports help.

Example:

```bash
kafka-topics.sh --help
```

This displays:

- Available commands
- Parameters
- Examples
- Supported options

---

# Command Structure

Most Kafka commands follow a similar format.

```bash
command

↓

bootstrap-server

↓

operation

↓

options
```

Example:

```bash
kafka-topics.sh \
--bootstrap-server localhost:9092 \
--list
```

---

# Working Inside Docker

When Kafka runs in Docker:

```bash
docker exec -it kafka bash
```

Example workflow:

```text
Host Machine

↓

Docker Container

↓

Kafka CLI

↓

Kafka Broker
```

No additional Kafka installation is required.

---

# Typical Administration Tasks

Kafka CLI is commonly used for:

- Creating topics
- Listing topics
- Describing topics
- Producing records
- Consuming records
- Monitoring consumer lag
- Viewing offsets
- Updating configurations
- Troubleshooting clusters

---

# CLI vs Kafka UI

| Kafka CLI | Kafka UI |
|------------|----------|
| Command-line | Graphical Interface |
| Scriptable | Manual Operations |
| Automation Friendly | Beginner Friendly |
| Production Administration | Visual Monitoring |
| Complete Feature Set | Common Operations |

Both tools complement each other.

---

# Automation

CLI commands are easily integrated into scripts.

Example workflow:

```text
Shell Script

↓

Kafka CLI

↓

Kafka Cluster
```

This makes CLI tools ideal for:

- CI/CD pipelines
- Infrastructure automation
- Health checks
- Deployment scripts

---

# Common Output

Most commands display:

```text
Topic Name

Partitions

Replication Factor

Leader

ISR
```

Understanding this output is essential for Kafka administration.

---

# Security Considerations

Secure clusters require additional configuration.

Example:

```bash
--command-config client.properties
```

The configuration file may contain:

- SSL settings
- SASL credentials
- Authentication properties

Without proper credentials, CLI commands cannot connect.

---

# CLI Workflow Example

```text
Start Kafka

↓

Create Topic

↓

Verify Topic

↓

Produce Messages

↓

Consume Messages

↓

Monitor Consumer Group

↓

Delete Topic
```

This workflow covers the most common development tasks.

---

# Advantages

- Complete access to Kafka features.
- Ideal for scripting and automation.
- Fast and lightweight.
- Available on every Kafka installation.
- Essential for production troubleshooting.
- Works without a graphical interface.

---

# Limitations

- Requires familiarity with command syntax.
- Output may be difficult for beginners.
- Less convenient for visual inspection than Kafka UI.

---

# Best Practices

- Learn the most common CLI tools before using Kafka libraries.
- Always verify commands with `--help`.
- Use Docker containers for consistent CLI environments.
- Prefer `--bootstrap-server` over deprecated ZooKeeper options.
- Combine CLI with Kafka UI for efficient administration.
- Use scripts to automate repetitive operations.
- Keep CLI examples in version-controlled documentation.

---

# Common Mistakes

- Forgetting to specify the bootstrap server.
- Using deprecated ZooKeeper-based commands with modern Kafka versions.
- Running CLI commands against the wrong cluster.
- Assuming Docker containers use `localhost` for broker communication.
- Ignoring error messages and broker logs.
- Executing destructive commands without verification.

---

# Summary

The Kafka CLI is the primary administrative interface for interacting with Kafka clusters. It provides powerful tools for managing topics, producing and consuming messages, monitoring consumer groups, configuring brokers, and troubleshooting production environments. Although graphical interfaces simplify many common tasks, mastering the Kafka CLI is essential for automation, DevOps workflows, production support, and advanced Kafka administration.

---

# Key Takeaways

- Kafka CLI provides complete administrative access to Kafka clusters.
- CLI tools are available with every Kafka installation.
- Most commands require a bootstrap server connection.
- Kafka CLI supports automation, scripting, and production operations.
- Docker containers include Kafka CLI tools by default.
- Kafka CLI complements Kafka UI rather than replacing it.
- Learning the CLI is essential for effective Kafka development and administration.
- Most production troubleshooting begins with Kafka CLI commands.