# 11 - BatchGetItem

## Overview

`BatchGetItem` is a DynamoDB operation that allows an application to retrieve **multiple items from one or more tables in a single request**.

Instead of issuing multiple individual `GetItem` requests, BatchGetItem combines them into a single API call, reducing:

- Network latency
- Round trips
- Client-side overhead
- API request count

It is ideal when the application already knows the **Primary Keys** of all items that need to be retrieved.

Unlike **Query**, BatchGetItem **does not search** for data.

Unlike **Scan**, BatchGetItem **does not examine** the table.

It simply retrieves specific items by their primary keys.

---

# Why BatchGetItem Exists

Suppose an application needs:

```text
User 101

User 205

User 390

User 421
```

Using GetItem:

```text
Application

↓

GetItem

↓

GetItem

↓

GetItem

↓

GetItem
```

Four network requests.

Using BatchGetItem:

```text
Application

↓

BatchGetItem

↓

Four Items Returned
```

Only one request.

---

# Internal Architecture

```text
             Application

                    │

                    ▼

             BatchGetItem

                    │

     ┌──────────────┼──────────────┐

     ▼              ▼              ▼

 Read Item A   Read Item B   Read Item C

     └──────────────┼──────────────┘

                    ▼

           Combine Responses

                    ▼

             Return Results
```

Each item is retrieved independently, but returned together.

---

# Request Structure

A BatchGetItem request specifies:

- Table name
- Primary Keys
- Optional Projection Expression

Example:

```text
Users Table

↓

UserID = 101

UserID = 205

UserID = 390
```

---

# Primary Key Requirement

Every requested item must include its complete primary key.

Simple Primary Key:

```text
PK = UserID
```

Example:

```text
UserID = 100
```

Composite Primary Key:

```text
PK = CustomerID

SK = OrderID
```

Example:

```text
Customer001

Order1001
```

Both values are required.

---

# Reading Multiple Tables

BatchGetItem supports multiple tables.

Example:

```text
Users

Orders

Products
```

Single request:

```text
Users

↓

Orders

↓

Products

↓

Combined Response
```

Useful for dashboard APIs.

---

# Capacity Consumption

BatchGetItem consumes RCUs exactly as if each GetItem were executed separately.

Example:

```text
10 Items
```

Capacity:

```text
RCUs

=

Sum of

All Reads
```

Batching reduces network overhead—not database read cost.

---

# Response Order

Items are **not guaranteed** to be returned in the same order as requested.

Example:

Request:

```text
101

102

103
```

Response:

```text
102

101

103
```

Applications should not rely on response ordering.

---

# Projection Expressions

BatchGetItem supports Projection Expressions.

Instead of:

```text
Entire User Record
```

Retrieve:

```text
UserID

Name

Email
```

Benefits:

- Smaller payload
- Faster network transfer

RCUs remain unchanged.

---

# Limits

BatchGetItem has several important limits.

Maximum items:

```text
100 Items
```

Maximum response size:

```text
16 MB
```

If either limit is exceeded:

```text
Partial Response
```

The remaining keys are returned as:

```text
UnprocessedKeys
```

---

# UnprocessedKeys

Sometimes DynamoDB cannot process every requested item because of:

- Throughput limits
- Response size limits
- Internal throttling

Example:

```text
100 Items Requested

↓

92 Returned

↓

8 UnprocessedKeys
```

Applications should retry only those keys.

---

# Retry Workflow

```text
BatchGetItem

↓

Receive

UnprocessedKeys

↓

Exponential Backoff

↓

Retry Remaining Keys

↓

Success
```

Retrying immediately without backoff can increase throttling.

---

# BatchGetItem vs GetItem

| Feature | GetItem | BatchGetItem |
|----------|----------|--------------|
| Reads One Item | ✅ | ❌ |
| Reads Multiple Items | ❌ | ✅ |
| Multiple Tables | ❌ | ✅ |
| One Network Call | ❌ | ✅ |
| Supports Projection Expressions | ✅ | ✅ |

---

# BatchGetItem vs Query

