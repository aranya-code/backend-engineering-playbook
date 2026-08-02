# Production Scenario Based Questions

## Overview

Senior Backend interviews rarely focus only on Redis commands.

Instead, interviewers present **real production incidents** and evaluate how you analyze the problem, identify root causes, discuss trade-offs, and propose scalable solutions.

These questions test your understanding of:

- System Design
- Distributed Systems
- Caching
- High Availability
- Monitoring
- Troubleshooting
- Performance
- Disaster Recovery

The goal is not to memorize answers but to demonstrate engineering thinking.

---

# Q1. Your Redis server suddenly becomes unavailable. What happens to your application?

### Answer

The behavior depends entirely on how the application is designed.

Good architecture

```
Application

↓

Redis

↓

Failure

↓

Database Fallback

↓

Response
```

Poor architecture

```
Application

↓

Redis

↓

Failure

↓

Application Crash
```

A production-ready application should

- Detect Redis failures
- Fall back to the database
- Retry intelligently
- Avoid cascading failures

---

## Follow-up

Would you retry forever?

No.

Retries should be

- Limited
- Exponential backoff
- Circuit breaker enabled

---

# Q2. Redis memory usage suddenly reaches 100%. What would you do?

### Answer

First identify the cause instead of restarting Redis.

Investigation checklist

- Current memory usage
- Eviction policy
- Large keys
- Hot keys
- TTL configuration
- Memory fragmentation
- Recent deployment

Useful commands

```bash
INFO MEMORY

MEMORY STATS

MEMORY USAGE key

MEMORY DOCTOR
```

Possible solutions

- Increase memory
- Enable eviction
- Delete unnecessary keys
- Optimize data structures
- Add Redis Cluster

---

# Q3. API latency suddenly increases although the database is healthy.

Redis CPU usage is 100%.

How would you investigate?

### Answer

Possible causes

- KEYS command
- Large Lua script
- Hot Key
- Slow client
- Huge pipeline
- Large SORT
- Massive SCAN COUNT

Investigation

```bash
SLOWLOG GET

INFO

MONITOR
```

Monitor

- Slow commands
- CPU
- Connected clients
- Network latency

---

# Q4. Cache hit ratio suddenly drops from 95% to 40%.

What would you investigate?

### Answer

Possible causes

- Cache flush
- Deployment
- TTL expiration
- Wrong cache key
- Serialization issue
- Application bug

Check

- Recent deployment
- TTL values
- Cache invalidation logic
- Evictions
- Application logs

---

# Q5. A single Redis key receives millions of requests every minute.

What is happening?

### Answer

This is called a

```
Hot Key
```

Example

```
Homepage

↓

Millions of Requests

↓

One Key

↓

One Redis Node

↓

CPU Spike
```

Solutions

- Local cache
- Replication
- Key sharding
- CDN
- Load balancing

---

# Q6. Users report seeing stale data.

What could be the cause?

### Answer

Possible reasons

- Long TTL
- Replication lag
- Cache invalidation bug
- Read from Replica
- Failed cache update

Solution

- Read from Primary
- Shorter TTL
- Better invalidation strategy
- Event-driven cache updates

---

# Q7. During deployment every API becomes slow for two minutes.

What could be happening?

### Answer

Likely causes

- Cache warming not performed
- Cache cleared
- Application restart
- Cold cache

Workflow

```
Deployment

↓

Empty Cache

↓

Millions of Database Reads

↓

Slow APIs
```

Solution

Use

- Cache warming
- Gradual rollout
- Blue-Green deployment

---

# Q8. Redis restart causes huge database load.

Why?

### Answer

Redis cache becomes empty.

```
Restart

↓

Cache Miss

↓

Database

↓

High Load
```

Known as

```
Cold Cache
```

Solutions

- Cache warming
- Lazy loading
- Staggered restarts

---

# Q9. Users occasionally lose session data.

What would you investigate?

### Answer

Check

- Redis persistence
- TTL
- Session expiration
- Application logic
- Evictions
- Redis restart

Also verify

```
appendonly

save
```

configuration.

---

# Q10. Your application stores 50 MB JSON objects inside Redis.

Is this a good design?

### Answer

No.

Problems

- High memory usage
- Slow replication
- Slow persistence
- Large network transfer
- Higher latency

Better approach

Store

- Smaller objects
- Hashes
- Split data into logical pieces

---

# Q11. A customer complains that after placing an order, immediately refreshing the page shows the old status.

Why?

### Answer

Likely causes

- Replication lag
- Eventual consistency
- Cache invalidation delay

Solution

Read critical data from the Primary immediately after writes.

---

# Q12. How would you investigate increasing Redis latency?

### Answer

Check

- CPU
- Network
- Slow commands
- Memory
- Fragmentation
- Replication lag
- Persistence

Useful commands

```bash
INFO

LATENCY LATEST

SLOWLOG GET
```

---

# Q13. A Redis Cluster node fails.

What happens?

### Answer

If a Replica exists

```
Primary

↓

Fails

↓

Replica Promoted

↓

Cluster Continues
```

If no Replica exists,

part of the cluster becomes unavailable.

---

# Q14. How would you migrate from a single Redis server to Redis Cluster?

### Answer

Typical approach

1. Build Cluster.
2. Configure replicas.
3. Migrate slots.
4. Test clients.
5. Redirect traffic.
6. Monitor cluster health.

Avoid downtime using gradual migration.

---

# Q15. Your application frequently executes `KEYS *`.

Why is this dangerous?

