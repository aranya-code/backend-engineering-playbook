# 04 - Querying & Performance

## Overview

Query performance is one of the most common discussion topics in senior DynamoDB interviews.

Interviewers often present a scenario such as:

> "Your DynamoDB API suddenly becomes slow. How would you troubleshoot it?"

This chapter focuses on how DynamoDB retrieves data, the performance implications of different operations, and how experienced backend engineers optimize production workloads.

---

# Learning Objectives

After completing this chapter, you'll be able to answer interview questions about:

- Query vs Scan
- Performance optimization
- Capacity consumption
- Pagination
- Projection Expressions
- Filter Expressions
- Strong vs Eventual consistency
- Hot partitions
- Performance troubleshooting

---

# Question 1

## What is the difference between Query and Scan?

### Expected Answer

A **Query** retrieves items using the table's partition key (and optionally the sort key).

A **Scan** reads every item in the table.

Query:

```text
Partition

↓

Matching Items
```

Scan:

```text
Entire Table

↓

Every Item
```

---

## Interview Tip

Always say:

> "Query is the preferred operation in production."

---

# Question 2

## Why should Scan be avoided?

### Expected Answer

Scan:

- Reads the full table
- Consumes large amounts of RCUs
- Increases latency
- Doesn't scale well

For large tables:

```text
100 Million Items

↓

Scan

↓

Very Expensive
```

Instead, design access patterns that support Query.

---

# Question 3

## Does Query scan the entire partition?

### Expected Answer

No.

A Query efficiently retrieves items matching the partition key and optional sort key conditions.

It does **not** scan unrelated partitions.

---

# Question 4

## How do you retrieve a single item?

### Expected Answer

Use:

```text
GetItem
```

Requires:

- Partition Key
- Sort Key (if applicable)

---

## Why?

GetItem is the fastest retrieval operation for a known primary key.

---

# Question 5

## When would you use BatchGetItem?

### Expected Answer

When retrieving multiple known items.

Instead of:

```text
100

GetItem Calls
```

Use:

```text
BatchGetItem
```

Benefits:

- Fewer network calls
- Better throughput
- Lower latency

---

# Question 6

## What is a Filter Expression?

### Expected Answer

A Filter Expression filters results **after** DynamoDB reads the data.

Workflow:

```text
Query

↓

100 Items Read

↓

Filter

↓

10 Returned
```

RCUs are consumed for all 100 items.

---

## Interview Tip

Filtering does **not** reduce read capacity consumption.

---

# Question 7

## What is a Projection Expression?

### Expected Answer

Projection Expressions return only required attributes.

Example:

Instead of:

```text
Entire Customer Record
```

Return:

```text
Name

Email
```

Benefits:

- Smaller responses
- Lower network usage
- Faster serialization

---

# Question 8

## Does Projection Expression reduce RCUs?

### Expected Answer

Not necessarily.

Projection Expressions primarily reduce:

- Network transfer
- Response size
- Application processing

Read capacity depends primarily on the amount of data read from storage.

---

# Question 9

## What is pagination?

### Expected Answer

DynamoDB returns up to:

```text
1 MB
```

per Query or Scan request.

If more data exists:

```text
Page 1

↓

LastEvaluatedKey

↓

Page 2
```

Applications must continue querying until `LastEvaluatedKey` is absent.

---

# Question 10

## What is LastEvaluatedKey?

### Expected Answer

It identifies where DynamoDB stopped reading.

The client sends it back as:

```text
ExclusiveStartKey
```

to retrieve the next page.

---

# Question 11

## What is the difference between strong and eventual consistency?

### Expected Answer

Strongly consistent read:

```text
Write

↓

Read

↓

Latest Value
```

Eventually consistent read:

```text
Write

↓

Read

↓

Possibly Older Value

↓

Replica Synchronizes
```

Eventually consistent reads are the default.

---

# Question 12

## Which is faster: strong or eventual consistency?

### Expected Answer

Eventually consistent reads generally provide:

- Higher throughput
- Better scalability
- Lower cost per read

Strong consistency should only be used when applications require the most recent committed data.

---

# Question 13

## What causes slow DynamoDB queries?

### Expected Answer

Common causes:

- Scan operations
- Hot partitions
- Large items
- Poor partition key
- Missing GSI
- Network latency
- Application bottlenecks

---

# Question 14

## What is a hot partition?

### Expected Answer

A hot partition occurs when one partition receives disproportionately high traffic.

Example:

```text
Trending Product

↓

Millions of Reads

↓

Single Partition

↓

Throttle
```

---

# Question 15

## How would you optimize DynamoDB performance?

### Expected Answer

Typical optimizations include:

- Replace Scan with Query
- Improve partition keys
- Add GSIs
- Cache frequently accessed data
- Reduce item size
- Use Projection Expressions
- Monitor CloudWatch metrics

---

# Question 16

## How do you retrieve recent orders for a customer?

### Expected Answer

Example:

Partition Key:

```text
CUSTOMER#100
```

Sort Key:

```text
OrderDate
```

Query:

```text
Customer

↓

Sort Descending

↓

Latest Orders
```

---

# Question 17

## How do you troubleshoot high latency?

### Expected Answer

Investigation:

```text
Application

↓

CloudWatch

↓

Query or Scan?

↓

Hot Partition?

↓

Network?

↓

Application Code?
```

Review:

- Latency metrics
- Throttling
- Capacity
- Logs

---

# Question 18

## Does DynamoDB performance degrade as tables grow?

### Expected Answer

No.

Performance depends on:

- Access patterns
- Partition design
- Item size

—not total table size.

---

# Question 19

## How would you design a table for high throughput?

### Expected Answer

Use:

- High-cardinality partition keys
- Even traffic distribution
- Small items
- Query-based access
- Appropriate GSIs
- Auto Scaling or On-Demand capacity

---

# Question 20

## Explain DynamoDB query optimization in one minute.

### Sample Answer

> DynamoDB performance depends primarily on table design rather than database size. Production workloads should rely on Query instead of Scan, use well-distributed partition keys, keep items reasonably small, design GSIs for additional access patterns, and monitor CloudWatch metrics for throttling and latency. Caching frequently accessed data and using Projection Expressions where appropriate further improve overall application performance.

---

# Rapid Fire Questions

| Question | Short Answer |
|-----------|--------------|
| Fastest read operation? | GetItem |
| Preferred operation? | Query |
| Avoid in production? | Scan |
| Pagination limit? | 1 MB |
| Pagination token? | LastEvaluatedKey |
| Filter before read? | No |
| Projection Expression? | Return fewer attributes |
| Default consistency? | Eventual |
| Strong consistency on GSI? | No |
| Performance depends on table size? | No |

---

# Senior Interview Tips

A strong candidate discusses:

- Access patterns
- Capacity planning
- Cost optimization
- CloudWatch metrics
- Hot partitions
- Caching strategies
- Trade-offs between consistency and performance

Avoid answers like:

> "Just increase capacity."

Instead explain:

> "I would first determine whether the bottleneck is due to poor data modeling, hot partitions, Scan operations, or application behavior before scaling capacity."

---

# Common Mistakes

## Using Scan for APIs

Production APIs should almost always use:

```text
Query
```

instead of:

```text
Scan
```

---

## Ignoring Pagination

Many developers assume a Query returns every item.

It returns up to:

```text
1 MB
```

per request.

---

## Misunderstanding Filter Expressions

Filtering occurs after data has already been read and therefore does not reduce read capacity consumption.

---

## Assuming More Capacity Solves Everything

Poor partition-key design can continue causing throttling even after increasing RCUs or WCUs.

---

# Interview Cheat Sheet

```text
Access Pattern

↓

Query

↓

Partition Key

↓

Sort Key

↓

Projection Expression

↓

Pagination

↓

CloudWatch

↓

Performance Optimization
```

---

# Key Takeaways

- Query operations are the foundation of efficient DynamoDB applications, while Scan should be reserved for exceptional cases.
- Performance depends far more on data modeling and access patterns than on table size.
- Projection Expressions, pagination, proper partition-key selection, and caching all contribute to scalable, low-latency systems.
- Strong interview answers emphasize trade-offs, troubleshooting methodology, and production optimization strategies rather than simply describing API operations.
- Senior engineers investigate root causes such as hot partitions, inefficient queries, and poor schema design before attempting to scale capacity.