# 02 - Read & Write Capacity Units (RCU & WCU)

## Overview

Every read and write operation in Amazon DynamoDB consumes capacity.

Unlike traditional databases where resources are measured in CPU cores, RAM, or disk IOPS, DynamoDB measures throughput using:

- **Read Capacity Units (RCUs)**
- **Write Capacity Units (WCUs)**

Understanding RCUs and WCUs is fundamental for:

- Performance tuning
- Cost optimization
- Capacity planning
- Preventing throttling
- Designing scalable applications

Senior backend engineers should be able to estimate capacity requirements before deploying production systems.

---

# Learning Objectives

After completing this chapter, you'll understand:

- What RCUs and WCUs are
- How DynamoDB calculates capacity consumption
- Strongly consistent vs eventually consistent reads
- Transactional read/write costs
- Capacity calculations
- Production sizing examples
- Best practices
- Common mistakes

---

# Capacity Units

Every request consumes capacity.

```text
Application

↓

Read / Write Request

↓

RCU / WCU Consumption

↓

DynamoDB
```

Capacity is based on:

- Item size
- Read consistency
- Operation type
- Number of items

---

# Read Capacity Units (RCU)

An RCU represents the throughput required to perform:

> **One strongly consistent read per second for an item up to 4 KB.**

For eventually consistent reads:

> **One RCU supports two reads per second for items up to 4 KB.**

---

# Write Capacity Units (WCU)

A WCU represents the throughput required to perform:

> **One standard write per second for an item up to 1 KB.**

Every write operation consumes WCUs based on the item size.

---

# Read Capacity Calculation

Formula:

```text
RCUs Required

=

Ceiling(Item Size ÷ 4 KB)

×

Consistency Factor
```

---

## Example 1

Item Size:

```text
2 KB
```

Strongly Consistent Read

```text
2 KB

↓

1 RCU
```

---

## Example 2

Item Size:

```text
8 KB
```

```text
8 KB ÷ 4 KB

↓

2 RCUs
```

---

## Example 3

Item Size:

```text
10 KB
```

```text
10 KB

↓

3 RCUs
```

Because capacity is rounded up.

---

# Write Capacity Calculation

Formula:

```text
WCUs Required

=

Ceiling(Item Size ÷ 1 KB)
```

---

## Example 1

Item Size:

```text
700 Bytes
```

Consumes:

```text
1 WCU
```

---

## Example 2

Item Size:

```text
3 KB
```

Consumes:

```text
3 WCUs
```

---

## Example 3

Item Size:

```text
6.5 KB
```

Consumes:

```text
7 WCUs
```

Always rounded upward.

---

# Capacity Consumption Diagram

```text
Application

↓

PutItem

↓

3 KB Item

↓

3 WCUs
```

---

```text
Application

↓

GetItem

↓

8 KB Item

↓

2 RCUs
```

---

# Read Consistency

DynamoDB supports:

```text
Eventually Consistent

Strongly Consistent
```

Capacity consumption differs.

| Read Type | Capacity Required |
|------------|------------------|
| Eventually Consistent | 0.5× |
| Strongly Consistent | 1× |
| Transactional Read | 2× |

---

# Eventually Consistent Reads

Example:

```text
4 KB Item

↓

Eventually Consistent

↓

0.5 RCU
```

Or viewed differently:

```text
1 RCU

↓

2 Eventually Consistent Reads
```

Suitable for:

- Product catalogs
- Social feeds
- Analytics
- Recommendation engines

---

# Strongly Consistent Reads

Example:

```text
4 KB Item

↓

Strong Read

↓

1 RCU
```

Suitable for:

- Banking
- Inventory
- Order processing
- Financial systems

---

# Transactional Reads

Transactions require additional capacity.

Example:

```text
4 KB Item

↓

Transactional Read

↓

2 RCUs
```

Because DynamoDB guarantees ACID semantics.

---

# Transactional Writes

Similarly:

```text
1 KB Write

↓

Transactional Write

↓

2 WCUs
```

Transactional operations approximately double capacity consumption.

---

# Batch Operations

Batch APIs consume the sum of all individual operations.

Example:

```text
BatchGetItem

↓

20 Items

↓

Total RCUs
```

There is no capacity discount for batching.

Batch operations reduce network overhead—not capacity usage.

