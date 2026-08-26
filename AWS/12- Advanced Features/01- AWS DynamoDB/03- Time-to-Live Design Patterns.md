# 10 - Time-to-Live (TTL) Design Patterns

## Overview

Time To Live (TTL) is more than an automatic deletion mechanism—it is a fundamental building block for designing scalable, self-cleaning distributed systems.

While the previous chapter explained **how TTL works**, this chapter focuses on **how experienced backend engineers use TTL in production**.

Rather than writing cleanup jobs or scheduled tasks, modern cloud-native applications often rely on TTL to automatically remove temporary data.

Common production use cases include:

- User sessions
- Authentication tokens
- Shopping carts
- OTP verification
- API rate limiting
- Distributed locks
- Cache invalidation
- Temporary reservations
- Event expiration
- IoT data lifecycle

---

# Why Design Patterns Matter

Imagine an application serving millions of users.

Every request creates temporary records.

```text
Sessions

OTP Codes

API Tokens

Shopping Carts

Rate Limits
```

Without expiration:

```text
Temporary Data

↓

Storage Grows Forever

↓

Higher Costs

↓

Slower Queries
```

Using TTL:

```text
Temporary Data

↓

Expiration Time

↓

Automatic Cleanup
```

The database continuously cleans itself.

---

# Pattern 1 — Session Management

One of the most common TTL use cases is user sessions.

```text
User Login

↓

Create Session

↓

Expire After 24 Hours
```

Architecture:

```text
User

↓

Authentication Service

↓

DynamoDB

↓

ExpireAt

↓

TTL
```

Expired sessions disappear automatically.

---

## Example Workflow

```text
Login

↓

Store Session

↓

ExpireAt = +24 Hours

↓

TTL

↓

Delete Session
```

No scheduled cleanup service is required.

---

# Pattern 2 — JWT Refresh Tokens

Many authentication systems issue:

```text
Access Token

↓

15 Minutes

────────────

Refresh Token

↓

30 Days
```

Each refresh token stores:

```text
TokenID

UserID

ExpireAt
```

After expiration:

```text
TTL

↓

Delete Token
```

This prevents unlimited token growth.

---

# Pattern 3 — One-Time Password (OTP)

Generate:

```text
OTP

↓

123456
```

Store:

```text
UserID

OTP

ExpireAt
```

Timeline:

```text
Generate

↓

Valid

5 Minutes

↓

TTL

↓

Delete
```

No background scheduler is necessary.

---

# Pattern 4 — Shopping Cart Expiration

Customer abandons cart.

```text
Cart

↓

7 Days

↓

TTL
```

Workflow:

```text
Create Cart

↓

Store Items

↓

ExpireAt

↓

Automatic Removal
```

Old carts no longer consume storage.

---

# Pattern 5 — Temporary Reservations

Booking systems often reserve inventory.

Example:

```text
Movie Ticket

↓

Reserved

↓

15 Minutes
```

If payment fails:

```text
Reservation

↓

Expires

↓

TTL Deletes Record
```

Inventory becomes available automatically.

---

# Pattern 6 — API Rate Limiting

Many APIs maintain request counters.

Example:

```text
User

↓

50 Requests

↓

1 Minute Window
```

Record:

```text
UserID

RequestCount

ExpireAt
```

After one minute:

```text
TTL

↓

Delete Counter
```

A new rate limit window begins.

---

# Pattern 7 — Cache Metadata

Suppose Redis stores product information.

Metadata table:

```text
ProductID

Cached

ExpireAt
```

Workflow:

```text
TTL

↓

Delete Metadata

↓

Stream

↓

Invalidate Redis
```

This keeps cache entries synchronized.

---

# Pattern 8 — Distributed Locks

Microservices often create temporary locks.

Example:

```text
Order123

↓

Locked

↓

Expire

30 Seconds
```

If a service crashes:

```text
TTL

↓

Delete Lock
```

Deadlocks are avoided.

---

# Pattern 9 — Temporary File References

File uploaded.

```text
Upload

↓

Temporary Metadata

↓

ExpireAt
```

Workflow:

```text
Temporary Upload

↓

TTL

↓

Delete Metadata

↓

Lambda

↓

Delete File
```

Storage remains clean.

---

# Pattern 10 — IoT Data Lifecycle

Sensor data:

```text
Temperature

↓

Keep 90 Days
```

Workflow:

```text
Store

↓

ExpireAt

↓

TTL

↓

Delete
```

Storage automatically remains within retention requirements.

---

# Combining TTL with DynamoDB Streams

TTL becomes significantly more powerful when combined with Streams.

Architecture:

```text
Expired Item

↓

TTL

↓

Stream Event

↓

Lambda

↓

Business Logic
```

