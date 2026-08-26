# 02 - Data Modeling

## Overview

Data modeling is arguably the most important topic in a DynamoDB interview.

Unlike relational databases where schemas are built around entities and relationships, DynamoDB schemas are designed around **application access patterns**.

This is one of the most frequently discussed topics in senior backend interviews because poor data modeling can make an application impossible to scale efficiently.

This chapter covers the most common interview questions on DynamoDB data modeling, along with expected answers and production insights.

---

# Learning Objectives

After completing this chapter, you'll be able to answer interview questions about:

- Access pattern design
- Single-table design
- Denormalization
- Composite keys
- Sparse indexes
- Entity relationships
- Data duplication
- Production trade-offs

---

# Question 1

## What is data modeling in DynamoDB?

### Expected Answer

Data modeling in DynamoDB is the process of designing tables, keys, and indexes based on how the application reads and writes data.

Instead of designing around entities like:

```text
Customer

Order

Invoice
```

you begin by identifying:

```text
Get Customer

↓

List Orders

↓

Find Pending Orders

↓

Retrieve Invoice
```

The schema is built to support these access patterns efficiently.

---

## Interview Tip

A senior engineer should emphasize:

> "In DynamoDB, access patterns drive schema design."

---

# Question 2

## What are access patterns?

### Expected Answer

Access patterns describe every way the application retrieves data.

Examples:

- Get user by ID
- Get product by SKU
- List orders for a customer
- Find unpaid invoices
- Retrieve comments for a post

The goal is to answer every required query without performing table scans.

---

# Question 3

## Why is data modeling different from SQL?

### Expected Answer

SQL databases are normalized to reduce duplication and support flexible queries.

DynamoDB prioritizes:

- Predictable performance
- Fast queries
- Horizontal scalability

This often requires denormalization.

---

## SQL Example

```text
Customer

↓

Orders

↓

Products

↓

JOIN
```

---

## DynamoDB Example

```text
Customer

↓

Customer + Orders

↓

Single Query
```

No joins required.

---

# Question 4

## What is denormalization?

### Expected Answer

Denormalization means intentionally storing duplicate data to optimize read performance.

Example:

Instead of joining:

```text
Order

↓

Customer
```

Store:

```text
Order

↓

Customer Name

Customer Email
```

inside the order item.

---

## Why?

Storage is generally cheaper than performing complex distributed joins.

---

# Question 5

## Isn't duplicated data bad?

### Expected Answer

In relational databases, excessive duplication is often avoided.

In DynamoDB, duplication is a deliberate optimization strategy.

Trade-offs:

Advantages:

- Faster reads
- Fewer queries
- Better scalability

Disadvantages:

- Additional writes
- Update complexity
- More storage

---

# Question 6

## What is Single-Table Design?

### Expected Answer

Single-table design stores multiple entity types inside one table.

Example:

```text
Customer

Order

Invoice

Payment

Shipment
```

All share the same table.

Relationships are modeled using partition and sort keys.

---

## Example

```text
PK

CUSTOMER#100

SK

PROFILE
```

Another item:

```text
PK

CUSTOMER#100

SK

ORDER#200
```

Everything related to the customer can be retrieved with a single query.

---

# Question 7

## When should you use Single-Table Design?

### Expected Answer

Use it when:

- Relationships are well understood
- Access patterns are known
- High performance is required
- Multiple entities are frequently queried together

---

## When might Multiple Tables be preferable?

- Independent services
- Separate ownership
- Different lifecycle requirements
- Simpler applications

---

# Question 8

## What is a Composite Primary Key?

### Expected Answer

A composite primary key consists of:

```text
Partition Key

+

Sort Key
```

Example:

```text
PK

CUSTOMER#100

SK

ORDER#200
```

This enables efficient grouping and sorting.

---

# Question 9

## Why are composite keys powerful?

### Expected Answer

They support:

- One-to-many relationships
- Range queries
- Hierarchical data
- Time-series data

Example:

```text
Customer

↓

Orders

↓

Invoices

↓

Payments
```

All within the same partition.

---

# Question 10

## What is a sparse index?

### Expected Answer

A sparse index contains only items that have the indexed attribute.

Example:

```text
Status

Exists

↓

Indexed
```

Item without the attribute:

```text
Not Indexed
```

This reduces storage and improves query efficiency.

---

# Question 11

## How do you model one-to-many relationships?

### Expected Answer

Example:

```text
Customer

↓

Orders
```

Partition key:

```text
CUSTOMER#100
```

