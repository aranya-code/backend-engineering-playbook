# ElastiCache Security and Monitoring

Operating in-memory data stores in production requires strict security boundaries and continuous monitoring of performance metrics. Because Redis and Memcached hold data directly in volatile memory and serve high-throughput traffic, securing access paths and detecting CPU/memory bottlenecks early is essential.

This guide details network isolation, authentication, encryption, and critical troubleshooting metrics for Amazon ElastiCache.

---

# Network Security

ElastiCache runs inside your VPC. It is not directly accessible from the public internet.

- **Private Subnets**: Always deploy ElastiCache nodes in private subnets with no route to an Internet Gateway.
- **Security Groups**: Restrict network access to the cache port (e.g., `6379` for Redis, `11211` for Memcached). Only allow inbound connections from the security groups of your application servers (EC2, ECS, Lambda).
- **Subnet Groups**: An ElastiCache Subnet Group is a collection of subnets (typically private) within a VPC that you associate with the cache nodes. Ensure the subnet group spans multiple Availability Zones to support Multi-AZ replication.

---

# Authentication and Encryption

ElastiCache provides transit and storage security controls:

## 1. Encryption in Transit (TLS)

Protects replication streams and client-to-cache query traffic from interception.
- **Enforcement**: Must be enabled when the cluster is created.
- **CA Rotation**: Clients must trust the root certificate authority to maintain connection stability.

## 2. Encryption at Rest (KMS)

Encrypts data written to disk (during snapshots, backups, and page swapping) using AES-256 via KMS keys.
- **Keys**: Supports AWS-managed keys or custom Customer Managed Keys (CMKs).

## 3. Access Control and Authentication

- **Redis AUTH (Token-Based)**: Authenticate client connections using a password token (`AUTH <password>`) configured when the cluster is created (requires TLS enabled).
- **Role-Based Access Control (RBAC)**: Manage access via **User Groups**. You can create specific users with distinct access permissions (e.g., read-only users, admin users) and assign them permissions using Redis ACL strings (e.g., `on ~* +@read -@write`).
- **IAM Authentication**: You can authenticate to ElastiCache using IAM roles and AWS credentials (available in newer ElastiCache Redis versions), eliminating the need for hardcoded tokens.

---

# Critical CloudWatch Metrics to Monitor

Redis is historically a single-threaded execution engine. This architectural design makes traditional monitoring metrics (like host CPU utilization) misleading.

## CPU Metrics (Crucial Distinction)

- **CPUUtilization**: Measures the average CPU usage across all cores of the underlying EC2 host.
  - **Limitation**: On a multi-core host (e.g., 4 vCPUs), if the single-threaded Redis engine is running at 100% on its assigned core, `CPUUtilization` will report only **25%** (100% / 4 cores). The database is completely saturated, but the host-level alert will not trigger.
- **EngineCPUUtilization**: Measures the CPU utilization of the specific thread running the Redis database engine.
  - **Best Practice**: Set alerts on `EngineCPUUtilization` at **80%**. This is the only accurate measure of Redis CPU capacity.

```text
Host-Level CPU Utilization (CPUUtilization):
Core 1: Running Redis Engine ──────► 100%
Core 2: Idle ──────────────────────► 0%
Core 3: Idle ──────────────────────► 0%
Core 4: Idle ──────────────────────► 0%
Average Host CPU = 25% (Looks safe, but database is saturated!)

Engine CPU Utilization (EngineCPUUtilization):
Redis Engine Thread ───────────────► 100% (Accurate saturation indicator)
```

## Performance and Hit Metrics

- **CacheHits / CacheMisses**: The number of successful key lookups vs. failed lookups.
- **CacheHitRatio**: Calculated as `CacheHits / (CacheHits + CacheMisses)`.
  - **Alert**: Set an alert if `CacheHitRatio` drops below a target baseline (e.g., <80%), indicating stale cache keys or cache thrashing.
- **CurrConnections**: The number of active client connections. Spikes in connections can indicate application connection leaks.
- **NetworkBytesIn / NetworkBytesOut**: Network throughput metrics. Saturated network links will cause query timeouts.

---

# Troubleshooting High EngineCPUUtilization

If `EngineCPUUtilization` spikes to 100%, query latency will increase and clients will experience timeouts. Common causes and resolutions:

## 1. Expensive O(N) Commands

- **Cause**: Executing high-complexity commands on large datasets (e.g., `KEYS *`, `SMEMBERS`, `HGETALL`, or complex Lua scripts). Because Redis is single-threaded, an O(N) command blocks all other queries until it completes.
- **Resolution**: Use cursor-based scanning commands (`SCAN`, `HSCAN`, `SSCAN`) instead of returning entire sets. Never run `KEYS` in production; use `SCAN` instead.

## 2. High Connection Rates

- **Cause**: Establishing new TLS/TCP connections at high frequencies (common with serverless Lambda scale-out). Handshaking consumes high CPU cycles.
- **Resolution**: Implement connection reuse in application code, use keep-alive settings, or evaluate caching middleware.

## 3. Large Payloads

- **Cause**: Storing large values (e.g., serialized JSON objects >10 MB). Network serialization and compression consume engine CPU time.
- **Resolution**: Compress values before writing to cache, or split large hashes/lists into smaller keys.

---

# Key Takeaways

- Deploy ElastiCache in **private subnets only** and restrict ports using security groups.
- Enable **TLS** (transit) and **KMS** (rest) encryption at cluster creation.
- Use **RBAC User Groups** or **Redis AUTH** to secure database client authentication.
- Always monitor and alert on **`EngineCPUUtilization`**, not standard `CPUUtilization`, due to the single-threaded nature of Redis.
- Avoid running expensive O(N) commands (`KEYS *`) in production to prevent blocking the engine thread.

---
