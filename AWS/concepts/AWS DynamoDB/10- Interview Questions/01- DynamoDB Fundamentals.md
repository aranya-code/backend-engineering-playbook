# 01 - DynamoDB Fundamentals

## Overview

This chapter contains senior-level interview questions covering the core concepts of Amazon DynamoDB.

Unlike documentation, these questions focus on **how interviewers evaluate your understanding**. Senior backend interviews typically emphasize:

- Internal architecture
- Design decisions
- Production trade-offs
- Scalability
- Performance
- Real-world experience

For every question, try answering it yourself before reading the explanation.

---

# Learning Objectives

After completing this chapter, you'll be able to answer interview questions about:

- DynamoDB architecture
- Primary keys
- Partitions
- Capacity
- Scaling
- Performance
- Internal workings
- Production considerations

---

# Question 1

## What is Amazon DynamoDB?

### Expected Answer

Amazon DynamoDB is a fully managed, serverless NoSQL database provided by AWS that delivers single-digit millisecond latency at virtually any scale.

Unlike traditional relational databases, DynamoDB distributes data across multiple partitions automatically and removes the need to manage:

- Servers
- Replication
- Storage
- Operating systems
- Scaling
- High availability

It is designed for applications requiring predictable performance under massive workloads.

---

## What Interviewers Expect

A senior engineer should explain **why DynamoDB exists**, not just what it is.

Good answer:

> "DynamoDB is optimized for horizontally scalable workloads where predictable latency is more important than relational features like joins."

---

# Question 2

## Why would you choose DynamoDB instead of PostgreSQL?

### Expected Answer

Choose DynamoDB when:

- Massive scale is required
- Extremely low latency is needed
- Access patterns are known
- Horizontal scaling is important
- High availability is critical

Choose PostgreSQL when:

- Complex joins
- ACID transactions across many tables
- Complex reporting
- Ad-hoc queries
- Rich relational modeling

are more important.

---

## Senior Discussion

Never say:

> DynamoDB is better.

Instead explain:

> Both databases solve different problems.

---

# Question 3

## Is DynamoDB SQL or NoSQL?

### Expected Answer

DynamoDB is a NoSQL key-value and document database.

It stores data as items rather than relational rows.

Relationships are modeled through access patterns rather than joins.

---

## Follow-up Question

Does DynamoDB support SQL?

Answer:

Partially.

It supports **PartiQL**, but internally DynamoDB remains a NoSQL database.

---

# Question 4

## Explain DynamoDB's partitioning mechanism.

### Expected Answer

Data is distributed across physical partitions based on the partition key.

```text
Partition Key

↓

Hash Function

↓

Physical Partition
```

Each partition has throughput limits.

A good partition key evenly distributes traffic.

---

## Interview Tip

Mention:

- Hashing
- Even distribution
- Horizontal scaling
- Hot partitions

These are keywords interviewers expect.

---

# Question 5

## What is a partition key?

### Expected Answer

The partition key determines:

- Where an item is stored
- Which partition receives requests
- Traffic distribution

A good partition key has:

- High cardinality
- Even request distribution
- Stable values

---

## Bad Example

```text
status

OPEN

CLOSED
```

Only a few partition values.

---

## Better Example

```text
customer_id
```

Millions of possible values.

---

# Question 6

## What is a sort key?

### Expected Answer

The sort key organizes items sharing the same partition key.

Example:

```text
Customer

↓

Orders

↓

Sorted by Date
```

This enables efficient range queries.

---

# Question 7

## Explain horizontal scaling in DynamoDB.

### Expected Answer

Unlike relational databases that often scale vertically, DynamoDB automatically adds partitions as storage and traffic increase.

```text
More Traffic

↓

More Partitions

↓

More Capacity
```

Applications generally do not manage this process.

---

# Question 8

## What is eventual consistency?

### Expected Answer

After writing data, replicas may take a short time to synchronize.

During this period:

```text
Write

↓

Replica Update

↓

Eventually Consistent Read
```

A read may temporarily return older data.

---

## Follow-up

Can DynamoDB perform strongly consistent reads?

Yes.

Strongly consistent reads are supported on the base table and Local Secondary Indexes (LSIs), but **not** on Global Secondary Indexes (GSIs).

---

# Question 9

## What causes hot partitions?

### Expected Answer

Hot partitions occur when a large percentage of requests target the same partition key.

Example:

```text
Product

↓

Trending

↓

Millions of Reads

↓

Single Partition
```

Result:

- Throttling
- Increased latency
- Reduced throughput

---

# Question 10

## Explain adaptive capacity.

### Expected Answer

Adaptive Capacity automatically shifts throughput toward busy partitions.

Benefits:

- Handles uneven traffic
- Reduces throttling
- Improves availability

