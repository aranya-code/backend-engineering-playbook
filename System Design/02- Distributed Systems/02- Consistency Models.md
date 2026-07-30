# Consistency Models

## Overview

In distributed systems, data is often replicated across multiple servers to improve availability, fault tolerance, and scalability. While replication provides many benefits, it also introduces a new challenge:

> **How quickly should all replicas agree on the same data?**

The answer depends on the **Consistency Model** used by the system.

A consistency model defines the rules that determine **when clients can observe updates** after data has been modified.

Different distributed databases provide different consistency guarantees depending on their design goals and the trade-offs they make between performance, availability, and correctness.

Understanding consistency models is essential because they directly influence user experience, data correctness, and system reliability.

---

# What is a Consistency Model?

A **Consistency Model** defines how and when updates made to replicated data become visible to clients.

In simple terms:

> It specifies what data a client is allowed to read after another client performs a write.

Example:

```
Replica A

Balance = $1000
```

```
Replica B

Balance = $1000
```

A client updates the balance:

```
Balance = $800
```

When another client immediately performs a read:

- Will it always see **$800**?
- Could it still see **$1000**?
- How long might it take before every replica agrees?

The consistency model answers these questions.

---

# Why Do We Need Different Consistency Models?

Imagine a globally distributed application.

```
India

↓

Europe

↓

United States
```

Every write must travel across continents.

If every update had to reach every replica before responding to the user, requests would become much slower.

Instead, architects choose a consistency model based on business requirements.

Some systems prioritize:

- Correctness

Others prioritize:

- Availability
- Low latency
- User experience

---

# Types of Consistency Models

The most common consistency models are:

```
Consistency Models

│

├── Strong Consistency

├── Eventual Consistency

├── Weak Consistency

├── Causal Consistency

├── Session Consistency

└── Read-Your-Writes Consistency
```

Each offers different guarantees.

---

# Strong Consistency

Strong Consistency guarantees that:

> Every client always reads the latest successful write.

Example:

```
Write

↓

Replica A

↓

Replica B

↓

Replica C
```

Only after every required replica has acknowledged the update does the system return success.

Now every client sees:

```
Latest Value
```

regardless of which replica they contact.

---

## Advantages

- No stale reads
- Predictable behavior
- High data correctness
- Easier application logic

---

## Disadvantages

- Higher latency
- Lower availability during failures
- More coordination between replicas

---

## Common Use Cases

- Banking
- Payments
- Inventory
- Airline reservations

---

# Eventual Consistency

Eventual Consistency guarantees:

> If no new updates occur, all replicas will eventually converge to the same value.

Example:

```
Write

↓

Replica A

↓

(Delay)

↓

Replica B

↓

(Delay)

↓

Replica C
```

Immediately after the write:

```
Replica A = New Value

Replica B = Old Value

Replica C = Old Value
```

A short time later:

```
Replica A = New Value

Replica B = New Value

Replica C = New Value
```

Eventually, every replica agrees.

---

## Advantages

- High availability
- Better performance
- Lower latency
- Excellent scalability

---

## Disadvantages

- Temporary stale reads
- Additional application complexity
- Synchronization delays

---

## Common Use Cases

- Social media
- Product catalogs
- DNS
- Recommendation systems

---

# Weak Consistency

Weak Consistency provides very few guarantees.

A read operation:

- May return old data
- May return new data
- Timing is unpredictable

Example:

```
Write

↓

Read

↓

Old Value
```

or

```
Write

↓

Read

↓

New Value
```

Both are possible.

Weak consistency maximizes performance but sacrifices predictability.

---

## Typical Use Cases

- Analytics
- Monitoring
- Logging
- Telemetry

---

# Causal Consistency

Causal Consistency preserves the order of related operations.

Example:

Alice sends:

```
Message 1

↓

Message 2
```

Every client sees:

```
Message 1

↓

Message 2
```

The messages cannot appear in reverse order.

However, unrelated operations may be observed differently by different users.

---

## Advantages

- Preserves logical ordering
- Better user experience
- More scalable than strong consistency

---

## Common Use Cases

- Chat applications
- Collaboration tools
- Social media comments

---

# Session Consistency

Session Consistency guarantees consistency only within a single user's session.

Example:

User A updates:

```
Profile Picture
```

Immediately afterward:

```
User A

↓

Reads

↓

New Profile Picture
```

Other users may still temporarily see the old picture.

---

## Benefits

- Better user experience
- Less synchronization overhead
- Higher scalability

---

## Common Use Cases

- User profiles
- Shopping carts
- User settings

---

# Read-Your-Writes Consistency

Read-Your-Writes guarantees:

> After a client performs a write, that same client always sees its own update.

Example:

```
Update Email

↓

Read Email

↓

Updated Value
```

The user never observes their own stale data.

Other users may still experience eventual consistency.

---

## Common Use Cases

- User dashboards
- Account settings
- Content creation platforms

---

# Comparison of Consistency Models

| Model | Latest Data Guaranteed | Performance | Availability |
|--------|------------------------|------------|--------------|
| Strong | ✅ Always | Lower | Lower |
| Eventual | ❌ Eventually | High | High |
| Weak | ❌ No Guarantee | Very High | Very High |
| Causal | ✅ For Related Operations | High | High |
| Session | ✅ Within Session | High | High |
| Read-Your-Writes | ✅ For Same User | High | High |

---

# Choosing the Right Consistency Model

Different applications require different guarantees.

| Application | Preferred Model |
|-------------|-----------------|
| Banking | Strong |
| Payment Systems | Strong |
| Airline Booking | Strong |
| Social Media | Eventual |
| Product Catalog | Eventual |
| Chat Applications | Causal |
| User Profiles | Session |
| Account Settings | Read-Your-Writes |

There is no universally best consistency model.

The correct choice depends on business requirements.

---

# Real-World Examples

## Amazon Product Catalog

Product descriptions and images are often eventually consistent.

A brief delay in synchronization is acceptable.

---

## Banking

Account balances require strong consistency.

Showing an outdated balance could result in incorrect financial transactions.

---

## WhatsApp

Messages from the same sender should appear in order.

This aligns well with causal consistency.

---

## Google Docs

A user's edits should appear immediately to them.

Session consistency and causal ordering help provide a smooth collaborative experience.

---

# Relationship with CAP Theorem

Consistency models determine **how consistent** a distributed system is.

CAP Theorem determines **what trade-offs** must be made during network partitions.

Together, they help architects decide:

- How quickly data should synchronize
- How much stale data is acceptable
- How available the system should remain during failures

---

# Common Mistakes

- Assuming every application requires strong consistency.
- Confusing eventual consistency with data loss.
- Ignoring business requirements when selecting a consistency model.
- Using strong consistency where temporary inconsistency is acceptable.
- Expecting all users to observe updates simultaneously in eventually consistent systems.

---

# Best Practices

- Choose the weakest consistency model that still satisfies business requirements.
- Use strong consistency only for critical operations.
- Prefer eventual consistency for highly scalable, user-facing features.
- Ensure users can always see their own updates when appropriate.
- Document consistency guarantees for each service and API.

---

# Key Takeaways

- A consistency model defines when updates become visible to clients in a distributed system.
- Different consistency models provide different trade-offs between correctness, performance, and availability.
- Strong consistency guarantees the latest data but increases latency.
- Eventual consistency improves scalability and availability by allowing temporary inconsistencies.
- The appropriate consistency model should always be selected based on business requirements rather than technical preference.