# ACID Properties

# Introduction

ACID is a set of guarantees provided by relational databases to ensure reliable and predictable transactions.

---

# Atomicity

A transaction either completes entirely or rolls back completely.

**Example**

Transferring money between bank accounts:
- Debit succeeds
- Credit fails

The database rolls back the debit to avoid data inconsistency.

---

# Consistency

A transaction always moves the database from one valid state to another.

Examples:
- Primary keys remain unique.
- Foreign key constraints are enforced.
- Business rules remain valid.

---

# Isolation

Concurrent transactions should not interfere with one another.

Common isolation levels:
- Read Uncommitted
- Read Committed
- Repeatable Read
- Serializable

Higher isolation generally provides better consistency but lower concurrency.

---

# Durability

Once a transaction is committed, it survives crashes, restarts, and power failures.

AWS RDS and Aurora achieve durability through persistent storage and backups.

---

# Real-World Example

E-commerce checkout:
1. Reserve inventory
2. Create order
3. Process payment
4. Commit transaction

If payment fails, the order is rolled back.

---

# Best Practices

- Use transactions only where required.
- Keep transactions short.
- Avoid long-running locks.

---

# Interview Questions

1. Explain ACID.
2. Why is Atomicity important?
3. What problems does Isolation solve?

---

# Quick Revision

- A = All or Nothing
- C = Valid State
- I = Concurrent Safety
- D = Permanent Commit
