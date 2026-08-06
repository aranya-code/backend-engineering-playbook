# Kafka CLI

Apache Kafka provides a comprehensive Command Line Interface (CLI) for managing, monitoring, and troubleshooting Kafka clusters. While graphical tools such as Kafka UI simplify visualization, the Kafka CLI remains the most powerful interface for administration, automation, scripting, and production support.

From creating topics and producing messages to monitoring consumer lag and inspecting broker configurations, Kafka CLI tools are used extensively by backend developers, DevOps engineers, and platform administrators.

This section covers the most commonly used Kafka CLI utilities and demonstrates how to perform everyday administrative tasks using practical command-line examples.

---

# Folder Structure

```text
06-CLI/
│
├── 01- Kafka CLI Overview.md
├── 02- Topic Commands.md
├── 03- Producer Commands.md
├── 04- Consumer Commands.md
├── 05- Consumer Group Commands.md
├── 06- Broker Commands.md
├── 07- Configuration Commands.md
├── 08- Useful Admin Commands.md
└── README.md
```

---

# Navigation

## Getting Started

- [01- Kafka CLI Overview](./01-%20Kafka%20CLI%20Overview.md)

---

## Topic Management

- [02- Topic Commands](./02-%20Topic%20Commands.md)

---

## Message Production & Consumption

- [03- Producer Commands](./03-%20Producer%20Commands.md)
- [04- Consumer Commands](./04-%20Consumer%20Commands.md)

---

## Consumer Administration

- [05- Consumer Group Commands](./05-%20Consumer%20Group%20Commands.md)

---

## Broker & Configuration Management

- [06- Broker Commands](./06-%20Broker%20Commands.md)
- [07- Configuration Commands](./07-%20Configuration%20Commands.md)

---

## Administration Reference

- [08- Useful Admin Commands](./08-%20Useful%20Admin%20Commands.md)

---

# Learning Path

Study the chapters in the following order:

```text
Kafka CLI Overview
        │
        ▼
Topic Commands
        │
        ▼
Producer Commands
        │
        ▼
Consumer Commands
        │
        ▼
Consumer Group Commands
        │
        ▼
Broker Commands
        │
        ▼
Configuration Commands
        │
        ▼
Useful Admin Commands
```

This progression starts with the fundamentals and gradually moves toward advanced administration and troubleshooting.

---

# Topics Covered

This section explains:

- Kafka CLI fundamentals
- Topic management
- Producer commands
- Consumer commands
- Consumer Group administration
- Broker inspection
- Configuration management
- Cluster metadata
- Offset management
- Consumer lag monitoring
- Docker-based Kafka administration
- Production troubleshooting commands

---

# Prerequisites

Before studying this section, you should understand:

- Kafka Architecture
- Topics
- Partitions
- Producers
- Consumers
- Consumer Groups
- Basic Docker commands
- Terminal and command-line usage

---

# Skills You'll Gain

After completing this section, you will be able to:

- Navigate Kafka using the command line.
- Create, inspect, modify, and delete Kafka topics.
- Produce and consume messages directly from the terminal.
- Monitor Consumer Groups and consumer lag.
- Inspect broker metadata and cluster information.
- View and modify Kafka configurations.
- Debug Kafka applications using CLI tools.
- Perform routine Kafka administrative tasks.
- Troubleshoot common Kafka issues in development and production.
- Automate Kafka operations using shell scripts.

---

# Real-World Applications

The commands covered in this section are widely used in:

- Backend Development
- Microservices
- Event-Driven Systems
- DevOps Automation
- CI/CD Pipelines
- Platform Engineering
- Production Support
- Site Reliability Engineering (SRE)
- Distributed System Operations
- Cloud Infrastructure Management

---

# Best Practices

- Learn the CLI before relying on graphical tools.
- Always specify the correct `--bootstrap-server`.
- Use explicit Kafka versions to avoid command differences.
- Verify topics and Consumer Groups before making changes.
- Preview offset resets before executing them.
- Check broker logs during troubleshooting.
- Monitor consumer lag regularly.
- Use Docker containers for consistent local environments.
- Keep frequently used commands documented.
- Automate repetitive administrative tasks with scripts.

---

# Common Mistakes

- Forgetting the `--bootstrap-server` parameter.
- Running commands against the wrong Kafka cluster.
- Resetting consumer offsets without understanding the impact.
- Ignoring consumer lag during troubleshooting.
- Assuming Kafka UI replaces CLI tools.
- Using deprecated ZooKeeper-based commands with modern Kafka versions.
- Modifying configurations without verifying the results.
- Ignoring broker logs when investigating failures.

---

# Summary

The Kafka CLI is the primary interface for administering Kafka clusters and is an essential skill for every backend engineer, DevOps engineer, and platform administrator. It provides powerful tools for managing topics, producers, consumers, Consumer Groups, brokers, and configurations while supporting automation, monitoring, and troubleshooting. Mastering these command-line utilities enables efficient cluster management and forms the foundation for production-ready Kafka operations.