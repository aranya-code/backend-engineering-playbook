# 03 - Querying & Scanning

## Overview

Reading data efficiently is one of the most important skills when working with Amazon DynamoDB.

Although both **Query** and **Scan** retrieve data from a table, they behave very differently.

A common interview question is:

> **Why is Scan discouraged in production?**

The answer is simple:

- Query reads only the required partition.
- Scan reads the entire table.

For small tables the difference may not be noticeable, but on production tables containing millions of items, the performance and cost differences are enormous.

This chapter explores Query and Scan operations using the AWS CLI, along with filtering, projections, pagination, sorting, and production best practices.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Query vs Scan
- Key Condition Expressions
- Filter Expressions
- Projection Expressions
- Pagination
- Limit
- Sorting
- Count operations
- Index querying
- Performance optimization
- Production best practices

---

# Query vs Scan

```text
               Query

Uses Partition Key

        │

        ▼

Single Partition

        │

        ▼

Fast
```

---

```text
                Scan

Reads Every Partition

        │

        ▼

Entire Table

        │

        ▼

Slow
```

---

# Why Query is Preferred

Suppose we have:

```text
Orders

10 Million Items
```

Looking for:

```text
Customer = C100
```

Using Query:

```text
Partition

↓

Customer Records
```

Using Scan:

```text
Entire Table

↓

10 Million Reads
```

---

# Query Syntax

Basic syntax:

```bash
aws dynamodb query \
    --table-name Orders \
    --key-condition-expression \
        "customer_id = :id" \
    --expression-attribute-values \
'{
":id":{"S":"C100"}
}'
```

---

# Query Architecture

```text
Application

↓

Partition Key

↓

Matching Partition

↓

Matching Items
```

---

# Key Condition Expression

A Query **must** specify the partition key.

Example:

```text
customer_id = C100
```

Without the partition key:

```text
Query

↓

Validation Error
```

---

# Query with Sort Key

Suppose:

```text
Partition Key

customer_id

Sort Key

order_date
```

Example:

```bash
aws dynamodb query \
    --table-name Orders \
    --key-condition-expression \
"customer_id = :id
AND order_date >= :date" \
--expression-attribute-values \
'{
":id":{"S":"C100"},
":date":{"S":"2026-01-01"}
}'
```

---

# Sort Key Operators

Supported operators:

```text
=

<

<=

>

>=

BETWEEN

begins_with()
```

---

# BETWEEN Example

```bash
--key-condition-expression \
"customer_id = :id
AND order_date BETWEEN :d1 AND :d2"
```

Useful for:

- Reports
- Date ranges
- Billing periods

---

# begins_with()

Example:

```bash
--key-condition-expression \
"customer_id = :id
AND begins_with(order_date,:prefix)"
```

Example value:

```text
2026-07
```

Returns:

```text
July Orders
```

---

# Querying a Global Secondary Index

```bash
aws dynamodb query \
    --table-name Orders \
    --index-name StatusIndex \
    --key-condition-expression \
        "status = :status" \
    --expression-attribute-values \
'{
":status":{"S":"PENDING"}
}'
```

The table remains unchanged.

The GSI provides another access pattern.

---

# Projection Expression

Instead of retrieving:

```text
Entire Item
```

Retrieve:

```text
order_id

status
```

Example:

```bash
--projection-expression \
"order_id,status"
```

Benefits:

- Smaller payload
- Faster responses
- Lower network usage

---

# Filter Expression

Suppose:

```text
Customer

↓

100 Orders

↓

Need Only SHIPPED
```

Example:

```bash
--filter-expression \
"#status = :status" \
--expression-attribute-names \
'{
"#status":"status"
}' \
--expression-attribute-values \
'{
":status":{"S":"SHIPPED"}
}'
```

---

# Query Execution Order

```text
Query

↓

Read Matching Keys

↓

Filter Expression

↓

Return Results
```

Notice:

Filtering occurs **after** DynamoDB reads matching items.

It does **not** reduce read capacity consumption.

---

# Sorting Results

Default:

```text
Ascending
```

Example:

```bash
--scan-index-forward false
```

Returns:

```text
Newest

↓

Oldest
```

Useful for:

- Recent orders
- Latest messages
- Activity feeds

---

# Limit

Retrieve only a subset.

```bash
--limit 20
```

Example:

```text
Query

↓

20 Items

↓

Stop
```

Useful for APIs.

---

# Pagination

Maximum response:

```text
1 MB
```

If more data exists:

```text
LastEvaluatedKey

↓

Next Request
```

Continue with:

```bash
--exclusive-start-key
```

---

# Count Only

Instead of retrieving items:

```bash
--select COUNT
```

Returns:

```json
{
  "Count": 125
}
```

Useful for dashboards.

---

# Scan

Basic syntax:

```bash
aws dynamodb scan \
    --table-name Orders
```

Execution:

```text
Entire Table

↓

Every Partition

↓

Results
```

---

# Filtering a Scan

```bash
aws dynamodb scan \
    --table-name Orders \
    --filter-expression \
"#status = :status"
```

Remember:

Filtering does **not** reduce scan cost.

---

# Parallel Scan

Large administrative jobs can use:

```text
Worker 1

Worker 2

Worker 3

Worker N
```

CLI supports:

```bash
--segment

--total-segments
```

Example:

```bash
aws dynamodb scan \
    --table-name Orders \
    --segment 0 \
    --total-segments 4
```

Each worker scans a different portion of the table.

---

# Query vs Scan Comparison

| Feature | Query | Scan |
|----------|-------|------|
| Requires Partition Key | ✅ | ❌ |
| Reads Entire Table | ❌ | ✅ |
| Fast | ✅ | ❌ |
| Low Cost | ✅ | ❌ |
| Production APIs | ✅ | ❌ |
| Reporting Jobs | Sometimes | Sometimes |

---

# Query Flow

```text
Client

↓

Query

↓

Partition Key

↓

Matching Partition

↓

Items Returned
```

---

# Scan Flow

```text
Client

↓

Scan

↓

Partition A

↓

Partition B

↓

Partition C

↓

Entire Table
```

---

# Production Example

Customer API:

```text
GET

/customers/C100/orders
```

Repository:

```text
Query

↓

Partition

↓

Orders
```

Never:

```text
Scan

↓

Entire Table
```

---

# CLI Example with JSON Output

```bash
aws dynamodb query \
    --table-name Orders \
    --key-condition-expression \
        "customer_id = :id" \
    --expression-attribute-values \
'{
":id":{"S":"C100"}
}' \
    --output json
```

---

# Using JMESPath

Retrieve only IDs.

```bash
aws dynamodb query \
    --table-name Orders \
    --query "Items[].order_id.S"
```

Example output:

```json
[
  "ORD-1001",
  "ORD-1002",
  "ORD-1003"
]
```

---

# Production Architecture

```text
            Application

                 │

                 ▼

            AWS CLI

                 │

                 ▼

       Query / Scan Request

                 │

                 ▼

         Amazon DynamoDB

                 │

                 ▼

          Matching Items
```

---

# Performance Considerations

- Prefer Query over Scan.
- Design tables around access patterns.
- Retrieve only required attributes.
- Use pagination for large datasets.
- Avoid scans on production APIs.
- Use GSIs instead of scanning when possible.

---

# Security Best Practices

- Restrict IAM permissions to required tables.
- Validate all CLI parameters before execution.
- Avoid running large scans on production without approval.
- Log administrative query operations.
- Use named profiles for different environments.

---

# Best Practices

- Always use Query when possible.
- Design partition keys carefully.
- Use Projection Expressions to reduce payload size.
- Use Filter Expressions only when necessary.
- Paginate large result sets.
- Use GSIs to support additional access patterns.
- Benchmark queries before deploying to production.

---

# Common Mistakes

## Using Scan for APIs

Poor:

```text
Mobile App

↓

Scan

↓

Entire Table
```

Better:

```text
Mobile App

↓

Query

↓

Partition
```

---

## Assuming Filters Reduce Cost

Incorrect:

```text
Scan

↓

Filter

↓

Cheap
```

Reality:

```text
Scan

↓

Read Everything

↓

Filter

↓

Return Results
```

---

## Returning Entire Items

Instead of:

```text
Complete Record
```

Use:

```text
ProjectionExpression
```

---

## Ignoring Pagination

Large queries should always process:

```text
Page

↓

Next Page

↓

Next Page
```

Never assume one request returns all results.

---

# Interview Notes

A common interview question is:

> **What is the difference between Query and Scan?**

A Query retrieves items using the partition key and reads only the required partitions, making it fast and cost-efficient. A Scan reads every item in the table regardless of the filter and is significantly more expensive.

---

Another common question is:

> **Does a Filter Expression reduce read capacity usage?**

No. DynamoDB first reads the matching items and then applies the filter. The consumed read capacity is based on the data read before filtering.

---

Another common question is:

> **Why is Query faster than Scan?**

Query directly targets the partition containing the requested data using the partition key, while Scan sequentially examines every partition in the table.

---

Another common question is:

> **When would you use a Scan?**

Scans are generally reserved for administrative tasks, analytics, data migration, maintenance scripts, or offline batch processing where reading the entire table is acceptable.

---

# Key Takeaways

- Query is the preferred method for retrieving data in DynamoDB because it is fast, scalable, and cost-efficient.
- Scan should be avoided for production APIs because it reads the entire table.
- Use Key Condition Expressions to identify partitions and Projection Expressions to minimize returned data.
- Filter Expressions refine results but do not reduce read capacity consumption.
- Efficient querying is achieved through proper table design, well-chosen partition keys, GSIs, and thoughtful access patterns.