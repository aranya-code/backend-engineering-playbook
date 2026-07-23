# 04 - GSI vs LSI

## Overview

One of the most common DynamoDB interview questions is:

> **What is the difference between a Global Secondary Index (GSI) and a Local Secondary Index (LSI)?**

Although both are secondary indexes that provide additional query capabilities, they are designed for **different architectural purposes**.

Choosing the wrong index can result in:

- Unnecessary costs
- Poor scalability
- Hot partitions
- Limited flexibility
- Future schema migrations

Understanding when to use a GSI versus an LSI is a fundamental DynamoDB design skill.

---

# High-Level Comparison

A GSI creates a completely new access path using a different Primary Key.

An LSI keeps the same Partition Key but allows a different Sort Key.

Think of it like this:

```text
Base Table

↓

Primary Key
```

GSI:

```text
Completely New Primary Key
```

LSI:

```text
Same Partition Key

↓

Different Sort Key
```

---

# Visual Representation

Base Table

```text
PK = CustomerID

SK = OrderID
```

GSI

```text
PK = Email

SK = CreatedDate
```

LSI

```text
PK = CustomerID

SK = OrderDate
```

Notice:

The GSI changes both keys.

The LSI changes only the Sort Key.

---

# Internal Architecture

## Global Secondary Index

```text
Application

        │

        ▼

      GSI

        │

        ▼

Independent Partitioning

        │

        ▼

Base Table
```

The GSI has its own partition layout.

---

## Local Secondary Index

```text
Application

        │

        ▼

      LSI

        │

        ▼

Same Partition

        │

        ▼

Base Table
```

The LSI stays inside the existing partition.

---

# Partition Key

## GSI

Can use:

```text
Email
```

or

```text
Department
```

or

```text
Country
```

Anything.

---

## LSI

Must always use:

```text
Same Partition Key

As Base Table
```

No exceptions.

---

# Sort Key

## GSI

May define:

```text
Optional Sort Key
```

Example:

```text
PK = Department

SK = JoiningDate
```

---

## LSI

Also allows:

```text
Different Sort Key
```

Example:

```text
PK = CustomerID

SK = OrderDate
```

---

# Creation Time

## GSI

Can be created:

```text
Before Deployment

OR

After Deployment
```

You can add a GSI to an existing table.

---

## LSI

Must be defined:

```text
During

Create Table
```

After table creation:

```text
Impossible
```

without recreating the table.

---

# Partitioning

## GSI

Uses:

```text
Own Partitions
```

Hashing:

```text
Email

↓

Hash

↓

Partition
```

Independent of the base table.

---

## LSI

Uses:

```text
Existing Partition
```

No repartitioning occurs.

---

# Consistency

## GSI

Supports:

```text
Eventually Consistent Reads
```

Updates propagate asynchronously.

---

## LSI

Supports:

```text
Strongly Consistent Reads
```

Applications immediately see committed updates.

---

# Capacity

## GSI

Has its own:

- Read Capacity
- Write Capacity

(or shares on-demand scaling independently)

Each write to the table may also consume write capacity on every affected GSI.

---

## LSI

Shares the throughput of the base table.

Reads and writes consume the same table capacity.

---

# Storage

## GSI

Stores:

Projected attributes

inside a completely separate index.

Additional storage:

```text
Yes
```

---

## LSI

Also stores projected attributes,

but inside the same partition's item collection.

---

# Item Collection Limit

## GSI

No item collection limit.

Scales with table.

---

## LSI

Subject to:

```text
10 GB

Per Partition Key
```

This is one of the biggest limitations of LSIs.

---

# Maximum Number

## GSI

Currently:

```text
Up to 20 GSIs

Per Table
```

(Default AWS service quota; can be increased in some cases.)

---

## LSI

Maximum:

```text
5 LSIs

Per Table
```

Cannot be increased.

---

# Example 1

Users Table

```text
PK = UserID
```

Need:

```text
Find User

By Email
```

Solution:

```text
GSI

PK = Email
```

An LSI cannot help because:

```text
Partition Key Changes
```

---

# Example 2

Orders Table

```text
PK = CustomerID

SK = OrderID
```

Need:

```text
Latest Orders

For Customer
```

Solution:

```text
LSI

PK = CustomerID

SK = OrderDate
```

Same partition.

Different ordering.

---

# Example 3

Banking System

Need:

```text
Find Account

By Account Number
```

Primary key already uses:

```text
CustomerID
```

Solution:

```text
GSI
```

because:

```text
Different Partition Key
```

---

# Example 4

E-commerce

Need:

```text
Show Customer Purchases

Sorted

By Total Amount
```

Partition:

```text
CustomerID
```

Sorting:

```text
TotalAmount
```

Solution:

```text
LSI
```

---

# Feature Comparison

