# 05 - Filter Expressions

## Overview

A **Filter Expression** is used to remove unwanted items **after** DynamoDB has already read them.

This is one of the most misunderstood concepts in DynamoDB.

Many developers assume a Filter Expression works like a SQL `WHERE` clause. It does **not**.

In DynamoDB:

- The **Key Condition Expression** determines **what DynamoDB reads**.
- The **Filter Expression** determines **what DynamoDB returns**.

Since filtering occurs **after the read operation**, Filter Expressions **do not reduce Read Capacity Unit (RCU) consumption**.

Understanding this distinction is critical for designing efficient DynamoDB applications.

---

# What is a Filter Expression?

A Filter Expression evaluates each item **after** it has been read from the table or index.

Example:

```text
CustomerID = CUST1001

↓

Read All Orders

↓

Status = Delivered

↓

Return Delivered Orders
```

Although only delivered orders are returned, DynamoDB still reads **every order** for that customer.

---

# Query Execution Flow

```text
Application

↓

Key Condition Expression

↓

Read Matching Items

↓

Filter Expression

↓

Discard Unwanted Items

↓

Return Results
```

The filtering occurs **after** DynamoDB has already consumed RCUs.

---

# Why Filter Expressions Exist

Sometimes the Partition Key retrieves a larger set of items than the application needs.

Example:

```text
PK = CustomerID

SK = OrderDate
```

Customer:

```text
CUST1001
```

Orders:

```text
Delivered

Pending

Cancelled

Delivered

Returned
```

Requirement:

```text
Only Delivered Orders
```

Instead of reading another table or creating a new index, a Filter Expression can remove unwanted results.

---

# Query with Filter Expression

Table:

```text
PK = CustomerID

SK = OrderDate
```

Query:

```text
CustomerID = CUST1001
```

Filter:

```text
Status = Delivered
```

Workflow:

```text
Read All Orders

↓

Remove Non-Delivered Orders

↓

Return Delivered Orders
```

---

# Scan with Filter Expression

Filter Expressions also work with Scan.

Workflow:

```text
Scan Entire Table

↓

Read Every Item

↓

Filter Active Users

↓

Return Active Users
```

The Scan still reads every item.

---

# Capacity Consumption

Suppose:

```text
Customer

1000 Orders
```

Query:

```text
CustomerID = CUST1001
```

Filter:

```text
Status = Delivered
```

Delivered Orders:

```text
40
```

RCUs are consumed for:

```text
1000 Orders
```

Not:

```text
40 Orders
```

This is one of the most common DynamoDB misconceptions.

---

# Supported Operators

Filter Expressions support a rich set of comparison operators.

| Operator | Purpose |
|----------|----------|
| = | Equal |
| <> | Not Equal |
| < | Less Than |
| <= | Less Than or Equal |
| > | Greater Than |
| >= | Greater Than or Equal |
| BETWEEN | Range |
| IN | Match Multiple Values |
| attribute_exists() | Attribute Exists |
| attribute_not_exists() | Attribute Missing |
| begins_with() | Prefix Matching |
| contains() | Contains Value |

---

# Example — Numeric Filter

Items:

```text
Amount

200

500

1500

2500
```

Filter:

```text
Amount > 1000
```

Returns:

```text
1500

2500
```

All items were still read.

---

# Example — Status Filter

Orders:

```text
Delivered

Pending

Cancelled

Delivered
```

Filter:

```text
Status = Delivered
```

Returns:

```text
Delivered

Delivered
```

---

# Example — contains()

Products:

```text
Tags

["Laptop","Gaming"]

["Office"]

["Electronics","Laptop"]
```

Filter:

```text
contains(

Tags,

Laptop
)
```

Returns:

Only products containing the "Laptop" tag.

---

# Example — begins_with()

Sort Key:

```text
USA#California

USA#Texas

Canada#Ontario
```

Filter:

```text
begins_with(

Location,

USA
)
```

Returns:

All USA locations.

Although possible, using `begins_with()` in a **Key Condition Expression** is generally more efficient.

---

# Multiple Conditions

Filter Expressions support logical operators.

Example:

```text
Status = Delivered

AND

Amount > 100
```

Or:

```text
Priority = High

OR

Priority = Critical
```

---

# Filter Expression vs Key Condition

Key Condition:

```text
Locate Data
```

Filter Expression:

```text
Remove Data
```

Comparison:

| Feature | Key Condition | Filter Expression |
|----------|---------------|-------------------|
| Determines Items Read | ✅ | ❌ |
| Determines Items Returned | ✅ | ✅ |
| Reduces RCUs | ✅ | ❌ |
| Evaluated Before Read | ✅ | ❌ |
| Evaluated After Read | ❌ | ✅ |

