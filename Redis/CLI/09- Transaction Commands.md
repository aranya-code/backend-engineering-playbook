# Transaction Commands

## Overview

Redis Transactions allow multiple commands to be executed as a single logical unit. Unlike traditional relational database transactions, Redis transactions do **not** provide full ACID guarantees, but they do guarantee that queued commands are executed **sequentially** without interruption from other clients.

Transactions are useful when an application needs to ensure that a group of related operations are executed together.

Common production use cases include:

- Banking operations
- Inventory management
- Shopping cart updates
- Order processing
- Distributed locking
- Financial transactions
- Cache synchronization
- Session management

Redis provides transaction support through the following commands:

- MULTI
- EXEC
- DISCARD
- WATCH
- UNWATCH

---

# How Redis Transactions Work

Instead of executing commands immediately, Redis queues them.

```
Client

↓

MULTI

↓

Queue Commands

↓

EXEC

↓

Execute All Commands
```

No other client can interleave commands during execution.

---

# Transaction Lifecycle

```
MULTI

↓

Queue Commands

↓

EXEC

↓

Transaction Complete
```

Or

```
MULTI

↓

Queue Commands

↓

DISCARD

↓

Transaction Cancelled
```

---

# Common Transaction Commands

| Command | Description |
|----------|-------------|
| MULTI | Start a transaction |
| EXEC | Execute queued commands |
| DISCARD | Cancel transaction |
| WATCH | Monitor keys for changes |
| UNWATCH | Stop monitoring keys |

---

# MULTI

Begins a transaction.

Syntax

```redis
MULTI
```

Example

```redis
MULTI
```

Output

```
OK
```

After MULTI, commands are queued instead of executed immediately.

---

# Queuing Commands

Example

```redis
MULTI

SET user:1 John

SET city London

INCR visits
```

Output

```
QUEUED

QUEUED

QUEUED
```

Nothing has been executed yet.

---

# EXEC

Executes every queued command.

Example

```redis
EXEC
```

Output

```
1) OK

2) OK

3) (integer) 101
```

Redis executes every queued command sequentially.

---

# Transaction Example

```
MULTI

↓

SET balance 1000

↓

SET status active

↓

INCR transactions

↓

EXEC
```

All commands execute together.

---

# DISCARD

Cancels a transaction.

Example

```redis
MULTI

SET username John

SET city London

DISCARD
```

Output

```
OK
```

No commands are executed.

---

# WATCH

WATCH enables optimistic locking.

Syntax

```redis
WATCH key
```

Example

```redis
WATCH account:1001
```

Redis now monitors the key.

If another client modifies it before EXEC:

```
EXEC

↓

Transaction Fails
```

---

# Why WATCH Exists

Consider two users updating the same account.

Without WATCH

```
Client A

↓

Read Balance

↓

100

Client B

↓

Read Balance

↓

100

Client A

↓

Write 150

Client B

↓

Write 80
```

One update is lost.

---

With WATCH

```
WATCH account

↓

Client A Updates

↓

Client B EXEC

↓

Fails

↓

Retry
```

Optimistic locking prevents lost updates.

---

# UNWATCH

Stops monitoring keys.

Example

```redis
UNWATCH
```

Useful when abandoning optimistic locking.

---

# Optimistic Locking Workflow

```
WATCH

↓

Read Value

↓

Application Logic

↓

MULTI

↓

Update

↓

EXEC
```

If another client modifies the watched key:

```
EXEC

↓

(nil)

↓

Retry Transaction
```

---

# Example: Inventory Update

Without transaction

```
Read Stock

↓

Decrease

↓

Write Stock
```

Another client may modify the value simultaneously.

---

With transaction

```
WATCH inventory

↓

Read

↓

MULTI

↓

Update Inventory

↓

EXEC
```

Safe concurrent updates.

---

# Example: Bank Transfer

```
Account A

↓

Subtract 500

↓

Account B

↓

Add 500
```

Transaction

```
MULTI

↓

DECRBY AccountA 500

↓

INCRBY AccountB 500

↓

EXEC
```

Both updates execute together.

---

# Shopping Cart Example

```
Customer Checkout

↓

MULTI

↓

Decrease Inventory

↓

Increase Sales

↓

Create Order

↓

EXEC
```

All operations are grouped.

---

# Session Management

```
Login

↓

MULTI

↓

Create Session

↓

Update Login Count

↓

Store Login Time

↓

EXEC
```

---

# Transaction Queue

```
MULTI

↓

Command 1

↓

Command 2

↓

Command 3

↓

Command 4

↓

EXEC
```

Redis stores commands internally until execution.

