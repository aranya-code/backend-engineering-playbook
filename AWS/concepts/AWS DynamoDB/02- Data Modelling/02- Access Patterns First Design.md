# 02 - Access Patterns First Design

## Overview

If there is one principle that defines successful DynamoDB design, it is this:

> **Design your database around how the application accesses data—not around how the data is stored.**

This concept is called **Access Pattern First Design**.

Unlike relational databases, where tables are designed first and queries come later, DynamoDB follows the opposite approach.

```text
Relational Database

Tables
    ↓
Relationships
    ↓
Queries
```

```text
DynamoDB

Business Requirements
        ↓
API Endpoints
        ↓
Access Patterns
        ↓
Keys
        ↓
Table Design
```

The database exists to efficiently answer application queries.

Everything else is secondary.

---

# What Is an Access Pattern?

An access pattern describes:

> **How an application reads, writes, updates, or deletes data.**

Examples include:

```text
Get Customer Profile

Get Order Details

List Customer Orders

Search Product

View Shopping Cart

Latest Notifications

Recent Transactions
```

Every button in your application usually represents one or more access patterns.

---

# Thinking Like a Backend Engineer

Suppose you are building an e-commerce platform.

Your instinct may be:

```text
Customers

Orders

Products

Payments

Invoices
```

That is a database-first approach.

Instead, ask:

```text
What APIs will my application expose?
```

Example:

```http
GET /customers/{id}

GET /customers/{id}/orders

GET /orders/{id}

POST /orders

PUT /orders/{id}

DELETE /cart/{id}
```

These APIs become your access patterns.

---

# Access Patterns Drive Schema Design

Business requirement:

```text
Customer wants to see recent orders.
```

Access pattern:

```text
Get Orders

WHERE CustomerId = ?
```

Now ask:

> Can this query be answered with a single DynamoDB Query operation?

If yes:

Good design.

If no:

The schema probably needs improvement.

---

# Step 1 – Gather Business Requirements

Everything starts with business requirements.

Example:

```text
Users can:

• Register
• Login
• View Profile
• Update Profile
• Place Orders
• View Orders
• Track Shipments
```

These are not database entities.

They are business capabilities.

---

# Step 2 – Convert Requirements into APIs

The backend team creates endpoints.

```http
POST /users

POST /login

GET /users/{id}

PUT /users/{id}

POST /orders

GET /users/{id}/orders

GET /orders/{id}
```

Now we know how the application will communicate.

---

# Step 3 – Extract Access Patterns

From those APIs:

| API | Access Pattern |
|------|----------------|
| GET /users/{id} | Retrieve user by ID |
| PUT /users/{id} | Update user |
| GET /users/{id}/orders | Retrieve all orders for a user |
| GET /orders/{id} | Retrieve order by ID |
| POST /orders | Create order |

Notice something.

There are **no tables** yet.

---

# Step 4 – Identify Query Conditions

Every access pattern should answer:

```text
What information do I already know?
```

Example:

```http
GET /orders/12345
```

Known:

```text
OrderId
```

Unknown:

```text
Everything else
```

Good candidate:

```text
Partition Key

↓

OrderId
```

---

Example:

```http
GET /customers/100/orders
```

Known:

```text
CustomerId
```

Need:

```text
All Orders
```

Possible design:

```text
PK = CUSTOMER#100

SK = ORDER#1001

SK = ORDER#1002

SK = ORDER#1003
```

One query retrieves every order.

---

# Step 5 – Design Keys Around Queries

Poor design:

```text
Orders Table

↓

Scan

↓

Find Customer Orders
```

Better:

```text
PK = CUSTOMER#100

Query

↓

All Orders
```

Notice the difference.

The query determines the key.

---

# Access Pattern Example

Imagine a music streaming service.

Requirements:

```text
View Artist

View Album

Play Song

Recently Played

Favorite Songs

Search Artist

Recommendations
```

These become access patterns.

Not:

```text
Artist Table

Album Table

Song Table
```

---

# API → Access Pattern Mapping

| API Endpoint | Partition Key Candidate | Sort Key Candidate |
|--------------|------------------------|-------------------|
| GET /users/{id} | USER#123 | PROFILE |
| GET /users/{id}/orders | USER#123 | ORDER#* |
| GET /orders/{id} | ORDER#500 | METADATA |
| GET /products/{id} | PRODUCT#20 | DETAILS |
| GET /cart/{id} | USER#123 | CART |

