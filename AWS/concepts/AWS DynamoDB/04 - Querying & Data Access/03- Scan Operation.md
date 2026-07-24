# 03 - Scan Operation

## Overview

The **Scan** operation reads **every item** in a DynamoDB table or secondary index before returning the matching results.

Unlike the **Query** operation, which directly locates data using a Partition Key, a Scan has **no knowledge of where the required data resides**.

As a result, Scan is:

- Slower
- More expensive
- Less scalable
- Higher latency
- More resource intensive

For these reasons, **Scan should rarely be used in production APIs**.

Instead, it is primarily intended for:

- Administrative tasks
- Analytics
- Data migration
- Background processing
- ETL pipelines

---

# What is a Scan?

A Scan operation sequentially examines every item stored in a table or index.

Example:

```text
Orders Table

100 Million Items
```

Application:

```text
Find

Orders

Greater Than

$1000
```

Without an appropriate key or index:

```text
Scan
```

Workflow:

```text
Read Every Item

↓

Evaluate Condition

↓

Return Matching Items
```

---

# Internal Architecture

```text
                  Application

                        │

                        ▼

                 Scan Request

                        │

                        ▼

          Read Partition 1

                        │

                        ▼

          Read Partition 2

                        │

                        ▼

          Read Partition 3

                        │

                        ▼

          ...

                        │

                        ▼

          Read Partition N

                        │

                        ▼

             Apply Filters

                        │

                        ▼

             Return Results
```

Unlike Query, DynamoDB cannot jump directly to the required partition.

---

# Why Scan is Expensive

Imagine a table with:

```text
500 Million Items
```

Application needs:

```text
One Customer
```

Without an index:

```text
Scan

↓

500 Million Reads

↓

One Result
```

Most of the work performed by DynamoDB is unnecessary.

---

# SQL Comparison

SQL:

```sql
SELECT *
FROM Orders
WHERE Amount > 1000;
```

A relational database may:

- Use an index
- Perform an optimized scan
- Build execution plans

DynamoDB:

Without an appropriate key:

```text
Scan Entire Table
```

---

# Scan vs Query

Query:

```text
Know Partition Key

↓

Read One Partition
```

Scan:

```text
No Partition Key

↓

Read Every Partition
```

---

# Capacity Consumption

Suppose:

Table size:

```text
20 Million Items
```

Application needs:

```text
15 Records
```

Query:

```text
Reads

15 Records
```

Scan:

```text
Reads

20 Million Records
```

Even though only 15 records are returned.

---

# Filter Expressions

Many developers assume:

```text
Scan

+

Filter

↓

Cheap
```

Reality:

```text
Read Every Item

↓

Apply Filter

↓

Discard Most Results
```

The filter is applied **after** the data is read.

Capacity consumption remains unchanged.

---

# Example

Table:

```text
Employees

1 Million Records
```

Need:

```text
Department = HR
```

Workflow:

```text
Scan

↓

1 Million Reads

↓

Filter

↓

200 Employees
```

---

# Better Solution

Create a GSI:

```text
PK = Department
```

Now:

```text
Query HR

↓

200 Reads
```

instead of:

```text
1 Million Reads
```

---

# Scan Pagination

Large scans are paginated.

Example:

```text
Scan

↓

1 MB

↓

LastEvaluatedKey

↓

Next Scan

↓

Next 1 MB
```

Applications continue until the table has been fully scanned.

---

# Parallel Scan

Large tables support Parallel Scan.

Instead of:

```text
Worker 1

↓

Entire Table
```

DynamoDB allows:

```text
Worker 1

↓

Segment 1
```

```text
Worker 2

↓

Segment 2
```

```text
Worker 3

↓

Segment 3
```

Each worker scans a different segment.

---

# Parallel Scan Architecture

```text
                 Table

      ┌─────────┼─────────┐

      ▼         ▼         ▼

 Segment 1  Segment 2  Segment 3

      ▼         ▼         ▼

 Worker 1  Worker 2  Worker 3

      └─────────┼─────────┘

                ▼

         Combined Results
```

Parallel Scan improves throughput but **does not reduce the total amount of data read**.

---

# Scanning Secondary Indexes

Scan can also operate on:

- Global Secondary Indexes
- Local Secondary Indexes

Example:

```text
Status GSI

↓

Scan

↓

Every Indexed Item
```

Although smaller than scanning the base table, it is still less efficient than a Query.

---

# Scan Performance

