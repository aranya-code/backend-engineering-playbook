# Amazon S3 Fundamentals

The **Fundamentals** module introduces the core concepts of **Amazon Simple Storage Service (Amazon S3)**. Before learning bucket management, security, versioning, lifecycle management, replication, and production architectures, it's essential to understand how Amazon S3 stores, organizes, and retrieves data.

This module explains the building blocks of Amazon S3, including **Object Storage**, **Buckets**, **Objects**, **Object Keys**, **Metadata**, **Global Architecture**, **Strong Consistency**, **Durability**, and the **AWS Shared Responsibility Model**.

Mastering these concepts provides the foundation for every other section of this handbook.

---

## Module Information

| Property | Value |
|----------|-------|
| Module | 01 |
| Difficulty | 🟢 Beginner |
| Estimated Reading Time | 60–90 minutes |
| Articles | 10 |
| Hands-on Labs | Covered later in Module 17 |
| Prerequisites | Basic AWS and Cloud Computing knowledge |

---

# 📚 Table of Contents

- Overview
- Learning Objectives
- Topics Covered
- File Navigation
- Learning Roadmap
- Architecture Overview
- Core Concepts
- Best Practices
- Common Mistakes
- Related Modules
- Navigation

---

# Overview

Amazon S3 is an **Object Storage Service**, not a traditional filesystem or block storage service.

Unlike traditional storage systems, Amazon S3 stores **Objects** inside **Buckets** and identifies them using **Object Keys**.

Understanding these concepts is essential before learning Versioning, Lifecycle Rules, Replication, Security, Encryption, and Production Architectures.

---

# Learning Objectives

After completing this module, you will be able to:

- Explain Object Storage
- Understand Bucket architecture
- Describe Objects and Object Keys
- Explain Metadata
- Understand Amazon S3 global architecture
- Explain Durability vs Availability
- Understand Strong Read-after-Write Consistency
- Explain the AWS Shared Responsibility Model

---

# Topics Covered

| # | Topic | Description |
|---|-------|-------------|
| 01 | [What is Amazon S3](./01-%20What%20is%20Amazon%20S3.md) | Introduction to Amazon S3 and Object Storage |
| 02 | [Object Storage](./02-%20Object%20Storage.md) | Understanding Object Storage architecture |
| 03 | [Buckets](./03-%20Buckets.md) | Bucket fundamentals, naming, and architecture |
| 04 | [Objects](./04-%20Objects.md) | Object components and storage model |
| 05 | [Object Keys](./05-%20Object%20Keys.md) | Naming conventions and prefixes |
| 06 | [Metadata](./06-%20Metadata.md) | System-defined and user-defined metadata |
| 07 | [Global Architecture](./07-%20Global%20Architecture.md) | Regional architecture and global namespace |
| 08 | [Durability vs Availability](./08-%20Durability%20vs%20Availability.md) | Understanding reliability metrics |
| 09 | [Strong Consistency](./09-%20Strong%20Consistency.md) | Read-after-write consistency model |
| 10 | [Shared Responsibility](./10-%20Shared%20Responsibility.md) | AWS vs Customer responsibilities |

---

# File Navigation

```text
01- Fundamentals
│
├── 01- What is Amazon S3.md
├── 02- Object Storage.md
├── 03- Buckets.md
├── 04- Objects.md
├── 05- Object Keys.md
├── 06- Metadata.md
├── 07- Global Architecture.md
├── 08- Durability vs Availability.md
├── 09- Strong Consistency.md
├── 10- Shared Responsibility.md
│
└── README.md
```

---

# Learning Roadmap

```text
What is Amazon S3
        │
        ▼
Object Storage
        │
        ▼
Buckets
        │
        ▼
Objects
        │
        ▼
Object Keys
        │
        ▼
Metadata
        │
        ▼
Global Architecture
        │
        ▼
Durability vs Availability
        │
        ▼
Strong Consistency
        │
        ▼
Shared Responsibility
```

---

# Architecture Overview

```text
                    Amazon S3

                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
    Bucket A                       Bucket B
        │                               │
   ┌────┼────┐                     ┌────┼────┐
   │    │    │                     │    │    │
   ▼    ▼    ▼                     ▼    ▼    ▼
Object Object Object          Object Object Object
```

Every object contains:

- Object Data
- Object Key
- Metadata
- Optional Version ID
- Object Tags
- Access Control Information

---

# Core Concepts

| Concept | Description |
|----------|-------------|
| Bucket | Logical container for storing objects |
| Object | Data stored inside a bucket |
| Object Key | Unique identifier of an object |
| Metadata | Information describing an object |
| Prefix | Logical grouping of object keys |
| Region | Physical AWS Region where the bucket resides |
| Version ID | Identifier assigned when Versioning is enabled |
| Consistency | Strong read-after-write consistency model |

---

# Best Practices

- Use globally unique bucket names.
- Design scalable object key naming conventions.
- Keep metadata lightweight and meaningful.
- Understand Region selection before creating buckets.
- Enable Versioning before production deployments.
- Use prefixes instead of deeply nested pseudo-folders.
- Follow the AWS Shared Responsibility Model.

---

# Common Mistakes

- Treating Amazon S3 like a traditional filesystem.
- Assuming folders physically exist.
- Confusing Metadata with Object Tags.
- Ignoring object key naming conventions.
- Choosing the wrong AWS Region.
- Misunderstanding Durability versus Availability.

---

# Related Modules

| Module | Purpose |
|----------|---------|
| [Bucket Management](../02-%20Bucket%20Management/README.md) | Configure buckets, ownership, policies, and CORS |
| [Object Management](../03-%20Object%20Management/README.md) | Upload, download, copy, delete, and manage objects |
| [Storage Classes](../04-%20Storage%20Classes/README.md) | Optimize storage cost and performance |

---

# Navigation

| Previous | Current | Next |
|----------|---------|------|
| Amazon S3 | Fundamentals | Bucket Management |

- ⬆️ **Parent:** [Amazon S3](../README.md)
- ➡️ **Next Module:** [Bucket Management](../02-%20Bucket%20Management/README.md)

---
