# 13 - Materialized Graph Pattern

## Overview

The **Adjacency List Pattern** allows applications to efficiently retrieve **direct relationships**.

However, many production systems require queries that span **multiple levels** of a graph.

Examples include:

- Organization hierarchies
- Product categories
- Folder structures
- Team reporting chains
- Bill of Materials (BOM)
- Permission inheritance

Traversing these hierarchies one node at a time requires multiple database queries.

The **Materialized Graph Pattern** solves this by storing additional relationship information so that higher-level graph traversals require fewer queries.

This is an example of DynamoDB's fundamental philosophy:

> **Duplicate data to optimize reads.**

---

# The Problem

Suppose an organization looks like this.

```text
CEO

│

├── VP Engineering

│      │

│      ├── Engineering Manager

│      │        │

│      │        ├── Developer A

│      │        └── Developer B

│

└── VP Sales
```

Question:

> Show everyone reporting to the CEO.

Using an Adjacency List:

```text
CEO

↓

VP Engineering

↓

Engineering Manager

↓

Developers
```

Requires multiple queries.

---

# Why This Becomes Expensive

Graph traversal becomes:

```text
CEO

↓

Query

↓

VP

↓

Query

↓

Manager

↓

Query

↓

Employees
```

Each level adds:

- Network latency
- Database requests
- Application complexity

---

# Materialized Graph Philosophy

Instead of computing relationships every time:

Store them.

Example:

```text
Developer

↓

Manager

↓

Director

↓

CEO
```

Each employee stores enough information to answer hierarchy queries efficiently.

---

# Example Table

```text
PK = EMPLOYEE#100

SK = PROFILE
```

Attributes:

```text
Manager = EMPLOYEE#20

Department = Engineering

Path = CEO/VP/Manager
```

Another employee:

```text
PK = EMPLOYEE#101

SK = PROFILE

Path = CEO/VP/Manager
```

Now multiple hierarchy queries become possible.

---

# Materialized Path

One common implementation stores the complete path.

Example:

```text
CEO

↓

VP

↓

Manager

↓

Developer
```

Stored as:

```text
CEO

/

VP

/

Manager

/

Developer
```

Or:

```text
CEO#VP#Manager#Developer
```

This is called a **Materialized Path**.

---

# Folder Structure Example

Folders:

```text
Root

↓

Documents

↓

Projects

↓

AWS
```

Store:

```text
Root/Documents/Projects/AWS
```

Applications can determine the full hierarchy immediately.

---

# Organization Example

Employee:

```text
Developer
```

Path:

```text
CEO

↓

Engineering VP

↓

Platform Manager

↓

Developer
```

Stored as:

```text
CEO#VP#Manager#Developer
```

Useful for:

- Org charts
- Reporting
- Permissions

---

# Product Category Example

Categories:

```text
Electronics

↓

Computers

↓

Laptops

↓

Gaming
```

Store:

```text
Electronics

/

Computers

/

Laptops

/

Gaming
```

Applications immediately know the complete category tree.

---

# Permission Systems

Enterprise systems often inherit permissions.

Example:

```text
Company

↓

Department

↓

Team

↓

User
```

Instead of calculating inheritance every request,

store:

```text
Company

↓

Department

↓

Team
```

inside the user record.

Authorization becomes faster.

---

# Bill of Materials (BOM)

Manufacturing systems frequently use:

```text
Car

↓

Engine

↓

Fuel System

↓

Injector
```

Each component stores:

```text
Car

↓

Engine

↓

Fuel System
```

Applications can trace dependencies quickly.

---

# Materialized Graph with GSIs

Suppose employees store:

```text
ManagerID

Department

Level
```

Create a GSI:

```text
PK = ManagerID

SK = EmployeeID
```

Now retrieving:

```text
Direct Reports
```

is efficient.

Additional attributes support richer graph queries.

---

# Data Duplication

Materialized Graphs intentionally duplicate information.

Instead of:

```text
Developer

↓

Manager
```

Store:

```text
Manager

Director

VP

CEO
```

inside the employee record.

Storage increases.

Reads become much faster.

---

# Read vs Write Trade-Off

