# Redis Sentinel

## Overview

Redis Sentinel is Redis's built-in **High Availability (HA)** solution. Its primary responsibility is to monitor Redis instances, detect failures, automatically perform failovers, and notify applications or administrators when the Redis topology changes.

In a production environment, simply having a Primary and one or more Replicas is not enough. If the Primary server crashes, applications lose the ability to write data unless another server is promoted automatically.

Redis Sentinel solves this problem by continuously monitoring the health of Redis servers and automatically promoting a healthy Replica to become the new Primary when necessary.

Unlike Redis Cluster, Sentinel **does not provide sharding**. Every Redis server still contains the complete dataset. Sentinel focuses entirely on **availability and failover**.

---

# Why Sentinel?

Consider a simple Redis deployment.

```
            Application
                 |
                 |
           +-----v------+
           |  Primary   |
           +------------+
```

Everything works until:

```
Primary

↓

Crash
```

Now:

- No write operations
- Application errors
- Service downtime

Someone must manually promote a Replica.

That process may take several minutes.

Sentinel automates it.

---

# What is Redis Sentinel?

Redis Sentinel is a monitoring service that runs independently of Redis servers.

```
             Sentinel

                │

      +---------+---------+

      │                   │

 Primary             Replica
```

Sentinel continuously checks whether Redis instances are healthy.

If something fails:

```
Detect Failure

↓

Promote Replica

↓

Update Clients
```

---

# Responsibilities of Sentinel

Redis Sentinel performs four major functions.

- Monitoring
- Notification
- Automatic Failover
- Service Discovery

Together these provide a highly available Redis deployment.

---

# Monitoring

Sentinel periodically checks:

- Primary availability
- Replica availability
- Network connectivity
- Replication status

Conceptually:

```
Sentinel

↓

PING

↓

Redis

↓

Healthy?
```

This monitoring occurs continuously.

---

# Notification

If Sentinel detects problems:

```
Primary

↓

Failure

↓

Alert
```

Administrators or monitoring systems can receive notifications.

---

# Automatic Failover

This is Sentinel's most important feature.

Suppose:

```
Primary

↓

Crash
```

Sentinel performs:

```
Detect Failure

↓

Select Best Replica

↓

Promote Replica

↓

Redirect Other Replicas

↓

Update Clients
```

The application continues with minimal downtime.

---

# Service Discovery

Applications no longer need to know which Redis server is Primary.

Instead:

```
Application

↓

Ask Sentinel

↓

Current Primary

↓

Connect
```

If failover occurs:

```
Sentinel

↓

Returns New Primary
```

Applications reconnect automatically.

---

# Sentinel Architecture

A production deployment typically looks like:

```
                    Sentinel 1

                        │

        +---------------+---------------+

        │                               │

 Sentinel 2                     Sentinel 3

        │                               │

        +---------------+---------------+

                        │

                  Redis Primary

                        │

          +-------------+-------------+

          │                           │

     Replica A                  Replica B
```

Multiple Sentinel instances avoid a single point of failure.

---

# Why Multiple Sentinels?

Suppose only one Sentinel exists.

```
Redis Healthy

↓

Sentinel Crashes
```

Now no automatic failover is possible.

Production deployments therefore use:

```
Sentinel A

Sentinel B

Sentinel C
```

Multiple Sentinels provide redundancy.

---

# Quorum

Sentinel does not perform failover based on a single opinion.

Instead, multiple Sentinels vote.

Example:

```
5 Sentinels

↓

Primary Failure

↓

4 Vote Yes

↓

Failover Starts
```

This voting mechanism is called a **Quorum**.

It prevents unnecessary failovers caused by temporary network issues.

---

# Subjective Down (SDOWN)

Suppose one Sentinel cannot contact the Primary.

```
Sentinel

↓

No Response

↓

Marks SDOWN
```

Only that Sentinel believes the server is unavailable.

No failover occurs yet.

---

# Objective Down (ODOWN)

Multiple Sentinels agree.

```
Sentinel A

↓

Primary Down
```

```
Sentinel B

↓

Primary Down
```

```
Sentinel C

↓

Primary Down
```

Consensus reached:

```
ODOWN

↓

Failover Begins
```

---

# Failover Process

The complete failover process:

```
Primary Fails

↓

Sentinels Detect Failure

↓

Voting

↓

Choose Replica

↓

Promote Replica

↓

Other Replicas Follow New Primary

↓

Clients Reconnect
```

