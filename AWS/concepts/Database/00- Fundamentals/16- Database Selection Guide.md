# Database Selection Guide

# Introduction

Choosing the right database depends on consistency, scalability, latency, data model, and workload rather than popularity.

---

# Decision Matrix

| Requirement | Recommended AWS Service |
|---|---|
| Relational OLTP | Amazon RDS |
| High-performance relational | Amazon Aurora |
| Massive key-value workloads | Amazon DynamoDB |
| In-memory cache | Amazon ElastiCache |
| Durable in-memory database | Amazon MemoryDB |
| Document database | Amazon DocumentDB |
| Graph relationships | Amazon Neptune |
| Time-series data | Amazon Timestream |
| Data warehouse | Amazon Redshift |

---

# Questions to Ask

- Is the data relational?
- Do I need ACID transactions?
- What is the expected read/write ratio?
- Will the workload scale globally?
- Is latency critical?

---

# Common Mistakes

- Choosing NoSQL without understanding access patterns.
- Using SQL for internet-scale key-value workloads.
- Ignoring operational cost.

---

# Best Practices

Start with workload requirements, then map them to database capabilities.

---

# Interview Questions

1. How do you choose between RDS and DynamoDB?
2. When is Aurora a better choice than RDS?

---

# Quick Revision

There is no universal best database—only the best fit for the workload.
