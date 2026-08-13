# 12 - Version Control Pattern

## Overview

Many production applications need to maintain the **history of changes** rather than simply storing the latest state.

Examples include:

- Documents
- Contracts
- Configuration files
- Source code
- Medical records
- User profiles
- Financial reports
- Product catalogs

Instead of overwriting old data, the application stores **multiple versions** of the same entity.

This is known as the **Version Control Pattern**.

The Version Control Pattern enables:

- Audit history
- Rollbacks
- Change tracking
- Compliance
- Event replay
- Debugging

It is widely used in enterprise applications where historical accuracy is important.

---

# Why Versioning Matters

Imagine a product price.

Today:

```text
$100
```

Tomorrow:

```text
$120
```

If the original value is overwritten,

the application loses:

- Historical data
- Audit trail
- Ability to restore
- Change history

Instead, keep both versions.

---

# SQL Approach

Relational databases often use:

```text
Products

↓

ProductHistory
```

or

```text
Audit Tables
```

Example:

```text
Products

ProductID

Price
```

History:

```text
ProductHistory

ProductID

Version

Price

Timestamp
```

---

# DynamoDB Approach

Each version becomes a separate item.

Example:

```text
PK = PRODUCT#100

SK = V1
```

```text
PK = PRODUCT#100

SK = V2
```

```text
PK = PRODUCT#100

SK = V3
```

Every version belongs to the same partition.

---

# Visual Representation

```text
PRODUCT#100

│

├── V1

├── V2

├── V3

└── V4
```

Query:

```text
PK = PRODUCT#100
```

Returns the complete version history.

---

# Example

Document:

```text
Employee Handbook
```

Versions:

```text
V1

Initial Release
```

```text
V2

Added Benefits
```

```text
V3

Updated Leave Policy
```

Table:

```text
PK = DOC#EMPLOYEE

SK = V1
```

```text
PK = DOC#EMPLOYEE

SK = V2
```

```text
PK = DOC#EMPLOYEE

SK = V3
```

---

# Retrieving the Latest Version

One option:

```text
Query

↓

Reverse Order

↓

Limit 1
```

Returns:

```text
Latest Version
```

No scan required.

---

# Timestamp-Based Versioning

Instead of numeric versions:

```text
V1

V2

V3
```

Store:

```text
2026-07-01

2026-07-10

2026-07-20
```

Example:

```text
PK = PRODUCT#100

SK = VERSION#2026-07-20T10:00:00Z
```

Benefits:

- Natural ordering
- Creation time included
- Easier auditing

---

# Maintaining a "Current" Item

Many production systems keep two records.

Example:

```text
PK = PRODUCT#100

SK = CURRENT
```

and

```text
PK = PRODUCT#100

SK = VERSION#2026-07-20
```

Workflow:

```text
Update

↓

Overwrite CURRENT

↓

Insert New Version
```

Applications needing only the latest state read:

```text
CURRENT
```

Applications needing history query all versions.

---

# Example Table

```text
PK                 SK

PRODUCT#100        CURRENT

PRODUCT#100        VERSION#2026-07-01

PRODUCT#100        VERSION#2026-07-10

PRODUCT#100        VERSION#2026-07-20
```

Fast reads.

Complete history.

---

# Version Metadata

Each version may contain:

```text
Version Number

Modified By

Timestamp

Reason

Status
```

Example:

```json
{
  "Version": 4,
  "ModifiedBy": "Alice",
  "ModifiedAt": "2026-07-20T10:30:00Z",
  "Reason": "Price update"
}
```

This greatly improves auditing.

---

# Optimistic Locking

Suppose two users edit the same document.

Timeline:

```text
Alice

↓

Version 5
```

At the same time:

```text
Bob

↓

Version 5
```

Without protection:

Last writer wins.

Changes may be lost.

---

# Conditional Writes

DynamoDB supports optimistic concurrency.

Example:

```text
Update

ONLY IF

Version = 5
```

If another update already created:

```text
Version = 6
```

the write fails.

Application:

- Reload latest version
- Retry update

This prevents accidental overwrites.

---

# Audit Trail

Version history provides:

```text
Who

↓

Changed What

↓

When

↓

Why
```

Useful for:

- Financial systems
- Healthcare
- Government
- Compliance
- Enterprise software

---

# Rollback

Suppose:

```text
Version 7

↓

Bug
```

Restore:

```text
Version 6
```

No data recovery required.

Simply copy Version 6 into:

```text
CURRENT
```

---

# Event Timeline

Imagine user profile changes.

```text
V1

Created
```

↓

```text
V2

Email Updated
```

↓

```text
V3

Phone Updated
```

↓

```text
V4

Address Updated
```

Complete history remains available.

---

# Storage Considerations

Versioning increases storage.

Example:

Without versioning:

```text
1 Item
```

With history:

```text
250 Versions
```

Storage grows over time.

Mitigation:

- Archive old versions
- Compress history
- Export to Amazon S3

---

# Combining with TTL

Some applications only need:

```text
Last 90 Days
```

Older versions:

```text
TTL

↓

Automatic Removal
```

Useful for temporary audit logs.

---

# Combining with DynamoDB Streams

Workflow:

```text
Update

↓

Streams

↓

Lambda

↓

Archive

↓

Amazon S3
```

Recent versions remain in DynamoDB.

Historical versions move to cheaper storage.

---

# Real-World Example

A document management system stores contracts.

Each modification creates:

```text
New Version
```

Latest document:

```text
CURRENT
```

Previous revisions:

```text
VERSION#Timestamp
```

Users can:

- View current document
- Compare revisions
- Restore previous versions
- View complete audit history

---

# Best Practices

- Never overwrite historical records.
- Keep a dedicated CURRENT item.
- Use ISO-8601 timestamps for version ordering.
- Store audit metadata.
- Use conditional writes for concurrent updates.
- Archive old versions when appropriate.

---

# Common Mistakes

## Overwriting Data

Avoid:

```text
Update Item

↓

Replace Previous Value
```

Historical information is lost.

---

## No Current Record

Without a dedicated:

```text
CURRENT
```

every request must search for the latest version.

---

## Ignoring Concurrency

Concurrent updates can overwrite each other.

Always use conditional writes or optimistic locking.

---

## Keeping Unlimited History

Very large histories increase:

- Storage
- Backup time
- Export cost

Implement retention policies.

---

# Architecture Perspective

```text
Application

        │

        ▼

Update Document

        │

        ├── Update CURRENT

        │

        └── Insert VERSION#Timestamp

                    │

                    ▼

Partition

DOCUMENT#100

        │

        ├── CURRENT

        ├── VERSION#2026-07-01

        ├── VERSION#2026-07-10

        ├── VERSION#2026-07-20

        └── VERSION#2026-07-25
```

The `CURRENT` item provides fast reads, while version items preserve a complete history.

---

# Production Considerations

Large enterprise systems often combine this pattern with:

- DynamoDB Transactions
- Streams
- EventBridge
- AWS Backup
- Point-in-Time Recovery (PITR)

This creates a highly resilient audit and recovery strategy suitable for regulated industries.

---

# Interview Notes

A common interview question is:

> **How do you implement version control in DynamoDB?**

Store each version as a separate item under the same partition key. Keep a dedicated `CURRENT` item for fast access to the latest state, while storing historical versions using timestamp- or version-based sort keys.

Another common question is:

> **Why keep a `CURRENT` item if all versions already exist?**

Because most application reads request the latest version. Reading `CURRENT` avoids querying and sorting multiple version records, reducing latency and simplifying application logic.

Another common question is:

> **How do you prevent concurrent updates from overwriting each other?**

Use conditional writes with a version number (optimistic locking). If the stored version has changed since it was read, DynamoDB rejects the update, allowing the application to retry safely.

---

# Key Takeaways

- The Version Control Pattern preserves historical changes instead of overwriting data.
- Store each version as a separate item within the same partition.
- Maintain a dedicated `CURRENT` item for efficient reads.
- Use conditional writes to protect against concurrent updates.
- Store audit metadata such as timestamps, users, and change reasons.
- Archive or expire old versions to control long-term storage costs.