This usually completes within seconds.

---

# Replica Selection

Sentinel selects the most suitable replica.

Factors include:

- Replication offset
- Replica priority
- Network connectivity
- Availability

The most up-to-date replica is usually promoted.

---

# Client Reconnection

Applications should never hardcode Redis IP addresses.

Instead:

```
Application

↓

Sentinel

↓

Current Primary

↓

Redis
```

After failover:

```
Application

↓

Sentinel

↓

New Primary
```

No configuration changes are required.

---

# Sentinel vs Replication

| Feature | Replication | Sentinel |
|----------|-------------|-----------|
| Data Copy | Yes | No |
| Monitoring | No | Yes |
| Automatic Failover | No | Yes |
| Service Discovery | No | Yes |
| High Availability | Partial | Yes |

Replication copies data.

Sentinel manages failover.

---

# Sentinel vs Redis Cluster

| Feature | Sentinel | Cluster |
|----------|-----------|----------|
| Sharding | No | Yes |
| High Availability | Yes | Yes |
| Automatic Failover | Yes | Yes |
| Multiple Primaries | No | Yes |
| Dataset | Complete Copy | Partitioned |

Sentinel provides HA.

Cluster provides HA plus horizontal scaling.

---

# Production Architecture

Typical deployment:

```
                    Application

                          │

                     Redis Sentinel

                          │

                    Redis Primary

                          │

        +-----------------+-----------------+

        │                                   │

   Redis Replica A                   Redis Replica B
```

Applications always communicate with Sentinel first.

---

# Common Production Use Cases

Redis Sentinel is widely used for:

- High availability
- Automatic failover
- Session storage
- Distributed caching
- E-commerce applications
- Banking systems
- Authentication services
- Gaming platforms
- Microservices
- API caching

---

# Common Mistakes

## Running Only One Sentinel

```
Sentinel

↓

Failure

↓

No Monitoring
```

Always deploy multiple Sentinels.

---

## Confusing Sentinel with Cluster

Sentinel:

```
High Availability
```

Cluster:

```
High Availability

+

Horizontal Scaling
```

They solve different problems.

---

## Hardcoding Redis IPs

Applications should query Sentinel instead.

Otherwise:

```
Failover

↓

Old IP

↓

Connection Failure
```

---

## Too Few Replicas

A single replica provides limited redundancy.

Production systems usually maintain at least two replicas.

---

# Best Practices

- Deploy at least three Sentinel instances.
- Place Sentinels on separate machines.
- Monitor failover events.
- Test failover regularly.
- Use replication together with Sentinel.
- Configure clients for automatic reconnection.
- Keep replicas synchronized.

---

# Production Considerations

When deploying Sentinel:

- Separate Sentinel and Redis processes where practical.
- Monitor replication lag.
- Verify quorum configuration.
- Test failover under realistic workloads.
- Ensure network reliability between Sentinels.
- Integrate Sentinel events with monitoring platforms such as Prometheus and Grafana.

---

# Sentinel in Microservice Architecture

```
                API Gateway
                     │
          +----------+----------+
          │                     │
    User Service         Order Service
          │                     │
          +----------+----------+
                     │
              Redis Sentinel
                     │
              Redis Primary
                     │
        +------------+------------+
        │                         │
   Redis Replica A         Redis Replica B
```

Every microservice queries Sentinel to discover the current Primary, ensuring seamless operation during failover.

---

# Summary

Redis Sentinel provides high availability by continuously monitoring Redis servers, detecting failures, automatically promoting replicas, and notifying clients about topology changes. It works alongside Redis Replication to eliminate manual failover and reduce downtime. Sentinel does not provide sharding or horizontal scaling; instead, it focuses entirely on ensuring that Redis remains available even when servers fail. For most production deployments that use a single Redis dataset, Sentinel is the recommended solution for high availability.

---

# Key Takeaways

- Redis Sentinel provides automatic failover and high availability.
- Sentinel continuously monitors Primary and Replica health.
- Multiple Sentinel instances use quorum-based voting before initiating failover.
- Applications should use Sentinel for service discovery instead of hardcoding Redis server addresses.
- Sentinel works with Replication but does not provide data sharding.
- Deploy at least three Sentinel instances for production reliability.
- Sentinel is the preferred high-availability solution for single-primary Redis deployments.