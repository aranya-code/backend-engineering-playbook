# Routing Policies

> Learn how Amazon Route 53 intelligently routes DNS traffic using Routing Policies. This chapter covers Simple, Weighted, Latency, Failover, Geolocation, Geoproximity, Multi-Value Answer routing, Traffic Flow, and production routing strategies.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Route 53 Routing Policies
- Configure different routing strategies
- Build highly available DNS architectures
- Distribute traffic across multiple resources
- Implement disaster recovery using DNS
- Design production traffic management solutions

---

# What are Routing Policies?

Routing Policies determine **how Route 53 responds to DNS queries**.

Instead of always returning the same IP address:

```text
Client

↓

Route 53

↓

One Response
```

Route 53 can intelligently decide which endpoint to return.

---

# Available Routing Policies

Amazon Route 53 supports several routing policies.

```text
Routing Policies

│

├── Simple

├── Weighted

├── Latency

├── Failover

├── Geolocation

├── Geoproximity

└── Multi-Value Answer
```

Each policy serves a different use case.

---

# Simple Routing

Simple Routing is the default policy.

```text
Client

↓

Route 53

↓

Single Record

↓

Application
```

Use when:

- Only one resource exists
- No load balancing required

---

# Simple Routing Example

```text
www.example.com

↓

ALB

↓

Application
```

---

# Weighted Routing

Weighted Routing distributes traffic according to assigned weights.

Example:

```text
Version A

Weight 80

↓

80% Traffic
```

```text
Version B

Weight 20

↓

20% Traffic
```

---

# Weighted Routing Use Cases

Ideal for:

- Canary deployments
- Blue/Green deployments
- Gradual rollouts
- A/B testing

---

# Weighted Routing Architecture

```text
Users

↓

Route 53

↓

80%

↓

ALB A

────────────

20%

↓

ALB B
```

---

# Latency-Based Routing

Latency Routing directs users to the Region with the lowest network latency.

Example:

```text
India

↓

Mumbai Region
```

```text
Germany

↓

Frankfurt Region
```

Users automatically receive the fastest response.

---

# Latency Routing Architecture

```text
Client

↓

Route 53

↓

Measure Latency

↓

Nearest AWS Region
```

---

# Latency Routing Use Cases

Useful for:

- Global applications
- Multi-region APIs
- SaaS platforms
- Gaming
- Video streaming

---

# Failover Routing

Failover Routing supports disaster recovery.

```text
Primary

↓

Healthy

↓

Serve Traffic
```

If unhealthy:

```text
Primary

↓

Failed

↓

Secondary
```

---

# Failover Architecture

```text
Users

↓

Route 53

↓

Health Check

│

├── Healthy

│       ↓

│   Primary

│

└── Failed

        ↓

    Secondary
```

---

# Active-Passive Design

Failover Routing is commonly used with Active-Passive architecture.

```text
Primary Region

↓

Failure

↓

Secondary Region
```

---

# Geolocation Routing

Routes traffic based on the user's geographic location.

Example:

```text
India

↓

Mumbai Website
```

```text
USA

↓

Virginia Website
```

---

# Geolocation Use Cases

Useful for:

- Country-specific websites
- Regulatory compliance
- Regional content
- Language-specific applications

---

# Geolocation Routing Architecture

```text
User Location

↓

Route 53

↓

Country Rules

↓

Regional Server
```

---

# Geoproximity Routing

Routes traffic based on geographic distance from AWS resources.

Unlike Geolocation:

```text
Location

↓

Distance

↓

Nearest Resource
```

Traffic bias can shift users toward specific Regions.

---

# Geoproximity Use Cases

Examples:

- Expanding into new Regions
- Regional traffic optimization
- Controlled traffic migration

---

# Multi-Value Answer Routing

Returns multiple healthy records.

Example:

```text
DNS Query

↓

Route 53

↓

Healthy Endpoints

↓

Client
```

If one endpoint becomes unhealthy, it is removed from responses.

---

# Multi-Value Routing Example

```text
Web Server A

Healthy

────────────

Web Server B

Healthy

────────────

Web Server C

Unhealthy
```

Route 53 returns:

- Server A
- Server B

Only healthy endpoints are returned.

---

# Routing Policy Comparison

| Policy | Best Use Case |
|----------|---------------|
| Simple | Single application |
| Weighted | Canary deployments |
| Latency | Global applications |
| Failover | Disaster recovery |
| Geolocation | Country-specific routing |
| Geoproximity | Regional optimization |
| Multi-Value | Basic load balancing |

---

# Traffic Flow

Traffic Flow is a visual policy editor.

It allows engineers to combine multiple routing policies.

Example:

```text
Latency

↓

Failover

↓

Weighted
```

Traffic Flow enables sophisticated routing strategies without manually creating many DNS records.

---

# Health Checks and Routing

Several routing policies integrate with Health Checks.

Example:

```text
Health Check

↓

Healthy

↓

Return Record
```

Otherwise:

```text
Health Check

↓

Failed

↓

Skip Record
```

---

# Multi-Region Architecture

```text
Users

↓

Route 53

↓

Latency Routing

↓

Mumbai

↓

Application

────────────

Frankfurt

↓

Application

────────────

Virginia

↓

Application
```

---

# Production Deployment Example

Canary deployment:

```text
Production

↓

Weighted Routing

↓

95%

↓

Version 1

────────────

5%

↓

Version 2
```

After validation:

```text
100%

↓

Version 2
```

---

# Common Errors

## Routing Policy Conflict

Occurs when incompatible routing configurations are used.

Verify:

- Record Name
- Record Type
- Routing Policy

---

## Health Check Failure

If all endpoints fail health checks:

- No healthy response may be returned.
- Verify endpoint availability.

---

## Incorrect Region

Latency Routing requires correct Region configuration.

Verify the AWS Region associated with each record.

---

# Production Best Practices

- Use Weighted Routing for gradual deployments.
- Use Failover Routing for disaster recovery.
- Deploy Latency Routing for global applications.
- Keep TTL values low during migrations.
- Test Health Checks regularly.
- Avoid unnecessary routing complexity.
- Document routing policies.
- Monitor DNS performance and availability.

---

# Real-World Workflow

```text
Deploy Application

↓

Create DNS Records

↓

Select Routing Policy

↓

Configure Health Checks

↓

Validate DNS

↓

Production
```

---

# Architecture Note

```text
Users
      │
      ▼
Amazon Route 53
      │
      ├── Simple
      ├── Weighted
      ├── Latency
      ├── Failover
      ├── Geolocation
      ├── Geoproximity
      └── Multi-Value
              │
              ▼
      AWS Resources
```

Route 53 Routing Policies allow DNS to become an intelligent traffic management layer rather than a simple name resolution service.

---

# Interview Note

### Question

**What is the difference between Weighted Routing and Latency-Based Routing in Route 53?**

### Answer

**Weighted Routing** distributes DNS traffic according to administrator-defined percentages, making it ideal for canary deployments, A/B testing, and gradual rollouts. **Latency-Based Routing** automatically directs users to the AWS Region that provides the lowest network latency, improving response times for globally distributed applications. Weighted Routing is controlled by configured weights, whereas Latency Routing is based on real-time network performance.

---

# Key Takeaways

- Routing Policies determine how Route 53 answers DNS queries.
- Simple Routing is suitable for single-resource deployments.
- Weighted Routing supports traffic splitting and canary deployments.
- Latency Routing improves performance for global users.
- Failover Routing enables disaster recovery.
- Geolocation and Geoproximity Routing support region-aware applications.
- Multi-Value Answer Routing provides basic DNS-level load balancing with health awareness.
```