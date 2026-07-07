# Replication

# Introduction

Replication copies data from one database instance to one or more replicas for availability, disaster recovery, and read scaling.

---

# Types of Replication

## Synchronous

- Primary waits for replica acknowledgement.
- Strong consistency.
- Higher write latency.

## Asynchronous

- Primary commits immediately.
- Replica updates later.
- Possible replication lag.

---

# AWS Examples

- Amazon RDS Multi-AZ → Synchronous replication
- Amazon RDS Read Replicas → Asynchronous replication
- Amazon Aurora → Distributed storage replication

---

# Benefits

- High availability
- Disaster recovery
- Read scaling
- Backup support

---

# Challenges

- Replica lag
- Failover planning
- Consistency trade-offs

---

# Best Practices

- Monitor replication lag.
- Use synchronous replication for HA.
- Use asynchronous replication for read-heavy workloads.

---

# Interview Questions

1. Synchronous vs asynchronous replication?
2. Why do read replicas lag?
3. Why doesn't Multi-AZ improve read performance?

---

# Quick Revision

- Multi-AZ = Sync = HA
- Read Replica = Async = Read Scaling
- Aurora = Storage-level replication
