# ECS Service Discovery

# What is Service Discovery?

Service Discovery is the process of automatically locating services within a distributed system.

Example:

```text
Order Service
      ↓
Payment Service
```

How does Order Service find Payment Service?

This is the problem Service Discovery solves.

---

# Why Service Discovery Matters

In ECS:

```text
Task A
Task B
Task C
```

Tasks are constantly:

- Created
- Destroyed
- Replaced
- Scaled

IP addresses change frequently.

---

# The Hardcoded IP Problem

Bad Example:

```text
Payment Service
10.0.1.15
```

Application Code:

```python
http://10.0.1.15:8000
```

---

What happens when:

```text
Task Restart
```

New IP:

```text
10.0.1.25
```

Application breaks.

---

# Service Discovery Solution

Instead of:

```text
10.0.1.15
```

Use:

```text
payment.internal
```

DNS resolves dynamically.

---

# Service Discovery Architecture

```text
Order Service
      ↓
payment.internal
      ↓
DNS Resolution
      ↓
Payment Service
```

Applications never need to know actual IP addresses.

---

# AWS Cloud Map

Cloud Map is AWS's service discovery solution.

Provides:

- Service Registration
- Service Discovery
- DNS Resolution
- Health Awareness

---

# Cloud Map Architecture

```text
ECS Task
      ↓
Cloud Map Registration
      ↓
DNS Record Created
```

Services become discoverable automatically.

---

# ECS + Cloud Map Integration

When ECS starts a task:

```text
Task Created
      ↓
Register In Cloud Map
```

---

When ECS stops a task:

```text
Task Removed
      ↓
Deregister From Cloud Map
```

Automatic cleanup.

---

# DNS-Based Service Discovery

Example:

```text
payment.internal
```

DNS Query:

```text
payment.internal
       ↓
10.0.1.20
```

---

If task changes:

```text
payment.internal
       ↓
10.0.1.35
```

Application unaffected.

---

# Route 53 Integration

Cloud Map integrates with:

```text
Amazon Route 53
```

Provides:

- Internal DNS
- Service Resolution
- High Availability

---

# Service Namespace

Namespaces organize services.

Example:

```text
prod.internal
```

---

Services:

```text
payment.prod.internal

order.prod.internal

user.prod.internal
```

---

# Environment Separation

Development:

```text
payment.dev.internal
```

---

Production:

```text
payment.prod.internal
```

---

Benefits:

- Isolation
- Reduced mistakes
- Cleaner architecture

---

# Service Registration

Registration includes:

- Service Name
- IP Address
- Port
- Health Status

Example:

```text
payment
10.0.1.25
8000
Healthy
```

---

# Service Deregistration

When a task stops:

```text
Task Terminated
      ↓
Cloud Map Updated
```

Stale entries removed.

---

# Health-Aware Discovery

Cloud Map can integrate with health checks.

Healthy:

```text
DNS Returned
```

---

Unhealthy:

```text
Removed From Results
```

---

# Service-to-Service Communication

Example:

```text
Order Service
      ↓
payment.internal
      ↓
Payment Service
```

---

Benefits:

- No hardcoded IPs
- Dynamic scaling
- Automatic updates

---

# Internal Load Balancer Pattern

Alternative approach:

```text
Order Service
      ↓
Internal ALB
      ↓
Payment Service
```

---

Advantages

- Traffic balancing
- Health checks
- Routing controls

---

Disadvantages

- Additional cost
- Additional complexity

---

# Cloud Map vs Internal ALB

| Feature | Cloud Map | Internal ALB |
|----------|-----------|--------------|
| Cost | Lower | Higher |
| DNS Resolution | Yes | Yes |
| Load Balancing | Limited | Yes |
| Health Checks | Yes | Yes |
| Complexity | Lower | Higher |

---

# Microservice Architecture Example

```text
User Service
      ↓
Order Service
      ↓
Payment Service
      ↓
Notification Service
```

Each service discovered dynamically.

---

# Service Discovery Workflow

```text
Order Service
      ↓
DNS Query
      ↓
Cloud Map
      ↓
Payment Service IP
      ↓
Connection Established
```

---

# ECS Scaling Example

Initial:

```text
2 Payment Tasks
```

---

Scale Out:

```text
5 Payment Tasks
```

Cloud Map updates automatically.

Applications continue using:

```text
payment.internal
```

No changes required.

---

# Multi-AZ Discovery

Cloud Map works across:

```text
AZ-A
AZ-B
AZ-C
```

Provides resilient service discovery.

---

# Production Architecture

```text
ALB
 ↓
Order Service
 ↓
payment.prod.internal
 ↓
Payment Service
 ↓
RDS
```

Benefits:

- Dynamic discovery
- High availability
- Reduced operational overhead

---

# Common Problems

## Service Not Resolving

Possible causes:

- DNS issues
- Cloud Map misconfiguration
- Missing namespace

---

## Stale Records

Possible causes:

- Failed deregistration
- Health check issues

---

## Incorrect Environment

Example:

```text
payment.dev.internal
```

Used in production.

---

# Troubleshooting Checklist

Verify:

```text
Cloud Map Service
Namespace
Route 53 Records
Task Registration
Health Status
```

---

# Production Best Practices

## Use Meaningful Names

Good:

```text
payment.prod.internal
```

Bad:

```text
service1.internal
```

---

## Separate Environments

Use:

```text
dev
qa
prod
```

Namespaces.

---

## Monitor Health Status

Avoid stale endpoints.

---

## Avoid Hardcoded IPs

Always use service discovery.

---

# Common Interview Questions

## What is Service Discovery?

Process of locating services dynamically.

---

## Why Not Use IP Addresses?

IPs change frequently.

---

## What is Cloud Map?

AWS service discovery solution.

---

## How Does ECS Register Services?

Automatic Cloud Map integration.

---

## Cloud Map vs Internal ALB?

Cloud Map:

DNS discovery.

ALB:

Traffic distribution.

---

# Senior Engineer Perspective

As systems evolve into microservices, service discovery becomes mandatory.

Without service discovery:

- Scaling becomes difficult
- Maintenance increases
- Deployments become fragile

Senior engineers design systems using service names, not IP addresses.

Service discovery is a foundational component of resilient distributed systems.

---

# Key Takeaways

- Service Discovery eliminates hardcoded IP addresses.
- Cloud Map provides DNS-based service discovery.
- ECS integrates directly with Cloud Map.
- Route 53 powers DNS resolution.
- Services automatically register and deregister.
- Health-aware discovery improves reliability.
- Service discovery is essential for microservice architectures.
