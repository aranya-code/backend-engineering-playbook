# 06 - Many-to-Many Relationships

## Overview

Many-to-many relationships are among the most challenging relationships to model in DynamoDB.

Examples include:

- Students enroll in many courses.
- Courses have many students.
- Users join many groups.
- Groups contain many users.
- Actors appear in many movies.
- Movies have many actors.

In relational databases, these relationships are typically solved using a **junction (bridge) table**.

In DynamoDB, there are no joins or bridge tables. Instead, many-to-many relationships are modeled using **multiple items**, **carefully designed keys**, and often **Global Secondary Indexes (GSIs)**.

The goal remains the same:

> Retrieve related data using efficient `Query` operations instead of expensive scans.

---

# Understanding Many-to-Many

Unlike one-to-many:

```text
Customer

↓

Orders
```

Many-to-many works both directions.

Example:

```text
Student

↓

Course

↑
```

Each student belongs to many courses.

Each course contains many students.

---

# SQL Approach

Relational databases solve this using a junction table.

```text
Students

StudentID
Name
```

```text
Courses

CourseID
Title
```

```text
Enrollments

StudentID

CourseID
```

Relationship:

```text
Student

↓

Enrollment

↓

Course
```

Query:

```sql
Students

JOIN Enrollments

JOIN Courses
```

Simple in SQL.

Not possible in DynamoDB.

---

# DynamoDB Philosophy

Instead of joins:

Store relationship records.

Example:

```text
Student

↓

Enrollment Item

↓

Course
```

Each enrollment becomes its own DynamoDB item.

---

# Example Table

Suppose:

Student:

```text
Alice
```

is enrolled in:

```text
Python

AWS

Redis
```

Table:

```text
PK                  SK

STUDENT#100         PROFILE

STUDENT#100         COURSE#Python

STUDENT#100         COURSE#AWS

STUDENT#100         COURSE#Redis
```

Now retrieving all courses becomes simple.

---

# Query Student's Courses

```text
PK = STUDENT#100
```

Returns:

```text
PROFILE

COURSE#Python

COURSE#AWS

COURSE#Redis
```

Single Query.

---

# But What About the Reverse?

Business requirement:

```text
List Students

Enrolled In

AWS
```

Current table:

```text
PK = STUDENT#
```

Cannot efficiently answer:

```text
COURSE → STUDENTS
```

Need another access path.

---

# Option 1 – Duplicate Relationship Items

One common solution is to duplicate the relationship.

```text
PK = STUDENT#100

SK = COURSE#AWS
```

Also create:

```text
PK = COURSE#AWS

SK = STUDENT#100
```

Now:

```text
Student

↓

Courses
```

AND

```text
Course

↓

Students
```

Both become Query operations.

---

# Visual Representation

```text
STUDENT#100

│

├── COURSE#Python

├── COURSE#AWS

└── COURSE#Redis
```

Another partition:

```text
COURSE#AWS

│

├── STUDENT#100

├── STUDENT#102

├── STUDENT#205

└── STUDENT#301
```

Both directions are optimized.

---

# Option 2 – Global Secondary Index (GSI)

Instead of duplicating data, another option is using a GSI.

Primary table:

```text
PK = STUDENT#100

SK = COURSE#AWS
```

Attributes:

```text
StudentId

CourseId
```

GSI:

```text
Partition Key

↓

CourseId
```

Now:

```text
Query GSI

↓

All Students

For AWS
```

---

# Comparing Both Approaches

| Approach | Advantages | Disadvantages |
|----------|------------|---------------|
| Duplicate Relationship Items | Fast queries in both directions | More storage and additional writes |
| Global Secondary Index | Less duplicated data | Additional write cost and index maintenance |

Both approaches are widely used.

---

# Example – GitHub

Relationship:

```text
Developer

↓

Repositories
```

Reverse:

```text
Repository

↓

Contributors
```

Table:

```text
PK = USER#John

SK = REPO#Backend
```

Also:

```text
PK = REPO#Backend

SK = USER#John
```

Retrieving either direction requires one Query.

---

# Example – Social Media Groups

Requirement:

```text
User

↓

Groups
```

Reverse:

```text
Group

↓

Members
```

Data:

```text
PK = USER#500

SK = GROUP#AWS
```