Performance depends on:

- Table size
- Item size
- Capacity mode
- Available throughput

Small tables:

```text
Fast
```

Large production tables:

```text
Potentially Minutes
```

---

# Real-World Example — Data Export

Requirement:

```text
Export Entire Orders Table
```

Workflow:

```text
Scan

↓

Every Order

↓

CSV Export
```

This is an appropriate use of Scan.

---

# Real-World Example — Data Migration

Migrating:

```text
Old Table

↓

New Table
```

Workflow:

```text
Scan Old Table

↓

Transform Data

↓

Write New Table
```

Scan is ideal because every record must be processed.

---

# Real-World Example — Background Analytics

Nightly job:

```text
Calculate Sales

For Entire Year
```

Workflow:

```text
Scan

↓

Aggregate

↓

Dashboard
```

Because the workload runs offline, Scan is acceptable.

---

# When Scan is Appropriate

Use Scan for:

- Full data export
- Data migration
- ETL pipelines
- Background analytics
- Administrative maintenance
- One-time cleanup jobs

---

# When Scan Should Be Avoided

Avoid Scan for:

- Customer dashboards
- Login systems
- Mobile applications
- REST APIs
- Real-time search
- High-traffic services

These should rely on Query operations.

---

# Query vs Scan

| Feature | Query | Scan |
|----------|-------|------|
| Requires Partition Key | ✅ | ❌ |
| Reads Entire Table | ❌ | ✅ |
| Supports Sort Key Conditions | ✅ | ❌ |
| Uses Index Efficiently | ✅ | ❌ |
| Capacity Consumption | Low | High |
| Performance | Excellent | Poor on Large Tables |
| Production APIs | Recommended | Avoid |

---

# Architecture Perspective

```text
                     Application

                           │

                Need Customer Data

                           │

          ┌────────────────┴────────────────┐

          ▼                                 ▼

       Query                            Scan

          │                                 │

          ▼                                 ▼

 Locate Correct Partition        Read Every Partition

          │                                 │

          ▼                                 ▼

   Read Matching Items         Read Entire Dataset

          │                                 │

          ▼                                 ▼

     Fast Response             Slow & Expensive
```

The Scan operation sacrifices efficiency because it has no direct path to the required data.

---

# Best Practices

- Prefer Query over Scan whenever possible.
- Design tables and indexes around access patterns.
- Use Parallel Scan only for large offline workloads.
- Paginate large Scan operations.
- Monitor Scan usage in CloudWatch.
- Replace frequent Scan operations with GSIs.
- Schedule large scans during off-peak hours.

---

# Common Mistakes

## Using Scan in REST APIs

A Scan may perform adequately during development but becomes a serious bottleneck as the table grows.

---

## Assuming Filters Reduce Cost

Filters reduce the number of returned items—not the number of items read.

---

## Ignoring Parallel Scan Limitations

Parallel Scan improves speed but still reads the entire dataset and consumes the same overall read capacity.

---

## Repeatedly Scanning Large Tables

If an application repeatedly performs Scans, it is usually a sign that the data model or indexing strategy needs improvement.

---

# Production Considerations

Large organizations generally avoid Scan operations in customer-facing applications.

Instead, Scan is reserved for:

- Scheduled ETL jobs
- Data lake exports
- Compliance reporting
- Disaster recovery validation
- Data quality checks
- One-time migration tasks

Production monitoring often includes alerts for unexpected Scan activity, as this can indicate inefficient application design or missing secondary indexes.

---

# Interview Notes

A common interview question is:

> **Why is Scan considered expensive in DynamoDB?**

Because Scan reads every item in the table or index regardless of how many items actually match the requested condition, consuming significantly more read capacity than a Query.

Another common question is:

> **When is it acceptable to use Scan?**

For offline workloads such as data migration, analytics, backups, ETL pipelines, and administrative maintenance where reading the entire dataset is expected.

Another common question is:

> **Does a Filter Expression make a Scan more efficient?**

No. DynamoDB reads all items first and then applies the filter, so Filter Expressions do not reduce read capacity consumption.

---

# Key Takeaways

- Scan sequentially reads every item in a table or index.
- It is significantly slower and more expensive than Query for large datasets.
- Filter Expressions reduce returned results but not the number of items read.
- Parallel Scan improves execution time but not total read capacity consumption.
- Production applications should rely on Query operations and well-designed secondary indexes instead of Scan whenever possible.
```