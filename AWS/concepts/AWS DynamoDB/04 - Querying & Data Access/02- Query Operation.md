# 02 - Query Operation

## Overview

The **Query** operation is the primary method for retrieving data from Amazon DynamoDB.

Unlike relational databases that can search arbitrary columns, DynamoDB Query operations are designed to retrieve data **efficiently using the table's Primary Key or a Secondary Index**.

A Query operation:

- Retrieves items sharing the same Partition Key
- Optionally filters results using Sort Key conditions
- Reads only the required partitions
- Delivers predictable, low-latency performance
- Scales to billions of items

For production applications, **Query should be the default read operation**.

---

# What is a Query?

A Query searches items by specifying:

- Partition Key (Required)
- Optional Sort Key condition

Example table:

```text
PK = CustomerID

SK = OrderDate
```

Query:

```text
CustomerID = CUST1001
```

DynamoDB immediately locates the partition containing that customer's data.

---

# Internal Architecture

```text
               Application

                     │

                     ▼

           Query Request

                     │

                     ▼

          Partition Key Lookup

                     │

                     ▼

         Locate Physical Partition

                     │

                     ▼

        Read Matching Item Collection

                     │

                     ▼

              Return Results
```

Unlike a Scan, DynamoDB never searches the entire table.

---

# Why Query is Fast

Every item sharing the same Partition Key is stored together.

Example:

```text
CustomerID = 1001
```

Stored as:

```text
Customer 1001

├── Order 1
├── Order 2
├── Order 3
├── Order 4
```

A Query retrieves only this item collection.

---

# Query Requirements

A Query always requires:

```text
Partition Key
```

Without a Partition Key:

```text
Query

↓

Impossible
```

Applications must instead use:

- A Secondary Index
- Or Scan (not recommended)

---

# Query Using Primary Key

Example table:

```text
PK = UserID

SK = LoginTime
```

Query:

```text
UserID = USER123
```

Returns:

```text
All Login Records

For USER123
```

---

# Query Using Sort Key

Suppose:

```text
PK = CustomerID

SK = OrderDate
```

Query:

```text
CustomerID = CUST1001

OrderDate > 2026-07-01
```

Result:

```text
Only Recent Orders
```

No unnecessary items are read.

---

# Sort Key Conditions

Supported operators include:

| Operator | Purpose |
|----------|----------|
| = | Exact match |
| < | Less than |
| <= | Less than or equal |
| > | Greater than |
| >= | Greater than or equal |
| BETWEEN | Range queries |
| begins_with() | Prefix matching |

---

# Example — BETWEEN

```text
PK = CustomerID

SK = OrderDate
```

Query:

```text
CustomerID = CUST1001

OrderDate BETWEEN

2026-07-01

AND

2026-07-31
```

Only July orders are returned.

---

# Example — begins_with()

Sort Key:

```text
USA#Texas#Dallas
```

Query:

```text
begins_with(

USA#Texas

)
```

Returns:

```text
All Texas Records
```

Useful for hierarchical data.

---

# Querying Global Secondary Indexes

Queries are not limited to the primary table.

Example:

Table:

```text
PK = UserID
```

GSI:

```text
PK = Email
```

Application:

```text
Find User

By Email
```

Workflow:

```text
Email

↓

Email GSI

↓

Matching User
```

---

# Querying Local Secondary Indexes

Example:

Table:

```text
PK = AccountID

SK = TransactionID
```

LSI:

```text
PK = AccountID

SK = TransactionDate
```

Retrieve:

```text
Latest Transactions
```

The Query executes against the LSI.

---

# Query Result Ordering

Results are automatically sorted by the Sort Key.

Example:

```text
2026-07-01

2026-07-03

2026-07-05

2026-07-08
```

Ascending order is the default.

Applications may also request:

```text
Descending Order
```

to retrieve the newest records first.

---

# Pagination

Large Query results are paginated.

Workflow:

```text
Query

↓

1 MB Returned

↓

LastEvaluatedKey

↓

Next Query

↓

Next Page
```

Applications continue querying until all pages are retrieved.

---

# Filter Expressions

Queries may include Filter Expressions.

Example:

```text
CustomerID

↓

Orders

↓

Status = Delivered
```

Important:

The Query first retrieves matching items using the key, then applies the filter.

Items removed by the filter still consume read capacity.

---

# Projection Expressions

Applications often need only a few attributes.

Example:

Instead of:

```text
Entire Order
```

Retrieve:

```text
OrderID

Status

Total
```

Projection Expressions reduce:

- Network traffic
- Response size

They do **not** reduce read capacity consumption.

---

# Capacity Consumption

Query operations consume:

```text
Read Capacity Units (RCUs)
```

