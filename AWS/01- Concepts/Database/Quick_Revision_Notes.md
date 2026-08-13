# Database Playbook: Quick Revision Notes

A highly condensed, high-value revision sheet summarizing essential Amazon RDS and Amazon ElastiCache concepts for production incidents and technical interviews.

---

# Amazon RDS Quick Reference

## 1. High Availability vs. Scaling
- **Multi-AZ**: Synchronous storage-level replication. Passive standby. Zero data loss (RPO = 0). Automatic failover by DNS CNAME change. Primary purpose: High Availability.
- **Read Replica**: Asynchronous engine-level replication (binlog/WAL). Active and readable. Eventual consistency (Replication Lag). Primary purpose: Read Scaling.

## 2. Storage Auto-Scaling
- Automatically expands database storage by 10% or 10 GB when free space falls below 10%.
- **Auto-Scale Up Only**: Storage can never be scaled down once increased.
- Cooldown period of **6 hours** enforced between consecutive storage modifications.

## 3. RDS Proxy
- Pools and multiplexes database connections, protecting CPU/memory from serverless (AWS Lambda) connection spikes.
- Reduces Multi-AZ failover times by up to 66% by preserving client-side connections and routing query traffic instantly.
- Integrates with Secrets Manager (credentials) and IAM Database Authentication.

## 4. Encryption at Rest
- Encryption **must be configured at database creation**.
- To encrypt an unencrypted database: Take snapshot → Copy & encrypt snapshot with KMS CMK → Restore snapshot to new database instance → Cutover endpoints.

## 5. Observability
- **EngineCPUUtilization**: The only accurate metric for Redis CPU tracking due to its single-threaded execution model. Standard `CPUUtilization` is host-average.
- **Performance Insights (AAS)**: Visualizes Database Load via Average Active Sessions. AAS exceeding the Max vCPU line indicates database bottleneck.

---

# ElastiCache Quick Reference

## 1. Caching Patterns
- **Cache-Aside (Lazy Loading)**: Read from cache; on miss, read from DB and write to cache. Writes go directly to DB. Safe against cache crash, but potential for stale data.
- **Write-Through**: Write to cache and DB simultaneously. Consistent data, but incurs write latency.
- **Write-Back (Write-Behind)**: Write to cache only (immediate ACK). Cache flushes asynchronously to DB in batches. Fast writes, but **high data loss risk** if cache crashes.

## 2. Cluster Deployment Modes
- **Cluster Mode Disabled**: 1 primary node, up to 5 read replicas. Max memory = size of one node. Scale writes vertically only.
- **Cluster Mode Enabled**: Sharded across up to 500 shards using 16,384 Hash Slots. Scales memory and writes horizontally. Multi-key operations require **Hash Tags `{}`** to avoid cross-slot errors.

## 3. Eviction and TTL
- **Eviction Policy (`maxmemory-policy`)**: Determines what happens when cache memory is full. `allkeys-lru` evicts cold keys; `noeviction` returns write errors.
- **Memory Reserves**: Always configure **`reserved-memory-percent` to 25%** to prevent OOM process kills during background snapshot forks (Copy-on-Write).
- **Swap Usage**: Monitor `SwapUsage` in CloudWatch. Swap activity indicates memory exhaustion and causes query latency to spike from sub-milliseconds to seconds.

## 4. Cache Failure Mitigation
- **Cache Stampede**: Multiple instances query the database simultaneously when a popular key expires. Mitigate with distributed locks (`SETNX`) or background pre-fetching.
- **Cache Penetration**: Queries for non-existent IDs bypass cache to hit the database. Mitigate by caching null results or placing a Bloom Filter in front.
- **Cache Avalanche**: Mass key expiration or cache crash overloads the database. Mitigate by adding random jitter to TTLs, utilizing Multi-AZ clustering, and rate limiting.

---
