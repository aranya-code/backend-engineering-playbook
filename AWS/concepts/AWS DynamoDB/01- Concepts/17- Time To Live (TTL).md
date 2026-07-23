# 17 - Time To Live (TTL)

## Overview

Not every piece of data should live forever.

Many applications generate **temporary data** that loses its value after a certain period.

Examples include:

- User sessions
- Login tokens
- OTPs
- Shopping carts
- Cache entries
- Temporary reservations
- IoT sensor readings
- Audit logs with retention policies

If this expired data remains in the database indefinitely, it consumes storage, increases costs, and slows down queries.

Instead of requiring applications to manually delete expired items, DynamoDB provides **Time To Live (TTL)**.

TTL allows developers to specify an expiration timestamp for each item. Once the timestamp is reached, DynamoDB automatically removes the item in the background.

TTL simplifies lifecycle management while reducing operational overhead.

---

# Why TTL Exists

Consider an authentication system.

A user logs in.

```text
User Login

↓

Create Session

↓

Store in DynamoDB
```

Sessions are valid for:

```text
24 Hours
```

After that:

```text
Session Expired
```

Without TTL:

```text
Expired Sessions

↓

Remain Forever
```

Over time:

- Storage increases
- Queries scan unnecessary data
- Costs rise

TTL removes expired items automatically.

---

# How TTL Works

Each item contains an attribute representing its expiration time.

Example:

```text
PK

SESSION#12345
```

```text
UserId

USER#1001
```

```text
ExpiresAt

1753296000
```

The value is stored as a **Unix Epoch Timestamp (seconds)**.

DynamoDB periodically scans for expired items.

```text
Current Time

↓

Expired?

↓

Yes

↓

Delete Item
```

No application code is required.

---

# TTL Workflow

```text
Application

↓

Create Item

↓

Set ExpiresAt

↓

Store in DynamoDB

↓

TTL Background Process

↓

Delete Expired Item
```

The deletion is handled entirely by DynamoDB.

---

# TTL is Asynchronous

One important detail:

TTL does **not** delete items exactly when the timestamp expires.

Example:

```text
Expires At

12:00 PM
```

The item may actually be deleted:

```text
12:05 PM

or

12:30 PM

or later
```

AWS only guarantees that expired items are removed **eventually**.

Applications should therefore treat expired items as invalid based on the timestamp rather than waiting for physical deletion.

---

# Reading Expired Items

Suppose an item expires at:

```text
10:00 AM
```

At:

```text
10:01 AM
```

The item may still exist because the background cleanup has not yet occurred.

Applications should check:

```text
Current Time

>

ExpiresAt
```

If true:

```text
Treat Item as Expired
```

Never assume physical deletion occurs immediately.

---

# TTL Deletion Process

Internally:

```text
Item Expires

↓

TTL Scanner

↓

Delete Request

↓

Item Removed
```

From the application's perspective, the deletion behaves like a normal delete operation.

---

# TTL and DynamoDB Streams

TTL deletions can generate stream events.

```text
Item Expires

↓

TTL Deletes Item

↓

Stream Record

↓

Lambda

↓

Cleanup Logic
```

This enables workflows such as:

- Clearing caches
- Sending notifications
- Archiving data
- Updating search indexes

Applications can react automatically when data expires.

---

# Common Use Cases

## Session Management

```text
Session

↓

Expires in 24 Hours
```

Old sessions disappear automatically.

---

## OTP Verification

```text
OTP

↓

Valid for 5 Minutes
```

Expired verification codes are removed without scheduled jobs.

---

## Shopping Cart

```text
Cart

↓

Inactive for 30 Days

↓

Delete Automatically
```

Reduces unnecessary storage.

---

## Temporary Reservations

Movie tickets.

Hotel bookings.

Seat reservations.

```text
Reservation

↓

Expires After 15 Minutes

↓

Automatically Deleted
```

---

## IoT Sensor Data

```text
Sensor Reading

↓

Retain for 30 Days

↓

TTL Deletes Old Data
```

No manual cleanup required.

---

## API Rate Limiting

Applications sometimes store request counters.

```text
User

↓

100 Requests

↓

Expire in 1 Minute
```

TTL automatically removes old counters.

---

# TTL vs Manual Deletes

Without TTL:

