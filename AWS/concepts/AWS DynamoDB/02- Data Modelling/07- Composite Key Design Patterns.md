# 07 - Composite Key Design Patterns

## Overview

The **Partition Key** and **Sort Key** together form the foundation of every well-designed DynamoDB table.

A good composite key design can:

- Retrieve multiple entity types with one query
- Eliminate table scans
- Support multiple access patterns
- Enable efficient sorting
- Minimize Global Secondary Indexes (GSIs)
- Scale to billions of items

A poor key design often results in:

- Hot partitions
- Excessive GSIs
- Complex application logic
- Expensive scans
- Costly redesigns

For this reason, experienced DynamoDB engineers spend far more time designing keys than writing code.

---

# What Is a Composite Key?

A composite key consists of:

```text
Partition Key (PK)

+

Sort Key (SK)
```

Example:

```text
PK = CUSTOMER#100

SK = ORDER#500
```

Together they uniquely identify an item.

---

# Why Use Composite Keys?

Suppose an e-commerce customer has:

- Profile
- Orders
- Addresses
- Payment Methods
- Wishlist

Instead of multiple tables:

```text
Customers

Orders

Addresses

Wishlist
```

Use one partition:

```text
CUSTOMER#100

│

├── PROFILE

├── ADDRESS

├── ORDER#1001

├── ORDER#1002

├── WISHLIST

└── PAYMENT#200
```

One Query retrieves everything.

---

# Designing the Partition Key

The partition key should answer:

> **What is the primary entity that owns this data?**

Examples:

```text
USER#100

CUSTOMER#500

DEVICE#900

ORDER#200

ACCOUNT#700
```

These values generally have:

- High cardinality
- Even distribution
- Stable identity

---

# Designing the Sort Key

The sort key should answer:

> **How do I organize related data?**

Examples:

```text
PROFILE

ADDRESS

ORDER#1001

ORDER#1002

ORDER#1003
```

The sort key provides structure within a partition.

---

# Pattern 1 – Entity Type Prefixes

One of the most common DynamoDB patterns is using prefixes.

Instead of:

```text
100

200

300
```

Use:

```text
USER#100

ORDER#200

PRODUCT#300
```

Benefits:

- Self-documenting
- Easier debugging
- Prevents ID collisions
- Supports mixed entity types

---

# Pattern 2 – Hierarchical Data

Suppose an organization contains departments.

```text
Company

↓

Department

↓

Employee
```

Keys:

```text
PK = COMPANY#AWS

SK = DEPARTMENT#Engineering
```

```text
PK = COMPANY#AWS

SK = DEPARTMENT#Finance
```

Retrieve every department:

```text
Query

PK = COMPANY#AWS

SK Begins With

DEPARTMENT#
```

---

# Pattern 3 – Time-Based Keys

Time-series applications are extremely common.

Example:

```text
PK = DEVICE#100

SK = READING#2026-07-22T10:00
```

More readings:

```text
READING#2026-07-22T10:01

READING#2026-07-22T10:02

READING#2026-07-22T10:03
```

Query:

```text
Latest Readings

↓

Reverse Order

↓

Limit 20
```

No additional sorting required.

---

# Pattern 4 – Versioned Records

Suppose documents have versions.

```text
PK = DOCUMENT#500

SK = V1

SK = V2

SK = V3

SK = V4
```

Query:

```text
Latest Version
```

Or:

```text
Entire History
```

This pattern is widely used in document management systems.

---

# Pattern 5 – Status-Based Keys

Example:

```text
PK = ORDER#100

SK = STATUS#PLACED

SK = STATUS#PAID

SK = STATUS#SHIPPED

SK = STATUS#DELIVERED
```

Entire order lifecycle resides within one partition.

---

# Pattern 6 – Composite Sort Keys

Sort keys themselves can contain multiple values.

Example:

```text
ORDER#2026#07#22
```

Or:

```text
ORDER#USA#PAID
```

Or:

```text
POST#2026-07-22#LIKES
```

Each component provides another level of organization.

---

# Composite Sort Key Structure

General format:

```text
Entity

#

Subtype

#

Timestamp

#

Identifier
```

Example:

```text
ORDER

#

SHIPPED

#

2026-07-22

#

1001
```

Now applications can query:

- All orders
- Shipped orders
- Orders for a day
- Specific order

