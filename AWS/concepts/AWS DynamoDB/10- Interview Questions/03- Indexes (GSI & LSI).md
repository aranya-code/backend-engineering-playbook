# 03 - Indexes (GSI & LSI)

## Overview

Indexes are one of the most frequently discussed topics in senior DynamoDB interviews because they directly impact query flexibility, scalability, and cost.

Interviewers are rarely interested in hearing:

> "A GSI is another index."

Instead, they expect you to understand:

- Why indexes exist
- How they work internally
- Their limitations
- Performance implications
- Cost trade-offs
- Production use cases

This chapter covers the most common interview questions related to Global Secondary Indexes (GSIs) and Local Secondary Indexes (LSIs).

---

# Learning Objectives

After completing this chapter, you'll be able to answer interview questions about:

- Global Secondary Indexes (GSIs)
- Local Secondary Indexes (LSIs)
- Eventual consistency
- Strong consistency
- Projection types
- Sparse indexes
- Index costs
- Production best practices

---

# Question 1

## Why do we need indexes in DynamoDB?

### Expected Answer

Indexes provide alternate access patterns.

Without indexes:

```text
Orders Table

↓

Partition Key

CustomerID
```

You can only efficiently query by:

```text
CustomerID
```

Suppose the application needs:

```text
Find Orders

↓

Status = SHIPPED
```

Without an index:

```text
Scan Entire Table
```

With a GSI:

```text
Query

↓

Fast
```

---

## Interview Tip

Always say:

> "Indexes exist to support additional access patterns."

---

# Question 2

## What is a Global Secondary Index (GSI)?

### Expected Answer

A GSI is an additional index that allows a table to be queried using a different partition key and optional sort key than the base table.

Example:

Base table:

```text
PK

CustomerID
```

GSI:

```text
PK

Email
```

Now the application can efficiently query by either:

- CustomerID
- Email

---

# Question 3

## What is a Local Secondary Index (LSI)?

### Expected Answer

An LSI uses:

- Same partition key
- Different sort key

Example:

Base table:

```text
PK

CustomerID

SK

OrderID
```

LSI:

```text
PK

CustomerID

SK

OrderDate
```

This enables multiple sort orders within the same partition.

---

# Question 4

## What is the difference between GSI and LSI?

### Expected Answer

| Feature | GSI | LSI |
|----------|-----|-----|
| Partition Key | Different | Same |
| Sort Key | Optional | Different |
| Creation | Anytime | Only during table creation |
| Consistency | Eventual only | Strong or eventual |
| Size Limit | No per-partition item collection limit | Subject to item collection size limit (10 GB per partition key) |

---

## Interview Tip

Most interviewers expect you to mention:

- Different partition key
- Eventual consistency
- LSI creation limitation

---

# Question 5

## Why are GSIs eventually consistent?

### Expected Answer

Writes occur:

```text
Application

↓

Base Table

↓

Asynchronous Replication

↓

GSI
```

Because propagation is asynchronous, a recently written item may not immediately appear in the index.

---

# Question 6

## Can GSIs perform strongly consistent reads?

### Expected Answer

No.

GSIs support:

```text
Eventually Consistent Reads
```

Only.

---

## Follow-up

Which index supports strong consistency?

Answer:

```text
Local Secondary Index (LSI)
```

---

# Question 7

## What are projection types?

### Expected Answer

Projection determines which attributes are copied into an index.

Three options:

```text
KEYS_ONLY

INCLUDE

ALL
```

---

## Example

KEYS_ONLY

Stores:

```text
Primary Keys
```

---

INCLUDE

Stores:

```text
Primary Keys

+

Selected Attributes
```

---

ALL

Stores:

```text
Entire Item
```

---

# Question 8

## Why not always use ALL projections?

### Expected Answer

ALL projections:

Advantages:

- No additional reads

Disadvantages:

- More storage
- Higher write costs
- Larger indexes

Choose the smallest projection that satisfies application requirements.

---

# Question 9

## What is a sparse index?

### Expected Answer

A sparse index contains only items that include the indexed attribute.

Example:

```text
Status Exists

↓

Indexed
```

Missing attribute:

```text
Not Indexed
```

Sparse indexes reduce storage and improve query efficiency.

---

# Question 10

## How does DynamoDB update a GSI?

### Expected Answer

Workflow:

```text
Write Item

↓

Update Base Table

↓

Replicate Change

↓

Update GSI
```

Propagation occurs asynchronously.

