# 01 - Data Modeling Principles

## Overview

Designing a DynamoDB database is fundamentally different from designing a relational database.

Most engineers coming from MySQL, PostgreSQL, Oracle, or SQL Server begin by asking:

> "What tables do I need?"

That is the wrong question in DynamoDB.

Instead, the first question should always be:

> **How will my application access the data?**

This simple shift in thinking changes everything.

Relational databases are designed around **entities and relationships**.

DynamoDB is designed around **access patterns**.

Understanding this difference is the foundation of every successful DynamoDB application.

---

# SQL Mindset vs DynamoDB Mindset

Traditional databases encourage normalization.

```text
Customer

↓

Orders

↓

Payments

↓

Products

↓

JOIN
```

Data is split into multiple tables.

Queries reconstruct the information using joins.

---

DynamoDB takes the opposite approach.

```text
Application Query

↓

Design Keys

↓

Store Data Together

↓

Single Read
```

Instead of minimizing duplicated data, DynamoDB minimizes database requests.

---

# Why DynamoDB Thinks Differently

Distributed databases have a unique challenge.

Imagine:

```text
Customer

↓

Server A
```

Orders:

```text
Server B
```

Products:

```text
Server C
```

A SQL JOIN now becomes:

```text
Server A

↓

Server B

↓

Server C

↓

Combine Results
```

Across thousands of machines this becomes extremely expensive.

DynamoDB avoids this entirely by encouraging related data to be stored together.

---

# The Golden Rule

Always model your database around **how data is read**.

Not:

```text
Entities
```

Instead:

```text
Access Patterns
```

Everything else follows from this principle.

---

# What Is an Access Pattern?

An access pattern describes:

> **How an application retrieves or modifies data.**

Examples:

```text
Get Customer

Get Order

List Orders

Find Orders By Customer

Latest Notifications

Shopping Cart

User Timeline
```

Each of these represents an application requirement.

---

# Example

Suppose an API exposes:

```http
GET /customers/123/orders
```

Instead of designing:

```text
Customers

Orders
```

Design around:

```text
CustomerId

↓

All Orders
```

One query.

No joins.

---

# Identify Access Patterns First

Before writing any schema, create a list.

Example:

```text
Customer

↓

View Profile
```

```text
Customer

↓

Update Address
```

```text
Customer

↓

View Orders
```

```text
Admin

↓

Search Customer
```

```text
Warehouse

↓

Pending Shipments
```

These become the blueprint for your database.

---

# Think About Reads More Than Writes

Many applications are read-heavy.

Example:

```text
Instagram

Reads

>>>>>>>>>

Writes
```

Netflix:

```text
Movie Reads

>>>>>>>>>>>>>>>>>

Movie Updates
```

E-commerce:

```text
Browse Products

>>>>>>>>>

Create Product
```

Optimizing for reads usually provides the greatest performance benefit.

---

# Denormalization Is a Feature

SQL developers often fear duplicated data.

DynamoDB embraces it.

Instead of:

```text
Order

↓

JOIN Customer

↓

JOIN Address
```

Store:

```text
Order

CustomerName

ShippingAddress

CustomerTier
```

Storage is inexpensive.

Network latency is not.

---

# Design for One Query

An ideal DynamoDB operation looks like:

```text
API Request

↓

Single Query

↓

Response
```

Not:

```text
Query

↓

Query

↓

Query

↓

Merge

↓

Return
```

The fewer round trips, the better.

---

# Think About Scale Early

Imagine today's traffic:

```text
100 Requests/sec
```

Now imagine:

```text
100,000 Requests/sec
```

Would the same schema work?

If not:

Redesign before production.

---

# Design Around Partitions

Every item eventually belongs to a partition.

Good design:

```text
Millions of Keys

↓

Millions of Partitions
```

Poor design:

```text
One Popular Key

↓

One Busy Partition
```

Good modeling naturally distributes workload.

---

# Avoid SQL Habits

Developers often try to recreate SQL concepts.

Examples:

```text
JOIN

Foreign Keys

Normalization

Cross-table Queries
```

Instead embrace:

```text
Partition Keys

Sort Keys

GSIs

Denormalization

Access Patterns
```

---

# Data Modeling Workflow

A typical design process looks like:

```text
Business Requirements

↓

API Endpoints

↓

Access Patterns

↓

Partition Key

↓

Sort Key

↓

Indexes

↓

Capacity Planning

↓

Implementation
```

Notice that table design comes **after** understanding the application.

---

# Example: E-Commerce

Requirements:

```text
View Product

↓

Add To Cart

↓

Checkout

↓

View Orders

↓

Track Shipment
```

These become access patterns.

The access patterns determine:

- Keys
- Sort keys
- GSIs
- Item structure

Not the other way around.

---

# Benefits of Access-Pattern Design

Applications become:

- Faster
- More scalable
- Less expensive
- Easier to cache
- Easier to scale globally

Most importantly:

Database requests remain predictable.

---

# Common Mistakes

## Designing Tables First

Wrong approach:

```text
Users

Orders

Products
```

Without understanding how the application uses them.

---

## Copying SQL Schemas

A normalized relational schema usually performs poorly in DynamoDB.

---

## Ignoring Future Access Patterns

Adding a new access pattern later may require:

- New GSIs
- Data migration
- Schema redesign

Planning early avoids expensive changes.

---

## Optimizing for Storage

Saving storage by normalizing data often increases:

- Reads
- Latency
- Cost

Optimize for request efficiency instead.

---

# Real-World Example

Amazon's shopping cart service is designed around customer interactions:

```text
Customer

↓

View Cart

↓

Update Quantity

↓

Checkout
```

The database is optimized so each operation requires as few requests as possible, even if some customer or product information is duplicated across items.

---

# Architecture Perspective

```text
Business Requirements

↓

API Design

↓

Access Patterns

↓

Data Model

↓

Partition Key Design

↓

Sort Key Design

↓

Indexes

↓

Capacity Planning

↓

Production Deployment
```

Every decision flows from understanding how the application uses the data.

---

# Interview Notes

A common interview question is:

> **What is the biggest difference between SQL data modeling and DynamoDB data modeling?**

Relational databases model **entities and relationships** first, then write queries.

DynamoDB models **access patterns** first, then designs keys and item structures to satisfy those patterns efficiently.

Another common question is:

> **Why does DynamoDB encourage denormalization?**

Because distributed joins are expensive. Storing related data together reduces network calls, lowers latency, and enables predictable single-query access.

---

# Key Takeaways

- DynamoDB data modeling starts with **access patterns**, not tables.
- Design for the queries your application will execute most frequently.
- Denormalization is a deliberate optimization strategy.
- Minimize the number of database requests per API call.
- High-quality partition key design is a direct result of understanding access patterns.
- A well-designed data model can scale from hundreds to millions of requests per second without requiring schema changes.