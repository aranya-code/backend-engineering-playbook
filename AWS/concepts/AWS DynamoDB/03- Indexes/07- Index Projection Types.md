# 07 - Index Projection Types

## Overview

Creating a secondary index in DynamoDB is not just about choosing the **Partition Key** and **Sort Key**.

Another equally important decision is **which attributes should be copied into the index**.

This is controlled using **Projection Types**.

Projection determines:

- Which attributes are stored in the index
- How much storage the index consumes
- How expensive writes become
- Whether additional reads to the base table are required

Choosing the correct projection type is one of the simplest ways to optimize DynamoDB performance and cost.

---

# What is Projection?

When DynamoDB creates a secondary index, it automatically stores:

- Index Partition Key
- Index Sort Key (if present)
- Base Table Primary Key

Beyond these required attributes, you decide what additional attributes should be copied into the index.

This copying process is called:

```text
Projection
```

---

# Why Are Projection Types Needed?

Consider an Orders table.

```text
OrderID

CustomerID

OrderDate

Status

ShippingAddress

PaymentMethod

TotalAmount

Items

Notes
```

Business requirement:

```text
Find Orders

By Customer
```

Does the index really need:

- Shipping Address?
- Order Notes?
- Full Item List?

Probably not.

Copying unnecessary data wastes:

- Storage
- Write capacity
- Money

Projection lets you avoid that.

---

# How Projection Works

Base Table

```text
OrderID

CustomerID

OrderDate

Status

Items

TotalAmount

Address
```

GSI

```text
PK = CustomerID

SK = OrderDate
```

Projection determines whether the GSI stores:

```text
Only Keys
```

or

```text
Some Attributes
```

or

```text
Everything
```

---

# Projection Types

DynamoDB supports three projection types.

```text
KEYS_ONLY

INCLUDE

ALL
```

Each serves different use cases.

---

# KEYS_ONLY Projection

Stores only:

- Index Partition Key
- Index Sort Key
- Base Table Primary Key

Nothing else.

Example:

Base Table

```text
OrderID

CustomerID

OrderDate

TotalAmount

Status
```

Index

```text
CustomerID

OrderDate

OrderID
```

Notice:

```text
Status

TotalAmount
```

are not copied.

---

# Visual Representation

Base Table

```text
+----------------------------------------------+

OrderID

CustomerID

OrderDate

Status

Amount

Items

Address

+----------------------------------------------+
```

KEYS_ONLY Index

```text
+---------------------------+

CustomerID

OrderDate

OrderID

+---------------------------+
```

Very small index.

---

# Advantages of KEYS_ONLY

- Smallest storage footprint
- Lowest write amplification
- Fast index updates
- Lower AWS costs

Ideal when the application only needs identifiers.

---

# Disadvantages

Suppose the application also needs:

```text
Status
```

The workflow becomes:

```text
Query Index

↓

Retrieve OrderID

↓

GetItem

↓

Base Table
```

Two reads instead of one.

---

# INCLUDE Projection

Stores:

- Required keys
- Selected non-key attributes

Example:

Index:

```text
CustomerID

OrderDate

Status

TotalAmount
```

Only the attributes useful for queries are copied.

---

# Visual Representation

Base Table

```text
CustomerID

OrderDate

Status

TotalAmount

Address

Items

Notes
```

INCLUDE Index

```text
CustomerID

OrderDate

Status

TotalAmount
```

Only useful business data is projected.

---

# Advantages of INCLUDE

- Balanced storage usage
- Faster queries
- Lower storage than ALL
- Avoids unnecessary base table reads

This is often the best production choice.

---

# ALL Projection

Copies every attribute.

Base Table

```text
Everything
```

↓

Index

```text
Everything
```

The index becomes a nearly complete copy of the table.

---

# Visual Representation

Base Table

```text
OrderID

CustomerID

OrderDate

Status

Items

Address

Payment
```

ALL Projection

```text
OrderID

CustomerID

OrderDate

Status

Items

Address

Payment
```

Everything exists in both places.

---

# Advantages of ALL

Applications can often satisfy queries entirely from the index.

Workflow:

```text
Query GSI

↓

Return Complete Item
```

No additional table lookup.

---

# Disadvantages

ALL projections:

- Increase storage
- Increase write cost
- Duplicate large attributes
- Increase replication overhead

Large documents become expensive.

---

# Comparison

## KEYS_ONLY

```text
Small

Fast

Cheap
```

Requires additional table reads.

---

## INCLUDE

```text
Medium Size

Balanced Cost

Most Common
```

Excellent production choice.

---

## ALL

```text
Largest

Most Expensive

Fastest Reads
```

Best when nearly every attribute is required.

---

# Storage Comparison

Imagine:

Table Item Size

```text
8 KB
```

Projected:

## KEYS_ONLY

```text
300 Bytes
```

---

## INCLUDE

```text
2 KB
```

---

## ALL

```text
8 KB
```