---

# Question 11

## What is GSI backfilling?

### Expected Answer

When creating a GSI on an existing table:

```text
Create Index

↓

Scan Existing Items

↓

Populate Index

↓

ACTIVE
```

Large tables may require considerable time before the index becomes available.

---

# Question 12

## Why can a GSI become throttled?

### Expected Answer

GSIs have their own read and write capacity consumption.

Poor key distribution can create:

```text
Hot Index

↓

Throttle

↓

Slow Queries
```

---

# Question 13

## How many GSIs should a table have?

### Expected Answer

Only as many as necessary.

Every GSI adds:

- Storage
- Write amplification
- Cost
- Operational complexity

Indexes should support real access patterns.

---

# Question 14

## What is write amplification?

### Expected Answer

One write:

```text
Base Table

↓

Update GSI

↓

Update Another GSI

↓

Update Another GSI
```

One application write becomes multiple storage operations.

---

# Question 15

## Can an index have a different partition key?

### Expected Answer

GSI:

```text
Yes
```

LSI:

```text
No
```

---

# Question 16

## How do you decide whether to create a GSI?

### Expected Answer

Questions to ask:

- Is this query frequent?
- Is Scan unacceptable?
- Can another access pattern solve it?
- Does the business justify additional write cost?

---

# Question 17

## Can a table work without GSIs?

### Expected Answer

Yes.

Many applications are designed around:

```text
Partition Key

+

Sort Key
```

alone.

GSIs are optional.

---

# Question 18

## What happens if a GSI is deleted?

### Expected Answer

The index data is removed.

The base table:

```text
Unaffected
```

Applications depending on that index:

```text
Queries Fail
```

---

# Question 19

## How do you troubleshoot slow GSI queries?

### Expected Answer

Investigate:

- CloudWatch metrics
- Hot partitions
- Projection type
- Capacity
- Partition-key design
- Eventual consistency expectations

---

# Question 20

## Explain GSIs in one minute.

### Sample Answer

> A Global Secondary Index provides alternate query capabilities by allowing a table to be queried using a different partition key and optional sort key. GSIs are maintained asynchronously, making them eventually consistent. They introduce additional storage and write costs because every write to the base table may also update one or more indexes. A well-designed GSI enables efficient Query operations while avoiding expensive table scans.

---

# Rapid Fire Questions

| Question | Short Answer |
|-----------|--------------|
| GSI Partition Key | Different |
| LSI Partition Key | Same |
| Strong consistency on GSI? | No |
| Strong consistency on LSI? | Yes |
| Created after table creation? | GSI only |
| Sparse Index? | Yes |
| Projection Types | KEYS_ONLY, INCLUDE, ALL |
| GSI updates | Asynchronous |
| GSI consistency | Eventual |
| Extra write cost? | Yes |

---

# Senior Interview Tips

Strong candidates explain:

- Why an index exists
- Cost implications
- Write amplification
- Eventual consistency
- Production trade-offs
- Access-pattern design

Avoid saying:

> "Create a GSI whenever you need another query."

Instead explain:

> "A GSI should be created only when the query is important enough to justify the additional storage, write cost, and operational overhead."

---

# Common Mistakes

## Creating Too Many GSIs

Each additional index increases:

- Storage usage
- Write latency
- Cost
- Maintenance effort

---

## Ignoring Eventual Consistency

Applications must tolerate propagation delays when reading from GSIs.

---

## Choosing ALL Projections by Default

Large projections increase:

- Storage
- Replication work
- Write amplification

---

## Poor Index Key Design

Low-cardinality values such as:

```text
ACTIVE

OPEN

YES
```

can create hot partitions and throttling.

---

# Interview Cheat Sheet

```text
Access Pattern

↓

Need New Query

↓

GSI?

↓

Different PK

↓

Eventual Consistency

↓

Projection

↓

Write Amplification

↓

CloudWatch Monitoring
```

---

# Key Takeaways

- GSIs and LSIs provide additional query flexibility but come with important performance and cost trade-offs.
- GSIs use different partition keys, are eventually consistent, and can be added after table creation, while LSIs share the base table's partition key and must be defined when the table is created.
- Projection type selection significantly affects storage usage, write costs, and query performance.
- Every index should exist to support a genuine access pattern rather than hypothetical future requirements.
- Senior interviewers expect candidates to discuss architecture decisions, operational costs, consistency guarantees, and production trade-offs rather than simply defining what an index is.