| Feature | GSI | LSI |
|----------|-----|-----|
| Partition Key | Different | Same as Base Table |
| Sort Key | Optional | Different Sort Key |
| Created Later | ✅ Yes | ❌ No |
| Strong Consistency | ❌ No | ✅ Yes |
| Eventual Consistency | ✅ Yes | ✅ Yes |
| Item Collection Limit | None | 10 GB |
| Independent Partitioning | ✅ Yes | ❌ No |
| Maximum per Table | 20 | 5 |
| Most Common Choice | ✅ Yes | Less Common |

---

# Performance Comparison

## Read Performance

Both provide:

- Low latency
- Efficient Query operations

Performance differences are usually negligible.

The design constraints matter far more.

---

## Write Performance

Every write updates:

```text
Base Table

↓

Indexes
```

More indexes:

```text
More Write Cost
```

Both GSIs and LSIs increase write overhead.

---

# Flexibility

## GSI

Highly flexible.

Supports:

- New business requirements
- Schema evolution
- New access patterns

Years after deployment.

---

## LSI

Rigid.

If requirements change:

```text
New Table

↓

Migration
```

may be required.

---

# Cost Considerations

GSI:

- Additional storage
- Additional write capacity
- Additional operational monitoring

LSI:

- Shares table capacity
- Still increases storage
- No separate capacity planning

Neither index is "free."

---

# When to Choose a GSI

Use a GSI when:

- You need a different Partition Key.
- New access patterns may appear later.
- Data spans multiple partitions.
- Scalability is the highest priority.
- You need maximum flexibility.

This is the most common production choice.

---

# When to Choose an LSI

Use an LSI when:

- Queries always stay within one partition.
- You need multiple sort orders.
- Strongly consistent reads are required.
- The item collection remains below 10 GB.
- The access pattern is known before deployment.

---

# Real-World Example

A ride-sharing application stores trips.

Base Table:

```text
PK = DriverID

SK = TripID
```

Business requirements:

```text
Trips by Driver

Sorted by Date
```

LSI:

```text
PK = DriverID

SK = TripDate
```

Another requirement:

```text
Find Driver

By Email
```

Requires:

```text
GSI

PK = Email
```

Both indexes solve different problems.

---

# Best Practices

- Prefer GSIs for new application features.
- Use LSIs only when their unique capabilities are required.
- Design LSIs before creating the table.
- Choose high-cardinality GSI partition keys.
- Monitor index usage in CloudWatch.
- Remove unused GSIs to reduce cost.

---

# Common Mistakes

## Using an LSI When the Partition Key Must Change

LSIs cannot change the Partition Key.

Use a GSI.

---

## Ignoring the 10 GB Limit

Large tenants or customers can exceed the LSI item collection limit.

---

## Adding Too Many GSIs

Every GSI increases:

- Storage
- Write cost
- Operational complexity

---

## Assuming GSIs Support Strong Consistency

Only LSIs support strongly consistent reads.

Applications requiring immediate consistency should query the base table or use an LSI where appropriate.

---

# Architecture Perspective

```text
                     Base Table

            PK = CustomerID

            SK = OrderID

                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼

      LSI                   GSI

PK = CustomerID       PK = Email

SK = OrderDate        SK = CreatedDate

        │                     │
        ▼                     ▼

Strong Consistency     Eventual Consistency

Same Partition         Independent Partition
```

The LSI extends the existing partition with alternate sort orders, while the GSI creates an entirely new access path with independent partitioning.

---

# Production Considerations

In modern cloud-native applications:

- **GSIs are the default choice** because they provide flexibility and can be added after deployment.
- **LSIs are used selectively** for workloads that require strong consistency and alternate sort orders within the same partition.

Large enterprise systems often have:

- 5–15 GSIs
- Zero or very few LSIs

This reflects the greater flexibility and scalability of GSIs.

---

# Interview Notes

A common interview question is:

> **What is the biggest difference between a GSI and an LSI?**

A GSI uses its own Partition Key and optional Sort Key, allowing completely new access patterns. An LSI shares the base table's Partition Key but provides a different Sort Key for alternate ordering within the same partition.

Another common question is:

> **Why are GSIs more commonly used than LSIs?**

GSIs can be created after table creation, support different partition keys, scale independently, and are not constrained by the 10 GB item collection limit, making them much more flexible.

Another common question is:

> **When should you choose an LSI?**

Choose an LSI when all queries remain within the same partition, multiple sort orders are needed, strong consistency is required, and the access pattern is known before the table is created.

---

# Key Takeaways

- GSIs and LSIs both provide alternate query paths but solve different problems.
- GSIs support different Partition Keys and can be added after deployment.
- LSIs share the base table's Partition Key and support alternate Sort Keys.
- LSIs provide strongly consistent reads but are limited by a 10 GB item collection size and must be created with the table.
- GSIs are the preferred choice for most production applications because of their flexibility and scalability.
- Choosing the correct index type is a key architectural decision that impacts performance, cost, and future maintainability.