Multiply this across millions of items.

The cost difference becomes substantial.

---

# Real-World Example

E-commerce application.

Dashboard needs:

```text
OrderID

CustomerID

Status

OrderDate

TotalAmount
```

It never displays:

- Shipping Address
- Payment Details
- Product Images
- Internal Notes

Projection:

```text
INCLUDE
```

Application retrieves everything it needs directly from the index.

---

# Another Example

Chat Application.

Messages contain:

- Text
- Attachments
- Images
- Metadata
- Delivery Status

Unread message dashboard only needs:

```text
MessageID

Sender

Timestamp
```

Projection:

```text
KEYS_ONLY
```

Message body is loaded only when opened.

---

# Large Document Example

Medical records.

Patient record:

```text
50 KB
```

Index:

```text
DoctorID

VisitDate
```

Doctor dashboard shows:

```text
Patient Name

Visit Date

Status
```

Projection:

```text
INCLUDE
```

Copying all 50 KB into the index would dramatically increase costs.

---

# Choosing the Right Projection

Use **KEYS_ONLY** when:

- Only identifiers are needed.
- Applications will fetch complete items later.
- Storage cost is a priority.

---

Use **INCLUDE** when:

- A few additional attributes satisfy most queries.
- You want to avoid extra table reads.
- Cost and performance should be balanced.

---

Use **ALL** when:

- Nearly every query needs the full item.
- Items are relatively small.
- Read performance is more important than storage cost.

---

# Best Practices

- Default to **INCLUDE** for most production workloads.
- Keep projected attributes minimal.
- Avoid projecting large blobs or documents.
- Review projected attributes as business requirements evolve.
- Monitor index size using CloudWatch.
- Design projections around actual query responses, not hypothetical future needs.

---

# Common Mistakes

## Always Choosing ALL

Many developers choose ALL for convenience.

This often doubles storage and write costs unnecessarily.

---

## Choosing KEYS_ONLY Without Measuring

Applications may perform an additional table read for every query, increasing latency.

Always measure end-to-end performance.

---

## Projecting Large Attributes

Avoid projecting:

- Images
- PDFs
- JSON documents
- Binary files

These dramatically increase index size.

---

## Ignoring Future Growth

An index that is inexpensive today may become costly after billions of writes.

Projection decisions should account for long-term scale.

---

# Projection Type Comparison

| Feature | KEYS_ONLY | INCLUDE | ALL |
|----------|-----------|----------|-----|
| Required Keys | ✅ | ✅ | ✅ |
| Selected Attributes | ❌ | ✅ | ✅ |
| All Attributes | ❌ | ❌ | ✅ |
| Storage Cost | Lowest | Medium | Highest |
| Write Cost | Lowest | Medium | Highest |
| Query Performance | Lowest | High | Highest |
| Additional Table Reads | Often | Sometimes | Rarely |
| Typical Production Usage | Low | Very High | Moderate |

---

# Architecture Perspective

```text
                  Base Table

        +-----------------------------+

        Complete Item

        +-----------------------------+

                 │

        Projection Type

                 │

    ┌────────────┼────────────┐

    ▼            ▼            ▼

KEYS_ONLY     INCLUDE       ALL

Small         Medium        Full Copy

Lowest Cost   Balanced      Highest Cost

                 │

                 ▼

         Secondary Index
```

Projection is the bridge between storage efficiency and query performance.

---

# Production Considerations

Enterprise applications frequently use **INCLUDE** projections because they provide an excellent balance between:

- Query latency
- Storage cost
- Write throughput
- Operational simplicity

**KEYS_ONLY** is popular for workflow engines and queue processing where identifiers are sufficient.

**ALL** projections are generally reserved for small items or read-heavy workloads where avoiding additional table lookups justifies the increased storage and write costs.

---

# Interview Notes

A common interview question is:

> **What are the three DynamoDB projection types?**

The three projection types are **KEYS_ONLY**, **INCLUDE**, and **ALL**, which determine which attributes from the base table are copied into a secondary index.

Another common question is:

> **Which projection type is most commonly used in production?**

**INCLUDE** is the most common because it balances storage efficiency with query performance by projecting only the attributes required by the application.

Another common question is:

> **When should you use KEYS_ONLY instead of ALL?**

Use **KEYS_ONLY** when the application only needs identifiers from the index and can retrieve the complete item from the base table later. This minimizes storage and write costs.

---

# Key Takeaways

- Projection types determine which attributes are copied into a secondary index.
- DynamoDB supports **KEYS_ONLY**, **INCLUDE**, and **ALL** projections.
- **KEYS_ONLY** minimizes storage and write costs but often requires additional table reads.
- **INCLUDE** offers the best balance between cost and performance and is the preferred choice for most production workloads.
- **ALL** provides the fastest index-only reads but significantly increases storage and write overhead.
- Selecting the appropriate projection type is an important optimization decision for scalable DynamoDB architectures.