Sort keys:

```text
PROFILE

ORDER#1001

ORDER#1002

ORDER#1003
```

One query retrieves all related records.

---

# Question 12

## How do you model many-to-many relationships?

### Expected Answer

Typically using:

- Composite keys
- GSIs
- Entity duplication

Example:

```text
Student

↓

Course
```

Store relationship items:

```text
STUDENT#1

COURSE#100
```

and

```text
COURSE#100

STUDENT#1
```

depending on required access patterns.

---

# Question 13

## Why should Scan be avoided?

### Expected Answer

Scan reads every item in the table.

Problems:

- Slow
- Expensive
- Consumes capacity
- Doesn't scale

Instead, design keys that allow Query operations.

---

# Question 14

## How do you model time-series data?

### Expected Answer

Example:

```text
PK

DEVICE#101
```

Sort key:

```text
2026-07-20T10:30:00Z
```

This enables:

- Latest records
- Date ranges
- Chronological ordering

---

# Question 15

## How do you model hierarchical data?

### Expected Answer

Example:

```text
ORG#1

↓

DEPARTMENT#10

↓

TEAM#5

↓

EMPLOYEE#100
```

Encoded within sort keys.

---

# Question 16

## What are common data modeling mistakes?

### Expected Answer

- Designing like SQL
- Overusing Scan
- Low-cardinality partition keys
- Ignoring access patterns
- Too many GSIs
- Storing large objects
- Poor naming conventions

---

# Question 17

## How do you choose a partition key?

### Expected Answer

A good partition key:

- High cardinality
- Even traffic distribution
- Frequently queried
- Stable
- Avoids hot partitions

---

# Question 18

## Can the schema evolve over time?

### Expected Answer

Yes.

Non-key attributes are flexible.

However:

Changing:

- Partition key
- Sort key

usually requires data migration because primary keys cannot be modified in place.

---

# Question 19

## What is an item collection?

### Expected Answer

All items sharing the same partition key form an item collection.

Example:

```text
PK

CUSTOMER#500

↓

PROFILE

ORDER#1

ORDER#2

PAYMENT#1

INVOICE#1
```

All can be retrieved using a single Query.

---

# Question 20

## Explain your approach to designing a DynamoDB table.

### Sample Answer

> I start by identifying every application access pattern. Next, I choose a partition key that distributes traffic evenly and supports the most common queries. I then design sort keys to model relationships and ordering, add GSIs only when additional query patterns are required, denormalize where appropriate to avoid joins, and validate the design against expected traffic, scalability, and future growth.

---

# Rapid Fire Questions

| Question | Short Answer |
|-----------|--------------|
| Normalize data? | Usually No |
| Design starts with? | Access Patterns |
| Supports joins? | No |
| Composite key? | PK + SK |
| One-to-many? | Same PK |
| Scan or Query? | Query |
| Duplicate data? | Yes, when beneficial |
| Sparse Index? | Indexes only matching items |
| Single-table design? | Recommended for many production workloads |
| Multiple tables allowed? | Yes |

---

# Senior Interview Tips

Strong interview answers should discuss:

- Access patterns
- Horizontal scaling
- Read optimization
- Denormalization
- Partition-key distribution
- Cost implications
- Trade-offs
- Production experience

Avoid saying:

> "I always use single-table design."

Instead explain:

> "The choice depends on application complexity, ownership boundaries, and access patterns."

---

# Common Mistakes

## Designing Like SQL

Trying to normalize everything leads to inefficient DynamoDB schemas.

---

## Choosing the Wrong Partition Key

Low-cardinality keys cause:

- Hot partitions
- Throttling
- Poor scalability

---

## Adding GSIs Too Early

Create indexes only for real query requirements.

---

## Ignoring Future Access Patterns

A schema should accommodate expected application growth without frequent redesign.

---

# Interview Cheat Sheet

```text
Access Patterns

↓

Partition Key

↓

Sort Key

↓

Composite Key

↓

Query

↓

Denormalization

↓

Single-Table Design

↓

GSI

↓

Horizontal Scaling
```

---

# Key Takeaways

- Data modeling is the foundation of every successful DynamoDB application.
- DynamoDB schemas are designed around access patterns rather than entities or relationships.
- Denormalization and single-table design are optimization techniques, not universal rules.
- Strong partition-key selection and thoughtful use of composite keys enable scalable, low-latency applications.
- Senior interviewers expect candidates to explain design trade-offs and justify their modeling decisions with real-world scenarios.