---

# Query Capacity

A Query consumes RCUs based on:

- Total data read
- Not data returned

Example:

```text
Read

↓

100 Items

↓

Filter

↓

Return 5 Items
```

Capacity is charged for all 100 items read.

---

# Scan Capacity

Scan reads every matching partition.

```text
Entire Table

↓

Scan

↓

Consumes RCUs
```

Large scans can consume significant capacity and affect application performance.

---

# Capacity Consumption Example

Suppose an application performs:

```text
500 Reads/sec

2 KB Items

Strong Reads
```

Each read:

```text
2 KB

↓

1 RCU
```

Total:

```text
500 RCUs
```

---

Now consider writes.

```text
200 Writes/sec

2 KB Items
```

Each write:

```text
2 WCUs
```

Total:

```text
400 WCUs
```

---

# Production Example

E-commerce application:

```text
Customers

↓

Browse Products

↓

Eventually Consistent Reads

────────────

Checkout

↓

Strong Reads

────────────

Order Creation

↓

Writes
```

Different operations require different capacity calculations.

---

# Capacity Planning Workflow

```text
Estimate Traffic

↓

Estimate Item Size

↓

Calculate RCUs

↓

Calculate WCUs

↓

Provision Capacity

↓

Monitor

↓

Optimize
```

Capacity planning should be revisited as workloads evolve.

---

# CloudWatch Metrics

Monitor:

```text
ConsumedReadCapacityUnits

ConsumedWriteCapacityUnits

ReadThrottleEvents

WriteThrottleEvents
```

These metrics indicate whether current capacity matches workload demands.

---

# Best Practices

- Keep item sizes as small as practical.
- Use eventually consistent reads when acceptable.
- Monitor consumed capacity regularly.
- Use Auto Scaling for Provisioned Capacity.
- Estimate peak traffic, not average traffic.
- Test with realistic production loads.
- Review access patterns before increasing capacity.

---

# Common Mistakes

## Assuming Returned Data Determines RCUs

Capacity is based on **data read**, not data returned.

```text
100 Items Read

↓

5 Returned

↓

Charged for 100
```

---

## Ignoring Item Size

Large items dramatically increase capacity usage.

Poor:

```text
50 KB Item
```

Better:

```text
3 KB Item
```

Smaller items improve both performance and cost efficiency.

---

## Using Strong Reads Everywhere

Many applications do not require strong consistency.

Using eventually consistent reads where appropriate reduces capacity consumption by approximately 50%.

---

## Overusing Scan

```text
Large Table

↓

Scan

↓

High RCU Usage
```

Prefer:

```text
Query

↓

Partition Key

↓

Efficient Reads
```

---

# Production Considerations

Large organizations typically:

- Estimate capacity during system design.
- Continuously monitor CloudWatch metrics.
- Optimize item size.
- Use Auto Scaling for predictable workloads.
- Select consistency levels based on business requirements.
- Periodically review access patterns to reduce unnecessary capacity consumption.

---

# Interview Notes

A common interview question is:

> **What is one Read Capacity Unit (RCU)?**

One RCU supports one strongly consistent read per second for an item up to **4 KB**, or two eventually consistent reads per second for an item up to **4 KB**.

---

Another common question is:

> **What is one Write Capacity Unit (WCU)?**

One WCU supports one standard write per second for an item up to **1 KB**. Larger items consume additional WCUs, rounded up to the next whole unit.

---

Another common question is:

> **Why do Scan operations consume so much capacity?**

A Scan reads every item in the scanned partitions, regardless of filtering. Capacity is consumed based on the total data read, making scans expensive on large tables.

---

Another common question is:

> **How do transactional operations affect capacity?**

Transactional reads and writes consume approximately **twice** the capacity of standard operations because DynamoDB provides ACID guarantees for transactions.

---

# Key Takeaways

- RCUs measure read throughput, while WCUs measure write throughput.
- Read capacity is calculated using **4 KB** blocks; write capacity uses **1 KB** blocks.
- Capacity consumption is rounded up based on item size.
- Eventually consistent reads consume half the capacity of strongly consistent reads.
- Transactional operations require approximately double the capacity of standard operations.
- Capacity planning, item size optimization, and CloudWatch monitoring are essential for building scalable and cost-efficient DynamoDB applications.