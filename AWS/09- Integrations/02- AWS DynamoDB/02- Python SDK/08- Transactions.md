# 08 - Transactions

## Overview

Most DynamoDB operations are **atomic at the individual item level**.

However, many real-world business operations involve **multiple items** that must succeed or fail together.

Examples include:

- Bank transfers
- Order placement
- Inventory reservation
- Payment processing
- Loyalty points
- Hotel bookings

In these scenarios, partial success is unacceptable.

Amazon DynamoDB provides **ACID Transactions** through:

- TransactWriteItems
- TransactGetItems

Transactions guarantee that **either every operation succeeds or none of them are applied**.

---

# Learning Objectives

After completing this chapter, you'll understand:

- What transactions are
- ACID properties
- TransactWriteItems
- TransactGetItems
- Transaction limits
- Atomicity
- Rollback behavior
- Performance considerations
- Production patterns
- Best practices
- Interview questions

---

# Why Transactions?

Suppose Alice transfers $500 to Bob.

Without transactions:

```text
Debit Alice

↓

Network Failure

↓

Credit Bob Never Happens

↓

Money Lost ❌
```

Business data becomes inconsistent.

---

# Transaction Architecture

```text
Application

        │

        ▼

Transaction

        │

 ┌──────┴────────┐

 ▼               ▼

All Success    Any Failure

 │               │

 ▼               ▼

Commit       Rollback
```

Either every operation succeeds or DynamoDB rolls everything back.

---

# ACID Properties

Transactions follow ACID principles.

| Property | Meaning |
|-----------|----------|
| Atomicity | All or nothing |
| Consistency | Data remains valid |
| Isolation | Concurrent transactions don't interfere |
| Durability | Committed data is permanent |

---

# Transaction APIs

DynamoDB supports:

| API | Purpose |
|------|----------|
| TransactWriteItems | Multiple writes |
| TransactGetItems | Multiple reads |

---

# Supported Write Operations

A transaction may contain:

- Put
- Update
- Delete
- Condition Check

Example:

```text
Transaction

↓

Put Order

↓

Update Inventory

↓

Update Customer

↓

Insert Audit Log
```

Everything succeeds together.

---

# TransactWriteItems

Example:

```python
import boto3

client = boto3.client("dynamodb")

client.transact_write_items(

    TransactItems=[

        {
            "Put": {
                "TableName": "Orders",
                "Item": {
                    "order_id": {"S": "ORD-1001"}
                }
            }
        },

        {
            "Update": {
                "TableName": "Inventory",
                "Key": {
                    "product_id": {"S": "P100"}
                },
                "UpdateExpression":
                    "SET stock = stock - :qty",
                "ExpressionAttributeValues": {
                    ":qty": {"N": "1"}
                }
            }
        }

    ]
)
```

---

# Execution Flow

```text
Application

↓

Validate Transaction

↓

Acquire Locks

↓

Execute Operations

↓

Commit

↓

Success
```

If validation fails:

```text
Rollback
```

---

# TransactGetItems

Read multiple items consistently.

```python
client.transact_get_items(

    TransactItems=[

        {
            "Get": {
                "TableName": "Orders",
                "Key": {
                    "order_id": {
                        "S": "ORD-1001"
                    }
                }
            }
        },

        {
            "Get": {
                "TableName": "Customers",
                "Key": {
                    "customer_id": {
                        "S": "C100"
                    }
                }
            }
        }

    ]
)
```

Useful when related items must be read together.

---

# ConditionCheck

A transaction may verify conditions without modifying data.

Example:

```text
Inventory

↓

Stock > 0 ?

↓

YES

↓

Continue Transaction
```

Example:

```python
{
    "ConditionCheck": {
        "TableName": "Inventory",
        "Key": {
            "product_id": {
                "S": "P100"
            }
        },
        "ConditionExpression":
            "stock > :zero",
        "ExpressionAttributeValues": {
            ":zero": {"N": "0"}
        }
    }
}
```

---

# Transaction Limits

Maximum:

- 100 operations
- 4 MB transaction size

```text
100 Operations

↓

Single Transaction

↓

Commit
```

---

# Atomicity

Suppose:

```text
Put Order

↓

Update Inventory

↓

Insert Payment

↓

Update Customer
```

If the payment insert fails:

```text
Entire Transaction

↓

Rollback
```

No partial updates remain.

---

# Isolation

Multiple users may execute transactions simultaneously.

```text
Transaction A

──────────────

Transaction B
```

DynamoDB ensures isolation so one transaction does not observe another's intermediate state.

---

# Rollback

Suppose:

```text
Operation 1

↓

Success

↓

Operation 2

↓

Failure
```

Result:

```text
Rollback

↓

Operation 1 Undone
```

---

# Banking Example

Without transactions:

```text
Debit Account

↓

Crash

↓

Credit Missing
```

With transactions:

```text
Debit

↓

Credit

↓

Audit Log

↓

Commit
```

Everything succeeds together.