Notice:

The API naturally suggests the key structure.

---

# Thinking About Read Frequency

Suppose an application performs:

```text
Login

5 Million/day
```

Profile update:

```text
20,000/day
```

Analytics export:

```text
Once/day
```

Should all operations be optimized equally?

No.

Optimize:

```text
Most Frequent Reads
```

Rare administrative operations can tolerate slower queries.

---

# Design for a Single Query

Ideal request flow:

```text
API Request

↓

Query

↓

Return Result
```

Avoid:

```text
Query

↓

Query

↓

Scan

↓

Merge

↓

Return
```

Multiple database requests increase:

- Latency
- Cost
- Complexity

---

# Example – Social Media Feed

Requirement:

```text
Show Latest Posts
```

Bad approach:

```text
Scan All Posts

↓

Filter User

↓

Sort

↓

Return
```

Good approach:

```text
PK = USER#123

SK = POST#Timestamp

Query

↓

Latest Posts
```

---

# Example – Banking System

Requirement:

```text
View Recent Transactions
```

Design:

```text
PK = ACCOUNT#789

SK

2026-07-01

2026-07-02

2026-07-03
```

Query:

```text
PK = ACCOUNT#789

LIMIT 20
```

Single efficient request.

---

# Validate Every Access Pattern

For every API ask:

```text
Can I retrieve this data
using one Query?
```

If not:

Consider:

- Different partition key
- Different sort key
- Global Secondary Index (GSI)
- Data duplication

---

# Access Pattern Matrix

Example:

| Business Requirement | API | DynamoDB Operation |
|----------------------|-----|--------------------|
| View Profile | GET /users/{id} | GetItem |
| View Orders | GET /users/{id}/orders | Query |
| View Product | GET /products/{id} | GetItem |
| View Notifications | GET /notifications | Query |
| Checkout | POST /checkout | PutItem + Transaction |

Creating this matrix before implementation helps identify missing indexes and inefficient queries.

---

# Benefits of Access Pattern First Design

Applications become:

- Faster
- More predictable
- Easier to scale
- Less expensive
- Simpler to maintain

Most importantly:

Performance remains consistent as traffic grows.

---

# Common Mistakes

## Designing Tables Before APIs

Many developers immediately create:

```text
Users

Orders

Products
```

without understanding application requirements.

---

## Optimizing Rare Queries

Do not sacrifice performance for millions of users to optimize an administrative report run once per month.

---

## Using Scan Because It's Easy

Scans may work during development but often become bottlenecks in production.

Design schemas that enable Query operations instead.

---

## Ignoring Future Features

Ask:

```text
What features might be added next year?
```

Planning for likely future access patterns can reduce costly schema changes.

---

# Real-World Example

An online food delivery application supports:

- View nearby restaurants
- Browse menus
- Place orders
- Track deliveries
- View order history

Instead of creating database tables first, engineers list these operations, identify the required queries, and then design partition keys, sort keys, and indexes to satisfy each operation with minimal database requests.

---

# Architecture Perspective

```text
Business Requirements

        │

        ▼

API Endpoints

        │

        ▼

Access Pattern Matrix

        │

        ▼

Partition Key Design

        │

        ▼

Sort Key Design

        │

        ▼

Secondary Indexes

        │

        ▼

DynamoDB Table
```

Every design decision is driven by how the application accesses data.

---

# Interview Notes

A common interview question is:

> **Why do we identify access patterns before designing a DynamoDB table?**

Because DynamoDB does not support arbitrary joins or ad hoc queries efficiently. Designing around access patterns ensures that the application's most common operations can be satisfied using efficient `GetItem` or `Query` operations.

Another common question is:

> **What information do you collect before creating a DynamoDB schema?**

A senior engineer should gather:

- Business requirements
- API endpoints
- Read and write frequency
- Query conditions
- Sorting requirements
- Expected traffic volume
- Scalability expectations
- Latency requirements

Only after understanding these requirements should keys and indexes be designed.

---

# Key Takeaways

- Every API endpoint represents one or more access patterns.
- Business requirements should drive schema design—not the other way around.
- Identify known query values before choosing partition and sort keys.
- Aim to satisfy every critical access pattern with a single `GetItem` or `Query` operation.
- Use an access pattern matrix to validate that all application requirements are covered.
- Access Pattern First Design is the foundation of scalable, production-ready DynamoDB applications.