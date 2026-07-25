# 08 - TTL Troubleshooting

## Overview

Amazon DynamoDB Time To Live (TTL) automatically deletes expired items without requiring application code.

Although TTL appears simple, it is frequently misunderstood in production.

A common misconception is:

> "The item should disappear immediately after the expiration timestamp."

This is **incorrect**.

TTL is a **background asynchronous process**, and expired items may remain in the table for several hours before they are removed.

Understanding how TTL works is essential for designing reliable expiration logic.

---

# Learning Objectives

After completing this chapter, you'll understand:

- How DynamoDB TTL works
- Common TTL problems
- Why expired items still exist
- TTL monitoring
- Streams integration
- Production troubleshooting
- Best practices

---

# What is TTL?

TTL (Time To Live) automatically deletes expired items.

Example:

```text
Session

Expires

2026-08-01 12:00 UTC
```

Once expired:

```text
Background Process

↓

Delete Item
```

No manual cleanup is required.

---

# TTL Architecture

```text
Application

      │

      ▼

Store Item

      │

      ▼

Expiration Timestamp

      │

      ▼

TTL Background Process

      │

      ▼

Delete Item
```

---

# TTL Workflow

```text
Item Created

↓

Expiration Time Stored

↓

Time Passes

↓

TTL Scanner

↓

Delete Item
```

---

# Common Problems

Production issues usually involve:

- TTL not enabled
- Wrong timestamp format
- Wrong attribute name
- Expired items still visible
- Missing delete events
- Incorrect application assumptions

---

# Problem 1 — TTL Not Enabled

Symptoms:

```text
Expired Items

↓

Never Deleted
```

Verify:

```bash
aws dynamodb describe-time-to-live \
    --table-name Sessions
```

Example:

```text
TimeToLiveStatus

↓

ENABLED
```

---

# Problem 2 — Wrong Attribute Name

TTL uses a single configured attribute.

Example:

Configured:

```text
expiresAt
```

Application writes:

```text
expiryTime
```

Result:

```text
TTL Never Executes
```

---

# Problem 3 — Wrong Data Type

TTL requires:

```text
Unix Epoch Time

(Number)
```

Incorrect:

```json
{
    "expiresAt": "2026-07-31"
}
```

Correct:

```json
{
    "expiresAt": 1785499200
}
```

The value must be stored as a **Number**, not a string.

---

# Problem 4 — Wrong Timestamp

Incorrect:

```text
Milliseconds
```

Example:

```text
1785499200000
```

Expected:

```text
Seconds
```

Example:

```text
1785499200
```

Milliseconds prevent TTL from working correctly.

---

# Problem 5 — Item Not Deleted

Most common production question:

```text
TTL Expired

↓

Item Still Exists
```

Reason:

TTL is asynchronous.

Deletion may occur:

```text
Minutes

Hours

Later
```

This is normal behavior.

---

# Timeline Example

```text
12:00 PM

TTL Expired

↓

12:05 PM

Item Still Exists

↓

2:30 PM

Item Deleted
```

Applications should never rely on immediate deletion.

---

# Problem 6 — Application Reads Expired Data

Bad workflow:

```text
Read Item

↓

Exists

↓

Use Data
```

Better:

```text
Read Item

↓

Compare Current Time

↓

Expired?

↓

Ignore
```

Applications should validate expiration themselves when required.

---

# Problem 7 — Streams Not Triggered

TTL deletions generate DynamoDB Stream events **only if Streams are enabled before the deletion occurs**.

Workflow:

```text
TTL Delete

↓

Streams Enabled?

      │

 ┌────┴────┐

 ▼         ▼

Yes        No

 │          │

 ▼          ▼

Event     No Event
```

---

# Monitoring TTL

Useful CLI command:

```bash
aws dynamodb describe-time-to-live \
    --table-name Sessions
```

Verify:

- Status
- Attribute name

---

# Production Example

Session table:

```text
session_id

user_id

expiresAt
```

Expired:

```text
User Logged Out

↓

Session Expired
```

Application should reject expired sessions immediately rather than waiting for TTL cleanup.

---

# Another Production Example

Shopping Cart

```text
Cart

↓

Inactive

↓

Expires
```

TTL removes abandoned carts automatically.

No scheduled cleanup job required.

---

# TTL vs Application Logic

TTL:

```text
Storage Cleanup
```

Application:

```text
Business Logic
```

Never use TTL as your only mechanism for enforcing expiration.

---

# Investigation Workflow

```text
Item Exists

↓

TTL Enabled?

↓

Correct Attribute?

↓

Epoch Seconds?

↓

Expired?

↓

Wait

↓

Deleted?
```

---

# Common Checklist

Verify:

- TTL enabled
- Correct attribute name
- Number data type
- Epoch seconds
- Expiration timestamp
- Application logic
- Stream configuration

---

# Performance Considerations

TTL:

- Does not consume write capacity for the delete operation.
- Runs asynchronously.
- Scales automatically.
- Does not guarantee immediate deletion.
- Should not be used for real-time workflows.

---

# Best Practices

- Use Unix epoch seconds.
- Store TTL attribute as a Number.
- Enable Streams if delete events are required.
- Validate expiration inside the application.
- Monitor TTL configuration during deployments.
- Test expiration logic in lower environments.

---

# Common Mistakes

## Expecting Immediate Deletion

TTL is eventually consistent.

Expired items may remain for hours.

---

## Using String Timestamps

Incorrect:

```text
"2026-07-31"
```

Correct:

```text
1785499200
```

---

## Using Milliseconds

TTL expects epoch **seconds**, not milliseconds.

---

## Depending on TTL for Security

Bad:

```text
Expired Token

↓

TTL Will Delete It
```

Good:

```text
Expired Token

↓

Application Rejects It

↓

TTL Cleans It Later
```

---

## Forgetting Streams

Applications expecting delete events must enable DynamoDB Streams before TTL deletions occur.

---

# Interview Notes

### What is DynamoDB TTL?

A background feature that automatically removes expired items based on a configured timestamp attribute.

---

### Does TTL delete items immediately?

No.

TTL is asynchronous and items may remain for several hours after expiration before being deleted.

---

### What timestamp format does TTL require?

Unix epoch time in **seconds**, stored as a Number.

---

### Does TTL consume write capacity?

No. TTL deletions are managed by DynamoDB and do not consume your table's write capacity.

---

### Should applications depend on TTL for authentication or authorization?

No.

Applications should validate expiration themselves. TTL should be viewed as a storage cleanup mechanism rather than a real-time enforcement mechanism.

---

# Key Takeaways

- TTL automatically removes expired items but does so asynchronously.
- The TTL attribute must contain a Unix epoch timestamp in seconds and be stored as a Number.
- Applications should never assume expired items disappear immediately and should enforce expiration through business logic.
- DynamoDB Streams can capture TTL-generated delete events when properly configured.
- Senior engineers use TTL to simplify data lifecycle management while ensuring application correctness through explicit expiration checks.