Consumption depends on:

- Item size
- Consistency model
- Number of items read

Not:

- Number of attributes returned

---

# Strong vs Eventual Consistency

Base Table:

Supports:

```text
Strong Reads

or

Eventually Consistent Reads
```

GSI:

Supports only:

```text
Eventually Consistent Reads
```

LSI:

Supports:

```text
Strong Reads
```

---

# Query Performance

Query performance is excellent because DynamoDB:

- Knows the correct partition
- Reads only matching items
- Avoids scanning unrelated data

Typical latency:

```text
Single-digit milliseconds
```

---

# Real-World Example — Banking

Table:

```text
PK = AccountID

SK = TransactionDate
```

Requirement:

```text
Last 10 Transactions
```

Query:

```text
AccountID

↓

Descending

↓

Limit 10
```

Efficient and predictable.

---

# Real-World Example — Social Media

Posts:

```text
PK = UserID

SK = CreatedTime
```

Requirement:

```text
Latest Posts
```

Query:

```text
UserID

↓

Descending

↓

Limit 20
```

Ideal for user timelines.

---

# Real-World Example — IoT

Sensor data:

```text
PK = DeviceID

SK = Timestamp
```

Requirement:

```text
Read Last Hour
```

Query:

```text
Timestamp BETWEEN

Start

End
```

Reads only the required data.

---

# Query Best Practices

- Design tables around Query operations.
- Always use high-cardinality Partition Keys.
- Keep Sort Keys meaningful.
- Use GSIs for alternate access patterns.
- Use Projection Expressions to reduce response size.
- Paginate large datasets.
- Monitor Query latency using CloudWatch.

---

# Common Mistakes

## Expecting Query Without Partition Key

A Query always requires a Partition Key.

Without it:

Use a GSI or redesign the schema.

---

## Using Filters Instead of Keys

Poor:

```text
Query

↓

10000 Items

↓

Filter

↓

20 Results
```

Better:

Design the Sort Key so only the required items are queried.

---

## Ignoring Pagination

Large result sets should never be retrieved in a single request.

Always paginate.

---

## Assuming Returned Attributes Affect Cost

Projection Expressions reduce response size but do not reduce RCUs because DynamoDB reads the full item before returning selected attributes.

---

# Query vs Scan

| Feature | Query | Scan |
|----------|-------|------|
| Requires Partition Key | ✅ | ❌ |
| Reads Entire Table | ❌ | ✅ |
| Supports Sort Key Conditions | ✅ | ❌ |
| Performance | Excellent | Poor |
| Capacity Consumption | Low | High |
| Production Recommendation | Always Preferred | Avoid When Possible |

---

# Architecture Perspective

```text
                    Application

                          │

                          ▼

                     Query Request

                          │

               Partition Key Known?

                ┌─────────┴─────────┐

               Yes                  No

                │                   │

                ▼                   ▼

         Locate Partition         Scan

                │                   │

                ▼                   ▼

       Read Matching Items   Read Entire Table

                │                   │

                ▼                   ▼

          Return Results      Filter Results
```

The Query operation succeeds because DynamoDB uses the Partition Key to locate the correct partition without searching unrelated data.

---

# Production Considerations

High-scale DynamoDB applications are designed so that nearly every customer-facing request uses a Query operation.

Typical production Query patterns include:

- Customer order history
- User activity timelines
- Financial transactions
- IoT device telemetry
- Chat conversations
- Product reviews
- Audit logs

Well-designed Partition Keys and Sort Keys enable these workloads to scale efficiently to billions of records while maintaining predictable latency.

---

# Interview Notes

A common interview question is:

> **Why is Query faster than Scan?**

Query uses the Partition Key to directly locate the required partition and reads only matching items. Scan examines every item in the table or index, making it significantly slower and more expensive.

Another common question is:

> **Can Query work without a Partition Key?**

No. A Query always requires a Partition Key. If an alternate access pattern is needed, a Global Secondary Index (GSI) or Local Secondary Index (LSI) should be created.

Another common question is:

> **Do Projection Expressions reduce RCU consumption?**

No. They reduce the amount of data returned over the network but do not reduce the read capacity consumed because DynamoDB reads the entire item before projecting the requested attributes.

---

# Key Takeaways

- Query is DynamoDB's primary and most efficient read operation.
- A Query always requires a Partition Key and can optionally use Sort Key conditions.
- Query operations read only the relevant partition, providing predictable low-latency performance.
- Projection Expressions reduce response size but not read capacity consumption.
- Filter Expressions are applied after the Query and do not reduce the number of items read.
- Proper table and index design ensures that production applications rely almost exclusively on Query operations rather than Scan.