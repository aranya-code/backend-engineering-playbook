# 04 - Global Tables

## Overview

Amazon DynamoDB Global Tables provide a **fully managed, multi-region, active-active database** that automatically replicates data across multiple AWS Regions.

Unlike traditional disaster recovery solutions where one Region acts as the primary and another as a standby, Global Tables allow every Region to both read and write data simultaneously.

This enables applications to serve users from the nearest AWS Region while maintaining synchronized copies of data worldwide.

Global Tables are commonly used for:

- Global SaaS platforms
- Multi-region APIs
- Disaster recovery
- Low-latency applications
- International e-commerce
- Financial services
- Gaming platforms
- Global user management

---

# Why Global Tables Exist

Imagine a global e-commerce platform.

Customers are located in:

```text
USA

Europe

Asia

Australia
```

Without Global Tables:

```text
Users Worldwide

↓

US Region

↓

High Latency
```

Every request travels across continents.

With Global Tables:

```text
US Users

↓

US Region

──────────────

Europe Users

↓

Europe Region

──────────────

Asia Users

↓

Asia Region
```

Each Region serves nearby users while data remains synchronized.

---

# Internal Architecture

```text
              Global Tables

      ┌────────────┬────────────┐

      ▼            ▼            ▼

US-East-1     EU-West-1    AP-Southeast-1

      ▲            ▲            ▲

      └────────────┼────────────┘

       Automatic Multi-Region Replication
```

Every Region stores a complete copy of the table.

Each Region accepts:

- Reads
- Writes
- Updates
- Deletes

---

# Active-Active Architecture

Unlike primary-secondary databases:

Traditional architecture:

```text
Primary

↓

Replica

(Read Only)
```

Global Tables:

```text
US

⇄

Europe

⇄

Asia
```

Every Region is writable.

---

# Replication Workflow

Suppose a user updates a profile in Europe.

```text
Application

↓

EU-West-1

↓

Update Item

↓

Replication

↓

US-East-1

↓

AP-Southeast-1
```

Replication occurs automatically.

---

# Read Workflow

European customer:

```text
Client

↓

EU Region

↓

Read Local Copy
```

US customer:

```text
Client

↓

US Region

↓

Read Local Copy
```

No cross-region reads are required.

---

# Write Workflow

Asian customer:

```text
Client

↓

Asia Region

↓

Write Item

↓

Replicate Worldwide
```

Applications write only once.

AWS handles replication.

---

# Conflict Resolution

Suppose two users update the same item.

```text
US Region

↓

Update Balance

────────────

Europe Region

↓

Update Balance
```

Which version wins?

Global Tables use:

```text
Last Writer Wins
```

based on timestamps.

---

# Last Writer Wins Example

Timeline:

```text
10:00

US Update

────────────

10:01

Europe Update
```

Final value:

```text
Europe Update
```

Earlier writes are overwritten.

---

# Eventual Consistency

Replication is asynchronous.

Workflow:

```text
Write

↓

Local Region

↓

Replication

↓

Remote Regions
```

For a brief period:

```text
Region A

≠

Region B
```

Eventually:

```text
Region A

=

Region B
```

---

# Global Tables Architecture

```text
            Client

               │

      Route to Nearest Region

               │

       Local DynamoDB Table

               │

        Automatic Replication

               │

       Other AWS Regions
```

Applications remain unaware of replication.

---

# High Availability

Suppose an AWS Region fails.

Without Global Tables:

```text
US Region

↓

Failure

↓

Application Down
```

With Global Tables:

```text
US Failure

↓

Route Traffic

↓

Europe

↓

Continue Serving Users
```

Applications remain available.

---

# Disaster Recovery

Traditional recovery:

```text
Failure

↓

Restore Backup

↓

Hours
```

Global Tables:

```text
Failure

↓

Traffic Redirect

↓

Immediate Recovery
```

Minimal downtime.

---

# Regional Latency

Without Global Tables:

```text
Australia

↓

US

↓

250 ms
```

With Global Tables:

```text
Australia

↓

Sydney Region

↓

20 ms
```

Users experience significantly lower latency.

---

# Global Tables vs Read Replicas

| Feature | Read Replica | Global Tables |
|----------|--------------|---------------|
| Multi-Region Reads | ✅ | ✅ |
| Multi-Region Writes | ❌ | ✅ |
| Automatic Replication | Limited | ✅ |
| Active-Active | ❌ | ✅ |
| Disaster Recovery | Partial | Excellent |

