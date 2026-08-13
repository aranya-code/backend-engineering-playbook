# 15 - Event Sourcing Pattern

## Overview

Traditional applications store the **current state** of an entity.

Example:

```text
Bank Account

Balance = $1,250
```

The application knows the current balance but does **not** know how that balance was reached.

With **Event Sourcing**, applications store **every business event** that changes an entity.

Instead of storing only the latest state, they store the complete sequence of events.

Examples:

- Money deposited
- Money withdrawn
- Order placed
- Order shipped
- User registered
- Password changed
- Subscription upgraded

The current state is derived by replaying these events.

Event Sourcing is widely used in:

- Financial systems
- Payment platforms
- Inventory systems
- Order management
- Audit-heavy enterprise software
- Event-driven microservices

---

# Traditional CRUD Model

Typical application:

```text
Account

↓

Balance = $100
```

Deposit:

```text
+50
```

Database:

```text
Balance = $150
```

The previous value is lost.

---

# Event Sourcing Model

Instead of updating one record:

Store events.

```text
Deposit $100

↓

Deposit $50

↓

Withdraw $25
```

Current balance:

```text
100

+

50

-

25

=

125
```

Nothing is lost.

---

# Event Store

Each event becomes a DynamoDB item.

Example:

```text
PK = ACCOUNT#100

SK = EVENT#2026-07-23T10:00:00Z
```

Event:

```json
{
    "EventType": "Deposit",
    "Amount": 100
}
```

Another event:

```text
PK = ACCOUNT#100

SK = EVENT#2026-07-23T10:10:00Z
```

```json
{
    "EventType": "Withdraw",
    "Amount": 25
}
```

Every event belongs to the same account partition.

---

# Visual Representation

```text
ACCOUNT#100

│

├── Deposit $100

├── Deposit $50

├── Withdraw $25

├── Deposit $80

└── Withdraw $10
```

The complete history is preserved.

---

# Current State

The application calculates:

```text
Replay Events

↓

Current Balance
```

Instead of storing:

```text
Balance = 195
```

it derives:

```text
100

+

50

-

25

+

80

-

10

=

195
```

---

# Event Structure

Typical event:

```json
{
    "EventId": "evt-001",
    "EventType": "OrderPlaced",
    "OccurredAt": "2026-07-23T10:30:00Z",
    "UserId": "USER#500",
    "Payload": {
        "ProductId": "P100",
        "Quantity": 2
    }
}
```

Each event represents one business action.

---

# Example — Order Processing

Instead of:

```text
Order

Status = Delivered
```

Store:

```text
Order Created

↓

Payment Received

↓

Inventory Reserved

↓

Order Packed

↓

Order Shipped

↓

Order Delivered
```

Complete lifecycle.

---

# Example Table

```text
PK                      SK

ORDER#500               EVENT#2026-07-01T10:00

ORDER#500               EVENT#2026-07-01T10:02

ORDER#500               EVENT#2026-07-01T10:05

ORDER#500               EVENT#2026-07-02T08:30
```

Query:

```text
PK = ORDER#500
```

Returns the complete history.

---

# Why Event Sourcing?

Benefits include:

- Complete audit trail
- Historical reconstruction
- Easy debugging
- Compliance
- Replay capability
- Temporal analysis

Nothing is permanently overwritten.

---

# Event Replay

Suppose a bug is fixed.

Application:

```text
Replay Events

↓

New Business Logic

↓

Correct State
```

No manual corrections required.

---

# CQRS

Event Sourcing is frequently combined with:

**CQRS (Command Query Responsibility Segregation)**

Commands:

```text
Create Events
```

Queries:

```text
Read Materialized View
```

Instead of replaying events for every request, another table stores the latest projection.

---

# Event Flow

```text
Application

↓

Command

↓

Validate

↓

Store Event

↓

Update Projection

↓

Return Response
```

Events become the source of truth.

---

# DynamoDB Streams Integration

After storing an event:

```text
DynamoDB

↓

Streams

↓

Lambda

↓

Update Read Model
```

or

```text
Publish

↓

Amazon EventBridge

↓

Other Services
```

This enables event-driven architectures.

---

# Snapshot Pattern

Suppose an account has:

```text
5 Million Events
```

Replaying every event becomes expensive.

Solution:

Create snapshots.

Example:

```text
Snapshot

Balance = $5000
```

Events after snapshot:

```text
+100

-20

+50
```

