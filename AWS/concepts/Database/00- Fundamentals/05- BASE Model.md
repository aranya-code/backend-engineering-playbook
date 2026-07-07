# BASE Model

# Introduction

BASE is commonly associated with distributed NoSQL databases that prioritize scalability and availability over strict consistency.

---

# BASE

- Basically Available
- Soft State
- Eventual Consistency

---

# Basically Available

The system remains available even when parts of the infrastructure fail.

---

# Soft State

Data may temporarily change because of asynchronous replication.

---

# Eventual Consistency

Given enough time and no new updates, all replicas converge to the same value.

---

# ACID vs BASE

| Feature | ACID | BASE |
|---------|------|------|
| Consistency | Strong | Eventual |
| Availability | Lower | Higher |
| Scalability | Moderate | Excellent |
| Typical DB | RDS, Aurora | DynamoDB |

---

# AWS Examples

ACID:
- Amazon RDS
- Amazon Aurora

BASE:
- Amazon DynamoDB

---

# Best Practices

Choose BASE when:
- Global scale is required.
- Temporary stale reads are acceptable.
- High availability is critical.

---

# Interview Questions

1. What is BASE?
2. BASE vs ACID?
3. Why do NoSQL databases prefer BASE?

---

# Quick Revision

BASE trades strict consistency for scalability and availability.
