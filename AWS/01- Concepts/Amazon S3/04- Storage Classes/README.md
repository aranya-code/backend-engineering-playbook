# Amazon S3 Storage Classes

The **Storage Classes** module explains how Amazon S3 optimizes storage costs while maintaining the durability, availability, and retrieval performance required by different workloads.

Not all data is accessed equally. Some objects are read frequently, while others may only be needed monthly, yearly, or never unless required for compliance. Amazon S3 provides multiple storage classes to match these varying access patterns, allowing organizations to significantly reduce storage costs without sacrificing data durability.

This module explores every Amazon S3 storage class, explains when each should be used, and demonstrates how Lifecycle Rules can automatically transition objects between storage classes based on age and access patterns.

---

## Module Information

| Property | Value |
|----------|-------|
| Module | 04 |
| Difficulty | 🟢 Beginner → 🟡 Intermediate |
| Estimated Reading Time | 75–90 minutes |
| Articles | 9 |
| Hands-on Labs | Covered later in Module 17 |
| Prerequisites | Modules 01–03 |

---

# 📚 Table of Contents

- Overview
- Learning Objectives
- Topics Covered
- File Navigation
- Learning Roadmap
- Storage Class Decision Flow
- Storage Class Comparison
- Best Practices
- Common Mistakes
- Related Modules
- Navigation

---

# Overview

Choosing the appropriate storage class is one of the most effective ways to optimize Amazon S3 costs.

Although every storage class provides **11 nines (99.999999999%) of durability**, they differ in:

- Availability
- Retrieval latency
- Retrieval cost
- Storage cost
- Minimum storage duration
- Availability Zone redundancy
- Intended workloads

Understanding these trade-offs allows engineers to build cost-effective architectures without compromising performance or reliability.

This module covers:

- Standard
- Intelligent-Tiering
- Standard-IA
- One Zone-IA
- Glacier Instant Retrieval
- Glacier Flexible Retrieval
- Glacier Deep Archive
- Storage Class selection strategies

---

# Learning Objectives

After completing this module, you will be able to:

- Explain every Amazon S3 Storage Class
- Compare storage costs and retrieval performance
- Select the correct storage class for different workloads
- Understand Intelligent-Tiering
- Design Lifecycle transitions
- Optimize long-term storage costs
- Apply production storage strategies

---

# Topics Covered

| # | Topic | Description |
|---|-------|-------------|
| 01 | [Overview](./01-%20Overview.md) | Introduction to Amazon S3 Storage Classes and pricing model |
| 02 | [Standard](./02-%20Standard.md) | Default storage class for frequently accessed data |
| 03 | [Intelligent-Tiering](./03-%20Intelligent-Tiering.md) | Automatic tier optimization based on access patterns |
| 04 | [Standard IA](./04-%20Standard%20IA.md) | Infrequently accessed data stored across multiple AZs |
| 05 | [One Zone IA](./05-%20One%20Zone%20IA.md) | Lower-cost storage in a single Availability Zone |
| 06 | [Glacier Instant Retrieval](./06-%20Glacier%20Instant%20Retrieval.md) | Archive storage with millisecond retrieval |
| 07 | [Glacier Flexible Retrieval](./07-%20Glacier%20Flexible%20Retrieval.md) | Low-cost archival with retrieval in minutes to hours |
| 08 | [Glacier Deep Archive](./08-%20Glacier%20Deep%20Archive.md) | Lowest-cost long-term archival storage |
| 09 | [Choosing the Right Storage Class](./09-%20Choosing%20the%20Right%20Storage%20Class.md) | Decision framework and production recommendations |

---

# File Navigation

```text
04- Storage Classes
│
├── 01- Overview.md
├── 02- Standard.md
├── 03- Intelligent-Tiering.md
├── 04- Standard IA.md
├── 05- One Zone IA.md
├── 06- Glacier Instant Retrieval.md
├── 07- Glacier Flexible Retrieval.md
├── 08- Glacier Deep Archive.md
├── 09- Choosing the Right Storage Class.md
│
└── README.md
```

---

# Learning Roadmap

```text
Storage Class Overview
          │
          ▼
Standard
          │
          ▼
Intelligent-Tiering
          │
          ▼
Standard IA
          │
          ▼
One Zone IA
          │
          ▼
Glacier Instant Retrieval
          │
          ▼
Glacier Flexible Retrieval
          │
          ▼
Glacier Deep Archive
          │
          ▼
Choosing the Right Storage Class
```

---

# Storage Class Decision Flow

```text
                    New Object
                         │
                         ▼
          Frequently Accessed?
                 │             │
               Yes             No
               │               │
               ▼               ▼
          Standard      Access Pattern Known?
                             │          │
                            No         Yes
                             │          │
                             ▼          ▼
                 Intelligent-Tiering   Infrequent Access?
                                         │          │
                                        Yes        Archive
                                         │          │
                                         ▼          ▼
                              Standard IA / One Zone IA
                                                   │
                                                   ▼
                                            Glacier Classes
```

---

# Storage Class Comparison

| Storage Class | Availability | Retrieval Time | Multi-AZ | Best For |
|---------------|:-----------:|:--------------:|:--------:|----------|
| Standard | 99.99% | Milliseconds | ✅ | Frequently accessed production workloads |
| Intelligent-Tiering | 99.9%+ | Milliseconds | ✅ | Unknown access patterns |
| Standard IA | 99.9% | Milliseconds | ✅ | Long-lived but infrequently accessed data |
| One Zone IA | 99.5% | Milliseconds | ❌ | Re-creatable data |
| Glacier Instant Retrieval | 99.9% | Milliseconds | ✅ | Archived data requiring instant access |
| Glacier Flexible Retrieval | 99.99% | Minutes–Hours | ✅ | Backups and archives |
| Glacier Deep Archive | 99.99% | Hours | ✅ | Compliance and long-term retention |

---

# Best Practices

- Start with **Standard** unless requirements indicate otherwise.
- Use **Intelligent-Tiering** for unpredictable access patterns.
- Transition objects automatically using Lifecycle Rules.
- Avoid Glacier storage for frequently accessed files.
- Consider minimum storage duration charges before transitioning objects.
- Review Storage Lens reports to identify optimization opportunities.
- Regularly evaluate storage costs using AWS Cost Explorer.

---

# Common Mistakes

- Selecting Glacier for frequently accessed data.
- Ignoring retrieval costs when estimating storage expenses.
- Using One Zone IA for business-critical data.
- Forgetting minimum storage duration charges.
- Moving objects manually instead of using Lifecycle Rules.
- Assuming cheaper storage classes provide lower durability.

---

# Related Modules

| Module | Purpose |
|----------|---------|
| [Object Management](../03-%20Object%20Management/README.md) | Learn how objects are stored before optimizing their storage class |
| [Versioning](../05-%20Versioning/README.md) | Understand how storage classes interact with object versions |
| [Lifecycle Management](../08-%20Lifecycle%20Management/README.md) | Automate transitions between storage classes |
| [Cost Optimization](../13-%20Cost%20Optimization/README.md) | Reduce Amazon S3 costs using storage class strategies |

---

# Navigation

| Previous | Current | Next |
|----------|---------|------|
| Object Management | Storage Classes | Versioning |

- ⬆️ **Previous Module:** [Object Management](../03-%20Object%20Management/README.md)
- 🏠 **Parent:** [Amazon S3](../README.md)
- ➡️ **Next Module:** [Versioning](../05-%20Versioning/README.md)

---
