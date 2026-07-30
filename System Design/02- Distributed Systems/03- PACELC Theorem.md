# PACELC Theorem

## Overview

After learning the CAP Theorem, many engineers assume that distributed systems only make trade-offs during **network partitions**.

However, in real-world systems, network partitions are relatively rare. Most of the time, distributed systems operate under normal network conditions.

This raises an important question:

> **How do distributed systems make trade-offs when there is no network partition?**

The **PACELC Theorem** answers this question.

PACELC extends the CAP Theorem by explaining that distributed systems make architectural trade-offs **both during network failures and during normal operation**.

Because of this, PACELC provides a more practical model for understanding the behavior of modern distributed databases.

---

# Why CAP Is Not Enough

The CAP Theorem focuses only on this situation:

```
Network Partition

↓

Choose

Consistency

or

Availability
```

But what happens when the network is healthy?

```
No Partition

↓

System Still Makes Choices
```

For example:

- Should every write wait for all replicas?
- Should users receive faster responses?
- Should replication happen asynchronously?

CAP does not answer these questions.

PACELC does.

---

# What is PACELC?

PACELC stands for:

```
If there is a

Partition (P)

↓

Choose

Availability (A)

or

Consistency (C)

Else (E)

↓

Choose

Latency (L)

or

Consistency (C)
```

In short:

```
P

↓

A or C

ELSE

↓

L or C
```

---

# Understanding PACELC

PACELC describes two situations.

## Situation 1

A network partition occurs.

The system chooses between:

```
Consistency

or

Availability
```

This is identical to CAP.

---

## Situation 2

There is **no** network partition.

Now the system chooses between:

```
Latency

or

Consistency
```

This is the new contribution made by PACELC.

---

# Why Latency and Consistency Conflict

Suppose a database has replicas in three regions.

```
India

↓

Europe

↓

United States
```

A user writes new data.

The system has two choices.

---

## Option 1

Wait until every replica confirms the write.

```
Client

↓

Replica A

↓

Replica B

↓

Replica C

↓

Success
```

Advantages:

- Strong consistency

Disadvantages:

- Higher latency

---

## Option 2

Return success immediately.

```
Client

↓

Primary Replica

↓

Success

↓

Replicate Later
```

Advantages:

- Lower latency

Disadvantages:

- Temporary inconsistency

---

# PACELC Decision Flow

```
               Request

                   │

                   ▼

      Is There a Network Partition?

            │              │

          Yes              No

           │                │

           ▼                ▼

Choose Between      Choose Between

Consistency         Consistency

or                  or

Availability        Latency
```

Every distributed database follows this decision process, whether explicitly or implicitly.

---

# PACELC Examples

## Database A

Characteristics:

- Strong consistency
- Higher latency

Classification:

```
PC/EC
```

Meaning:

- During a partition, choose Consistency.
- Otherwise, choose Consistency over lower latency.

---

## Database B

Characteristics:

- Eventual consistency
- Very fast responses

Classification:

```
PA/EL
```

Meaning:

- During a partition, choose Availability.
- Otherwise, optimize for low latency.

---

# Common PACELC Categories

## PA/EL

```
Partition

↓

Availability

Else

↓

Latency
```

Characteristics:

- High availability
- Very low latency
- Eventual consistency

Suitable for:

- Social media
- Product catalogs
- News feeds
- Recommendation systems

---

## PA/EC

```
Partition

↓

Availability

Else

↓

Consistency
```

Characteristics:

- Highly available
- Stronger consistency during normal operation
- Slightly higher latency

Less common but useful for systems requiring a balance between responsiveness and correctness.

---

## PC/EL

```
Partition

↓

Consistency

Else

↓

Latency
```

Characteristics:

- Rejects requests during partitions
- Fast during normal operation

Useful when correctness is critical but latency must remain low whenever possible.

---

## PC/EC

```
Partition

↓

Consistency

Else

↓

Consistency
```

Characteristics:

- Strong correctness
- Highest coordination cost
- Higher latency

Often chosen for financial systems and mission-critical workloads.

---

# Real-World Examples

## Banking

Requirements:

- Accurate balances
- Correct transactions
- No stale reads

Typical behavior:

```
PC/EC
```

Correctness is prioritized both during failures and during normal operation.

---

## Social Media

Requirements:

- Fast user experience
- Continuous availability

Typical behavior:

```
PA/EL
```

Users prefer immediate responses, even if some information is temporarily stale.

---

## E-Commerce

Different services may choose different PACELC strategies.

| Service | Typical Strategy |
|----------|------------------|
| Payments | PC/EC |
| Inventory | PC/EC |
| Product Search | PA/EL |
| Recommendations | PA/EL |
| Reviews | PA/EL |

PACELC decisions are often made at the service level rather than the application level.

---

# CAP vs PACELC

| Feature | CAP | PACELC |
|---------|-----|---------|
| Focus | Network partitions | Partitions and normal operation |
| Considers latency | ❌ No | ✅ Yes |
| Considers consistency | ✅ Yes | ✅ Yes |
| Considers availability | ✅ Yes | ✅ Yes |
| Practical for modern systems | Limited | More comprehensive |

PACELC builds upon CAP rather than replacing it.

---

# Why PACELC Matters

Modern cloud systems spend most of their time operating without network partitions.

Architects therefore spend much of their effort deciding:

- Should writes be synchronous?
- Should reads be served from nearby replicas?
- How much replication delay is acceptable?
- Is lower latency more valuable than immediate consistency?

PACELC provides a framework for answering these questions.

---

# Relationship with Replication

PACELC is closely related to replication strategies.

For example:

**Synchronous Replication**

- Higher consistency
- Higher latency

**Asynchronous Replication**

- Lower latency
- Eventual consistency

These trade-offs will become clearer in the next chapter on Replication.

---

# Common Mistakes

- Assuming CAP fully explains distributed systems.
- Forgetting that latency matters even when the network is healthy.
- Believing strong consistency is always worth the additional latency.
- Applying the same PACELC strategy to every service.
- Ignoring user experience when choosing consistency guarantees.

---

# Best Practices

- Use PACELC alongside CAP when evaluating distributed systems.
- Choose consistency for business-critical operations.
- Optimize latency for user-facing features whenever temporary inconsistency is acceptable.
- Evaluate PACELC decisions independently for each service.
- Understand how your database implements replication and synchronization before selecting a consistency strategy.

---

# Key Takeaways

- PACELC extends the CAP Theorem by considering both network failures and normal system operation.
- During a partition, a system chooses between Consistency and Availability.
- When there is no partition, a system chooses between Latency and Consistency.
- PACELC provides a more practical framework for understanding modern distributed databases.
- Different services within the same application may intentionally adopt different PACELC strategies based on business requirements.