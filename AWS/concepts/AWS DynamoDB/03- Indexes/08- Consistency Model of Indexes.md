# 08 - Consistency Model of Indexes

## Overview

One of the most misunderstood aspects of Amazon DynamoDB is the **consistency behavior of secondary indexes**.

Many developers assume that if a write succeeds, every index immediately reflects that change.

This is **not always true**.

Understanding index consistency is critical because it directly affects:

- Application correctness
- User experience
- Data freshness
- Read-after-write behavior
- System architecture

The key rule to remember is:

> **Global Secondary Indexes (GSIs) are eventually consistent, while Local Secondary Indexes (LSIs) can support strongly consistent reads.**

Choosing the wrong index without understanding its consistency guarantees can lead to stale reads and subtle production bugs.

---

# What is Consistency?

Consistency defines **how quickly a read operation reflects the latest successful write**.

Imagine a user updates their profile.

```text
Update Email

↓

Database Updated

↓

User Reads Data
```

The question is:

**Will the user immediately see the updated value?**

The answer depends on the consistency model.

---

# Strong Consistency

A strongly consistent read guarantees:

```text
Write

↓

Success

↓

Next Read

↓

Latest Data
```

No stale data is returned.

Example:

```text
Account Balance

$100

↓

Deposit

$50

↓

Strong Read

↓

$150
```

The latest committed value is always returned.

---

# Eventual Consistency

An eventually consistent read allows a short propagation delay.

Workflow:

```text
Write

↓

Database Updated

↓

Replication

↓

Read

↓

Latest Data
```

Sometimes:

```text
Write

↓

Read

↓

Old Value
```

After a short delay:

```text
Read Again

↓

New Value
```

Most updates propagate within milliseconds, but the delay is not guaranteed.

---

# DynamoDB Consistency Model

Base Table

Supports:

```text
Eventually Consistent Reads
```

and

```text
Strongly Consistent Reads
```

Applications choose the desired consistency level when querying the base table.

---

# Consistency of GSIs

Global Secondary Indexes only support:

```text
Eventually Consistent Reads
```

Workflow:

```text
Write

↓

Base Table Updated

↓

Background Replication

↓

GSI Updated
```

Immediately after a write:

```text
Query GSI

↓

Old Data

Possible
```

---

# Why Are GSIs Eventually Consistent?

GSIs are physically separate data structures.

They have:

- Independent partitions
- Separate storage
- Separate replication

Updating both the base table and every GSI synchronously would increase write latency and reduce scalability.

Instead:

```text
Write

↓

Base Table

↓

Async Replication

↓

GSI
```

This design allows DynamoDB to achieve extremely high throughput.

---

# Consistency of LSIs

Local Secondary Indexes share the same partition as the base table.

Because of this,

they support:

```text
Strongly Consistent Reads
```

Workflow:

```text
Write

↓

Partition Updated

↓

LSI Updated

↓

Read

↓

Latest Data
```

No replication delay exists between the base table and the LSI.

---

# Visual Comparison

```text
               Base Table

                    │

       ┌────────────┴────────────┐

       ▼                         ▼

      LSI                      GSI

Strong Consistency     Eventual Consistency
```

---

# Example – User Profile

Table:

```text
PK = UserID
```

GSI:

```text
PK = Email
```

Workflow:

```text
Update Email

↓

Base Table Updated

↓

Query Email GSI
```

Possible result:

```text
Old Email
```

After replication:

```text
Query Again

↓

New Email
```

---

# Example – Banking

Account table:

```text
PK = AccountID

SK = TransactionID
```

LSI:

```text
PK = AccountID

SK = TransactionDate
```

Customer deposits money.

Immediately requests:

```text
Latest Transactions
```

Using:

```text
Strong Read

LSI
```

Latest transaction appears immediately.

---

# Read-After-Write Behavior

## Base Table

Supports:

```text
Strong Read

↓

Latest Data
```

---

## GSI

Supports:

```text
Eventually Consistent Read

↓

May Return Stale Data
```

---

## LSI

Supports:

```text
Strong Read

↓

Latest Data
```

---

# Replication Timeline

GSI:

```text
Time 0

Write Item

↓

Time 1

Base Table Updated

↓

Time 2

Replication Begins

↓

Time 3

GSI Updated
```

Between Time 1 and Time 3,

queries against the GSI may return stale data.

---

# Real-World Example – E-commerce

Customer places an order.

Order table updates:

```text
Status = Processing
```

Dashboard queries a GSI:

```text
StatusIndex
```

Immediately after the update,

dashboard may still show:

```text
Pending
```

A few milliseconds later:

```text
Processing
```

appears.

Applications should tolerate this brief inconsistency.

---

# Real-World Example – Messaging

Messages:

```text
Unread

↓

Read
```

Unread messages are stored in a Sparse GSI.

User opens the message.

Immediately querying:

```text
Unread Messages
```

may temporarily still include the message until GSI replication completes.

---

# Designing Around Eventual Consistency

Applications should:

- Retry after a short delay.
- Avoid immediate read-after-write using GSIs.
- Query the base table when immediate consistency is required.
- Design workflows that tolerate brief propagation delays.

---

# Common Design Patterns

## Pattern 1

Write:

```text
Base Table
```

Read:

```text
Base Table

Strong Read
```

Guaranteed latest data.

---

## Pattern 2

Write:

```text
Base Table
```

Search:

```text
GSI
```

Accept eventual consistency.

Ideal for:

- Search
- Reporting
- Dashboards
- Analytics

---

## Pattern 3

Use LSI

when:

```text
Immediate Ordering

+

Strong Consistency
```

are required.

---

# Performance Trade-Off

Strong consistency:

```text
More Coordination

↓

Higher Latency
```

Eventual consistency:

```text
Less Coordination

↓

Higher Throughput
```

This trade-off enables DynamoDB to scale horizontally across many partitions.

---

# Best Practices

- Use strongly consistent reads only when necessary.
- Expect temporary staleness when querying GSIs.
- Design applications to tolerate eventual consistency.
- Use retries with exponential backoff if required.
- Query the base table immediately after critical writes.
- Document consistency expectations for application teams.

---

# Common Mistakes

## Assuming GSIs Are Immediately Updated

Many developers expect GSI queries to reflect writes instantly.

This assumption leads to inconsistent application behavior.

---

## Using GSIs for Critical Read-After-Write Workflows

If an application requires immediate confirmation after an update, query the base table instead of the GSI.

---

## Ignoring User Experience

A stale dashboard may be acceptable.

A stale financial transaction is usually not.

Choose the consistency model based on business requirements.

---

## Overusing Strong Reads

Strongly consistent reads increase resource usage and are not always necessary.

Use them selectively.

---

# Consistency Comparison

| Feature | Base Table | LSI | GSI |
|----------|------------|-----|-----|
| Eventually Consistent Reads | ✅ | ✅ | ✅ |
| Strongly Consistent Reads | ✅ | ✅ | ❌ |
| Replication Delay | None | None | Yes |
| Read-After-Write Guarantee | Yes (Strong Reads) | Yes (Strong Reads) | No |
| Best For | Critical operations | Ordered partition queries | Flexible search patterns |

---

# Architecture Perspective

```text
                    Application

                          │

                Update Customer

                          │

                          ▼

                    Base Table

                          │

          ┌───────────────┴───────────────┐

          ▼                               ▼

        LSI                              GSI

 Strong Consistency            Async Replication

          │                               │

          ▼                               ▼

 Latest Data                   Possible Stale Data
```

The LSI is updated synchronously with the base table, while the GSI is updated asynchronously to maximize scalability.

---

# Production Considerations

Enterprise applications frequently use both consistency models.

Examples:

| Application | Preferred Consistency |
|-------------|-----------------------|
| Banking Transactions | Strong |
| Shopping Cart | Strong |
| Product Search | Eventual |
| Analytics Dashboard | Eventual |
| Log Search | Eventual |
| User Timeline | Eventual |
| Order Confirmation | Strong |

The correct choice depends on whether **immediate correctness** or **maximum scalability** is more important.

---

# Interview Notes

A common interview question is:

> **Why are GSIs eventually consistent?**

GSIs are stored separately from the base table and updated asynchronously to improve scalability and write throughput. Because replication is asynchronous, a short delay may occur before writes become visible in the index.

Another common question is:

> **Can Local Secondary Indexes support strongly consistent reads?**

Yes. LSIs share the same partition as the base table, allowing them to participate in strongly consistent reads.

Another common question is:

> **How should applications handle GSI consistency?**

Applications should expect brief propagation delays, avoid immediate read-after-write workflows using GSIs, and query the base table when immediate consistency is required.

---

# Key Takeaways

- DynamoDB supports both strongly consistent and eventually consistent reads on the base table.
- GSIs only support eventually consistent reads because they are updated asynchronously.
- LSIs support strongly consistent reads because they share the same partition as the base table.
- Eventual consistency improves scalability and write throughput but may briefly return stale data.
- Applications should choose consistency models based on business requirements rather than assuming all reads behave the same.
- Understanding index consistency is essential for designing reliable, scalable DynamoDB applications.