Without Materialized Graph:

Reads:

```text
Many Queries
```

Writes:

```text
Simple
```

With Materialized Graph:

Reads:

```text
One Query
```

Writes:

```text
Must Update

Multiple Items
```

The pattern optimizes read performance at the expense of more complex writes.

---

# Updating Hierarchies

Suppose:

```text
Manager

↓

Changes
```

All descendants may require updates.

Example:

```text
Developer A

Developer B

Developer C
```

Each stored path changes.

Large hierarchy updates may involve:

- Batch operations
- DynamoDB Streams
- Lambda
- Step Functions

---

# Performance Considerations

Materialized Graphs perform well when:

- Reads greatly outnumber writes.
- Hierarchies change infrequently.
- Fast graph lookups are required.

They perform less well when:

- Relationships change constantly.
- Graphs are highly dynamic.

---

# Real-World Example

A cloud IAM platform stores organizational units.

Hierarchy:

```text
Organization

↓

Division

↓

Department

↓

Team

↓

User
```

Instead of traversing the hierarchy for every authorization request, each user stores:

```text
Organization

↓

Division

↓

Department

↓

Team
```

Permission checks become significantly faster.

---

# Best Practices

- Duplicate hierarchy information intentionally.
- Keep paths consistent.
- Use descriptive delimiters.
- Automate hierarchy updates.
- Combine with GSIs when alternate lookups are needed.
- Keep frequently changing hierarchies as small as possible.

---

# Common Mistakes

## Computing Hierarchies on Every Request

Avoid repeated recursive queries.

Materialize the hierarchy instead.

---

## Ignoring Update Costs

Hierarchy changes may require updating many records.

Design update workflows before deployment.

---

## Storing Unnecessary Data

Store only information required by your access patterns.

Avoid bloated items.

---

## Choosing the Wrong Pattern

If only direct relationships are required,

an Adjacency List is usually sufficient.

Use Materialized Graphs only when higher-level traversals are common.

---

# Adjacency List vs Materialized Graph

| Feature | Adjacency List | Materialized Graph |
|----------|----------------|-------------------|
| Direct Relationships | Excellent | Excellent |
| Multi-Level Traversal | Multiple Queries | Often Single Query |
| Storage | Low | Higher |
| Write Complexity | Low | Higher |
| Read Performance | Moderate | Excellent |
| Data Duplication | Minimal | High |

---

# Architecture Perspective

```text
Application

        │

        ▼

Query Employee

        │

        ▼

EMPLOYEE#500

        │

        ├── Profile

        ├── ManagerID

        ├── Department

        ├── Organization Path

        └── Access Level

        │

        ▼

Application Response
```

The application retrieves both the employee and the relevant hierarchy information in a single read, avoiding recursive graph traversal.

---

# Production Considerations

Large organizations often combine this pattern with:

- Global Secondary Indexes
- DynamoDB Streams
- AWS Lambda
- EventBridge
- Step Functions

These services help synchronize hierarchy updates whenever organizational structures change.

---

# Interview Notes

A common interview question is:

> **What is the Materialized Graph Pattern?**

It is a DynamoDB data modeling pattern where hierarchical or graph relationship information is stored directly within items instead of being calculated through recursive queries. This improves read performance by trading additional storage and write complexity.

Another common question is:

> **When should you use a Materialized Graph instead of an Adjacency List?**

Use an Adjacency List when only direct relationships are queried. Use a Materialized Graph when applications frequently need to retrieve ancestors, descendants, or complete hierarchy paths with minimal database requests.

Another common question is:

> **What is the biggest trade-off of the Materialized Graph Pattern?**

Hierarchy updates become more expensive because duplicated relationship data must remain synchronized across multiple items.

---

# Key Takeaways

- The Materialized Graph Pattern stores hierarchy information directly within items.
- It reduces recursive graph traversal and minimizes database queries.
- The pattern intentionally duplicates data to optimize read performance.
- It is ideal for organizational hierarchies, folder trees, permission systems, and product categories.
- Hierarchy updates are more complex and often require automation.
- Materialized Graphs are most effective when read performance is more important than write simplicity.