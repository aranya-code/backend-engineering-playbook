# 02 - Time To Live (TTL)

## Overview

Time To Live (TTL) is a DynamoDB feature that automatically removes expired items from a table without requiring application code or scheduled cleanup jobs.

Unlike traditional databases that rely on cron jobs or background cleanup services, DynamoDB manages expiration automatically by monitoring a designated timestamp attribute.

TTL is designed for data that has a natural expiration time, including:

- User sessions
- Authentication tokens
- Cache entries
- Temporary files
- Shopping carts
- OTP codes
- API rate limits
- IoT telemetry
- Temporary reservations

TTL helps reduce storage costs while simplifying application architecture.

---

# Why TTL Exists

Consider an authentication service.

Users log in.

```text
User Login

↓

Session Created

↓

Valid for 24 Hours
```

Without TTL:

```text
Expired Sessions

↓

Remain Forever

↓

Storage Grows

↓

Cleanup Job Required
```

With TTL:

```text
Session Created

↓

Expiration Timestamp

↓

Automatically Removed
```

No cleanup application is required.

---

# Internal Architecture

```text
               Application

                     │

                PutItem

                     │

      Expiration Timestamp Added

                     │

                     ▼

             DynamoDB Table

                     │

      TTL Background Scanner

                     │

      Expired Item Detected

                     │

                     ▼

            Automatic Deletion
```

TTL deletion occurs asynchronously in the background.

---

# How TTL Works

Each item contains a timestamp attribute.

Example:

```text
ExpireAt

↓

1754256000
```

The value represents:

```text
Unix Epoch Time

(in Seconds)
```

Once the current time exceeds this value:

```text
Current Time

>

ExpireAt
```

The item becomes eligible for deletion.

---

# TTL Workflow

```text
Application

↓

Create Item

↓

Set Expiration Timestamp

↓

Item Stored

↓

Time Passes

↓

TTL Scanner

↓

Delete Item
```

Applications never invoke a delete operation themselves.

---

# Expiration Timeline

```text
10:00

↓

Create Session

↓

Expires at 11:00

↓

11:00

↓

Eligible for Deletion

↓

TTL Process

↓

Item Removed
```

Important:

Deletion is **not immediate**.

---

# TTL Is Eventually Consistent

A common misconception:

```text
Expiration Time

↓

Item Deleted Immediately
```

Incorrect.

Actual behavior:

```text
Expiration Time

↓

Eligible

↓

Background Process

↓

Deleted Later
```

Deletion may occur minutes or even hours after expiration.

Applications should never rely on immediate deletion.

---

# Expired Items Before Deletion

Suppose:

```text
Current Time

>

ExpireAt
```

The item may still exist.

Applications should verify:

```text
ExpireAt

>

Current Time
```

This prevents serving expired data.

---

# TTL Attribute Requirements

TTL requires:

- One attribute
- Unix Epoch timestamp
- Seconds (not milliseconds)

Example:

```text
ExpireAt

↓

1754256000
```

Invalid:

```text
2026-07-24

10:30 PM
```

TTL only understands Unix timestamps.

---

# TTL and DynamoDB Streams

TTL deletions appear in DynamoDB Streams.

Workflow:

```text
Item Expires

↓

TTL Deletes Item

↓

Stream Event

↓

Lambda

↓

Cleanup Logic
```

Applications can react automatically.

---

# TTL and Global Tables

TTL deletions replicate across Global Tables.

```text
Region A

↓

TTL Delete

↓

Replication

↓

Region B

↓

Delete
```

This keeps all replicas synchronized.

---

# TTL vs Manual Delete

| Feature | Manual Delete | TTL |
|----------|---------------|-----|
| Automatic | ❌ | ✅ |
| Application Code | Required | Not Required |
| Scheduled Job | Often Required | Not Required |
| Immediate | ✅ | No |
| Storage Cleanup | Manual | Automatic |

---

# TTL vs Cron Job

| Feature | Cron Job | TTL |
|----------|----------|-----|
| Infrastructure | Required | Managed |
| Maintenance | High | None |
| Cost | Compute Required | Managed |
| Simplicity | Lower | Higher |

TTL removes the need for dedicated cleanup services.

---

# Real-World Example — Authentication

User session:

```text
SessionID

↓

Expires

24 Hours
```

After expiration:

```text
TTL

↓

Delete Session
```

No logout cleanup service required.

---

# Real-World Example — OTP Verification

Generate OTP:

```text
123456
```

Expires:

```text
5 Minutes
```

Workflow:

```text
Store OTP

↓

ExpireAt

↓

TTL Deletes
```

Old OTPs disappear automatically.

---

# Real-World Example — Shopping Cart

Customer abandons cart.

```text
Cart

↓

ExpireAfter

7 Days
```

TTL removes abandoned carts without scheduled cleanup.

---

# Real-World Example — API Rate Limiting

Each request creates:

```text
RateLimit Record

↓

Expire

60 Seconds
```

TTL removes expired counters automatically.

---

# Real-World Example — IoT

Sensor data:

```text
Temperature

↓

Retain

30 Days
```

Older data automatically disappears, reducing storage costs.

---

# Performance Considerations

TTL has minimal impact on application performance because:

- Expiration is asynchronous.
- Background workers perform deletion.
- Applications continue reading and writing normally.

However:

- Expired items may remain temporarily.
- Queries may still return expired records until deletion occurs.

Applications should validate expiration timestamps when freshness is critical.

---

# Best Practices

- Store expiration timestamps as Unix Epoch seconds.
- Use descriptive attribute names such as `ExpireAt`.
- Filter expired items at the application level when required.
- Enable Streams if downstream cleanup is needed.
- Use TTL for temporary—not permanent—business data.
- Monitor storage growth to verify expiration behavior.

---

# Common Mistakes

## Assuming Immediate Deletion

Incorrect:

```text
Expiration Time

↓

Deleted Immediately
```

TTL provides eventual deletion.

---

## Using Human-Readable Dates

Incorrect:

```text
July 24, 2026
```

Correct:

```text
1754256000
```

---

## Depending on TTL for Business Logic

Poor:

```text
Check If Item Exists
```

Better:

```text
Check

ExpireAt

>

Current Time
```

Applications should never assume expired items have already been removed.

---

## Forgetting Stream Processing

TTL deletions generate Stream events.

If downstream systems maintain search indexes or caches, they should process TTL deletion events.

---

# Architecture Perspective

```text
              Client Request

                    │

             Create Item

                    │

         Store Expiration Time

                    │

             DynamoDB Table

                    │

          Background TTL Scanner

                    │

          Expired Item Found

                    │

             Automatic Delete

                    │

        Stream Event (Optional)
```

TTL separates expiration management from application logic, simplifying distributed systems.

---

# Production Considerations

TTL is heavily used in production environments for managing temporary or short-lived data.

Typical workloads include:

- Authentication sessions
- JWT refresh tokens
- Shopping carts
- Temporary reservations
- API rate limits
- IoT telemetry
- Analytics staging
- Distributed locks
- Cache metadata

Many production systems combine TTL with:

- DynamoDB Streams
- AWS Lambda
- Redis
- Amazon EventBridge

to build automated cleanup and event-driven workflows.

---

# Interview Notes

A common interview question is:

> **Does TTL delete items immediately when they expire?**

No. Expired items become eligible for deletion, but DynamoDB removes them asynchronously using background processes.

Another common question is:

> **Can expired items still be returned by Query or Scan?**

Yes. Until the background TTL process removes them, applications may still retrieve expired items and should validate the expiration timestamp if freshness is important.

Another common question is:

> **What timestamp format does DynamoDB TTL require?**

A Unix Epoch timestamp expressed in **seconds**.

Another common question is:

> **Does TTL work with DynamoDB Streams and Global Tables?**

Yes. TTL deletions generate Stream events and are replicated across Global Tables, enabling downstream consumers to react consistently across Regions.

---

# Key Takeaways

- TTL automatically removes expired items without application-managed cleanup.
- Expiration is based on a Unix Epoch timestamp stored in a designated attribute.
- Items are deleted asynchronously, so expiration and deletion are not simultaneous.
- Applications should validate expiration timestamps if immediate expiration behavior is required.
- TTL integrates with DynamoDB Streams and Global Tables for event-driven cleanup and multi-region consistency.
- It is ideal for sessions, tokens, caches, shopping carts, IoT data, and other temporary datasets.