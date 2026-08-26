# 09 - Sparse Index Pattern

## Overview

One of the biggest advantages of DynamoDB is that **Global Secondary Indexes (GSIs) are sparse by default**.

Unlike relational database indexes, which usually contain entries for every row, a DynamoDB GSI only contains items that have the indexed attributes.

This behavior enables an extremely powerful data modeling technique known as the **Sparse Index Pattern**.

Instead of indexing every item, we intentionally add an attribute **only to the items we want to query**, allowing the GSI to contain only a small subset of the table.

The result is:

- Lower storage cost
- Lower write cost
- Faster queries
- Cleaner data models

Sparse indexes are widely used in production systems to efficiently retrieve **rare, high-value, or filtered records**.

---

# What Is a Sparse Index?

A sparse index is simply a Global Secondary Index that contains **only items possessing the indexed attribute**.

Suppose a GSI is built on:

```text
GSI1PK
```

Items without `GSI1PK`:

```text
Not Indexed
```

Items with `GSI1PK`:

```text
Indexed
```

No extra configuration is required.

This is DynamoDB's default behavior.

---

# Example

Consider an Orders table.

```text
OrderID

Customer

Status
```

Orders:

```text
Order 1

Status = Pending
```

```text
Order 2

Status = Shipped
```

```text
Order 3

Status = Delivered
```

Suppose customer service frequently needs:

> Show all pending orders.

Scanning millions of orders would be inefficient.

---

# Traditional Solution

Relational database:

```sql
SELECT *

FROM Orders

WHERE Status='Pending'
```

Requires an index on:

```text
Status
```

Every row participates in the index.

---

# DynamoDB Sparse Index Solution

Instead of indexing every order:

Only pending orders receive:

```text
GSI1PK = PENDING
```

Example:

```text
Order 1

Status = Pending

GSI1PK = PENDING
```

```text
Order 2

Status = Shipped
```

(No GSI attribute)

```text
Order 3

Status = Delivered
```

(No GSI attribute)

---

# What Happens?

Main table:

```text
Order1

Order2

Order3
```

GSI:

```text
PENDING

↓

Order1
```

Only pending orders appear.

---

# Visual Representation

```text
Orders Table

│

├── Pending Order

├── Delivered Order

├── Cancelled Order

├── Pending Order

└── Shipped Order
```

Sparse GSI:

```text
PENDING

│

├── Order A

└── Order B
```

Only matching records exist.

---

# Query Example

Instead of:

```text
Scan Entire Table
```

Use:

```text
Query GSI

↓

PENDING
```

Returns only pending orders.

---

# Another Example

Suppose an application stores users.

Only premium users need quick lookup.

Users:

```text
Alice

Premium
```

```text
Bob

Free
```

```text
Charlie

Free
```

```text
David

Premium
```

Only premium users receive:

```text
GSI1PK = PREMIUM
```

Now:

```text
Query

PREMIUM
```

Returns:

- Alice
- David

---

# Example – Error Logs

Suppose millions of log entries exist.

Only errors require monitoring.

Logs:

```text
INFO

INFO

WARNING

ERROR

INFO

ERROR
```

Only errors receive:

```text
GSI1PK = ERROR
```

Monitoring system:

```text
Query ERROR
```

Instead of scanning terabytes of logs.

---

# Example – Expiring Sessions

Sessions:

```text
Active

Expired

Expired

Active

Expired
```

Only expired sessions contain:

```text
Cleanup = TRUE
```

GSI:

```text
Cleanup

↓

Expired Sessions
```

Background workers retrieve only expired sessions.

---

# Example – Fraud Detection

Transactions:

```text
Normal

Normal

Suspicious

Normal

Suspicious
```

Suspicious transactions receive:

```text
FraudFlag = TRUE
```

Security service:

```text
Query Fraud GSI
```

Returns only suspicious transactions.

---

# Why Is This Efficient?

Without sparse indexes:

```text
Millions of Items

↓

Index
```

Large index.

With sparse indexes:

```text
Millions of Items

↓

Hundreds Indexed
```

Tiny index.

Lower storage.

Lower write amplification.

Faster lookups.

---

# Storage Benefits

Suppose:

Table:

```text
100 Million Orders
```

Pending:

```text
50,000
```

Traditional index:

```text
100 Million Entries
```

Sparse index:

```text
50,000 Entries
```

Huge reduction in storage.

---

# Cost Benefits

Because fewer items exist inside the GSI:

- Less storage
- Fewer index writes
- Lower replication overhead
- Faster queries
- Lower operational cost

This is especially valuable for high-volume workloads.

---

# Real-World Use Cases

Sparse indexes are commonly used for:

- Pending orders
- Failed payments
- Active subscriptions
- Premium users
- Expired sessions
- Security alerts
- Fraud detection
- Retry queues
- Inventory below threshold
- Unprocessed messages

---

# Combining with Single Table Design

Sparse indexes work extremely well with Single Table Design.

Example table:

```text
USER

ORDER

PAYMENT

DEVICE

SESSION
```

Only failed payments include:

```text
GSI1PK = FAILED_PAYMENT
```

Only active sessions include:

```text
GSI2PK = ACTIVE_SESSION
```

Each GSI becomes highly specialized.

---

# Sparse Index vs Filter Expression

Some developers write:

```text
Scan

↓

Filter Status='Pending'
```

This is inefficient.

Why?

Because:

```text
Scan

↓

Reads Every Item

↓

Then Filters
```

RCUs are consumed for all scanned items.

Sparse index:

```text
Query

↓

Reads Only Matching Items
```

Much cheaper.

---

# Best Practices

- Index only frequently queried subsets.
- Choose descriptive GSI partition keys.
- Keep sparse indexes focused on one access pattern.
- Avoid indexing unnecessary attributes.
- Monitor GSI write capacity for high-write workloads.
- Remove indexed attributes when items no longer qualify.

---

# Common Mistakes

## Indexing Everything

If every item contains the indexed attribute:

```text
Sparse Index

↓

Not Sparse
```

Storage costs increase unnecessarily.

---

## Using Scan Instead of Query

A sparse GSI exists to avoid table scans.

Always prefer:

```text
Query GSI
```

---

## Creating Too Many Sparse GSIs

Each GSI increases:

- Write cost
- Storage
- Operational complexity

Create indexes only for important access patterns.

---

## Forgetting Attribute Removal

Suppose:

```text
Status = Pending
```

Later:

```text
Status = Delivered
```

If the sparse index attribute isn't removed or updated appropriately, stale index entries can remain until the item is updated consistently.

---

# Real-World Example

An online marketplace processes millions of orders every day.

Most orders are successfully fulfilled, but customer support frequently needs to identify orders requiring manual intervention.

Instead of indexing every order, only problematic orders receive:

```text
SupportQueue = TRUE
```

A GSI on `SupportQueue` allows the support application to retrieve only those orders needing attention, regardless of the total table size.

---

# Architecture Perspective

```text
Orders Table

        │

        ├── Pending Order

        ├── Delivered Order

        ├── Cancelled Order

        ├── Pending Order

        └── Shipped Order

                │

                ▼

      Sparse Global Secondary Index

                │

        ├── Pending Order

        └── Pending Order

                │

                ▼

      Customer Support Dashboard
```

The sparse index isolates a small, meaningful subset of data, enabling efficient queries without scanning the full table.

---

# Interview Notes

A common interview question is:

> **What is a Sparse Index in DynamoDB?**

A Sparse Index is a Global Secondary Index that contains only items with the indexed attribute. Items lacking that attribute are automatically excluded from the index.

Another common question is:

> **Why are Sparse Indexes useful?**

They reduce storage and write costs while enabling extremely efficient queries for specific subsets of data, such as pending orders, failed payments, or premium users.

Another common question is:

> **How is a Sparse Index different from a Filter Expression?**

A Filter Expression is applied **after** items have been read, so read capacity is consumed for all matching partition items. A Sparse Index avoids reading irrelevant items altogether by indexing only the subset of interest.

---

# Key Takeaways

- GSIs in DynamoDB are sparse by default.
- Only items containing the indexed attributes appear in the index.
- Sparse indexes are ideal for querying rare or high-value subsets of data.
- They significantly reduce storage, write amplification, and query costs.
- Sparse indexes are commonly used for workflows such as support queues, fraud detection, retries, and monitoring.
- Designing sparse indexes around important access patterns is a hallmark of scalable DynamoDB data modeling.