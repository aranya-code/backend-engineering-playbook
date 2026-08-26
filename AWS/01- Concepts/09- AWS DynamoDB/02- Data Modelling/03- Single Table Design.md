# 03 - Single Table Design

## Overview

If there is one DynamoDB topic that separates **junior developers** from **senior backend engineers**, it is **Single Table Design**.

Most developers coming from relational databases are surprised when they first hear:

> **Store multiple entities in the same DynamoDB table.**

Their immediate reaction is:

> "Isn't that bad database design?"

In SQL, yes.

In DynamoDB, **it is often the recommended approach.**

Single Table Design is not about putting everything into one table randomly.

It is about organizing data around **access patterns**, allowing related information to be retrieved with as few database operations as possible.

---

# The Relational Database Approach

Consider an e-commerce application.

A relational database might contain:

```text
Customers

Orders

Products

Payments

Addresses

Invoices
```

Relationships are handled using:

- Foreign Keys
- JOINs
- Normalization

Example:

```sql
Customers

JOIN Orders

JOIN Payments

JOIN Addresses
```

The database reconstructs the data during query execution.

---

# Why This Doesn't Scale Well

Imagine the tables are distributed.

```text
Customer

↓

Server A
```

Orders

```text
↓

Server B
```

Payments

```text
↓

Server C
```

Invoices

```text
↓

Server D
```

Now one API request becomes:

```text
Server A

↓

Server B

↓

Server C

↓

Server D

↓

Merge Results
```

Across millions of requests this becomes expensive.

Distributed joins introduce:

- Network latency
- Increased CPU usage
- Higher operational cost
- Reduced scalability

---

# DynamoDB's Philosophy

Instead of joining data later:

Store related data together.

```text
Customer

+

Orders

+

Addresses

↓

Same Partition
```

Now the application performs:

```text
One Query

↓

Everything Returned
```

---

# What Is Single Table Design?

Single Table Design stores **multiple entity types inside one DynamoDB table**.

Example:

```text
Table

↓

Customer

Order

Payment

Shipment

Invoice
```

Everything shares the same table.

The difference comes from:

- Partition Key
- Sort Key

---

# How Does DynamoDB Differentiate Items?

Items contain different key values.

Example:

```text
PK = CUSTOMER#100

SK = PROFILE
```

Customer Profile

---

```text
PK = CUSTOMER#100

SK = ORDER#1001
```

Customer Order

---

```text
PK = CUSTOMER#100

SK = ORDER#1002
```

Another Order

---

```text
PK = CUSTOMER#100

SK = ADDRESS
```

Customer Address

Everything belongs to the same customer partition.

---

# Example Table

```text
PK                 SK

CUSTOMER#100       PROFILE

CUSTOMER#100       ORDER#1001

CUSTOMER#100       ORDER#1002

CUSTOMER#100       ADDRESS

CUSTOMER#100       PAYMENT#500
```

A single Query returns:

- Customer
- Orders
- Address
- Payments

No joins required.

---

# Visualizing the Partition

```text
Partition

CUSTOMER#100

│

├── PROFILE

├── ADDRESS

├── ORDER#1001

├── ORDER#1002

├── PAYMENT#500

└── PAYMENT#501
```

Everything is physically grouped together.

---

# Why This Is Faster

Traditional approach:

```text
API

↓

Customer Query

↓

Orders Query

↓

Payments Query

↓

Merge

↓

Response
```

Single Table Design:

```text
API

↓

Query CUSTOMER#100

↓

Response
```

One request.

Lower latency.

---

# Item Types

Multiple entities are distinguished using prefixes.

Example:

```text
CUSTOMER#

ORDER#

PRODUCT#

PAYMENT#

SHIPMENT#

INVOICE#
```

Likewise, sort keys may contain:

```text
PROFILE

ORDER#

PAYMENT#

ADDRESS

SETTINGS

WISHLIST
```

This naming convention makes the table self-describing.

---

# Composite Key Strategy

Partition Key:

```text
CUSTOMER#100
```

Sort Keys:

```text
PROFILE

ORDER#1001

ORDER#1002

ORDER#1003

PAYMENT#900

ADDRESS
```

