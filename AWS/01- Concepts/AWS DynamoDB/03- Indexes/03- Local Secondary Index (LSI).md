# 03 - Local Secondary Index (LSI)

## Overview

A **Local Secondary Index (LSI)** is a secondary index that allows a DynamoDB table to support **multiple sort orders while keeping the same Partition Key**.

Unlike a Global Secondary Index (GSI), an LSI **shares the Partition Key of the base table** but allows a different Sort Key.

LSIs are particularly useful when:

- You always query within the same partition.
- You need different ways to sort related data.
- Strongly consistent reads are required.
- Multiple ordering strategies are needed for the same entity.

Although LSIs are less commonly used than GSIs, they remain an important feature for specific production workloads.

---

# Why Do We Need LSIs?

Consider an Orders table.

Primary Key:

```text
PK = CustomerID

SK = OrderID
```

Business requirement:

```text
Get Customer Orders
```

Works perfectly.

Later, a new requirement appears:

```text
Show Customer Orders

Sorted By Order Date
```

Current Sort Key:

```text
OrderID
```

cannot provide chronological ordering.

An LSI solves this problem.

---

# What is a Local Secondary Index?

An LSI provides:

- Same Partition Key
- Different Sort Key

Base Table:

```text
PK = CustomerID

SK = OrderID
```

LSI:

```text
PK = CustomerID

SK = OrderDate
```

The customer partition remains the same.

Only the ordering changes.

---

# Why Is It Called "Local"?

The word **Local** means:

The index is restricted to the same partition as the base table.

Example:

```text
Customer#100

│

├── Order 1

├── Order 2

├── Order 3
```

LSI only reorganizes data inside:

```text
Customer#100
```

It cannot create entirely new partitions.

---

# Visual Representation

```text
             Base Table

PK             SK

Customer100    Order001

Customer100    Order002

Customer100    Order003
```

LSI

```text
PK             SK

Customer100    2026-07-01

Customer100    2026-07-10

Customer100    2026-07-22
```

Same customer.

Different ordering.

---

# Example

Suppose an online shopping application.

Table:

```text
PK = CustomerID

SK = OrderID
```

Items:

| Customer | OrderID | OrderDate |
|----------|----------|-----------|
| C100 | O101 | July 2 |
| C100 | O102 | July 15 |
| C100 | O103 | July 20 |

Business requirement:

```text
Show

Latest Orders
```

Create LSI:

```text
PK = CustomerID

SK = OrderDate
```

Query:

```text
Customer

↓

Orders Sorted by Date
```

---

# Another Example

Student grades.

Table:

```text
PK = StudentID

SK = CourseID
```

Requirement:

```text
Show Courses

Sorted by Grade
```

LSI:

```text
PK = StudentID

SK = Grade
```

Now courses can be retrieved in grade order.

---

# Architecture

```text
Application

        │

        ▼

Query Student

        │

        ▼

Local Secondary Index

        │

        ▼

Same Student Partition

        │

        ▼

Sorted Results
```

---

# Shared Partition Key

This is the defining feature.

Base Table:

```text
PK = CustomerID
```

LSI:

```text
PK = CustomerID
```

Never changes.

Only:

```text
Sort Key
```

changes.

---

# Strongly Consistent Reads

Unlike GSIs,

LSIs support:

```text
Strongly Consistent Reads
```

Workflow:

```text
Write

↓

Table Updated

↓

LSI Updated

↓

Strong Read
```

Applications immediately see the latest data.

This makes LSIs useful for workloads where stale data is unacceptable.

---

# LSI Creation Limitation

One important restriction:

LSIs **must be created when the table is created**.

Example:

```text
Create Table

↓

Define LSIs
```

After the table exists:

```text
Cannot Add New LSI
```

Changing an LSI later requires creating a new table and migrating data.

---

# Item Collection

Because LSIs share the Partition Key,

all items with the same key form an **Item Collection**.

Example:

```text
Customer100

│

├── Order001

├── Order002

├── Order003

└── Order004
```

Every LSI works only within this collection.

---

# Item Collection Size Limit

An important limitation of LSIs is the **10 GB Item Collection limit**.

All items sharing the same Partition Key—including the base table and all LSIs—must fit within:

```text
10 GB
```

Example:

```text
Customer100

↓

Orders

↓

Invoices

↓

Payments

↓

Reviews
```

Everything together must remain below the limit.

This restriction is one reason GSIs are often preferred for large-scale workloads.

---

# Query Examples

Without LSI:

```text
Customer

↓

Orders

↓

OrderID Order
```

With LSI:

```text
Customer

↓

Orders

↓

Date Order
```

or

```text
Customer

↓

Orders

↓

Highest Value First
```

depending on the chosen Sort Key.

---

# Comparison Example

Base Table:

```text
PK = CustomerID

SK = OrderID
```

LSI 1

```text
PK = CustomerID

SK = OrderDate
```

LSI 2

```text
PK = CustomerID

SK = TotalAmount
```

Same customer.

Different sorting methods.

---

# Capacity

Unlike GSIs,

LSIs share the throughput capacity of the base table.

Writes affect:

```text
Base Table

↓

LSI
```

Capacity planning should consider both.

---

# Real-World Example

A banking application stores transactions.

Base table:

```text
PK = AccountID

SK = TransactionID
```

Business requirements:

- Latest transactions
- Largest transactions
- Transactions by posting date

LSIs:

```text
AccountID + PostingDate
```

```text
AccountID + Amount
```

Customers can retrieve the same account data using different sort orders without scanning.

---

# Benefits

LSIs provide:

- Multiple sort orders
- Strong consistency
- Efficient queries
- Shared partition organization
- Low-latency retrieval

---

# Limitations

LSIs have several constraints:

- Must be created with the table
- Cannot change the Partition Key
- 10 GB Item Collection limit
- Maximum of 5 LSIs per table
- Less flexible than GSIs

---

# Best Practices

- Use LSIs only when the Partition Key should remain unchanged.
- Design LSIs during initial table creation.
- Keep item collections well below the 10 GB limit.
- Use LSIs when strong consistency is required.
- Monitor partition growth for large tenants or entities.
- Prefer GSIs when future schema flexibility is important.

---

# Common Mistakes

## Choosing an LSI Instead of a GSI

If the query requires a different Partition Key,

an LSI cannot help.

Use a GSI instead.

---

## Ignoring the 10 GB Limit

Large item collections can exceed LSI limits.

Monitor storage growth carefully.

---

## Forgetting Table Creation Constraints

LSIs cannot be added later.

Plan index requirements before deployment.

---

## Using LSIs for Cross-Partition Queries

LSIs only reorganize items within the same partition.

They cannot support global searches.

---

# SQL Index vs LSI

| Feature | SQL Index | DynamoDB LSI |
|----------|-----------|--------------|
| Partition Key | N/A | Same as Base Table |
| Sort Order | Flexible | Different Sort Key |
| Creation | Anytime | Only at Table Creation |
| Strong Consistency | Yes | Yes |
| Scope | Entire Table | Single Partition |
| Maximum | Database-dependent | 5 per Table |

---

# Architecture Perspective

```text
                 Application

                      │

                      ▼

            Query Customer Orders

                      │

                      ▼

          Local Secondary Index

                      │

                      ▼

           Customer Partition

                      │

      ┌───────────────┴───────────────┐

      ▼                               ▼

Order by Date                 Order by Amount

                      │

                      ▼

             Application Response
```

The LSI provides multiple sorted views of data within the same partition while maintaining strong consistency.

---

# Production Considerations

Although LSIs are less common than GSIs, they are valuable in workloads where:

- Queries always target a single partition.
- Immediate consistency is required.
- Data volume per partition remains well below the 10 GB limit.
- Multiple sort orders are frequently needed.

Many modern applications favor GSIs because they are more flexible and can be added after deployment. However, LSIs remain a strong choice for specialized use cases with predictable access patterns.

---

# Interview Notes

A common interview question is:

> **What is a Local Secondary Index?**

A Local Secondary Index is a secondary index that shares the base table's Partition Key but uses a different Sort Key, allowing multiple sort orders within the same partition.

Another common question is:

> **What are the biggest limitations of an LSI?**

LSIs must be created when the table is created, cannot change the Partition Key, support a maximum of five LSIs per table, and are subject to the 10 GB item collection limit.

Another common question is:

> **When would you choose an LSI over a GSI?**

Choose an LSI when queries always use the same Partition Key, require different sort orders, and need strongly consistent reads. If a different Partition Key is required or future flexibility is important, a GSI is usually the better choice.

---

# Key Takeaways

- A Local Secondary Index (LSI) shares the base table's Partition Key while providing an alternate Sort Key.
- LSIs are ideal for supporting multiple sort orders within the same partition.
- They support strongly consistent reads, unlike GSIs.
- LSIs must be created during table creation and cannot be added later.
- Item collections using LSIs are limited to 10 GB and tables can have a maximum of five LSIs.
- LSIs are best suited for predictable, partition-scoped access patterns where consistency is critical.