using prefix matching.

---

# Prefix Queries

Suppose sort keys:

```text
ORDER#1001

ORDER#1002

ORDER#1003

PAYMENT#200

PAYMENT#201
```

Query:

```text
Begins With

ORDER#
```

Returns only orders.

Another query:

```text
Begins With

PAYMENT#
```

Returns only payments.

---

# Range Queries

Sort keys naturally support ranges.

Example:

```text
READING#2026-07-20

READING#2026-07-21

READING#2026-07-22
```

Query:

```text
Between

2026-07-20

and

2026-07-22
```

Very efficient.

---

# Composite Keys in Single Table Design

Example:

```text
PK = USER#500

SK = PROFILE
```

```text
PK = USER#500

SK = ORDER#1001
```

```text
PK = USER#500

SK = ORDER#1002
```

```text
PK = USER#500

SK = ADDRESS
```

The partition represents one business aggregate.

---

# Designing for Future Growth

Good composite keys anticipate future requirements.

Example:

Current API:

```text
View Orders
```

Future API:

```text
View Orders

By Status
```

Instead of:

```text
ORDER#1001
```

Design:

```text
ORDER#SHIPPED#1001
```

Now both access patterns are supported.

---

# Common Naming Conventions

Many production systems use uppercase prefixes.

Examples:

```text
USER#

ORDER#

PRODUCT#

INVOICE#

PAYMENT#

DEVICE#

SESSION#

MESSAGE#

POST#

COMMENT#
```

Consistency simplifies maintenance.

---

# Choosing Good Delimiters

Most applications use:

```text
#
```

or

```text
:
```

Example:

```text
USER#100

ORDER#500
```

Readable.

Consistent.

Easy to parse.

---

# Best Practices

- Use descriptive prefixes.
- Keep naming conventions consistent.
- Design sort keys around query requirements.
- Use timestamps for chronological ordering.
- Consider future access patterns.
- Keep partition keys highly distributed.
- Avoid unnecessary complexity.

---

# Common Mistakes

## Using Random Sort Keys

Example:

```text
ABC123

XYZ456
```

No meaningful ordering.

No prefix queries.

---

## Encoding Too Much Information

Avoid:

```text
CUSTOMER#USA#PAID#ACTIVE#PREMIUM#2026#07#22#001
```

Keys should remain readable.

---

## Ignoring Future Queries

Poor key design often requires expensive data migrations later.

Plan ahead.

---

## Inconsistent Naming

Avoid mixing:

```text
User#

USER#

Usr#

customer#
```

Use one convention throughout the application.

---

# Real-World Example

A ride-sharing platform stores trip history.

```text
PK = DRIVER#500
```

Sort keys:

```text
TRIP#2026-07-20#1001

TRIP#2026-07-21#1002

TRIP#2026-07-22#1003
```

The application can efficiently retrieve:

- Latest trips
- Trips within a date range
- A specific trip

without scanning the table.

---

# Architecture Perspective

```text
Application

        │

        ▼

Query

PK = USER#500

        │

        ▼

Partition

USER#500

        │

        ├── PROFILE

        ├── ADDRESS

        ├── ORDER#2026#1001

        ├── ORDER#2026#1002

        ├── PAYMENT#500

        └── SETTINGS

        │

        ▼

Application Response
```

Composite keys organize related entities while supporting multiple efficient access patterns within the same partition.

---

# Interview Notes

A common interview question is:

> **Why do DynamoDB developers use prefixes like `USER#123` instead of just `123`?**

Prefixes identify entity types, prevent key collisions, improve readability, and support Single Table Design by allowing different entity types to coexist within the same table.

Another common question is:

> **What are composite sort keys used for?**

Composite sort keys encode multiple pieces of information—such as entity type, status, timestamp, or version—into a single sort key. This enables prefix searches, range queries, and multiple access patterns without additional indexes.

---

# Key Takeaways

- Composite keys are the foundation of efficient DynamoDB data models.
- Partition keys determine data distribution; sort keys organize related items.
- Prefix-based naming improves readability and supports mixed entity types.
- Composite sort keys enable prefix matching, chronological ordering, and range queries.
- Good key design minimizes scans and reduces the need for additional GSIs.
- Investing time in composite key design results in scalable, maintainable, and cost-efficient DynamoDB applications.