Query:

```text
PK = CUSTOMER#100
```

Result:

Everything related to the customer.

---

# Querying Specific Items

Need only orders?

```text
PK = CUSTOMER#100

SK Begins With

ORDER#
```

Need only payments?

```text
PK = CUSTOMER#100

SK Begins With

PAYMENT#
```

Need profile?

```text
PK = CUSTOMER#100

SK = PROFILE
```

The same partition supports multiple access patterns.

---

# Another Example

Imagine a blogging platform.

Partition:

```text
USER#200
```

Contains:

```text
PROFILE

POST#100

POST#101

POST#102

COMMENT#500

FOLLOWER#700
```

Everything for one user exists together.

---

# Benefits of Single Table Design

## Fewer Queries

Most operations require only one Query.

---

## Lower Latency

Fewer database round trips.

---

## Better Scalability

No distributed joins.

---

## Lower Cost

Fewer reads.

Lower RCUs.

---

## Better Cache Performance

Entire partitions are naturally cached.

---

# Trade-Offs

Single Table Design is not free.

Challenges include:

- More planning
- Better key design
- Understanding access patterns
- More complex schema

The complexity shifts from the database engine to the application designer.

---

# When Single Table Design Works Best

Excellent for:

- E-commerce
- Banking
- Gaming
- IoT
- SaaS
- Social Media
- Messaging
- Ticket Booking

Any system with predictable access patterns benefits greatly.

---

# When Multiple Tables Are Better

Separate tables are reasonable when:

- Completely unrelated domains
- Different lifecycle requirements
- Different IAM permissions
- Different backup policies
- Different throughput requirements
- Independent ownership by separate teams

Example:

```text
Customer Analytics

↓

Separate Table
```

Production systems commonly use **a small number of tables**, not literally one table for every workload.

---

# Common Mistakes

## Creating One Table Per Entity

Example:

```text
Users

Orders

Payments

Invoices

Products
```

This recreates a relational database.

---

## Mixing Unrelated Data

Single Table Design groups **related** data.

Do not place unrelated business domains into one partition.

---

## Ignoring Access Patterns

Without understanding application queries, Single Table Design becomes difficult to maintain.

---

## Overusing GSIs

Poor table design often leads to creating many GSIs to compensate.

Good key design minimizes additional indexes.

---

# Real-World Example

Consider Amazon's order system.

When a customer opens the **"My Orders"** page, the application needs:

- Customer profile
- Recent orders
- Shipment status
- Payment information

Instead of querying multiple tables, these related entities can reside under the same partition key, allowing the service to retrieve them with a small number of efficient `Query` operations.

---

# Architecture Perspective

```text
Business Requirements

        │

        ▼

Access Patterns

        │

        ▼

Partition Key

CUSTOMER#100

        │

        ▼

Sort Keys

PROFILE

ORDER#

PAYMENT#

ADDRESS

        │

        ▼

Single DynamoDB Table

        │

        ▼

One Query

        │

        ▼

Application Response
```

The table is organized around **how the application reads data**, not around individual entity types.

---

# Interview Notes

A common interview question is:

> **Why is Single Table Design recommended in DynamoDB?**

Because DynamoDB is optimized for predictable access patterns rather than joins. Storing related entities under the same partition key reduces network calls, improves latency, and scales better in distributed environments.

Another common question is:

> **Does Single Table Design mean every application should have only one table?**

No.

Single Table Design is a modeling technique, not a rule. Many production systems use multiple DynamoDB tables to separate unrelated business domains, security boundaries, retention policies, or throughput requirements. Within a domain, however, related entities are often modeled in a single table.

---

# Key Takeaways

- Single Table Design stores multiple related entity types in one DynamoDB table.
- Related data is grouped using a shared partition key and differentiated with sort key prefixes.
- The approach eliminates joins by organizing data around access patterns.
- Prefixes such as `CUSTOMER#`, `ORDER#`, and `PAYMENT#` make mixed entity types easy to identify.
- Single Table Design improves scalability, reduces latency, and lowers costs by minimizing database requests.
- It requires careful planning and is most effective when access patterns are well understood.