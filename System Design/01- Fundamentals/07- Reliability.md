# Reliability

## Overview

A system that is available is not necessarily reliable.

Imagine an online banking application that is accessible 24/7 but occasionally transfers money to the wrong account. Although users can always access the service, they cannot trust it.

Reliability is the ability of a system to consistently perform its intended function correctly, even when components fail or unexpected situations occur.

Building reliable systems is one of the primary goals of System Design because users value correctness just as much as availability.

---

# What is Reliability?

Reliability measures a system's ability to produce **correct and consistent results over time**.

In simple terms:

> Reliability answers the question: **"Can the system perform its intended function correctly every time?"**

A reliable system:

- Produces accurate results
- Handles failures gracefully
- Prevents data corruption
- Maintains consistency
- Recovers without losing critical information

---

# Why Reliability Matters

Consider these examples:

### Banking

A customer transfers $1,000.

The transfer must:

- Complete exactly once
- Debit the correct account
- Credit the correct recipient
- Never duplicate the transaction

---

### E-commerce

A customer places an order.

The system should:

- Create only one order
- Charge the customer once
- Update inventory correctly
- Generate an accurate invoice

---

### Healthcare

A hospital system stores patient records.

The system must:

- Never lose medical records
- Store correct information
- Ensure prescriptions remain accurate

In these systems, correctness is more important than speed.

---

# Reliability vs Availability

These concepts are closely related but serve different purposes.

| Reliability | Availability |
|-------------|--------------|
| Measures correctness | Measures accessibility |
| Focuses on accurate operation | Focuses on uptime |
| Ensures expected behavior | Ensures users can access the service |
| Prevents incorrect results | Prevents downtime |

Example:

A website that is online but frequently loses customer orders has:

- High Availability
- Low Reliability

A website that correctly processes every order but experiences occasional downtime has:

- High Reliability
- Lower Availability

The ideal system provides both.

---

# Characteristics of a Reliable System

Reliable systems exhibit several important characteristics.

## Correctness

Every operation should produce the expected result.

Examples:

- Correct calculations
- Accurate reports
- Valid transactions

---

## Consistency

Data should remain accurate and synchronized.

Example:

When transferring money:

```
Account A

$500
   │
Transfer $100
   ▼
Account A = $400

Account B = Previous Balance + $100
```

Both updates must succeed together.

---

## Durability

Once data has been successfully stored, it should not disappear.

Examples:

- Banking transactions
- Medical records
- Purchase history

Durability ensures users can trust the system.

---

## Recoverability

Failures should not permanently damage the system.

Examples:

- Automatic restart
- Database recovery
- Backup restoration
- Transaction rollback

---

# Common Causes of Reliability Issues

Applications become unreliable for many reasons.

Common causes include:

- Software bugs
- Hardware failures
- Network interruptions
- Database corruption
- Partial failures
- Duplicate requests
- Race conditions
- Human errors
- Configuration mistakes

Reliable architectures are designed to minimize the impact of these failures.

---

# Designing for Reliability

Reliable systems use multiple techniques to maintain correctness.

## Data Replication

Critical data is copied across multiple servers.

```
Primary Database
      │
      ├────────► Replica 1
      │
      └────────► Replica 2
```

Benefits include:

- Data protection
- Disaster recovery
- Reduced risk of data loss

---

## Transactions

Transactions ensure multiple operations either:

- Complete successfully together, or
- Fail together

Example:

Money Transfer

```
Debit Account A
        │
Credit Account B
```

If either operation fails, both changes are rolled back.

---

## Retry Mechanisms

Temporary failures often resolve themselves.

Instead of failing immediately:

```
Attempt 1 ❌

Retry

Attempt 2 ✅
```

Retries improve reliability when failures are temporary.

However, retries should be carefully controlled to avoid overloading the system.

---

## Idempotency

Some requests may be sent multiple times due to network issues.

An idempotent operation produces the same result regardless of how many times it is repeated.

Example:

```
Payment Request

Client sends request

Network timeout

Client retries

Server processes payment only once
```

Idempotency prevents duplicate operations.

---

## Validation

Reliable systems validate all incoming data.

Examples:

- Required fields
- Input formats
- Business rules
- Data types

Validation prevents invalid data from entering the system.

---

## Monitoring

Reliable systems continuously monitor:

- Errors
- Failures
- Response times
- Resource usage
- Database health

Early detection allows engineers to resolve issues before they affect users.

---

# Redundancy Improves Reliability

Having multiple copies of critical components reduces the chance of complete failure.

Example:

```
Application

      │

Load Balancer

   │      │

Server 1  Server 2
```

If one server fails, another continues processing requests.

---

# Fault Isolation

A failure in one component should not bring down the entire application.

Example:

```
Payment Service

Recommendation Service

Notification Service
```

If the recommendation service fails, users should still be able to make purchases.

Fault isolation improves overall reliability.

---

# Reliability in Distributed Systems

Distributed systems introduce additional challenges.

Examples include:

- Network partitions
- Message duplication
- Clock synchronization
- Partial failures
- Replica inconsistency

Architects use techniques such as:

- Consensus algorithms
- Replication
- Distributed transactions
- Message acknowledgements

to improve reliability.

---

# Measuring Reliability

Organizations commonly monitor metrics such as:

- Failure Rate
- Success Rate
- Error Rate
- Mean Time Between Failures (MTBF)
- Mean Time To Recovery (MTTR)

These metrics help evaluate whether the system consistently performs as expected.

---

# Real-World Examples

## Banking Systems

Banks prioritize reliability over speed.

Every transaction must be:

- Accurate
- Durable
- Consistent

Even a single incorrect transaction can have serious financial consequences.

---

## Airline Reservation Systems

Airline systems must avoid:

- Double booking seats
- Losing reservations
- Incorrect ticket generation

Reliability is essential for maintaining customer trust.

---

## Cloud Storage Services

Cloud storage providers replicate data across multiple servers to prevent data loss and ensure files remain accessible.

---

## Online Retail Platforms

When a customer places an order, the system must:

- Reserve inventory
- Process payment
- Generate the order
- Send confirmation

Each step must execute correctly to avoid inconsistencies.

---

# Common Mistakes

- Ignoring partial failures.
- Assuming networks are always reliable.
- Not validating user input.
- Processing duplicate requests.
- Skipping backups.
- Not using transactions for critical operations.
- Failing to monitor system health.
- Treating temporary failures as permanent.

---

# Best Practices

- Design systems assuming failures will occur.
- Use transactions for critical business operations.
- Implement idempotency for APIs.
- Replicate important data.
- Validate all incoming requests.
- Monitor failures continuously.
- Automate recovery whenever possible.
- Regularly test backup and disaster recovery procedures.

---

# Key Takeaways

- Reliability measures a system's ability to consistently produce correct results.
- A reliable system continues functioning correctly even when failures occur.
- Reliability is achieved through techniques such as transactions, replication, retries, idempotency, validation, and monitoring.
- Reliability and availability complement each other but measure different aspects of system quality.
- Users trust systems that not only remain online but also consistently behave correctly.