---

# Global Tables vs Backup

| Feature | Backup | Global Tables |
|----------|---------|--------------|
| Disaster Recovery | Slow | Fast |
| Continuous Availability | ❌ | ✅ |
| Multi-Region | Manual | Automatic |
| Read Traffic | No | Yes |

Backups protect data.

Global Tables provide availability.

---

# Real-World Example — SaaS Platform

Users:

```text
USA

Europe

Asia
```

Each Region hosts:

```text
User Profiles

Subscriptions

Settings
```

All updates synchronize globally.

---

# Real-World Example — Banking

Customer updates contact information.

```text
Singapore

↓

Write

↓

Replicate

↓

London

↓

New York
```

Every branch sees the latest information.

---

# Real-World Example — Multiplayer Gaming

Player inventory:

```text
Japan

↓

Update

↓

Replicated

↓

US

↓

Europe
```

Players receive a consistent experience regardless of location.

---

# Real-World Example — Inventory Management

Warehouse:

```text
Germany

↓

Inventory Updated
```

Replicated instantly to:

```text
US

Canada

India
```

Global inventory remains synchronized.

---

# Performance Considerations

Global Tables improve:

- Regional latency
- Availability
- Disaster recovery

However:

- Replication introduces network traffic.
- Cross-region writes increase cost.
- Replication is asynchronous.
- Conflicting writes require resolution.

Applications should avoid frequent concurrent updates to the same item across Regions.

---

# Best Practices

- Deploy tables close to users.
- Design applications to tolerate eventual consistency.
- Minimize cross-region write conflicts.
- Use Route 53 or Global Accelerator for intelligent routing.
- Monitor replication latency.
- Test regional failover regularly.

---

# Common Mistakes

## Assuming Immediate Replication

Incorrect:

```text
Write

↓

Every Region Updated Instantly
```

Replication is asynchronous.

---

## Ignoring Conflict Resolution

Two Regions writing simultaneously may overwrite one another.

Applications should:

- Avoid concurrent updates.
- Use versioning where appropriate.
- Design idempotent operations.

---

## Using Global Tables for Single-Region Applications

If users are located in one Region:

```text
US Only
```

Global Tables add unnecessary complexity and cost.

---

## Forgetting Cost Implications

Replication increases:

- Write capacity usage
- Network traffic
- Storage

Plan capacity for every participating Region.

---

# Architecture Perspective

```text
                  Route 53

                      │

      ┌───────────────┼───────────────┐

      ▼               ▼               ▼

 US-East-1       EU-West-1     AP-Southeast-1

      │               │               │

      └───────────────┼───────────────┘

        Automatic Multi-Region Sync
```

Applications interact with the nearest Region while DynamoDB manages replication behind the scenes.

---

# Production Considerations

Global Tables are ideal for applications requiring:

- Global user access
- Low regional latency
- High availability
- Disaster recovery
- Multi-region write capability

Typical production workloads include:

- Global e-commerce
- Financial platforms
- Multiplayer gaming
- International SaaS products
- Healthcare systems
- Enterprise collaboration tools

Before adopting Global Tables, evaluate:

- Replication costs
- Write conflict frequency
- Consistency requirements
- Regulatory and data residency constraints

---

# Interview Notes

A common interview question is:

> **What are DynamoDB Global Tables?**

Global Tables are fully managed, active-active DynamoDB tables that automatically replicate data across multiple AWS Regions, enabling low-latency access and high availability.

Another common question is:

> **How do Global Tables resolve write conflicts?**

Global Tables use a **last writer wins** strategy based on timestamps. The most recent write overwrites previous conflicting updates.

Another common question is:

> **Are Global Tables strongly consistent across Regions?**

No. Replication between Regions is asynchronous, so Global Tables provide eventual consistency across Regions.

Another common question is:

> **When should you use Global Tables?**

Use them when applications require global availability, low-latency regional access, disaster recovery, and active-active multi-region deployments.

---

# Key Takeaways

- Global Tables provide fully managed, active-active replication across multiple AWS Regions.
- Every Region can independently process both reads and writes.
- Data is replicated asynchronously, providing eventual consistency across Regions.
- Write conflicts are resolved using a last writer wins strategy.
- Global Tables improve latency, availability, and disaster recovery for globally distributed applications.
- They are best suited for applications serving users across multiple geographic regions.
- Proper planning around write conflicts, replication costs, and consistency requirements is essential for production deployments.