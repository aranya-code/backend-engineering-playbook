# 04 - One-to-One Relationships

## Overview

In relational databases, one-to-one relationships are usually modeled by creating two tables connected through a **foreign key**.

Example:

```text
Users

↓

UserProfile
```

The relationship is enforced using:

- Primary Keys
- Foreign Keys
- JOIN operations

In DynamoDB, there are **no joins** and **no foreign keys**.

Instead, one-to-one relationships are modeled by **co-locating related entities within the same partition**, allowing them to be retrieved with a single `Query` operation.

---

# What is a One-to-One Relationship?

A one-to-one relationship means:

> One entity owns exactly one related entity.

Examples include:

```text
User
    ↓
Profile
```

```text
Employee
    ↓
Payroll Information
```

```text
Vehicle
    ↓
Registration
```

```text
Customer
    ↓
Preferences
```

Each parent has exactly one child.

---

# SQL Approach

A relational database might use:

```text
Users

UserID
Name
Email
```

```text
Profiles

ProfileID
UserID
Photo
Address
Bio
```

The application retrieves data using:

```sql
SELECT *

FROM Users

JOIN Profiles

ON Users.UserID = Profiles.UserID
```

Simple in SQL.

Expensive in distributed databases.

---

# DynamoDB Approach

Instead of separating entities:

Store them together.

Example:

```text
PK = USER#100

SK = PROFILE
```

```text
PK = USER#100

SK = SETTINGS
```

Both belong to the same user.

---

# Example Table

```text
PK              SK

USER#100        PROFILE

USER#100        SETTINGS

USER#101        PROFILE

USER#101        SETTINGS
```

Each user owns exactly one:

- Profile
- Settings

Everything resides inside one partition.

---

# Visual Representation

```text
Partition

USER#100

│

├── PROFILE

└── SETTINGS
```

A single query retrieves both items.

---

# Query Example

Retrieve everything for a user.

```text
Query

PK = USER#100
```

Result:

```text
PROFILE

SETTINGS
```

One request.

No joins.

---

# Why Separate Items?

Sometimes developers ask:

> Why not store everything in one item?

Good question.

You certainly can.

Example:

```json
{
  "UserId": 100,
  "Name": "Alice",
  "Email": "alice@example.com",
  "Theme": "Dark",
  "Language": "English"
}
```

This works well.

However, separate items become useful when:

- Different update frequencies
- Different sizes
- Different access patterns
- Different lifecycle policies

---

# Example

Profile:

```text
Changes

Once per year
```

Settings:

```text
Changes

Daily
```

Keeping them separate avoids rewriting unnecessary attributes.

---

# Access Pattern

Business requirement:

```text
View User Profile
```

Query:

```text
PK = USER#100
```

Retrieve:

```text
PROFILE

SETTINGS
```

Or retrieve only the profile:

```text
PK = USER#100

SK = PROFILE
```

---

# Another Example

Employee system.

```text
PK = EMPLOYEE#200

SK = PROFILE
```

```text
PK = EMPLOYEE#200

SK = PAYROLL
```

Query:

```text
EMPLOYEE#200
```

Returns:

- Employee Profile
- Payroll Information

---

# Embedded vs Separate Items

Two common approaches exist.

---

## Option 1 — Embedded Document

```json
{
  "PK": "USER#100",
  "SK": "PROFILE",
  "Name": "Alice",
  "Settings": {
      "Theme": "Dark",
      "Language": "English"
  }
}
```

Advantages:

- One item
- One read
- Simpler structure

Disadvantages:

- Entire item rewritten during updates
- Item grows larger over time

---

## Option 2 — Separate Items

```text
USER#100

↓

PROFILE

↓

SETTINGS
```

Advantages:

- Independent updates
- Smaller items
- Better separation of concerns

Disadvantages:

- Requires a Query instead of a single GetItem

---

# Choosing Between Both

Use embedded documents when:

- Child object is small
- Always retrieved together
- Rarely updated independently

Use separate items when:

- Child object changes independently
- Child object becomes large
- Independent lifecycle exists

---

# Item Collection

Everything sharing the same partition key forms an **Item Collection**.

Example:

```text
USER#100

│

├── PROFILE

├── SETTINGS

├── PREFERENCES

└── SECURITY
```

One partition.

Multiple related entities.

---

# Performance Considerations

One-to-one relationships perform extremely well because:

```text
Single Partition

↓

Single Query

↓

Low Latency
```

No network joins.

No distributed lookups.

---

# Cost Considerations

Retrieving:

```text
PROFILE
```

requires:

```text
1 Read
```

Retrieving:

```text
PROFILE

+

SETTINGS
```

still requires:

```text
1 Query
```

Since all items reside within the same partition, read efficiency remains high.

---

# Real-World Example

A streaming platform stores user information.

Each subscriber has:

- Profile
- Playback preferences
- Subscription details
- Security settings

Instead of four tables:

```text
Users

Preferences

Subscriptions

Security
```

they are modeled as:

```text
PK = USER#500

PROFILE

PREFERENCES

SUBSCRIPTION

SECURITY
```

One partition.

Minimal database requests.

---

# Best Practices

- Keep related one-to-one entities within the same partition.
- Use descriptive sort key prefixes.
- Embed small child objects when appropriate.
- Separate frequently updated objects.
- Design around access patterns.
- Keep items below the 400 KB limit.

---

# Common Mistakes

## Creating Separate Tables

Avoid:

```text
Users

Settings

Preferences
```

when all data belongs to one entity.

---

## Over-Embedding

Large embedded documents increase:

- Item size
- Update cost
- Read cost

Split them when necessary.

---

## Ignoring Update Frequency

If one attribute changes every minute and another changes yearly, consider separate items.

---

## Thinking Like SQL

Don't ask:

> Which table should this belong to?

Instead ask:

> Which partition should this belong to?

---

# Architecture Perspective

```text
Application

        │

        ▼

Query

PK = USER#100

        │

        ▼

Partition

USER#100

        │

        ├── PROFILE

        ├── SETTINGS

        ├── SECURITY

        └── PREFERENCES

        │

        ▼

Application Response
```

Notice that DynamoDB models **relationships through partition locality** rather than foreign keys.

---

# Interview Notes

A common interview question is:

> **How do you model a one-to-one relationship in DynamoDB?**

A common approach is to store both entities under the same partition key using different sort keys. This allows both entities to be retrieved efficiently with a single `Query` operation.

Another common question is:

> **When would you embed data instead of creating separate items?**

Embed data when the child object is small, always accessed with the parent, and rarely updated independently. Use separate items when the child has a different lifecycle, grows significantly in size, or changes frequently.

---

# Key Takeaways

- DynamoDB does not use foreign keys or joins to model one-to-one relationships.
- Related entities are typically stored within the same partition.
- Sort keys distinguish different entity types such as `PROFILE`, `SETTINGS`, and `SECURITY`.
- Small, tightly coupled data can be embedded in a single item.
- Larger or independently updated data is often modeled as separate items within the same partition.
- The goal is to satisfy application access patterns with as few database operations as possible.