Examples:

- Delete files from S3
- Invalidate Redis cache
- Send expiration notifications
- Archive records
- Update analytics

---

# TTL + Lambda Pattern

```text
Session Expires

↓

TTL Deletes Item

↓

DynamoDB Stream

↓

Lambda Triggered

↓

Audit Log
```

Applications become event-driven.

---

# TTL + EventBridge Pattern

```text
TTL

↓

Stream

↓

Lambda

↓

EventBridge

↓

Microservices
```

Multiple services react independently.

---

# TTL + SQS Pattern

```text
Expired Item

↓

Stream

↓

Lambda

↓

Amazon SQS

↓

Worker Services
```

Useful for large cleanup workloads.

---

# Architecture Pattern

```text
Application

↓

Store Temporary Record

↓

ExpireAt

↓

TTL

↓

Automatic Delete

↓

Stream

↓

Lambda

↓

Downstream Systems
```

TTL removes operational complexity.

---

# Production Considerations

When using TTL:

Remember:

```text
Expiration

≠

Immediate Deletion
```

Applications should always validate:

```text
Current Time

>

ExpireAt
```

before using temporary data.

---

# Choosing Expiration Times

| Data | Typical TTL |
|--------|------------|
| OTP | 5 Minutes |
| Session | 24 Hours |
| Refresh Token | 30 Days |
| Shopping Cart | 7 Days |
| Rate Limit | 1 Minute |
| Distributed Lock | 30 Seconds |
| Temporary Upload | 24 Hours |
| Reservation | 15 Minutes |

These values vary depending on business requirements.

---

# Best Practices

- Store expiration timestamps using Unix Epoch seconds.
- Give TTL attributes consistent names such as `ExpireAt`.
- Combine TTL with DynamoDB Streams for automation.
- Validate expiration in application code.
- Keep TTL focused on temporary data.
- Monitor storage growth to verify cleanup behavior.

---

# Common Mistakes

## Relying on Immediate Deletion

TTL deletes items asynchronously.

Never assume:

```text
Expired

=

Deleted
```

---

## Using TTL for Permanent Business Records

Poor candidates:

- Orders
- Invoices
- Payments
- Audit Logs

TTL should only remove temporary or disposable data.

---

## Ignoring Stream Events

TTL deletions generate Stream records.

Ignoring these events can leave:

- Redis caches stale
- Search indexes outdated
- Analytics inconsistent

---

## Creating Cleanup Jobs Anyway

Many teams continue running:

```text
Cron Job

↓

Delete Expired Data
```

This duplicates functionality already provided by TTL.

---

# Architecture Perspective

```text
               Temporary Data

                     │

               ExpireAt Field

                     │

              DynamoDB Table

                     │

          Background TTL Scanner

                     │

               Automatic Delete

                     │

          DynamoDB Streams

                     │

      ┌──────────────┼──────────────┐

      ▼              ▼              ▼

   Lambda         EventBridge      SQS

      ▼              ▼              ▼

 Notifications   Cache Cleanup   Analytics
```

TTL is not just a deletion mechanism—it is an event source for distributed systems.

---

# Production Skills You'll Learn

After mastering TTL design patterns, you'll be able to:

- Design self-cleaning cloud-native applications.
- Eliminate scheduled cleanup jobs.
- Build scalable authentication systems.
- Implement automatic session management.
- Design resilient distributed locking.
- Manage temporary business workflows.
- Build event-driven cleanup pipelines using Streams and Lambda.

---

# Interview Notes

A common interview question is:

> **What are common production use cases for DynamoDB TTL?**

TTL is commonly used for user sessions, JWT refresh tokens, OTP verification, shopping carts, API rate limiting, distributed locks, temporary reservations, cache metadata, and IoT data retention.

Another common question is:

> **Why combine TTL with DynamoDB Streams?**

Because TTL deletions generate Stream events, allowing downstream systems to automatically invalidate caches, archive data, trigger notifications, or perform additional cleanup.

Another common question is:

> **Should applications rely on TTL for immediate expiration?**

No. TTL performs asynchronous deletion, so applications should always validate the expiration timestamp before using temporary data.

---

# Key Takeaways

- TTL is a powerful architectural tool, not just a storage optimization feature.
- It enables self-cleaning applications by automatically removing temporary records.
- Combining TTL with DynamoDB Streams enables event-driven cleanup workflows.
- Common production patterns include sessions, tokens, shopping carts, rate limiting, distributed locks, and IoT data retention.
- Applications should always validate expiration timestamps because TTL deletion is asynchronous.
- Proper TTL design reduces operational overhead, simplifies application code, and lowers storage costs.