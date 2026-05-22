# RDS Read Replicas

## Purpose

Used for read scalability.

---

## Key Features

- Up to 15 replicas
- Async replication
- Cross-AZ and Cross-Region support
- Read-only workloads

---

## Use Cases

- Reporting
- Analytics
- Read-heavy applications

---

## Important Notes

- Writes go to primary DB
- Reads can go to replicas
- Replicas can be promoted to standalone DBs

---

## Interview Tip

Read replicas improve READ performance only, not write performance.
