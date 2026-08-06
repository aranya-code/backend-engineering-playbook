# Apache Kafka Playbook

> A comprehensive, production-focused guide to Apache Kafka for Backend Engineers, Software Architects, and Distributed Systems Engineers.

---

# Overview

Apache Kafka has become one of the most important technologies in modern backend engineering. It powers real-time event streaming, asynchronous communication, distributed messaging, log aggregation, analytics pipelines, and event-driven microservices for some of the world's largest technology companies.

This playbook is designed to take you from **Kafka fundamentals to production-ready expertise** through structured documentation, architecture diagrams, practical examples, troubleshooting guides, interview preparation, and real-world best practices.

Unlike traditional notes that only explain concepts, this repository emphasizes **how Kafka works internally**, **how it is deployed in production**, **how it is monitored**, **how failures occur**, and **how experienced backend engineers design scalable Kafka-based systems**.

Whether you're learning Kafka for the first time, preparing for interviews, or building production-grade event-driven systems, this repository serves as a complete learning resource.

---

# Repository Structure

```text
Kafka/
│
├── README.md
│
├── 01- Concepts/
├── 02- Producers/
├── 03- Consumers/
├── 04- Topics/
├── 05- Docker/
├── 06- CLI/
├── 07- Architecture/
├── 08- Security/
├── 09- Production/
├── 10- Troubleshooting/
├── 11- Interview/
└── 12- Sample Files/
```

---

# Complete Navigation

## 01. Concepts

Learn the core building blocks of Kafka.

- [Introduction](./01-%20Concepts/01-%20Introduction.md)
- [Kafka Architecture](./01-%20Concepts/02-%20Kafka%20Architecture.md)
- [Topics](./01-%20Concepts/03-%20Topics.md)
- [Partitions](./01-%20Concepts/04-%20Partitions.md)
- [Offsets](./01-%20Concepts/05-%20Offsets.md)
- [Producers](./01-%20Concepts/06-%20Producers.md)
- [Consumers](./01-%20Concepts/07-%20Consumers.md)
- [Consumer Groups](./01-%20Concepts/08-%20Consumer%20Groups.md)
- [Message Keys](./01-%20Concepts/09-%20Message%20Keys.md)
- [Brokers](./01-%20Concepts/10-%20Brokers.md)
- [Leaders, Followers & ISR](./01-%20Concepts/11-%20Leaders,%20Followers%20&%20ISR.md)
- [Replication](./01-%20Concepts/12-%20Replication.md)
- [Delivery Guarantees](./01-%20Concepts/13-%20Delivery%20Guarantees.md)
- [Message Ordering](./01-%20Concepts/14-%20Message%20Ordering.md)
- [Log Segments](./01-%20Concepts/15-%20Log%20Segments.md)
- [Retention Policies](./01-%20Concepts/16-%20Retention%20Policies.md)
- [Log Compaction](./01-%20Concepts/17-%20Log%20Compaction.md)
- [ZooKeeper vs KRaft](./01-%20Concepts/18-%20ZooKeeper%20vs%20KRaft.md)

---

## 02. Producers

Master Kafka Producer internals and performance tuning.

- Producer Architecture
- Producer Workflow
- Message Serialization
- Partitioning Strategy
- Producer Acknowledgements
- Retries
- Producer Batching
- Compression
- Idempotent Producer
- Transactions
- Producer Configuration
- Performance Tuning
- Producer Metrics
- Error Handling

📂 [Open Producer Notes](./02-%20Producers/README.md)

---

## 03. Consumers

Understand Consumer internals and scalable consumption.

- Consumer Architecture
- Consumer Workflow
- Poll Loop
- Offset Management
- Auto Commit
- Manual Commit
- Consumer Rebalancing
- Partition Assignment
- Assign & Seek
- Consumer Groups in Depth
- Delivery Semantics
- Consumer Configuration
- Performance Tuning
- Consumer Metrics
- Error Handling

📂 [Open Consumer Notes](./03-%20Consumers/README.md)

---

## 04. Topics

Learn how to design scalable Kafka topics.

- Topic Design
- Naming Conventions
- Partition Strategy
- Retention Strategy
- Compacted Topics

📂 [Open Topic Notes](./04-%20Topics/README.md)

---

## 05. Docker

Run Kafka locally for development.

- Running Kafka with Docker
- Docker Compose
- Kafka UI
- Multi-Broker Cluster

📂 [Open Docker Guide](./05-%20Docker/README.md)

---

## 06. Kafka CLI

Master Kafka administration commands.

- Kafka CLI Overview
- Topic Commands
- Producer Commands
- Consumer Commands
- Consumer Group Commands
- Broker Commands
- Configuration Commands
- Useful Admin Commands