### Answer

`KEYS` scans the complete keyspace.

```
Millions of Keys

↓

Single Thread

↓

Application Latency
```

Use

```bash
SCAN
```

instead.

---

# Q16. Your cache hit ratio is excellent, but users still complain about slow APIs.

What else would you investigate?

### Answer

Redis is only one part of the request path.

Investigate

- Application CPU
- Network latency
- Serialization
- External APIs
- Database writes
- Lock contention
- Thread pool exhaustion

---

# Q17. How would you reduce Redis network latency?

### Answer

Techniques

- Connection pooling
- Pipelining
- Deploy Redis near applications
- Reduce payload size
- Compress large values when appropriate

---

# Q18. Your Redis server experiences frequent failovers.

What should you investigate?

### Answer

Possible causes

- Network instability
- Sentinel quorum issues
- Memory exhaustion
- CPU saturation
- Hardware failures
- Container restarts

Repeated failovers indicate an infrastructure problem rather than a Redis problem.

---

# Q19. Your Redis instance stores mostly temporary cache data.

Would you enable persistence?

### Answer

Not necessarily.

If Redis is purely a cache,

disabling persistence can

- Improve performance
- Reduce disk I/O
- Reduce restart time

Business requirements determine the correct choice.

---

# Q20. Your database becomes overloaded every midnight.

Redis is heavily used.

What might be happening?

### Answer

Possible causes

- All cache entries expire simultaneously.
- Batch jobs.
- Cache warming failure.

This is commonly called

```
Cache Avalanche
```

Solution

Randomize TTL values.

---

# Q21. Redis memory usage keeps growing every day.

How would you troubleshoot?

### Answer

Check

- Missing TTLs
- Memory leaks
- Large values
- Eviction policy
- Key growth
- Background jobs

Commands

```bash
INFO MEMORY

MEMORY STATS

SCAN
```

---

# Q22. How would you secure Redis in production?

### Answer

Best practices

- Enable authentication
- Disable dangerous commands
- Use TLS
- Restrict network access
- Enable ACLs
- Monitor access logs
- Rotate credentials

Never expose Redis directly to the public internet.

---

# Q23. A Redis backup becomes corrupted.

How should disaster recovery work?

### Answer

Good disaster recovery includes

- Multiple backups
- Off-site storage
- Backup validation
- Automated restore testing
- Replica backups

Never rely on a single backup.

---

# Q24. Which metrics should always be monitored?

### Answer

Monitor

- Memory usage
- CPU
- Latency
- Hit ratio
- Evictions
- Replication lag
- Connected clients
- Network traffic
- Persistence status
- Failover events

---

# Q25. Design a production-ready Redis architecture for a large e-commerce platform.

### Answer

```
                 Internet

                     │

                     ▼

             Load Balancer

                     │

                     ▼

           Application Servers

                     │

                     ▼

              Redis Cluster

      ┌──────────┼──────────┐

      ▼          ▼          ▼

   Primary     Primary     Primary

      │          │          │

      ▼          ▼          ▼

   Replica     Replica     Replica

                     │

                     ▼

             PostgreSQL Cluster
```

Redis stores

- Sessions
- Product cache
- Inventory cache
- Recommendation cache
- Rate limiting
- Shopping carts

PostgreSQL remains the source of truth.

---

# Rapid Fire Questions

| Question | Answer |
|----------|--------|
| CPU 100%? | Check Slow Log |
| Cache miss spike? | Investigate TTL |
| Hot Key? | Shard or Replicate |
| Server restart? | Cold Cache |
| Redis unavailable? | Database fallback |
| Millions of expired keys? | Cache Avalanche |
| Stale data? | Replication Lag or Cache Invalidation |
| Safe production scan? | SCAN |

---

# Senior Interview Tips

Interviewers rarely expect a single correct answer.

Instead, they evaluate your thinking process.

A strong answer should include

1. Identify the symptoms.
2. Gather evidence.
3. Form hypotheses.
4. Verify with metrics.
5. Implement the least risky solution.
6. Monitor after deployment.

Thinking like an SRE or Senior Backend Engineer is often more important than knowing every Redis command.

---

# Common Mistakes

## Restarting Redis Immediately

Always investigate the root cause before restarting production services.

---

## Assuming Redis Is Always the Problem

Many latency issues originate in the application, network, or database.

---

## Ignoring Monitoring

Without metrics, troubleshooting becomes guesswork.

---

## No Disaster Recovery Plan

Production systems should always have tested backup and recovery procedures.

---

# Best Practices

- Design applications to tolerate Redis failures.
- Monitor Redis continuously.
- Use High Availability and Replication.
- Test failover regularly.
- Implement cache warming after deployments.
- Keep disaster recovery procedures documented and tested.
- Treat Redis as one component of the overall system rather than the entire solution.

---

# Summary

Production Redis interviews focus on practical engineering rather than command memorization. Senior engineers are expected to diagnose incidents, reason about trade-offs, identify root causes, and design resilient systems. Understanding how Redis behaves under failure conditions is essential for building highly available, scalable backend applications.

---

# Key Takeaways

- Always approach production incidents methodically.
- Redis failures should not bring down the application.
- Cache hit ratio, latency, memory, and CPU are critical monitoring metrics.
- Hot Keys, Cache Avalanche, and Cold Cache are common production challenges.
- High Availability, monitoring, and disaster recovery are as important as performance.
- Senior interview answers emphasize reasoning, evidence, and production trade-offs rather than quick fixes.