It helps mitigate imbalance but cannot compensate for fundamentally poor partition-key design.

---

# Question 11

## Does DynamoDB have a schema?

### Expected Answer

DynamoDB has:

- Fixed primary key schema
- Flexible attributes

Example:

```text
User

Name

Age
```

Another item:

```text
User

Email

Phone

Address
```

Both can exist in the same table.

---

# Question 12

## What is single-table design?

### Expected Answer

Single-table design stores multiple entity types in one table and models relationships through carefully designed partition and sort keys.

Example:

```text
Customer

Order

Invoice

Payment
```

All stored together.

This reduces the need for joins and enables efficient queries.

---

# Question 13

## Why are joins not supported?

### Expected Answer

Joins require distributed coordination, which increases latency and reduces scalability.

Instead, DynamoDB encourages denormalization and modeling data around access patterns.

---

# Question 14

## What are access patterns?

### Expected Answer

Access patterns describe how an application retrieves data.

Examples:

- Get user by ID
- List orders by customer
- Find orders by status
- Retrieve invoices for a month

DynamoDB schema design starts with these patterns rather than with entities.

---

# Question 15

## Why is data modeling more important in DynamoDB than SQL databases?

### Expected Answer

Because queries are constrained by the table's key design.

A poor schema often cannot support required queries efficiently without redesign.

---

# Question 16

## Can DynamoDB automatically scale?

### Expected Answer

Yes.

Scaling options include:

- On-Demand mode
- Auto Scaling for Provisioned mode

DynamoDB automatically manages partitions behind the scenes.

---

# Question 17

## What are the maximum item size limits?

### Expected Answer

A single DynamoDB item can be up to:

```text
400 KB
```

Large binary objects should be stored in Amazon S3 instead.

---

# Question 18

## What are the advantages of DynamoDB?

### Expected Answer

- Fully managed
- Serverless
- Automatic scaling
- High availability
- Low latency
- Multi-AZ replication
- Tight AWS integration
- High durability

---

# Question 19

## What are the disadvantages?

### Expected Answer

- No joins
- Limited ad-hoc querying
- Requires careful data modeling
- Eventual consistency in some scenarios
- GSI write amplification
- Can become expensive with poor design

---

# Question 20

## Explain DynamoDB in one minute.

### Sample Answer

> Amazon DynamoDB is a fully managed NoSQL database designed for high-performance applications requiring predictable single-digit millisecond latency at virtually any scale. It distributes data across partitions using a hash of the partition key, automatically scales storage and throughput, and integrates closely with AWS services such as Lambda, Streams, CloudWatch, and IAM. Instead of relational joins, DynamoDB relies on denormalized schemas designed around application access patterns, making data modeling one of the most critical aspects of building scalable systems.

---

# Rapid Fire Questions

| Question | Short Answer |
|-----------|--------------|
| Is DynamoDB relational? | No |
| Maximum item size? | 400 KB |
| Supports joins? | No |
| Supports transactions? | Yes |
| Serverless? | Yes |
| Multi-AZ? | Yes |
| Supports SQL? | PartiQL |
| Uses partitions? | Yes |
| Supports TTL? | Yes |
| Automatic scaling? | Yes |

---

# Senior Interview Tips

During interviews:

- Explain *why*, not just *what*.
- Discuss trade-offs.
- Mention production experiences.
- Use terms like:
  - Partitioning
  - Horizontal scaling
  - Access patterns
  - Eventual consistency
  - Hot partitions
  - Adaptive Capacity
- Avoid memorized textbook definitions.

---

# Common Mistakes

## Saying DynamoDB Is Faster Than SQL

Correct answer:

It is optimized for different workloads.

---

## Ignoring Access Patterns

Schema design always starts with application queries.

---

## Thinking NoSQL Means No Structure

DynamoDB requires careful primary key design even though non-key attributes are flexible.

---

## Assuming Infinite Scalability

Poor partition-key design can still cause throttling and hot partitions despite DynamoDB's automatic scaling.

---

# Interview Cheat Sheet

```text
Fully Managed

↓

Serverless

↓

NoSQL

↓

Partition Key

↓

Hashing

↓

Horizontal Scaling

↓

Access Pattern Design

↓

Single-Digit Latency

↓

Automatic Scaling

↓

High Availability
```

---

# Key Takeaways

- Senior interviews focus on DynamoDB's architecture, scalability, and design trade-offs rather than memorized definitions.
- Understanding partitioning, access patterns, and data modeling is more valuable than remembering API names.
- Strong answers explain **why** DynamoDB behaves the way it does and when it is the appropriate database choice.
- Real-world examples and production experience significantly strengthen interview responses.
- Mastering these fundamentals provides the foundation for more advanced interview topics such as indexing, transactions, consistency, and system design.