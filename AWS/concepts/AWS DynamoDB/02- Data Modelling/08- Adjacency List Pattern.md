# 08 - Adjacency List Pattern

## Overview

Many real-world systems contain **graph-like relationships** where entities are connected to one another rather than existing in simple parent-child hierarchies.

Examples include:

- Social networks
- Followers and following
- Friends
- Employees and managers
- Organizational hierarchies
- Network topologies
- Product recommendations
- Dependency graphs

Relational databases typically model these relationships using **join tables** and recursive queries.

DynamoDB approaches the problem differently using the **Adjacency List Pattern**.

Instead of traversing relationships through joins, each entity explicitly stores its immediate connections, allowing efficient traversal using `Query` operations.

---

# What is an Adjacency List?

An adjacency list represents:

> **A node and all of its directly connected neighbors.**

Instead of storing an entire graph, each node stores only the nodes directly connected to it.

Example:

```text
Alice

↓

Bob

Charlie

David
```

Alice does not store the entire social network.

She stores only her immediate relationships.

---

# Why Is This Pattern Useful?

Many applications need to answer questions like:

- Who follows this user?
- Who reports to this manager?
- Which services depend on this microservice?
- Which users belong to this group?
- Which products are related?

These relationships naturally form graphs.

---

# SQL Approach

Consider an employee hierarchy.

```text
Employees

EmployeeID

Name
```

Relationship table:

```text
EmployeeManager

EmployeeID

ManagerID
```

Query:

```sql
SELECT *

FROM Employees

JOIN EmployeeManager

ON ...
```

Multiple joins become increasingly expensive as the hierarchy grows.

---

# DynamoDB Approach

Instead of joins:

Store relationships directly.

Example:

```text
PK = USER#100

SK = FRIEND#200
```

```text
PK = USER#100

SK = FRIEND#300
```

```text
PK = USER#100

SK = FRIEND#400
```

All friendships belong to one partition.

---

# Example Table

```text
PK              SK

USER#100        PROFILE

USER#100        FRIEND#200

USER#100        FRIEND#300

USER#100        FRIEND#400
```

Query:

```text
PK = USER#100
```

Returns:

- User Profile
- Friend 200
- Friend 300
- Friend 400

---

# Visual Representation

```text
USER#100

│

├── PROFILE

├── FRIEND#200

├── FRIEND#300

└── FRIEND#400
```

Every connection is stored as an item.

---

# Social Network Example

Suppose:

```text
Alice

↓

Bob

Charlie

David
```

Table:

```text
PK = USER#Alice

SK = FRIEND#Bob
```

```text
PK = USER#Alice

SK = FRIEND#Charlie
```

```text
PK = USER#Alice

SK = FRIEND#David
```

Query:

```text
USER#Alice
```

Returns every direct friendship.

---

# Bidirectional Relationships

Friendships are usually mutual.

Instead of:

```text
Alice

↓

Bob
```

Store:

```text
Alice

↓

Bob
```

and

```text
Bob

↓

Alice
```

Example:

```text
PK = USER#Alice

SK = FRIEND#Bob
```

```text
PK = USER#Bob

SK = FRIEND#Alice
```

Now both users can retrieve their friend lists efficiently.

---

# Directed Relationships

Some relationships are **not** bidirectional.

Example:

Twitter.

```text
Alice

↓

Follows

↓

Bob
```

Bob does not automatically follow Alice.

Table:

```text
PK = USER#Alice

SK = FOLLOWING#Bob
```

Need followers?

Create another access path.

```text
PK = USER#Bob

SK = FOLLOWER#Alice
```

Or build a GSI.

---

# Organization Chart Example

Company:

```text
CEO

↓

VP

↓

Manager

↓

Engineer
```

Manager partition:

```text
PK = EMPLOYEE#Manager100

SK = REPORT#Employee201

SK = REPORT#Employee202

SK = REPORT#Employee203
```

Query:

```text
Manager

↓

Direct Reports
```

One Query.

---

# Product Recommendation Example

Amazon frequently recommends related products.

Example:

```text
Laptop

↓

Mouse

Keyboard

Dock

Monitor
```

