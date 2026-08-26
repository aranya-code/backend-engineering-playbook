# 05 - Sparse Indexes

## Overview

A **Sparse Index** is one of the most powerful optimization techniques in Amazon DynamoDB.

Unlike a traditional index that contains **every item** in a table, a Sparse Index contains **only items that have a specific indexed attribute**.

This allows applications to efficiently query a small subset of data without scanning the entire table.

Sparse indexes are commonly used in production systems for:

- Active orders
- Failed jobs
- Pending payments
- VIP customers
- Products on sale
- Unprocessed events
- High-priority tickets
- Fraud detection
- Workflow queues

They reduce storage costs, lower write amplification, and significantly improve query performance.

---

# Why Are Sparse Indexes Needed?

Suppose an Orders table contains:

```text
10 Million Orders
```

Only:

```text
15,000

Pending Orders
```

Business requirement:

```text
Show All Pending Orders
```

Without an index:

```text
Scan

10 Million Records

↓

Filter

Pending
```

Very expensive.

Instead,

only pending orders are indexed.

---

# What Makes an Index "Sparse"?

A DynamoDB secondary index only includes an item **if the index's Partition Key attribute exists on that item**.

Example:

Table

```text
OrderID

Status

PendingFlag
```

Only pending orders have:

```text
PendingFlag = TRUE
```

All completed orders simply omit:

```text
PendingFlag
```

Result:

```text
Only Pending Orders

Appear

In Index
```

---

# Visual Representation

Base Table

```text
Order 101

Status = Pending

PendingFlag = TRUE
```

```text
Order 102

Status = Completed
```

```text
Order 103

Status = Pending

PendingFlag = TRUE
```

Sparse Index

```text
Order 101

PendingFlag
```

```text
Order 103

PendingFlag
```

Completed orders never enter the index.

---

# Internal Architecture

```text
                Base Table

       Order101   Pending

       Order102   Completed

       Order103   Pending

       Order104   Cancelled

               │

               ▼

         Sparse GSI

       Pending Orders

       Order101

       Order103
```

The index is dramatically smaller than the table.

---

# How It Works

Suppose a GSI uses:

```text
PK = PendingFlag
```

Items with:

```text
PendingFlag
```

appear.

Items without:

```text
PendingFlag
```

do not.

Example:

```json
{
    "OrderId": 101,
    "PendingFlag": "YES"
}
```

Indexed.

Another:

```json
{
    "OrderId": 102
}
```

Not indexed.

---

# Example – Order Processing

Orders:

```text
Pending

Processing

Completed

Cancelled
```

Only:

```text
Pending
```

requires immediate attention.

Index:

```text
PK = PendingFlag
```

Applications query:

```text
PendingFlag = YES
```

Only active work appears.

---

# Example – Background Jobs

Millions of jobs.

Only failed jobs require investigation.

Base table:

```text
JobID

Status

FailureFlag
```

Only failures contain:

```text
FailureFlag = TRUE
```

Sparse Index:

```text
Failed Jobs
```

Support engineers immediately retrieve failed jobs.

---

# Example – Fraud Detection

Transactions:

```text
Normal

Suspicious
```

Only suspicious transactions contain:

```text
FraudFlag
```

Sparse GSI:

```text
FraudFlag

↓

Suspicious Transactions
```

No scanning required.

---

# Example – Support Tickets

Tickets:

```text
Open

Closed

Escalated
```

Only escalated tickets include:

```text
EscalationLevel
```

Sparse Index:

```text
Escalated Tickets
```

Operations teams immediately see urgent issues.

---

# Example – Inventory

Products:

```text
In Stock

Out of Stock
```

Only out-of-stock products contain:

```text
RestockRequired
```

Index:

```text
RestockRequired
```

Warehouse systems retrieve only products needing replenishment.

---

# Sparse Index vs Normal GSI

Normal GSI

```text
Every Item

↓

Index
```

Sparse GSI

```text
Only Matching Items

↓

Index
```

This difference has a major impact on storage and write costs.

---

# Benefits

Sparse indexes provide:

- Smaller indexes
- Faster queries
- Lower storage costs
- Lower write costs
- Better cache efficiency
- Simpler application logic

---

# Storage Savings

Imagine:

```text
100 Million Records
```

Only:

```text
20,000

Pending Orders
```

Sparse index stores:

```text
20,000
```

instead of

```text
100 Million
```

Huge storage savings.

---

# Write Cost Savings

Every indexed item generates additional writes.

Sparse indexes only update when the indexed attribute exists.

Example:

Completed order:

```text
No PendingFlag

↓

No Index Write
```

Less write amplification.

---

# State Transitions

Suppose:

Order:

```text
Pending
```

Later becomes:

```text
Completed
```

Workflow:

```text
PendingFlag Removed

↓

Automatically Removed

From Sparse Index
```

DynamoDB keeps the index synchronized automatically.

---

# Design Pattern

Base Table

```text
OrderID

Status

PriorityFlag
```

Only urgent orders:

```text
PriorityFlag = HIGH
```

Index:

```text
PK = PriorityFlag

SK = CreatedDate
```

Applications query:

```text
HIGH

↓

Newest First
```

---

# Combining with GSIs

Sparse indexes are almost always implemented using:

```text
Global Secondary Index
```

Example:

```text
PK = FraudFlag

SK = TransactionTime
```

Only suspicious transactions exist in the index.

---

# Combining with TTL

Workflow:

```text
Pending Job

↓

Sparse Index

↓

Completed

↓

TTL

↓

Deleted
```

Temporary workflows become highly efficient.

---

# Real-World Example

An e-commerce platform processes millions of orders daily.

Less than 1% require manual review.

Instead of scanning every order, only orders containing:

```text
ManualReview = TRUE
```

are copied into a Sparse GSI.

Operations dashboards query the index directly, reducing read latency and minimizing infrastructure costs.

---

# Best Practices

- Use Sparse Indexes for small subsets of data.
- Index only items supporting critical workflows.
- Remove index attributes when no longer needed.
- Combine Sparse GSIs with meaningful sort keys.
- Monitor index size and access frequency.
- Keep projected attributes minimal.

---

# Common Mistakes

## Indexing Everything

Adding the indexed attribute to every item defeats the purpose of a Sparse Index.

---

## Using Sparse Indexes for Large Datasets

If nearly every item qualifies,

the index is no longer sparse.

A regular GSI may be more appropriate.

---

## Forgetting Attribute Removal

When workflow status changes,

remove the indexed attribute if the item should disappear from the Sparse Index.

---

## Poor Partition Keys

Example:

```text
Pending = TRUE
```

Millions of pending records may create a hot partition.

Consider:

```text
Pending#Region

Pending#Date

Pending#Shard
```

for better distribution.

---

# SQL Filter vs Sparse Index

| Feature | SQL WHERE Clause | DynamoDB Sparse Index |
|----------|------------------|-----------------------|
| Data Read | Reads matching rows after index/table lookup | Reads only indexed items |
| Storage | No additional filtering structure | Separate index with matching items |
| Performance | Depends on query planner | Extremely efficient |
| Cost | Query-dependent | Lower reads and smaller index |
| Scale | Database-dependent | Built for horizontal scaling |

---

# Architecture Perspective

```text
                    Application

                         │

                         ▼

             Query Pending Orders

                         │

                         ▼

                  Sparse GSI

                         │

             Pending Orders Only

                         │

         ┌───────────────┴──────────────┐

         ▼                              ▼

     Order101                     Order103

                         │

                         ▼

                  Application Response
```

The application never scans completed or cancelled orders because they do not exist in the index.

---

# Production Considerations

Sparse indexes are widely used in enterprise applications for:

- Operational dashboards
- Workflow engines
- Queue processing
- Incident management
- Fraud monitoring
- Alerting systems
- Compliance reviews

Because only relevant records are indexed, these systems maintain predictable performance even when the primary table contains billions of items.

---

# Interview Notes

A common interview question is:

> **What is a Sparse Index in DynamoDB?**

A Sparse Index is a secondary index that contains only items with a specific indexed attribute. Items missing that attribute are automatically excluded from the index.

Another common question is:

> **Why are Sparse Indexes useful?**

They reduce storage costs, lower write amplification, and allow applications to efficiently query a small subset of important data without scanning the entire table.

Another common question is:

> **Give a real-world use case for a Sparse Index.**

Examples include pending orders, failed jobs, fraud alerts, escalated support tickets, inventory requiring restocking, or records awaiting manual approval. In each case, only the relevant items appear in the index, making operational queries extremely efficient.

---

# Key Takeaways

- Sparse Indexes contain only items that include the indexed attribute.
- They are typically implemented using Global Secondary Indexes (GSIs).
- Sparse indexes reduce storage, write costs, and query latency.
- They are ideal for workflows involving a small subset of records.
- DynamoDB automatically adds or removes items from the index as indexed attributes appear or disappear.
- Sparse Indexes are one of the most effective optimization techniques for large-scale DynamoDB applications.