---

# Error Handling

Redis transaction errors fall into two categories.

## Syntax Errors

```
MULTI

↓

Invalid Command

↓

EXEC

↓

Fails Before Execution
```

Redis refuses to execute the transaction.

---

## Runtime Errors

```
MULTI

↓

SET

↓

Wrong Command

↓

EXEC
```

Example

```
SET age thirty

↓

INCR age
```

Output

```
OK

(error)

```

Redis continues executing remaining commands.

Transactions are **not rolled back**.

---

# Important Limitation

Redis Transactions are **not** like SQL transactions.

Redis does **not** support:

- Rollback
- Undo
- Partial recovery

Once EXEC begins:

```
Execute

↓

Complete

↓

Finished
```

---

# Transaction Isolation

Redis is single-threaded.

During EXEC:

```
Client A

↓

EXEC

↓

Command 1

↓

Command 2

↓

Command 3

↓

Complete

↓

Client B Executes
```

No client interrupts execution.

---

# Transactions vs Pipelines

| Feature | Transaction | Pipeline |
|----------|-------------|-----------|
| Atomic Execution | ✅ | ❌ |
| Reduces Network Trips | ❌ | ✅ |
| Command Ordering | ✅ | ✅ |
| Rollback | ❌ | ❌ |
| Optimistic Locking | ✅ | ❌ |

Transactions ensure consistency.

Pipelines improve performance.

---

# Transaction vs Lua Script

| Feature | Transaction | Lua Script |
|----------|-------------|------------|
| Multiple Commands | ✅ | ✅ |
| Conditional Logic | Limited | Excellent |
| Atomic | ✅ | ✅ |
| Complex Business Logic | Limited | Excellent |

Lua scripts are often preferred for complex operations.

---

# Common Production Use Cases

Transactions are commonly used for:

- Banking systems
- Payment processing
- Shopping carts
- Inventory updates
- User registration
- Loyalty points
- Session creation
- Order processing
- Financial reconciliation
- Resource allocation

---

# Common Mistakes

## Expecting Rollback

Redis does not automatically undo successful commands.

Design applications accordingly.

---

## Forgetting WATCH

Concurrent updates may overwrite each other.

Use WATCH when necessary.

---

## Long Transactions

Keep transactions short.

Avoid:

```
MULTI

↓

Hundreds of Commands
```

---

## Mixing Business Logic

Business logic belongs in the application or Lua script.

Transactions should primarily group Redis operations.

---

# Best Practices

- Keep transactions small.
- Use WATCH for optimistic locking.
- Retry failed optimistic transactions.
- Validate data before EXEC.
- Prefer Lua scripts for complex conditional logic.
- Avoid blocking commands inside transactions.
- Log transaction failures.

---

# Performance Considerations

| Command | Complexity |
|----------|------------|
| MULTI | O(1) |
| EXEC | O(N) |
| DISCARD | O(1) |
| WATCH | O(1) |
| UNWATCH | O(1) |

*N = number of queued commands.*

---

# Production Considerations

For production deployments:

- Keep transactions as short as possible to minimize contention.
- Use `WATCH` only when optimistic locking is required.
- Implement retry logic for failed optimistic transactions.
- Consider Lua scripts for atomic operations involving conditional business logic.
- Monitor transaction failure rates to identify concurrency issues.
- Avoid assuming SQL-like transactional guarantees such as rollback or isolation levels.

---

# Transaction Architecture

```
                Client
                   │
                   ▼
               WATCH Key
                   │
                   ▼
            Read Current Data
                   │
                   ▼
               MULTI Queue
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
     Update A   Update B   Update C
        │          │          │
        └──────────┼──────────┘
                   ▼
                 EXEC
                   │
                   ▼
           All Commands Execute
```

---

# Summary

Redis Transactions provide a mechanism for grouping multiple commands into a single atomic execution block. Although they do not offer full ACID semantics or rollback capabilities like relational databases, they ensure that queued commands execute sequentially without interruption. Combined with optimistic locking through `WATCH`, transactions help developers safely implement inventory management, financial operations, shopping carts, and other concurrent workflows. For more advanced conditional logic, Lua scripting is often the preferred alternative.

---

# Key Takeaways

- `MULTI` starts a transaction and queues commands.
- `EXEC` executes all queued commands atomically.
- `DISCARD` cancels a queued transaction.
- `WATCH` enables optimistic locking to prevent lost updates.
- Redis transactions do **not** support rollback.
- Runtime errors do not abort the remaining queued commands.
- Keep transactions small and retry optimistic locking failures when necessary.
- Consider Lua scripts for complex atomic business logic.