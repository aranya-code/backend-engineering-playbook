# 06 - Streams, TTL & Advanced Features

## Overview

Amazon DynamoDB offers several advanced capabilities beyond simple key-value storage. Features such as DynamoDB Streams, Time To Live (TTL), Point-in-Time Recovery (PITR), Backups, Global Tables, and PartiQL enable developers to build event-driven, highly available, and production-ready applications.

Senior interviewers often ask these questions because they reveal whether a candidate understands how DynamoDB integrates into larger distributed systems rather than just functioning as a database.

---

# Learning Objectives

After completing this chapter, you'll be able to answer interview questions about:

- DynamoDB Streams
- Stream Views
- AWS Lambda integration
- Time To Live (TTL)
- Point-in-Time Recovery (PITR)
- On-Demand Backup
- Global Tables
- PartiQL
- Production event-driven architectures

---

# Question 1

## What are DynamoDB Streams?

### Expected Answer

DynamoDB Streams capture changes made to items in a table.

Whenever an item is:

- Inserted
- Updated
- Deleted

an event is written to the stream.

Example:

```text
Application

↓

Update Item

↓

DynamoDB

↓

Stream Record

↓

Lambda

↓

Process Event
```

---

## Interview Tip

Think of Streams as:

> "The change log for a DynamoDB table."

---

# Question 2

## Why are DynamoDB Streams useful?

### Expected Answer

Streams enable event-driven architectures.

Common use cases include:

- Sending notifications
- Updating search indexes
- Triggering Lambda functions
- Synchronizing databases
- Cache invalidation
- Audit logging
- Analytics pipelines

---

# Question 3

## What are Stream View Types?

### Expected Answer

DynamoDB supports four stream view types.

### KEYS_ONLY

Stores only primary keys.

```text
PK

SK
```

---

### NEW_IMAGE

Stores the item after modification.

---

### OLD_IMAGE

Stores the item before modification.

---

### NEW_AND_OLD_IMAGES

Stores both versions.

Most production systems use this option for auditing and change tracking.

---

# Question 4

## How long are stream records retained?

### Expected Answer

DynamoDB Streams retain records for:

```text
24 Hours
```

Applications should process events before they expire.

---

# Question 5

## Are DynamoDB Streams ordered?

### Expected Answer

Ordering is guaranteed **within a single shard**.

Events affecting the same partition key maintain their order.

Ordering is **not guaranteed across different shards**.

---

# Question 6

## Can DynamoDB Streams trigger Lambda?

### Expected Answer

Yes.

This is one of the most common production integrations.

Workflow:

```text
Item Updated

↓

DynamoDB Stream

↓

Lambda Trigger

↓

Business Logic

↓

SNS / SQS / EventBridge
```

---

# Question 7

## What is Time To Live (TTL)?

### Expected Answer

TTL automatically deletes expired items.

Applications specify a timestamp attribute.

Example:

```text
Session

↓

ExpiresAt

↓

Automatic Deletion
```

---

## Common Use Cases

- User sessions
- OTP records
- Cache entries
- Temporary files
- Shopping carts

---

# Question 8

## Does TTL delete items immediately?

### Expected Answer

No.

TTL is a background process.

Expired items are typically removed within a reasonable period after expiration, but there is no guarantee of immediate deletion.

Applications should not depend on TTL for precise timing.

---

# Question 9

## Does TTL consume write capacity?

### Expected Answer

No.

TTL deletions are performed automatically by DynamoDB.

Applications are not charged write capacity for the deletion itself.

---

# Question 10

## What is Point-in-Time Recovery (PITR)?

### Expected Answer

PITR allows restoration of a table to any second within the configured recovery window.

Workflow:

```text
10:00

↓

10:30

↓

11:00

↓

Accidental Delete

↓

Restore to 10:59
```

---

## Production Benefit

Protects against:

- Accidental deletion
- Corruption
- Faulty deployments

---

# Question 11

## What is the difference between PITR and On-Demand Backup?

### Expected Answer

| Feature | PITR | On-Demand Backup |
|----------|------|------------------|
| Automatic | Yes | No |
| Restore Time | Any second within recovery window | Specific backup |
| Continuous | Yes | No |
| Manual Snapshot | No | Yes |

---

# Question 12

## What are Global Tables?

### Expected Answer

Global Tables replicate DynamoDB tables across multiple AWS Regions.

Example:

```text
US-East-1

↓

Replication

↓

Europe-West-1

↓

Replication

↓

Asia-Pacific
```

Benefits:

- Low latency
- Disaster recovery
- Global applications

---

# Question 13

## How does conflict resolution work in Global Tables?

### Expected Answer

Global Tables use:

```text
Last Writer Wins
```

based on timestamps managed by DynamoDB.

Applications with complex business rules may need additional conflict resolution logic.

---

# Question 14

## What is PartiQL?

### Expected Answer

PartiQL is a SQL-compatible query language for DynamoDB.

Example:

Instead of SDK code:

```text
GetItem()
```

You can write:

```sql
SELECT * FROM Orders
WHERE CustomerID = '123'
```

Internally, DynamoDB still uses its NoSQL architecture.

---

# Question 15

## Does PartiQL make DynamoDB a relational database?

### Expected Answer

No.

PartiQL provides a familiar SQL-like syntax but does not add relational features such as joins, foreign keys, or normalized schemas.

---

# Question 16

## How would you implement an audit log?

### Expected Answer

Use DynamoDB Streams.

Workflow:

```text
Update Item

↓

Stream

↓

Lambda

↓

Audit Table

↓

CloudWatch
```

This provides a reliable history of changes.

---

# Question 17

## How would you synchronize Elasticsearch or OpenSearch?

### Expected Answer

Architecture:

```text
DynamoDB

↓

Streams

↓

Lambda

↓

OpenSearch
```

Every change automatically updates the search index.

---

# Question 18

## Can Streams replace a message queue?

### Expected Answer

No.

Streams capture database changes.

They are not a general-purpose messaging system like:

- Amazon SQS
- Apache Kafka
- Amazon MQ

Streams should be used for change data capture (CDC), not as an application message broker.

---

# Question 19

## How would you build an event-driven system using DynamoDB?

### Expected Answer

Example architecture:

```text
User Places Order

↓

DynamoDB

↓

Streams

↓

Lambda

↓

SNS

↓

Email Service

↓

Analytics

↓

Inventory Service
```

This decouples services and improves scalability.

---

# Question 20

## Explain DynamoDB Streams in one minute.

### Sample Answer

> DynamoDB Streams provide a time-ordered record of item-level changes in a table. They are commonly used to build event-driven architectures by triggering AWS Lambda functions that perform downstream processing such as notifications, search index synchronization, auditing, or analytics. Stream records are retained for 24 hours and can include keys, old images, new images, or both. Combined with features like TTL, PITR, and Global Tables, Streams enable highly scalable and resilient distributed systems.

---

# Rapid Fire Questions

| Question | Short Answer |
|-----------|--------------|
| Stream retention? | 24 Hours |
| Lambda integration? | Yes |
| TTL automatic? | Yes |
| TTL immediate? | No |
| PITR continuous? | Yes |
| Manual backup? | On-Demand Backup |
| Multi-region replication? | Global Tables |
| Conflict resolution? | Last Writer Wins |
| SQL support? | PartiQL |
| Streams for CDC? | Yes |

---

# Senior Interview Tips

Strong candidates discuss:

- Change Data Capture (CDC)
- Event-driven architecture
- Asynchronous processing
- Disaster recovery
- Multi-region design
- Audit logging
- Production trade-offs

Avoid saying:

> "Streams are just Lambda triggers."

Instead explain:

> "Streams provide an event source that enables loosely coupled, event-driven architectures where downstream services react to data changes asynchronously."

---

# Common Mistakes

## Using TTL for Immediate Deletion

TTL is asynchronous.

Applications should not rely on it for time-critical workflows.

---

## Treating Streams Like Kafka

Streams are designed for database change events, not general messaging or event streaming.

---

## Ignoring Conflict Resolution in Global Tables

Multi-region writes can overwrite one another.

Applications with strict consistency requirements may need additional safeguards.

---

## Forgetting Stream Retention

Events older than:

```text
24 Hours
```

cannot be replayed from DynamoDB Streams.

---

# Interview Cheat Sheet

```text
DynamoDB

↓

Streams

↓

Lambda

↓

Event Processing

↓

Audit Logs

↓

TTL

↓

PITR

↓

Global Tables

↓

Disaster Recovery
```

---

# Key Takeaways

- DynamoDB Streams enable efficient change data capture and are a core building block for event-driven architectures.
- TTL automatically removes expired data, but deletion is asynchronous and should not be treated as an exact scheduler.
- PITR and On-Demand Backups provide complementary disaster recovery capabilities.
- Global Tables enable low-latency, multi-region deployments but require understanding of conflict resolution.
- Senior interviewers expect candidates to connect these features into real production architectures rather than describing them in isolation.