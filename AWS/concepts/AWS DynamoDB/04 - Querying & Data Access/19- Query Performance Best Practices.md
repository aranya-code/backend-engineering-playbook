# 19 - Query Performance Best Practices

## Overview

One of DynamoDB's biggest strengths is its ability to serve **single-digit millisecond latency** at virtually any scale. However, achieving that level of performance depends heavily on **table design** and **access patterns** rather than simply increasing hardware resources.

Unlike relational databases, where performance tuning often focuses on indexes and query optimization, DynamoDB performance is primarily determined by:

- Partition Key design
- Data distribution
- Access patterns
- Item size
- Read patterns
- Capacity planning

A poorly designed Query can increase:

- Read Capacity Unit (RCU) consumption
- Response latency
- Application costs
- Hot partitions

This chapter discusses the production best practices for designing highly efficient Query operations.

---

# Design Access Patterns First

The biggest performance optimization happens **before** creating the table.

Poor approach:

```text
Create Table

↓

Insert Data

↓

Figure Out Queries Later
```

Recommended approach:

```text
Business Requirements

↓

Identify Access Patterns

↓

Design Primary Keys

↓

Create Table
```

This is known as **Access Pattern Driven Design**, which is fundamental to DynamoDB.

---

# Prefer Query Over Scan

Always prefer:

```text
Query
```

Instead of:

```text
Scan
```

Example:

Poor:

```text
Scan Users Table

↓

Find Customer
```

Better:

```text
Query

PK = CustomerID
```

Query reads only one partition.

Scan reads every partition.

---

# Use High-Cardinality Partition Keys

Partition Keys should distribute traffic evenly.

Good:

```text
CustomerID

OrderID

DeviceID

UserID
```

Poor:

```text
Country

Status

City
```

These values are repeated by many items and can create hot partitions.

---

# Design Composite Sort Keys

Instead of storing unrelated values:

```text
Order001

Order002

Order003
```

Use meaningful Sort Keys.

Example:

```text
ORDER#2026#0001

ORDER#2026#0002

ORDER#2026#0003
```

Benefits:

- Range queries
- Prefix searches
- Chronological sorting

---

# Read Only Required Attributes

Avoid retrieving entire items.

Poor:

```text
Customer Record

↓

5 KB
```

Need:

```text
Customer Name

Email
```

Use:

```text
Projection Expression
```

Benefits:

- Smaller response payload
- Lower network latency
- Faster APIs

---

# Avoid Filter Expressions for Large Datasets

Remember:

```text
Query

↓

Read Items

↓

Filter
```

Filtering happens **after** DynamoDB has already read the items.

Poor:

```text
Query 50,000 Orders

↓

Filter

Status = SHIPPED
```

Better:

Create a:

- GSI
- Better Sort Key
- Sparse Index

---

# Use GSIs for Additional Access Patterns

Instead of:

```text
Scan

↓

Find Orders by Status
```

Create:

```text
GSI

PK = Status
```

Then:

```text
Query GSI
```

This dramatically reduces RCU consumption.

---

# Keep Items Small

Large items increase:

- RCUs
- Network transfer
- Latency

Example:

Poor:

```text
Customer

↓

50 KB Item
```

Better:

```text
Customer Profile

↓

3 KB
```

Store large objects in:

- Amazon S3

Reference them from DynamoDB.

---

# Paginate Large Queries

A Query response is limited to:

```text
1 MB
```

Instead of requesting huge datasets:

```text
Query

↓

1 MB

↓

LastEvaluatedKey

↓

Next Page
```

Applications should implement pagination.

---

# Choose Eventual Consistency When Possible

Eventually consistent reads:

- Lower latency
- Lower cost
- Better throughput

Only use strongly consistent reads when business requirements demand the latest committed data.

---

# Minimize Transactional Reads

Transactions require additional coordination.

Poor:

```text
Every Read

↓

TransactGetItems
```

Better:

```text
Most Reads

↓

Query

↓

GetItem
```

Reserve transactions for critical workflows.

---

# Cache Frequently Read Data

Frequently accessed data should be cached.

Example:

```text
Application

↓

Redis

↓

Cache Hit

↓

Return Data
```

Instead of:

```text
Application

↓

DynamoDB

↓

Every Request
```

Caching reduces:

- RCUs
- Latency
- Costs

---

# Monitor Hot Partitions

Uneven traffic causes:

```text
Partition

↓

High Traffic

↓

Throttle
```

Monitor:

- Consumed RCUs
- Throttled Requests
- CloudWatch metrics

If necessary:

- Redesign Partition Keys
- Apply Write Sharding
- Introduce Distributed Counters

---

# Query Performance Checklist

| Best Practice | Benefit |
|---------------|----------|
| Use Query instead of Scan | Lower RCUs |
| Design good Partition Keys | Even load distribution |
| Use GSIs | Efficient alternate access patterns |
| Keep items small | Lower latency |
| Use Projection Expressions | Reduce payload size |
| Paginate results | Better scalability |
| Cache hot data | Reduce database load |
| Monitor CloudWatch metrics | Detect bottlenecks early |

