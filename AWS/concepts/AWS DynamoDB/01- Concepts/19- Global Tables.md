# 19 - Global Tables

## Overview

Modern applications often serve users from multiple geographic regions.

For example:

- Netflix serves viewers worldwide.
- Amazon processes orders globally.
- Spotify streams music across continents.
- Banking applications support customers in multiple countries.

If all requests are routed to a single DynamoDB table located in one AWS Region, users located far away experience higher network latency.

For example:

```text
User

Tokyo

↓

DynamoDB

Virginia (us-east-1)
```

Every request must travel thousands of miles.

This increases:

- Network latency
- Response time
- Dependency on a single region

To solve this problem, DynamoDB provides **Global Tables**.

A Global Table automatically replicates data across multiple AWS Regions, allowing users to read and write to the nearest regional copy while DynamoDB synchronizes changes behind the scenes.

---

# Why Global Tables Exist

Imagine an international e-commerce company.

Customers exist in:

```text
North America

Europe

Asia
```

Without Global Tables:

```text
All Requests

↓

us-east-1
```

European and Asian users experience unnecessary latency.

With Global Tables:

```text
US Users

↓

Virginia
```

```text
European Users

↓

Frankfurt
```

```text
Asian Users

↓

Tokyo
```

Each user communicates with the nearest DynamoDB replica.

---

# Global Table Architecture

Suppose we deploy a Global Table in three AWS Regions.

```text
             Global Table

      +------------------------+

      |   Logical Table        |

      +------------------------+

        /          |          \

       /           |           \

      ▼            ▼            ▼

us-east-1    eu-central-1   ap-northeast-1

Virginia      Frankfurt        Tokyo
```

Each region contains a fully functional DynamoDB table.

Applications can perform:

- Reads
- Writes
- Updates
- Deletes

against any regional replica.

---

# Multi-Active Architecture

Unlike traditional primary-secondary databases, every regional replica is writable.

```text
Virginia

↓

Write
```

```text
Frankfurt

↓

Write
```

```text
Tokyo

↓

Write
```

Every region accepts application traffic simultaneously.

This model is known as:

```text
Active-Active Replication
```

---

# How Replication Works

Suppose a user in Europe updates their profile.

```text
Application

↓

Frankfurt

↓

Update Item
```

DynamoDB automatically replicates the change.

```text
Frankfurt

↓

Virginia

↓

Tokyo
```

Replication occurs asynchronously.

Eventually, every region contains the same data.

---

# Replication Flow

```text
Write

↓

Regional Table

↓

Replication Engine

↓

Other Regions

↓

Data Synchronized
```

Developers do not write replication logic.

AWS manages replication automatically.

---

# Eventual Consistency

One important characteristic:

Replication is **eventually consistent**.

Suppose:

```text
Frankfurt

↓

Update Balance

↓

Immediately Read

Virginia
```

Virginia may temporarily return the older value until replication completes.

Eventually:

```text
All Regions

↓

Same Data
```

Applications should be designed with this behavior in mind.

---

# Conflict Resolution

Consider two users.

```text
User A

Virginia

↓

Update Name
```

At nearly the same time:

```text
User B

Tokyo

↓

Update Name
```

Both updates modify the same item.

Which value wins?

DynamoDB uses:

```text
Last Writer Wins
```

The update with the latest timestamp becomes the final version.

Applications requiring more sophisticated conflict resolution must implement it at the application layer.

---

# Example — Global Shopping Platform

Customer in Europe:

```text
Frankfurt

↓

Create Order
```

Customer in Japan:

```text
Tokyo

↓

Create Order
```

Customer in America:

```text
Virginia

↓

Create Order
```

Each request remains within its local region.

Replication keeps all regions synchronized.

---

# Example — Social Media

Users upload posts worldwide.

```text
London

↓

Write
```

```text
New York

↓

Write
```

```text
Singapore

↓

Write
```

Followers in every region eventually receive the same content.

---

# High Availability

Another major advantage is regional resilience.

Without Global Tables:

```text
Application

↓

Virginia

↓

Region Failure

↓

Application Offline
```

With Global Tables:

```text
Virginia

↓

Failure

↓

Route Traffic

↓

Frankfurt

↓

Application Continues
```

Because another replica already contains the data, failover is significantly simpler.

---

# Disaster Recovery

Global Tables improve disaster recovery.