| Feature | BatchGetItem | Query |
|----------|--------------|-------|
| Knows Primary Keys | Required | Partition Key Required |
| Reads Multiple Random Items | ✅ | ❌ |
| Range Queries | ❌ | ✅ |
| Sort Key Conditions | ❌ | ✅ |
| Retrieves Item Collection | ❌ | ✅ |

---

# BatchGetItem vs Scan

| Feature | BatchGetItem | Scan |
|----------|--------------|------|
| Reads Entire Table | ❌ | ✅ |
| Requires Keys | ✅ | ❌ |
| Performance | Excellent | Poor |
| Production APIs | Recommended | Avoid |

---

# Real-World Example — E-commerce

Shopping cart:

```text
Product IDs

101

205

410

512
```

Instead of:

```text
GetItem

×

4
```

Application performs:

```text
BatchGetItem

↓

Retrieve

All Products
```

Lower latency.

---

# Real-World Example — Banking

Dashboard:

```text
Customer Profile

Latest Loan

Savings Account

Credit Card
```

Stored in separate tables.

Application:

```text
BatchGetItem

↓

Retrieve

Everything

↓

Dashboard
```

One request.

---

# Real-World Example — Social Media

Homepage:

```text
User Profile

Trending Topics

Recommended Friends

Notifications
```

Each stored independently.

BatchGetItem retrieves all required records efficiently.

---

# Internal Workflow

```text
Application

↓

BatchGetItem

↓

Locate Keys

↓

Read Items

↓

Merge Results

↓

Return Response
```

No table scan occurs.

---

# Best Practices

- Use BatchGetItem when all Primary Keys are known.
- Retry only `UnprocessedKeys`.
- Implement exponential backoff for retries.
- Use Projection Expressions to reduce payload size.
- Keep requests below API limits.
- Use Query instead of BatchGetItem for range-based access patterns.

---

# Common Mistakes

## Using BatchGetItem Instead of Query

Poor:

```text
Need

All Orders

For Customer
```

Using:

```text
BatchGetItem
```

Impossible because the Order IDs are unknown.

Use:

```text
Query
```

instead.

---

## Ignoring UnprocessedKeys

Many developers assume every requested item is always returned.

Production applications should always check for:

```text
UnprocessedKeys
```

and retry them.

---

## Assuming Response Order

The response order is undefined.

Applications should map returned items using their keys.

---

## Requesting Too Much Data

Large items increase the likelihood of hitting the 16 MB response limit.

Projection Expressions can help reduce payload size.

---

# Architecture Perspective

```text
                Application

                      │

                BatchGetItem

                      │

      ┌───────────────┼───────────────┐

      ▼               ▼               ▼

   Read Key A     Read Key B     Read Key C

      └───────────────┼───────────────┘

                      ▼

              Merge Responses

                      ▼

               Return Items
```

BatchGetItem optimizes network communication by grouping multiple point reads into a single API request.

---

# Production Considerations

BatchGetItem is commonly used in high-performance microservices where multiple independent records are required to build a single response.

Typical use cases include:

- Shopping carts
- User dashboards
- Order summaries
- Product recommendations
- Financial account overviews
- Composite REST or GraphQL APIs

Production systems should always:

- Handle `UnprocessedKeys`
- Retry with exponential backoff
- Monitor throttling through CloudWatch
- Avoid oversized requests that approach the 16 MB response limit

---

# Interview Notes

A common interview question is:

> **When should you use BatchGetItem instead of Query?**

Use BatchGetItem when you already know the complete primary keys of multiple items. Use Query when you need to retrieve an item collection using a Partition Key and optional Sort Key conditions.

Another common question is:

> **Does BatchGetItem reduce RCU consumption?**

No. It reduces network round trips but consumes approximately the same RCUs as multiple individual GetItem requests.

Another common question is:

> **What are `UnprocessedKeys`?**

They identify items that DynamoDB could not process in the current request due to limits or throttling. Applications should retry only those keys using exponential backoff.

---

# Key Takeaways

- `BatchGetItem` retrieves multiple known items in a single API request.
- It supports reading from multiple DynamoDB tables simultaneously.
- It reduces network overhead but **does not** reduce read capacity consumption.
- Responses may include `UnprocessedKeys`, which should be retried with exponential backoff.
- `BatchGetItem` is ideal for dashboards, shopping carts, and APIs that need several independent records at once.