Also:

```text
PK = GROUP#AWS

SK = USER#500
```

Simple.

Scalable.

---

# Example – Movie Database

Actor:

```text
Tom
```

Movies:

```text
Movie A

Movie B

Movie C
```

Relationship:

```text
PK = ACTOR#Tom

SK = MOVIE#A
```

Reverse:

```text
PK = MOVIE#A

SK = ACTOR#Tom
```

Both searches become efficient.

---

# Write Workflow

Creating an enrollment:

```text
Student

↓

Enroll

↓

Write

Student → Course

↓

Write

Course → Student
```

Two writes.

Much faster than expensive scans during reads.

---

# Read Workflow

Retrieve courses.

```text
Query

PK = STUDENT#100
```

Retrieve students.

```text
Query

PK = COURSE#AWS
```

No joins.

No scans.

---

# Trade-Offs

Many-to-many relationships require:

- More planning
- More writes
- More storage

But provide:

- Fast reads
- Predictable performance
- Horizontal scalability

This is an intentional trade-off in DynamoDB.

---

# When to Duplicate Data

Duplicate data when:

- Reads greatly outnumber writes.
- Low latency is important.
- Bidirectional access is common.
- Storage cost is acceptable.

Storage is relatively inexpensive compared to network latency and database joins.

---

# Performance Considerations

Every enrollment requires:

```text
2 Writes
```

But every lookup requires:

```text
1 Query
```

Production systems often optimize for reads because they occur far more frequently than writes.

---

# Best Practices

- Model relationships based on access patterns.
- Optimize both directions if both are frequently queried.
- Use descriptive key prefixes.
- Consider GSIs for alternate access paths.
- Accept data duplication when it improves read performance.
- Keep relationship items lightweight.

---

# Common Mistakes

## Trying to Recreate SQL Joins

DynamoDB is not designed for runtime joins.

Model relationships explicitly.

---

## Using Scan for Reverse Lookups

Avoid:

```text
Scan

↓

Find Students

For Course
```

Use duplicated relationship items or GSIs.

---

## Storing Large Objects in Relationship Items

Relationship records should only contain:

- Keys
- Essential metadata

Retrieve full entity details separately if necessary.

---

## Forgetting Bidirectional Access

Ask:

```text
Will users search

Both Directions?
```

If yes:

Design both access paths from the beginning.

---

# Real-World Example

An online learning platform stores enrollments.

Requirement:

- View all courses for a student.
- View all students enrolled in a course.

Data model:

```text
PK = STUDENT#500

SK = COURSE#AWS
```

and

```text
PK = COURSE#AWS

SK = STUDENT#500
```

This allows both API endpoints to execute using efficient `Query` operations, regardless of the number of students or courses.

---

# Architecture Perspective

```text
Student

        │

        ▼

STUDENT#500

        │

        ├── COURSE#Python

        ├── COURSE#AWS

        └── COURSE#Redis

────────────────────────────

Course

        │

        ▼

COURSE#AWS

        │

        ├── STUDENT#100

        ├── STUDENT#500

        ├── STUDENT#700

        └── STUDENT#900
```

Notice that relationships are represented explicitly in the data model rather than being computed through joins at query time.

---

# Interview Notes

A common interview question is:

> **How do you model a many-to-many relationship in DynamoDB?**

A common solution is to create relationship items that can be queried efficiently from both directions. This is often implemented by duplicating relationship records (for example, `STUDENT → COURSE` and `COURSE → STUDENT`) or by using a Global Secondary Index (GSI) when appropriate.

Another common question is:

> **Is data duplication considered bad practice in DynamoDB?**

No.

Data duplication is a deliberate design strategy in DynamoDB. It reduces the need for joins and enables low-latency queries. The increase in storage and write operations is usually an acceptable trade-off for predictable read performance.

---

# Key Takeaways

- Many-to-many relationships require explicit modeling because DynamoDB does not support joins.
- Relationship items connect entities and enable efficient queries.
- Bidirectional access can be achieved through duplicated relationship items or GSIs.
- Designing around access patterns is more important than minimizing data duplication.
- Accept additional writes when they significantly improve read performance.
- Well-designed many-to-many relationships scale efficiently while maintaining predictable query latency.