---

# Inventory Example

Customer purchases one laptop.

Transaction:

```text
Verify Stock

↓

Decrease Stock

↓

Create Order

↓

Create Payment

↓

Commit
```

If stock becomes unavailable:

```text
Rollback
```

---

# Payment Processing

Typical payment transaction:

```text
Insert Payment

↓

Update Order

↓

Update Inventory

↓

Update Customer Balance

↓

Commit
```

---

# Transactions vs Batch Operations

| Feature | Transaction | Batch |
|----------|-------------|--------|
| Atomic | ✅ | ❌ |
| Rollback | ✅ | ❌ |
| Performance | Lower | Higher |
| Cost | Higher | Lower |
| Financial Operations | ✅ | ❌ |
| Bulk Import | ❌ | ✅ |

---

# Transactions vs Conditional Writes

| Feature | Conditional Write | Transaction |
|----------|------------------|-------------|
| Single Item | ✅ | ✅ |
| Multiple Items | ❌ | ✅ |
| Atomic | Item Level | Multi-item |
| Cost | Lower | Higher |

Conditional writes are usually sufficient for single-item business rules.

---

# Common Failure Reasons

Transactions may fail because of:

- Conditional check failure
- Item conflict
- Validation error
- Capacity limits
- Duplicate operations
- Transaction size limits

---

# Error Handling

```python
from botocore.exceptions import ClientError

try:

    client.transact_write_items(...)

except ClientError as e:

    print(e.response["Error"]["Code"])
```

Common errors:

```text
TransactionCanceledException

TransactionConflictException

ProvisionedThroughputExceededException
```

---

# Idempotency

Production payment APIs should use idempotency.

Example:

```text
Client

↓

Retry

↓

Same Transaction

↓

Single Result
```

Avoid duplicate payments caused by network retries.

---

# Repository Pattern

```python
class OrderRepository:

    def place_order(self):

        self.client.transact_write_items(...)
```

Architecture:

```text
FastAPI

↓

Service Layer

↓

Repository

↓

DynamoDB Transaction
```

Business logic remains independent of DynamoDB.

---

# Production Architecture

```text
                Client

                   │

                   ▼

             API Gateway

                   │

                   ▼

               FastAPI

                   │

                   ▼

            Service Layer

                   │

                   ▼

       Repository Transaction

                   │

                   ▼

         Amazon DynamoDB
```

---

# Performance Considerations

Transactions introduce additional overhead because DynamoDB coordinates multiple operations atomically.

Use them only when business consistency requires it.

Prefer:

- Conditional writes
- Single-item updates

when transactions are unnecessary.

---

# Security Best Practices

- Apply least-privilege IAM permissions.
- Validate all transaction inputs.
- Keep transactions as small as possible.
- Log transaction failures for auditing.
- Monitor transaction conflicts and throttling.
- Use idempotency keys for financial operations.

---

# Best Practices

- Use transactions only when multiple items must succeed together.
- Keep transactions short.
- Avoid unnecessary items in a transaction.
- Combine transactions with conditional checks.
- Handle transaction retries carefully.
- Monitor transaction cancellation metrics.

---

# Common Mistakes

## Using Transactions for Every Write

Poor:

```text
Every Update

↓

Transaction
```

Transactions add latency and cost.

Use them only when required.

---

## Confusing Batch Operations with Transactions

Batch operations improve throughput.

Transactions guarantee consistency.

These solve different problems.

---

## Ignoring Transaction Failures

Always handle:

```text
TransactionCanceledException
```

Gracefully and determine whether the request should be retried.

---

## Large Transactions

Smaller transactions reduce contention, improve throughput, and minimize conflicts.

---

# Interview Notes

A common interview question is:

> **What is the difference between BatchWriteItem and TransactWriteItems?**

`BatchWriteItem` improves throughput by grouping multiple writes but does not provide atomicity. `TransactWriteItems` guarantees that all operations succeed or all fail, making it suitable for business-critical workflows.

---

Another common question is:

> **When should you use DynamoDB transactions?**

Use transactions when multiple items or tables must be updated atomically, such as financial transfers, inventory management, or order processing.

---

Another common question is:

> **What are the ACID properties of DynamoDB transactions?**

DynamoDB transactions provide Atomicity, Consistency, Isolation, and Durability, ensuring reliable execution of multi-item operations.

---

Another common question is:

> **Do transactions affect performance?**

Yes. Transactions introduce additional coordination overhead compared to standard writes, so they should be reserved for scenarios where atomic multi-item consistency is required.

---

# Key Takeaways

- DynamoDB transactions provide ACID guarantees across multiple items and tables.
- `TransactWriteItems` performs atomic write operations, while `TransactGetItems` performs consistent multi-item reads.
- Transactions automatically roll back if any operation fails, preventing partial updates.
- Use transactions for financial operations, inventory management, and other business-critical workflows.
- Prefer simpler operations such as conditional writes or batch APIs when atomic multi-item consistency is not required.