Replay only recent events.

---

# Snapshot Example

Table:

```text
PK = ACCOUNT#100

SK = SNAPSHOT#2026-07-01
```

Then:

```text
EVENT#2026-07-02

EVENT#2026-07-03

EVENT#2026-07-04
```

Current state:

```text
Snapshot

+

Recent Events
```

Much faster.

---

# Event Immutability

Events should never change.

Wrong:

```text
Update Deposit Event
```

Correct:

```text
Deposit Event

↓

Correction Event
```

History remains accurate.

---

# Event Versioning

Business rules evolve.

Example:

```text
OrderPlaced v1
```

Later:

```text
OrderPlaced v2
```

Include:

```text
EventVersion
```

Applications can process old and new events safely.

---

# Event Ordering

Events should always have:

- Timestamp
- Sequence number
- Unique Event ID

Example:

```text
EVENT#000001

EVENT#000002

EVENT#000003
```

Ordering is critical for replay.

---

# Benefits

Event Sourcing provides:

- Complete history
- Immutable records
- Easy auditing
- Replay capability
- Event-driven integration
- Better debugging

---

# Challenges

Event Sourcing introduces:

- More complex architecture
- Event schema evolution
- Snapshot management
- Projection maintenance
- Event ordering concerns

It is more powerful than CRUD but also more complex.

---

# Real-World Example

A payment processing platform stores every financial transaction as an immutable event.

Instead of updating an account balance directly, it records:

```text
Account Opened

↓

Deposit

↓

Withdrawal

↓

Refund

↓

Transfer
```

Customer balances are derived from events, while reporting systems, fraud detection, and analytics consume the same event stream independently.

---

# Best Practices

- Keep events immutable.
- Store timestamps using ISO-8601 format.
- Use unique event IDs.
- Create snapshots for long-lived entities.
- Include event version information.
- Keep event payloads focused on business facts.
- Publish events through Streams or EventBridge when integrating services.

---

# Common Mistakes

## Updating Existing Events

Events should represent facts that already happened.

Never modify historical events.

---

## Storing Only Current State

Without historical events:

- Replay is impossible.
- Auditing becomes difficult.
- Debugging loses valuable context.

---

## Ignoring Snapshots

Large event streams become slow to replay.

Create snapshots periodically.

---

## Using Events as Database Rows

Events describe **business actions**, not entity state.

Design them around domain events.

---

# Architecture Perspective

```text
Client

        │

        ▼

Command

        │

        ▼

Store Event

        │

        ▼

DynamoDB Event Store

        │

        ├── EVENT#1

        ├── EVENT#2

        ├── EVENT#3

        └── EVENT#4

        │

        ▼

DynamoDB Streams

        │

        ▼

Lambda

        │

        ▼

Materialized Read Model

        │

        ▼

Application Queries
```

The Event Store becomes the system of record, while optimized read models are built asynchronously.

---

# Production Considerations

Large event-driven systems commonly integrate Event Sourcing with:

- DynamoDB Streams
- AWS Lambda
- Amazon EventBridge
- Amazon SQS
- Amazon SNS
- Step Functions
- Amazon S3 (long-term archive)

This architecture enables scalable, loosely coupled microservices while preserving a complete history of business events.

---

# Interview Notes

A common interview question is:

> **What is Event Sourcing?**

Event Sourcing is an architectural pattern where every state change is stored as an immutable event. Instead of persisting only the latest state, the application reconstructs the current state by replaying the sequence of events.

Another common question is:

> **Why combine Event Sourcing with DynamoDB?**

DynamoDB's high write throughput, ordered sort keys, Streams integration, and horizontal scalability make it well suited for storing immutable event streams and powering event-driven architectures.

Another common question is:

> **Why are snapshots important in Event Sourcing?**

Without snapshots, reconstructing an entity with millions of events requires replaying the entire history. Snapshots store periodic state, allowing applications to replay only the events created after the latest snapshot.

---

# Key Takeaways

- Event Sourcing stores business events instead of only the latest entity state.
- Events are immutable and form the source of truth.
- Current state is reconstructed by replaying events or loading a snapshot followed by recent events.
- DynamoDB Streams integrate naturally with Event Sourcing for building asynchronous read models.
- Event Sourcing provides excellent auditing, replay, and debugging capabilities but introduces additional architectural complexity.
- It is widely used in financial systems, enterprise software, and event-driven microservices.