```text
Region Failure

↓

Replica Already Exists

↓

Minimal Recovery Time
```

Compared to restoring backups, no manual data restoration is typically required.

However, Global Tables are **not a substitute for backups**, because accidental deletions or bad writes can also replicate to every region.

---

# Global Tables vs Read Replicas

Many SQL databases support read replicas.

Comparison:

| Feature | Read Replica | Global Table |
|----------|--------------|--------------|
| Read Operations | Replica | Every Region |
| Write Operations | Primary Only | Every Region |
| Multi-Region Writes | ❌ | ✅ |
| Automatic Replication | ✅ | ✅ |
| Active-Active | ❌ | ✅ |

Global Tables allow writes from every participating region.

---

# Global Tables vs Backup

These services solve different problems.

| Feature | Global Tables | Backup |
|----------|---------------|---------|
| Disaster Recovery | ✅ Regional Failure | ✅ Data Recovery |
| Accidental Delete Recovery | ❌ No | ✅ Yes |
| Replication | Automatic | No |
| Multi-Region Access | ✅ | ❌ |

Global Tables improve availability.

Backups protect against data loss.

Production systems commonly use both.

---

# Performance Benefits

Instead of:

```text
Tokyo

↓

Virginia

↓

80 ms
```

Users read from:

```text
Tokyo

↓

Tokyo Region

↓

5 ms
```

Latency improves significantly because requests remain geographically local.

---

# Cost Considerations

Global Tables increase infrastructure costs because:

- Data is stored in every participating region.
- Every write is replicated to all replicas.
- Cross-region replication generates additional charges.
- Each regional table incurs its own read/write/storage costs.

Architects should balance improved performance and availability against increased operational cost.

---

# Best Practices

- Deploy replicas close to users.
- Design applications for eventual consistency.
- Use Global Tables for worldwide applications.
- Continue using backups for disaster recovery.
- Monitor replication metrics and replication lag.
- Minimize conflicting writes across regions.

---

# Common Mistakes

## Assuming Strong Global Consistency

Replication is asynchronous.

Different regions may temporarily observe different values.

---

## Treating Global Tables as Backups

Mistaken updates and deletions replicate everywhere.

Global Tables do not protect against logical data corruption.

---

## Ignoring Conflict Resolution

Simultaneous updates to the same item may overwrite one another due to the "last writer wins" strategy.

Applications handling collaborative editing or financial records should design accordingly.

---

## Deploying Replicas Unnecessarily

If all users are located in one region, Global Tables add cost without providing meaningful benefits.

---

# Real-World Example

A multiplayer online game has players in:

- North America
- Europe
- Asia

Each player writes game progress to the nearest region.

```text
Player

↓

Nearest Region

↓

Local DynamoDB Table

↓

Automatic Replication

↓

Other Regions
```

Players experience low latency regardless of location while game state remains synchronized worldwide.

---

# Architecture Perspective

Typical global deployment:

```text
Users

        │

 ┌──────┼─────────┐

 ▼      ▼         ▼

US     Europe    Asia

 │        │        │

 ▼        ▼        ▼

DynamoDB  DynamoDB  DynamoDB

Virginia  Frankfurt Tokyo

      │      │      │

      └──────┼──────┘

             ▼

      Global Replication
```

Each regional application communicates with its local DynamoDB replica, reducing latency and eliminating a single regional bottleneck.

---

# Interview Notes

A common interview question is:

> **If Global Tables already replicate data across regions, why do we still need backups?**

Because replication copies **both good and bad changes**.

If an application accidentally deletes an item in one region, that deletion is replicated to every other region. Backups allow data to be restored after accidental deletions, corruption, or application bugs.

Another common interview question is:

> **How does DynamoDB resolve simultaneous writes to the same item in different regions?**

Global Tables use a **last writer wins** conflict resolution strategy based on timestamps. While simple and efficient, this may not be appropriate for every workload. Applications with complex merge requirements should implement custom conflict resolution logic.

---

# Key Takeaways

- Global Tables replicate DynamoDB tables across multiple AWS Regions.
- Every regional replica is fully writable, enabling active-active architectures.
- Replication is automatic and eventually consistent.
- Global Tables reduce latency by serving users from the nearest AWS Region.
- They improve regional resilience and disaster recovery but do not replace backups.
- Conflict resolution uses a **last writer wins** strategy.
- Global Tables are ideal for globally distributed applications requiring low latency and high availability.