---

# Internal Query Execution

```text
                 Query Request

                       │

          Locate Partition Key

                       │

             Read Partition

                       │

          Apply Sort Key Range

                       │

      Apply Filter (Optional)

                       │

     Projection Expression

                       │

           Return Results
```

Notice that the Filter Expression is applied **after** reading the data, reinforcing why it should not be relied upon for performance optimization.

---

# SQL Comparison

Relational databases often optimize performance by adding indexes after queries become slow.

```sql
SELECT *
FROM Orders
WHERE CustomerID = 100;
```

Developers may later add:

```sql
CREATE INDEX idx_customer;
```

In DynamoDB:

- Access patterns are identified first.
- Primary Keys and GSIs are designed before the application is built.
- Query performance depends primarily on data modeling rather than query optimization.

---

# Real-World Example — E-commerce

Requirement:

```text
Customer

↓

Recent Orders

↓

Last 30 Days
```

Recommended design:

```text
PK = CustomerID

SK = ORDER#Timestamp
```

Query:

```text
CustomerID

+

BETWEEN

StartDate

EndDate
```

No filtering required.

---

# Real-World Example — IoT

Requirement:

```text
Sensor

↓

Last Hour
```

Design:

```text
PK = SensorID

SK = Timestamp
```

Query:

```text
BETWEEN

StartTime

EndTime
```

Reads only the required sensor data.

---

# Real-World Example — Social Media

Requirement:

```text
User Feed

↓

Latest Posts
```

Design:

```text
PK = UserID

SK = POST#Timestamp
```

Retrieve:

```text
Latest 20 Posts
```

Using:

```text
Limit = 20
```

Avoid retrieving thousands of older posts.

---

# Best Practices

- Design tables around access patterns.
- Prefer Query over Scan.
- Use high-cardinality Partition Keys.
- Keep items small and focused.
- Use Projection Expressions.
- Design GSIs for alternate access patterns.
- Paginate large result sets.
- Cache frequently accessed data.
- Monitor CloudWatch metrics continuously.

---

# Common Mistakes

## Using Scan in Production APIs

Poor:

```text
Scan

↓

Find One Record
```

Always use Query or GetItem whenever possible.

---

## Overusing Filter Expressions

Filters do not reduce RCUs.

If filtering is required frequently, redesign the table or add a GSI.

---

## Large Item Design

Putting hundreds of attributes into one item increases:

- Latency
- RCUs
- Costs

Split infrequently accessed data into separate items or store large binary objects in Amazon S3.

---

## Poor Partition Key Design

Choosing a low-cardinality Partition Key leads to uneven traffic distribution and hot partitions.

Select keys that naturally distribute requests across many partitions.

---

# Architecture Perspective

```text
              Client Request

                    │

            Query Operation

                    │

        Locate Partition Key

                    │

          Read Partition Data

                    │

     Sort Key Evaluation (Optional)

                    │

 Projection & Filtering (Optional)

                    │

           Return Response
```

Well-designed access patterns ensure that DynamoDB reads only the minimum required data, keeping latency low even under heavy load.

---

# Production Considerations

High-performance DynamoDB applications are built around **predictable access patterns**, not complex queries.

Production systems commonly combine:

- Well-designed Partition Keys
- Composite Sort Keys
- GSIs
- Projection Expressions
- Pagination
- Redis or DAX caching
- CloudWatch monitoring

These techniques allow applications to maintain consistent low latency while serving millions of requests per second.

---

# Interview Notes

A common interview question is:

> **What is the single most important factor affecting Query performance in DynamoDB?**

Table design, especially choosing appropriate Partition Keys and modeling access patterns before implementation.

Another common question is:

> **Do Filter Expressions improve Query performance?**

No. DynamoDB reads the matching items first and applies the filter afterward, so Filter Expressions do not reduce RCU consumption.

Another common question is:

> **Why should Query be preferred over Scan?**

Query reads only the relevant partition, while Scan examines every partition in the table, making Query significantly faster and more cost-efficient.

Another common question is:

> **How do you optimize DynamoDB for millions of reads per second?**

Use well-distributed Partition Keys, GSIs, Projection Expressions, pagination, caching (Redis or DAX), and continuous monitoring with CloudWatch.

---

# Key Takeaways

- Query performance in DynamoDB depends primarily on **data modeling**, not query tuning.
- Design access patterns before creating tables.
- Prefer `Query` and `GetItem` over `Scan`.
- Use high-cardinality Partition Keys and meaningful Sort Keys.
- Avoid relying on Filter Expressions for performance.
- Use GSIs, Projection Expressions, pagination, and caching to build scalable, low-latency applications.
- Continuously monitor throughput, latency, and throttling metrics to identify performance bottlenecks before they impact users.