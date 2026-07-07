# CAP Theorem

# Introduction

Distributed databases cannot simultaneously guarantee all three properties:

- Consistency
- Availability
- Partition Tolerance

---

# Consistency

Every client sees the latest committed data.

---

# Availability

Every request receives a response.

---

# Partition Tolerance

The system continues operating despite network failures.

---

# Reality

Modern distributed systems must tolerate partitions.

Therefore, architects generally choose between:

- CP
- AP

---

# AWS Examples

| Service | Preference |
|----------|------------|
| Amazon RDS | Strong consistency |
| Amazon Aurora | Strong consistency |
| Amazon DynamoDB | Configurable (eventual or strong reads) |

---

# Why It Matters

CAP influences database selection, replication strategy, and global architecture.

---

# Interview Questions

- Explain CAP theorem.
- Can a distributed database provide CA?
- Why is partition tolerance considered mandatory?

---

# Quick Revision

C = Correct data

A = Always responds

P = Survives network partition
