# Common Mistakes

Amazon EventBridge is simple to use, but poor architectural decisions can reduce reliability, increase costs, and make applications difficult to maintain.

This chapter highlights common mistakes and explains how to avoid them.

------------------------------------------------------------------------

# Tight Coupling

❌ Bad

```text
Order Service

↓

Payment Service

↓

Inventory Service
```

Each service depends directly on another.

✅ Good

```text
Order Service

↓

EventBridge

↓

Payment

Inventory

Email
```

------------------------------------------------------------------------

# Large Event Payloads

Maximum event size:

```text
256 KB
```

Avoid placing:

- Images
- Videos
- Large JSON documents

Instead:

- Store data in Amazon S3
- Publish only the object reference

------------------------------------------------------------------------

# Poor Event Names

❌ Bad

```text
Event1

Test

Message
```

✅ Good

```text
OrderCreated

PaymentSucceeded

InvoiceGenerated
```

------------------------------------------------------------------------

# Ignoring Retry Policies

Without retries:

Temporary failures result in lost events.

Always configure:

- Retry Attempts
- Maximum Event Age
- DLQ

------------------------------------------------------------------------

# No Dead-Letter Queue

Without a DLQ:

Failed events disappear permanently.

Always configure DLQs for critical business events.

------------------------------------------------------------------------

# Too Many Event Buses

Creating numerous Event Buses unnecessarily increases complexity.

Create Custom Event Buses only when there is a clear business or security requirement.

------------------------------------------------------------------------

# No Monitoring

Never deploy EventBridge without monitoring.

Monitor:

- FailedInvocations
- DLQs
- Retry Attempts
- Triggered Rules

------------------------------------------------------------------------

# Ignoring Schema Versioning

Changing event structures without versioning breaks downstream consumers.

Instead:

```text
OrderCreated v1

↓

OrderCreated v2
```

------------------------------------------------------------------------

# Using EventBridge as a Database

EventBridge is an event router.

Do not use it for:

- Long-term storage
- Data querying
- Business reporting

Use:

- Amazon S3
- DynamoDB
- Amazon RDS

------------------------------------------------------------------------

# Publishing Duplicate Events

Duplicate events increase:

- Costs
- Processing time
- Complexity

Ensure producers publish events only when necessary.

------------------------------------------------------------------------

# Best Practices

- Design immutable events.
- Version schemas.
- Configure retries.
- Configure DLQs.
- Keep payloads small.
- Monitor everything.

------------------------------------------------------------------------

# Key Takeaways

- Avoid tight coupling.
- Keep events lightweight.
- Configure retries and DLQs.
- Monitor EventBridge continuously.
- Version schemas carefully.