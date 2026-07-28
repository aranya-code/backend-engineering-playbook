# CAP Theorem

## Overview

One of the most fundamental concepts in Distributed Systems is the **CAP Theorem**. It explains why distributed databases and distributed applications cannot simultaneously guarantee every desirable property during a network failure.

The CAP Theorem does **not** state that distributed systems are inherently unreliable. Instead, it helps architects understand the trade-offs that must be made when designing systems that operate across multiple machines.

Modern databases such as Cassandra, MongoDB, DynamoDB, CockroachDB, and Redis Cluster all make different CAP-related design decisions depending on the problems they are designed to solve.

Understanding CAP Theorem is essential because it influences decisions related to database selection, replication, fault tolerance, consistency models, and distributed system architecture.

---

# What is the CAP Theorem?

The **CAP Theorem**, proposed by computer scientist **Eric Brewer** and later formally proven by Seth Gilbert and Nancy Lynch, states:

> A distributed system cannot simultaneously guarantee **Consistency**, **Availability**, and **Partition Tolerance** during a network partition.

When a partition occurs, a distributed system must choose between:

- Consistency
- Availability

because Partition Tolerance is generally unavoidable in distributed systems.

---

# The Three Properties

```
             CAP

              ▲
             / \
            /   \
           /     \
Consistency  Availability
        \       /
         \     /
          \   /
 Partition Tolerance
```

---

# Consistency (C)

Consistency means that **every client sees the same data at the same time**, regardless of which server processes the request.

After a successful write:

```
Write

↓

Server A

↓

Server B

↓

Server C
```

Every server immediately returns the latest value.

Example:

```
Account Balance

$500

↓

Update

↓

$300
```

Every user should immediately see:

```
$300
```

No server should return the old value.

---

# Availability (A)

Availability means that **every request receives a response**, even if some servers are unavailable.

Example:

```
Server A ❌

Server B ✅

Server C ✅
```

Users continue receiving responses from healthy servers.

The response may not always contain the most recent data.

Availability focuses on keeping the application online.

---

# Partition Tolerance (P)

A partition occurs when servers cannot communicate with each other because of a network failure.

Example:

```
      Network Failure

Server A      X      Server B
                  \
                   X
                    \
                  Server C
```

The servers are still running but communication between them has been interrupted.

Network partitions are inevitable in distributed systems.

---

# Why Partition Tolerance Is Mandatory

Consider servers deployed in multiple regions.

```
India

↓

Europe

↓

United States
```

If the network connection between regions fails, the system cannot simply stop expecting partitions.

Since network failures cannot be eliminated, modern distributed systems are generally designed to tolerate partitions.

This means the real architectural choice becomes:

```
CP

or

AP
```

---

# Understanding the Trade-off

Imagine two database servers.

```
Server A

Balance = $500
```

```
Server B

Balance = $500
```

Now a customer withdraws:

```
$200
```

Server A updates:

```
Balance = $300
```

Before Server B receives the update, the network fails.

Now another customer reads from Server B.

The system has two choices.

---

# Option 1: Prioritize Consistency (CP)

Server B refuses to answer until synchronization is restored.

```
Request

↓

Server B

↓

Error / Retry
```

Advantages:

- No stale data
- Correct results
- Strong consistency

Disadvantages:

- Some requests fail
- Lower availability

---

# Option 2: Prioritize Availability (AP)

Server B immediately responds.

```
Request

↓

Server B

↓

Balance = $500
```

Advantages:

- Application remains available
- Better user experience

Disadvantages:

- User receives stale data
- Temporary inconsistency

---

# CP Systems

A CP (Consistency + Partition Tolerance) system prefers correctness over availability during a partition.

```
Partition

↓

Reject Request

↓

Wait for Synchronization

↓

Return Latest Data
```

Characteristics:

- Strong consistency
- Some requests may fail
- Ideal when incorrect data is unacceptable

Typical use cases:

- Banking
- Financial systems
- Inventory management
- Reservation systems

---

# AP Systems

An AP (Availability + Partition Tolerance) system prefers continuous service even if some data is temporarily inconsistent.

```
Partition

↓

Continue Serving Requests

↓

Synchronize Later
```

Characteristics:

- High availability
- Eventual consistency
- Better user experience during failures

Typical use cases:

- Social media
- Product catalogs
- Messaging systems
- Recommendation engines

---

# What About CA?

CA stands for:

- Consistency
- Availability

without Partition Tolerance.

```
Client

↓

Single Database
```

CA systems are possible only when network partitions are not considered, such as in a single-node or non-distributed environment.

In real distributed systems, partitions are always a possibility, making pure CA systems impractical.

---

# CAP Decision Matrix

| Partition Occurs | Choice | Result |
|------------------|--------|--------|
| Yes | Consistency | Some requests are rejected |
| Yes | Availability | Some users may receive stale data |

The system cannot guarantee both simultaneously during the partition.

---

# Real-World Examples

## Banking System

Priority:

```
Consistency

>

Availability
```

If account balances are inconsistent, financial loss may occur.

The system may temporarily reject transactions instead of returning incorrect data.

---

## Social Media

Priority:

```
Availability

>

Strong Consistency
```

If a "Like" count is delayed for a few seconds, users generally accept the inconsistency.

Keeping the platform responsive is more important.

---

## Online Shopping

Different components make different choices.

| Component | Typical Priority |
|-----------|------------------|
| Payment | CP |
| Inventory | CP |
| Product Search | AP |
| Recommendations | AP |
| Analytics | AP |

One application may contain both CP and AP components.

---

# CAP and Eventual Consistency

Many highly available systems use **Eventual Consistency**.

Instead of requiring every replica to update immediately:

```
Write

↓

Replica A

↓

Replica B

↓

Replica C
```

updates propagate over time.

Eventually:

```
All Replicas

↓

Same Data
```

Temporary inconsistencies are accepted to maximize availability.

---

# CAP Is About Network Partitions

A common misconception is:

> "You must always choose only two of the three."

This is incorrect.

The CAP Theorem specifically applies **during a network partition**.

When no partition exists, many distributed systems can provide both consistency and availability.

The difficult decision arises only after communication between nodes is disrupted.

---

# Common Misconceptions

### Misconception 1

CAP means choosing any two properties forever.

**Reality:** The trade-off occurs only during a network partition.

---

### Misconception 2

AP systems are incorrect.

**Reality:** AP systems often use eventual consistency and converge to the correct state over time.

---

### Misconception 3

CP systems are always better.

**Reality:** The appropriate choice depends entirely on business requirements.

---

# Common Mistakes

- Assuming network failures never occur.
- Choosing strong consistency where eventual consistency is sufficient.
- Sacrificing availability without business justification.
- Assuming every service within an application requires the same CAP choice.
- Misunderstanding CAP as a database feature rather than a distributed systems principle.

---

# Best Practices

- Design assuming network partitions will eventually occur.
- Let business requirements determine whether consistency or availability has higher priority.
- Use strong consistency only where correctness is critical.
- Use eventual consistency for user-facing features that can tolerate brief delays.
- Understand the CAP behavior of the databases and distributed systems you use.
- Remember that different services in the same application may require different CAP trade-offs.

---

# Key Takeaways

- CAP Theorem explains the fundamental trade-off between Consistency, Availability, and Partition Tolerance in distributed systems.
- During a network partition, a distributed system must choose between Consistency and Availability.
- Partition Tolerance is effectively mandatory in real distributed systems because network failures are unavoidable.
- CP systems prioritize correct data, while AP systems prioritize continuous service.
- The correct CAP choice depends on business requirements, not on a universally "better" architecture.