📂 [Open CLI Guide](./06-%20CLI/README.md)

---

## 07. Architecture

Understand Kafka's role in distributed systems.

- Producer to Consumer Flow
- Event Driven Architecture
- Publish–Subscribe Pattern
- Message Queue vs Kafka
- Kafka Internals

📂 [Open Architecture Guide](./07-%20Architecture/README.md)

---

## 08. Security

Secure production Kafka clusters.

- Kafka Security Overview
- SSL
- SASL
- ACLs
- Authentication
- Authorization

📂 [Open Security Guide](./08-%20Security/README.md)

---

## 09. Production

Deploy and operate Kafka in production.

- Production Checklist
- Topic Design Best Practices
- Partition Planning
- Monitoring Kafka
- Capacity Planning
- Backup & Recovery
- Upgrade Strategy

📂 [Open Production Guide](./09-%20Production/README.md)

---

## 10. Troubleshooting

Diagnose production failures.

- Broker Issues
- Consumer Lag
- Rebalancing Issues
- Offset Problems
- Producer Errors
- Serialization Errors
- Performance Problems
- Replication Problems

📂 [Open Troubleshooting Guide](./10-%20Troubleshooting/README.md)

---

## 11. Interview Preparation

Prepare for Backend, Staff, and Architect interviews.

- Kafka Fundamentals
- Producer Questions
- Consumer Questions
- Architecture Questions
- Scenario Based Questions
- System Design Questions

📂 [Open Interview Guide](./11-%20Interview/README.md)

---

## 12. Sample Files

Visual examples explaining Kafka internals.

- Producer Flow
- Consumer Flow
- Partition Example
- Consumer Group Example
- Replication Example
- Delivery Guarantee Example

📂 [Open Examples](./12-%20Sample%20Files/README.md)

---

# Recommended Learning Roadmap

```text
Kafka Fundamentals
        │
        ▼
Producers
        │
        ▼
Consumers
        │
        ▼
Topics
        │
        ▼
Docker Setup
        │
        ▼
Kafka CLI
        │
        ▼
Architecture
        │
        ▼
Security
        │
        ▼
Production
        │
        ▼
Troubleshooting
        │
        ▼
Examples
        │
        ▼
Interview Preparation
```

---

# Skills You'll Gain

By completing this playbook, you will be able to:

- Understand Kafka internals
- Design scalable event-driven systems
- Build reliable Producer and Consumer applications
- Configure partitions and replication correctly
- Deploy Kafka using Docker
- Administer Kafka using the CLI
- Secure Kafka clusters with SSL, SASL, and ACLs
- Monitor Kafka in production
- Troubleshoot common production failures
- Optimize Kafka performance
- Prepare for senior backend and system design interviews

---

# Intended Audience

This repository is ideal for:

- Backend Developers
- Python Developers
- Java Developers
- Go Developers
- Node.js Developers
- Platform Engineers
- DevOps Engineers
- Site Reliability Engineers
- Software Architects
- Distributed Systems Engineers
- Students preparing for backend interviews

---

# Prerequisites

Basic knowledge of the following is recommended:

- Programming fundamentals
- REST APIs
- Networking basics
- Linux commands
- Docker
- Basic distributed systems concepts

---

# Best Practices Followed

Throughout this playbook, you'll learn production-oriented practices such as:

- Designing scalable topics
- Choosing effective partition keys
- Monitoring Consumer Lag
- Using Replication Factor = 3
- Configuring `acks=all`
- Enabling idempotent producers
- Handling consumer failures safely
- Securing clusters using SSL/SASL
- Capacity planning
- Disaster recovery
- Performance tuning
- Operational troubleshooting

---

# Who This Repository Is For

If your goal is to:

- Learn Kafka from scratch
- Become interview-ready
- Build production-grade event-driven systems
- Understand distributed messaging
- Improve backend architecture skills
- Operate Kafka clusters confidently

then this repository provides a structured path from beginner concepts to advanced production engineering.

---

# Repository Highlights

- Structured learning path
- Production-focused documentation
- Practical architecture diagrams
- Real-world examples
- Docker setup guides
- CLI reference
- Security implementation
- Production deployment practices
- Troubleshooting playbooks
- Interview questions
- System Design discussions
- Backend engineering best practices

---

# Summary

Apache Kafka is much more than a messaging system—it's the backbone of many modern distributed applications. Mastering Kafka requires understanding not only how producers and consumers exchange messages, but also how partitions, replication, Consumer Groups, security, monitoring, and operational practices work together to deliver scalable and fault-tolerant systems.

This playbook provides a structured, end-to-end learning experience that progresses from foundational concepts to production operations, making it a valuable reference for developers, technical leads, and software architects working with event-driven architectures.