---

# Internal Architecture

```text
                  Query

                    │

                    ▼

       Key Condition Expression

                    │

                    ▼

          Read Matching Items

                    │

                    ▼

          Filter Expression

                    │

        ┌───────────┴───────────┐

        ▼                       ▼

 Keep Item                Discard Item

        │

        ▼

 Return Results
```

---

# Real-World Example — E-commerce

Table:

```text
PK = CustomerID

SK = OrderDate
```

Need:

```text
Delivered Orders

Above $500
```

Query:

```text
CustomerID = CUST1001
```

Filter:

```text
Status = Delivered

AND

Amount > 500
```

---

# Real-World Example — Banking

Transactions:

```text
PK = AccountID

SK = Timestamp
```

Need:

```text
Debit Transactions

Above $1000
```

Query:

```text
AccountID = ACC100
```

Filter:

```text
Type = Debit

AND

Amount > 1000
```

---

# Real-World Example — IoT

Sensor Data:

```text
PK = DeviceID

SK = Timestamp
```

Need:

```text
Temperature Alerts
```

Query:

```text
DeviceID = SENSOR01
```

Filter:

```text
Temperature > 90
```

---

# When to Use Filter Expressions

Use Filter Expressions when:

- The Query already retrieves a relatively small dataset.
- Creating a new GSI is unnecessary.
- Filtering is performed occasionally.
- The additional read cost is acceptable.

---

# When NOT to Use Filter Expressions

Avoid Filter Expressions when:

- Millions of items must be filtered.
- Queries consistently discard most retrieved items.
- High-traffic APIs require low latency.
- A better Partition Key or GSI can satisfy the access pattern.

If the filter removes most of the queried items, consider redesigning the table or creating a secondary index.

---

# Best Practices

- Prefer Key Condition Expressions over Filter Expressions whenever possible.
- Design Sort Keys to minimize filtering.
- Use GSIs for common filtering requirements.
- Keep Query result sets small.
- Monitor RCU usage in CloudWatch.
- Measure whether a Filter Expression is hiding a poor data model.

---

# Common Mistakes

## Treating Filter Expressions Like SQL WHERE

In SQL:

```sql
SELECT *
FROM Orders
WHERE Status = 'Delivered';
```

The optimizer may use an index.

In DynamoDB:

```text
Query

↓

Read Items

↓

Filter Items
```

Filtering occurs after reading.

---

## Filtering Large Result Sets

Poor:

```text
Read

100,000 Items

↓

Return

20 Items
```

Better:

Redesign the key schema or add a GSI.

---

## Assuming Filters Reduce Cost

They reduce:

- Response size

They do **not** reduce:

- Read Capacity Units
- Number of items read

---

# Architecture Perspective

```text
                Application

                      │

                Query Request

                      │

                      ▼

        Key Condition Expression

                      │

                      ▼

            Read Matching Items

                      │

                      ▼

          Filter Expression

          ┌─────────┴─────────┐

          ▼                   ▼

     Keep Item          Discard Item

          │

          ▼

      Return Results
```

A Filter Expression influences only the **response**, not the **read operation**.

---

# Production Considerations

In production systems, Filter Expressions should be used sparingly.

If dashboards, APIs, or services repeatedly retrieve thousands of items only to discard most of them, it is usually a sign that:

- The Partition Key is poorly designed.
- The Sort Key is not optimized.
- A Global Secondary Index (GSI) is missing.

Senior engineers typically view heavy reliance on Filter Expressions as a signal to revisit the data model.

---

# Interview Notes

A common interview question is:

> **Do Filter Expressions reduce read capacity consumption?**

No. DynamoDB reads the items first and then applies the Filter Expression, so RCUs are consumed for all items read, not just those returned.

Another common question is:

> **When should you use a Filter Expression instead of a GSI?**

Use a Filter Expression when the query already returns a relatively small dataset and the additional read cost is acceptable. If filtering is frequent or discards most items, a GSI or redesigned key schema is usually the better solution.

Another common question is:

> **What is the difference between a Key Condition Expression and a Filter Expression?**

A Key Condition Expression determines which items DynamoDB reads and directly affects performance and RCUs. A Filter Expression is evaluated after the read operation and only determines which items are returned to the application.

---

# Key Takeaways

- Filter Expressions are evaluated **after** DynamoDB reads the data.
- They reduce the number of returned items but **not** the number of items read.
- Filter Expressions do not lower RCU consumption.
- Key Condition Expressions should always be used to narrow the dataset before filtering.
- Frequent use of Filter Expressions on large result sets often indicates that the table design or indexing strategy should be improved.