Table:

```text
PK = PRODUCT#Laptop

SK = RELATED#Mouse

SK = RELATED#Keyboard

SK = RELATED#Dock

SK = RELATED#Monitor
```

Application:

```text
View Product

↓

Related Products
```

Single Query.

---

# Service Dependency Graph

Microservices often depend on one another.

Example:

```text
Payment Service

↓

Inventory

↓

Notification

↓

Audit
```

Table:

```text
PK = SERVICE#Payment

SK = DEPENDS_ON#Inventory

SK = DEPENDS_ON#Notification

SK = DEPENDS_ON#Audit
```

Useful for:

- Deployment planning
- Dependency visualization
- Impact analysis

---

# Traversing Relationships

Suppose:

```text
Alice

↓

Bob

↓

Charlie
```

First Query:

```text
USER#Alice
```

Returns:

```text
Bob
```

Second Query:

```text
USER#Bob
```

Returns:

```text
Charlie
```

Graph traversal occurs one level at a time.

---

# Advantages

The Adjacency List Pattern offers:

- Efficient relationship queries
- Horizontal scalability
- Simple writes
- Predictable latency
- Flexible graph modeling

---

# Limitations

It is optimized for:

```text
Direct Relationships
```

It is **not** ideal for:

- Deep graph traversal
- Shortest path algorithms
- Complex graph analytics
- Multi-hop queries

Those workloads are better suited to graph databases like Amazon Neptune.

---

# When to Use Amazon Neptune Instead

If your application frequently asks:

```text
Find friends of friends

↓

Find shortest path

↓

Recommend based on graph distance
```

DynamoDB becomes increasingly inefficient.

Amazon Neptune is purpose-built for these graph traversal workloads.

---

# Best Practices

- Store only immediate relationships.
- Keep relationship items lightweight.
- Duplicate relationships when bidirectional access is required.
- Use GSIs for alternate traversal paths.
- Design relationship keys with descriptive prefixes.
- Avoid deep recursive traversals inside DynamoDB.

---

# Common Mistakes

## Trying to Store the Entire Graph

Each partition should represent only one node and its direct neighbors.

---

## Forgetting Reverse Relationships

If the application requires:

```text
A → B

and

B → A
```

Both relationships must exist.

---

## Storing Large Objects

Relationship items should contain:

- IDs
- Relationship metadata

Retrieve full entity details separately.

---

## Using DynamoDB for Complex Graph Analytics

DynamoDB excels at key-value access patterns.

It is not a graph analytics engine.

---

# Real-World Example

A professional networking platform stores user connections.

Partition:

```text
PK = USER#500
```

Contains:

```text
PROFILE

CONNECTION#100

CONNECTION#250

CONNECTION#720

CONNECTION#900
```

The application retrieves a user's professional network with a single `Query`, while reverse connections are maintained separately to support reciprocal lookups.

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

        ├── FRIEND#100

        ├── FRIEND#250

        ├── FRIEND#720

        └── FRIEND#900

        │

        ▼

Application Response
```

The partition represents one node in the graph and all of its directly connected neighbors.

---

# Interview Notes

A common interview question is:

> **What is the Adjacency List Pattern in DynamoDB?**

It is a data modeling technique where each entity stores its direct relationships as individual items under the same partition key. This enables efficient graph-like traversals using `Query` operations without requiring joins.

Another common question is:

> **When should you use DynamoDB versus Amazon Neptune for graph data?**

Use DynamoDB when relationships are shallow and access patterns are predictable, such as followers, memberships, or organizational hierarchies. Use Amazon Neptune when applications require deep graph traversal, shortest-path calculations, recommendation engines, or complex graph analytics.

---

# Key Takeaways

- The Adjacency List Pattern models graph relationships using partition keys and relationship items.
- Each partition represents one node and its immediate neighbors.
- Bidirectional relationships are usually modeled by storing two relationship records.
- The pattern is ideal for social networks, hierarchies, memberships, and service dependencies.
- DynamoDB efficiently handles direct relationship lookups but is not designed for complex graph traversals.
- For advanced graph workloads, Amazon Neptune is the more appropriate database.