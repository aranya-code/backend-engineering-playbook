# 13 - TransactGetItems

## Overview

`TransactGetItems` is a DynamoDB operation that retrieves **multiple items atomically** from one or more tables.

Unlike `BatchGetItem`, which simply groups multiple read requests into a single API call, `TransactGetItems` guarantees that **all returned items represent a consistent snapshot of the data at the time the transaction started**.

This is particularly important in applications where multiple related records must be read together without observing partial updates.

Typical use cases include:

- Banking systems
- Financial transactions
- Inventory management
- Reservation systems
- Order processing
- Healthcare applications

---

# Why TransactGetItems Exists

Imagine a banking application.

Money is transferred from:

```text
Account A

↓

Account B
```

The application must retrieve:

- Source account
- Destination account

If separate `GetItem` operations are used:

```text
Get Account A

↓

Transfer Occurs

↓

Get Account B
```

The application may observe inconsistent data.

With `TransactGetItems`:

```text
Read Both Accounts

↓

Single Consistent Snapshot
```

Both items represent the same point in time.

---

# Atomic Read

Unlike BatchGetItem:

```text
Read Item A

↓

Read Item B

↓

Read Item C
```

TransactGetItems performs:

```text
Transaction Begins

↓

Read A

↓

Read B

↓

Read C

↓

Return Snapshot
```

All items belong to the same transactional read.

---

# Internal Architecture

```text
                 Application

                       │

                       ▼

              TransactGetItems

                       │

              Start Transaction

                       │

      ┌────────────┼────────────┐

      ▼            ▼            ▼

 Read Item A  Read Item B  Read Item C

      └────────────┼────────────┘

                   ▼

      Build Consistent Snapshot

                   ▼

             Return Response
```

---

# Maximum Operations

A single transaction supports:

```text
100 Items
```

across one or more DynamoDB tables.

---

# Primary Key Requirement

Like BatchGetItem,

every requested item must include its complete primary key.

Simple key:

```text
UserID
```

Composite key:

```text
CustomerID

+

OrderID
```

Both values are required.

---

# Strong Consistency

TransactGetItems provides:

```text
Serializable Isolation
```

Meaning:

```text
Transaction

↓

Consistent Snapshot

↓

Application Reads Data
```

No partial updates are visible.

---

# Capacity Consumption

TransactGetItems consumes:

```text
Read Capacity Units
```

for every item retrieved.

Transactions also introduce additional internal coordination compared to ordinary reads.

Therefore:

```text
TransactGetItems

>

BatchGetItem
```

in terms of latency and overhead.

---

# Multiple Tables

Transactions may span several tables.

Example:

```text
Customers

Orders

Payments
```

Single request:

```text
Customer

↓

Order

↓

Payment

↓

Consistent Response
```

---

# Failure Behavior

Unlike BatchGetItem,

the transaction either succeeds completely or fails.

Example:

```text
Read A

Read B

Read C
```

If one read cannot be completed consistently:

```text
Entire Transaction Fails
```

No partial snapshot is returned.

---

# TransactGetItems vs BatchGetItem

| Feature | BatchGetItem | TransactGetItems |
|----------|--------------|------------------|
| Multiple Reads | ✅ | ✅ |
| Multiple Tables | ✅ | ✅ |
| Atomic Snapshot | ❌ | ✅ |
| Serializable Isolation | ❌ | ✅ |
| Performance | Faster | Slightly Slower |

---

# TransactGetItems vs Query

| Feature | Query | TransactGetItems |
|----------|-------|------------------|
| Reads Item Collections | ✅ | ❌ |
| Reads Known Items | ❌ | ✅ |
| Transactional | ❌ | ✅ |
| Uses Partition Key | ✅ | Requires Full Primary Key |

---

# TransactGetItems vs GetItem

| Feature | GetItem | TransactGetItems |
|----------|----------|------------------|
| One Item | ✅ | ❌ |
| Multiple Items | ❌ | ✅ |
| Transactional | ❌ | ✅ |
| Consistent Snapshot | ❌ | ✅ |

---

# Real-World Example — Banking

Transfer:

```text
Account A

↓

Account B
```

Application needs:

```text
Source Balance

Destination Balance
```

Using:

```text
TransactGetItems
```

Both balances are guaranteed to belong to the same point in time.

---

# Real-World Example — Order Processing

Retrieve:

```text
Customer

Order

Payment

Shipment
```

Application:

```text
TransactGetItems

↓

Consistent Order View
```

No partially updated information is returned.

---

# Real-World Example — Healthcare

Patient record:

```text
Patient

Prescription

Insurance

Appointment
```

A transactional read guarantees that every document represents the same consistent state.

---

# Performance Considerations

Transactions require:

- Internal locking coordination
- Distributed consensus
- Serializable isolation

Therefore:

```text
Higher Latency

than

BatchGetItem
```

Use transactions only when consistency requirements justify the additional overhead.

---

# Best Practices

- Use TransactGetItems only when atomic consistency is required.
- Use BatchGetItem for independent reads.
- Keep transactions small.
- Avoid unnecessary cross-table transactions.
- Design tables to minimize transactional reads.
- Monitor transaction latency using CloudWatch.

---

# Common Mistakes

## Using Transactions Everywhere

Transactions are more expensive than ordinary reads.

Do not replace every BatchGetItem with TransactGetItems.

---

## Reading Unrelated Data

Independent records should be retrieved using BatchGetItem.

Transactions should be reserved for logically related data.

---

## Large Transactions

Although up to 100 items are supported,

smaller transactions generally perform better.

---

## Assuming Better Performance

Transactions provide stronger consistency,

not higher speed.

---

# Architecture Perspective

```text
                 Application

                       │

               TransactGetItems

                       │

            Start Transaction

                       │

      ┌────────────┼────────────┐

      ▼            ▼            ▼

 Read Item A  Read Item B  Read Item C

      └────────────┼────────────┘

                   ▼

       Consistent Snapshot

                   ▼

            Return Results
```

Every item is read from the same transactional snapshot.

---

# Production Considerations

TransactGetItems is primarily used in systems where data consistency is more important than raw performance.

Typical workloads include:

- Banking
- Trading platforms
- Inventory management
- Reservation systems
- Healthcare records
- Financial reporting

Most customer-facing APIs do **not** require transactional reads and instead use:

- Query
- GetItem
- BatchGetItem

to maximize throughput and minimize latency.

---

# Interview Notes

A common interview question is:

> **What is the difference between BatchGetItem and TransactGetItems?**

BatchGetItem retrieves multiple items efficiently but does not guarantee that they represent the same point in time. TransactGetItems returns all requested items as a single, consistent transactional snapshot.

Another common question is:

> **When should you use TransactGetItems?**

When multiple related records must be read together without observing partial updates, such as in banking, inventory, or financial systems.

Another common question is:

> **Is TransactGetItems faster than BatchGetItem?**

No. Transactions introduce additional coordination to provide serializable isolation, making them slightly slower than BatchGetItem.

---

# Key Takeaways

- `TransactGetItems` retrieves up to **100 items** atomically across one or more DynamoDB tables.
- It provides **serializable isolation**, ensuring all items are read from the same consistent snapshot.
- It is ideal for applications requiring strong consistency across multiple related records.
- Transactions introduce additional latency and overhead compared to `BatchGetItem`.
- Use `TransactGetItems` only when transactional consistency is required; otherwise, prefer simpler read operations such as `Query`, `GetItem`, or `BatchGetItem`.