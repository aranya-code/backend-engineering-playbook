# ECS Load Balancing

# Why Load Balancing Matters

Imagine:

```text
User Requests
      ↓
Single ECS Task
```

Problems:

- Single point of failure
- Limited scalability
- Poor availability

---

Now consider:

```text
Users
  ↓
Load Balancer
  ↓
Task A
Task B
Task C
```

Benefits:

- High Availability
- Scalability
- Fault Tolerance

---

# What is a Load Balancer?

A Load Balancer distributes traffic across multiple targets.

Targets can be:

- ECS Tasks
- EC2 Instances
- IP Addresses
- Lambda Functions

---

# ECS Load Balancer Architecture

```text
Internet
    ↓
ALB
    ↓
Target Group
    ↓
ECS Tasks
```

The load balancer becomes the entry point to the application.

---

# Types of AWS Load Balancers

AWS provides:

```text
Application Load Balancer (ALB)
Network Load Balancer (NLB)
Gateway Load Balancer (GWLB)
```

For ECS:

Most common:

```text
ALB
```

---

# Application Load Balancer (ALB)

ALB operates at:

```text
Layer 7
```

Application Layer.

Understands:

- HTTP
- HTTPS
- WebSockets

---

# ALB Features

Supports:

- Path Routing
- Host Routing
- SSL Termination
- WebSockets
- Health Checks

---

# Example Architecture

```text
Internet
    ↓
ALB
    ↓
User Service
Order Service
Payment Service
```

Single ALB.

Multiple services.

---

# Host-Based Routing

Route traffic based on hostname.

Example:

```text
api.company.com
```

→ API Service

---

```text
admin.company.com
```

→ Admin Service

---

# Architecture

```text
ALB
 ↓
api.company.com
 ↓
API Service

ALB
 ↓
admin.company.com
 ↓
Admin Service
```

---

# Path-Based Routing

Route traffic based on URL path.

Example:

```text
/api/*
```

→ API Service

---

```text
/admin/*
```

→ Admin Service

---

# Architecture

```text
ALB
 ↓
/api/*
 ↓
Service A

ALB
 ↓
/admin/*
 ↓
Service B
```

---

# SSL/TLS Termination

Without SSL Termination:

```text
Client
 ↓
HTTPS
 ↓
Task
```

Each task manages certificates.

---

With ALB:

```text
Client
 ↓
HTTPS
 ↓
ALB
 ↓
HTTP
 ↓
Task
```

Certificates managed centrally.

---

# Benefits

- Simpler operations
- Centralized certificates
- Reduced complexity

---

# ALB Health Checks

ALB continuously checks:

```text
/health
```

or

```text
/healthz
```

---

Healthy Response:

```text
200 OK
```

---

Unhealthy Response:

```text
500 Error
```

---

# Health Check Workflow

```text
Task
 ↓
Health Check Fails
 ↓
Marked Unhealthy
 ↓
Traffic Removed
```

---

# Target Groups

ALB does not send traffic directly to ECS.

Traffic flows:

```text
ALB
 ↓
Target Group
 ↓
Tasks
```

---

# Why Target Groups?

Provide:

- Health Checks
- Routing Logic
- Target Registration

---

# ECS Integration

When a task starts:

```text
Task
 ↓
Target Group Registration
```

---

When task stops:

```text
Task
 ↓
Target Group Deregistration
```

Automatic.

---

# Listener

A Listener checks incoming traffic.

Example:

```text
Port 80
Port 443
```

---

Architecture

```text
Internet
 ↓
Listener
 ↓
Rule
 ↓
Target Group
```

---

# Listener Rules

Rules decide:

```text
Where Traffic Goes
```

Examples:

- Hostname
- Path
- Headers

---

# Example

```text
/checkout/*
```

→ Checkout Service

---

```text
/orders/*
```

→ Order Service

---

# Sticky Sessions

Normally:

```text
Request 1 → Task A
Request 2 → Task B
Request 3 → Task C
```

---

Sticky Sessions:

```text
User
 ↓
Task A
```

All requests stay on same task.

---

# Use Cases

Useful for:

- Legacy applications
- Session-based systems

---

Avoid When

Using:

```text
Stateless APIs
```

Usually unnecessary.

---

# WebSocket Support

ALB supports:

```text
WebSockets
```

Useful for:

- Chat Applications
- Real-time Dashboards
- Notifications

---

# Network Load Balancer (NLB)

NLB operates at:

```text
Layer 4
```

Transport Layer.

Supports:

- TCP
- UDP

---

# NLB Architecture

```text
Internet
 ↓
NLB
 ↓
Tasks
```

---

# NLB Advantages

- Extremely High Performance
- Very Low Latency
- Static IP Addresses
- TCP Support

---

# NLB Use Cases

Examples:

- Gaming
- VoIP
- Financial Systems
- High Throughput Services

---

# ALB vs NLB

| Feature | ALB | NLB |
|----------|------|------|
| Layer | 7 | 4 |
| HTTP/HTTPS | Yes | Limited |
| TCP | No | Yes |
| Host Routing | Yes | No |
| Path Routing | Yes | No |
| SSL Termination | Yes | Limited |
| Static IP | No | Yes |

---

# Internal Load Balancer

Not accessible from internet.

Used for:

```text
Service-to-Service Communication
```

Example:

```text
Order Service
      ↓
Internal ALB
      ↓
Payment Service
```

---

# Internet-Facing Load Balancer

Publicly accessible.

Used for:

```text
Customer Traffic
```

---

# Production Architecture

```text
Internet
    ↓
CloudFront
    ↓
ALB
    ↓
ECS Services
    ↓
RDS
```

Features:

- SSL Termination
- Health Checks
- Auto Scaling
- High Availability

---

# Common Production Problems

## Failed Health Checks

Symptoms:

```text
No Healthy Targets
```

Causes:

- Wrong path
- Application failure
- Security groups

---

## Target Registration Failures

Causes:

- Incorrect ports
- Task startup failure

---

## SSL Issues

Causes:

- Expired certificates
- ACM configuration problems

---

## 502 Errors

Causes:

- Application crash
- Port mismatch
- Connectivity problems

---

# Troubleshooting Checklist

Check:

```text
Target Groups
Health Checks
Listeners
Certificates
Security Groups
Task Status
```

---

# Production Best Practices

## Always Use Health Checks

Detect failures automatically.

---

## Use HTTPS

Encrypt traffic.

---

## Use ACM Certificates

Simplify certificate management.

---

## Prefer Stateless Services

Avoid sticky sessions when possible.

---

## Monitor ALB Metrics

Use CloudWatch.

---

# Common Interview Questions

## Why Use ALB With ECS?

Provides:

- Traffic Distribution
- Health Checks
- High Availability

---

## Difference Between ALB and NLB?

ALB:

Layer 7

NLB:

Layer 4

---

## What is a Target Group?

Collection of backend targets.

---

## What Happens When Health Checks Fail?

Target removed from traffic rotation.

---

## Why Use SSL Termination?

Simplifies certificate management.

---

# Senior Engineer Perspective

Load balancers are not just traffic routers.

They provide:

- Availability
- Security
- Observability
- Deployment Safety

Most production ECS architectures place ALB at the center of the application stack.

A properly configured load balancer significantly improves reliability and user experience.

---

# Key Takeaways

- ALB is the most common ECS load balancer.
- NLB provides high-performance TCP/UDP routing.
- Target Groups manage ECS targets.
- Health Checks improve availability.
- SSL Termination simplifies certificate management.
- Listener Rules enable advanced routing.
- Load Balancers are critical for production ECS deployments.
