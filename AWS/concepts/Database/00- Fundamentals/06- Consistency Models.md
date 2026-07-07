# Consistency Models

# Introduction

Consistency determines when clients observe the latest data after a write operation.

---

# Strong Consistency

Every read returns the most recent successful write.

Examples:
- Amazon RDS
- Amazon Aurora
- DynamoDB (strongly consistent reads)

Advantages:
- Predictable
- Ideal for financial systems

---

# Eventual Consistency

Reads may temporarily return stale data until replicas synchronize.

Examples:
- DynamoDB (default reads)
- Globally distributed systems

Advantages:
- Higher availability
- Better scalability
- Lower latency

---

# Read-After-Write Consistency

Immediately after writing an object, subsequent reads return the latest version.

Many AWS services support this behavior under specific conditions.

---

# Choosing a Model

| Requirement | Recommendation |
|-------------|----------------|
| Banking | Strong Consistency |
| Social Media Feed | Eventual Consistency |
| Analytics | Eventual Consistency |
| Inventory | Strong Consistency |

---

# Best Practices

- Use strong consistency only when required.
- Prefer eventual consistency for internet-scale applications.

---

# Interview Questions

1. Strong vs Eventual consistency?
2. Why is eventual consistency acceptable in many systems?
3. How does consistency affect scalability?

---

# Quick Revision

- Strong = Latest data
- Eventual = Latest data after replication
- Strong consistency usually has higher coordination costs.