```text
Cron Job

↓

Find Expired Records

↓

Delete

↓

Repeat
```

With TTL:

```text
Application

↓

Set Expiration Time

↓

AWS Deletes Automatically
```

TTL removes operational complexity.

---

# TTL vs Scheduled Lambda

Some teams schedule Lambda functions to delete old records.

Comparison:

| Feature | TTL | Scheduled Lambda |
|----------|-----|------------------|
| Automatic | ✅ | ❌ |
| No Code Required | ✅ | ❌ |
| Fine-Grained Expiration | ✅ | Limited |
| Deletes Individual Items | ✅ | Usually Batch |
| Operational Overhead | Low | Higher |

TTL is generally the preferred solution when simple expiration is sufficient.

---

# Limitations

TTL has several important limitations.

## No Immediate Deletion

Deletion is asynchronous.

Applications must tolerate expired items remaining briefly.

---

## Only Deletes Entire Items

TTL cannot remove:

- Individual attributes
- Nested objects
- List elements

It deletes the entire item.

---

## One TTL Attribute

Each table can define only one TTL attribute.

Applications requiring multiple expiration rules must manage them explicitly.

---

## Unix Timestamp Only

TTL expects:

```text
Epoch Seconds
```

Not:

```text
ISO Date

2026-07-23T10:00:00Z
```

Applications must convert timestamps appropriately.

---

# Cost Benefits

Removing expired data reduces:

- Storage costs
- Backup size
- Scan time
- Index storage
- Operational maintenance

For high-volume systems, TTL can significantly reduce monthly DynamoDB costs.

---

# Best Practices

- Store expiration times as Unix epoch seconds.
- Continue validating expiration in application logic.
- Use TTL for temporary data only.
- Monitor storage growth to verify TTL effectiveness.
- Combine TTL with Streams for automated cleanup workflows.
- Test expiration behavior in development before production deployment.

---

# Common Mistakes

## Expecting Instant Deletion

TTL is eventually consistent.

Applications should not depend on immediate removal.

---

## Forgetting Application Validation

Expired items may still exist temporarily.

Always compare:

```text
Current Time

>

ExpiresAt
```

---

## Using Human-Readable Dates

Incorrect:

```text
2026-07-23
```

Correct:

```text
1753296000
```

---

## Using TTL for Business Logic

TTL is designed for automatic cleanup.

Business workflows requiring guaranteed execution at an exact time should use services like EventBridge Scheduler or Step Functions instead.

---

# Real-World Example

A video streaming platform issues authentication tokens.

```text
Login

↓

Create Token

↓

ExpiresAt = Current Time + 24 Hours

↓

Store in DynamoDB
```

After 24 hours:

```text
TTL

↓

Delete Token

↓

Streams

↓

Lambda

↓

Clear User Cache
```

The authentication service remains simple while expired credentials are automatically cleaned up.

---

# Architecture Perspective

A common production architecture:

```text
Client

↓

API Gateway

↓

Lambda

↓

DynamoDB

↓

TTL Expiration

↓

DynamoDB Streams

↓

Lambda

↓

Cleanup / Notifications / Archive
```

TTL becomes part of the data lifecycle rather than the application workflow.

---

# Interview Notes

A common interview question is:

> **If TTL automatically deletes expired items, why should the application still check the expiration timestamp?**

Because TTL deletion is asynchronous.

An item may remain in the table for some time after its expiration timestamp. Applications should therefore treat the timestamp as the source of truth and reject expired data even if the item has not yet been physically removed.

Another common question is:

> **Would you use TTL to schedule business events, such as sending reminders at exactly 9:00 AM?**

No.

TTL provides eventual cleanup, not precise scheduling. For time-sensitive workflows, services such as EventBridge Scheduler, Amazon SQS Delay Queues, or AWS Step Functions are more appropriate.

---

# Key Takeaways

- TTL automatically removes expired DynamoDB items based on a timestamp attribute.
- Expiration timestamps must be stored as Unix epoch seconds.
- Deletion is asynchronous and should not be treated as immediate.
- Applications must still validate expiration timestamps when reading data.
- TTL is ideal for sessions, tokens, carts, temporary reservations, and other short-lived data.
- TTL integrates with DynamoDB Streams to support event-driven cleanup workflows.
- It simplifies data lifecycle management while reducing storage costs and operational overhead.