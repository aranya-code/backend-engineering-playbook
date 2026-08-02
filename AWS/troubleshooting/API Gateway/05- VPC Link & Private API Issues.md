# VPC Link & Private API Issues

## Overview

Amazon API Gateway supports private integrations through **VPC Link**, allowing APIs to communicate securely with resources inside an Amazon VPC without exposing them to the public internet.

Typical backend integrations include:

- Application Load Balancer (ALB)
- Network Load Balancer (NLB)
- Amazon ECS
- EC2
- Internal HTTP Services
- Private REST APIs

Although the architecture is straightforward, networking misconfigurations are one of the most common causes of production issues.

This guide explains the most common VPC Link and Private API problems, how to diagnose them, and how to resolve them.

---

# Architecture

```text
Client

↓

API Gateway

↓

VPC Link

↓

Load Balancer

↓

Backend Service
```

For Private APIs:

```text
Client

↓

VPC Endpoint

↓

Private API Gateway

↓

Lambda
```

---

# Common Problems

| Problem | Typical Error |
|----------|---------------|
| VPC Link Unavailable | 500 |
| Backend Unreachable | 502 |
| Backend Timeout | 504 |
| Access Denied | 403 |
| DNS Resolution Failure | Connection Failed |
| Target Unhealthy | 503 |

---

# VPC Link Status is FAILED

## Symptoms

API Gateway cannot invoke the backend.

---

## Diagnose

Navigate:

```text
API Gateway

↓

VPC Links

↓

Status
```

Possible values:

```text
AVAILABLE

FAILED

PENDING
```

---

## Common Causes

- Incorrect Subnets
- Incorrect Security Groups
- Deleted Load Balancer
- Networking Issues

---

## Solution

Verify:

- Subnets
- Security Groups
- Target Load Balancer
- VPC configuration

---

# 502 Bad Gateway

## Example

```http
HTTP/1.1 502 Bad Gateway
```

---

## Common Causes

- Backend returned invalid response
- ALB unavailable
- ECS service stopped
- Incorrect integration

---

## Diagnose

Check:

- ALB Target Group
- ECS Tasks
- Backend Logs

---

## Solution

Ensure:

- Healthy targets
- Correct backend port
- Proper HTTP responses

---

# 503 Service Unavailable

## Example

```http
HTTP/1.1 503 Service Unavailable
```

---

## Common Causes

- No healthy targets
- ECS service unavailable
- Target group empty

---

## Diagnose

Review:

```text
Target Group

↓

Healthy Targets
```

---

## Solution

Restore healthy backend instances.

---

# 504 Gateway Timeout

## Example

```http
HTTP/1.1 504 Gateway Timeout
```

---

## Common Causes

- Slow backend
- Database latency
- Long-running request

---

## Diagnose

Review:

- ALB Target Response Time
- ECS Logs
- Application Logs
- CloudWatch Metrics

---

## Solution

Optimize:

- Database queries
- Backend processing
- External API calls

---

# Security Group Blocks Traffic

## Symptoms

```text
Connection Timeout
```

---

## Common Causes

Security Group blocks:

```text
HTTPS

↓

TCP 443
```

or

```text
HTTP

↓

TCP 80
```

---

## Diagnose

Verify:

- Inbound Rules
- Outbound Rules

---

## Solution

Allow required ports between:

- VPC Link
- Load Balancer
- Backend

---

# Target Group Unhealthy

## Symptoms

```text
503 Service Unavailable
```

---

## Diagnose

Open:

```text
EC2

↓

Target Groups

↓

Health
```

---

## Common Causes

- Wrong health check path
- Wrong port
- Application crashed

---

## Solution

Verify:

```text
GET /health
```

returns:

```http
200 OK
```

---

# Wrong Backend Port

Example

Backend listens on:

```text
8000
```

Target Group:

```text
80
```

---

## Symptoms

Health check failures.

---

## Solution

Use the correct container port.

---

# DNS Resolution Failure

Symptoms

```text
Backend Host Not Found
```

---

## Common Causes

- Private DNS disabled
- Incorrect Route 53 configuration

---

## Diagnose

From EC2:

```bash
nslookup backend.internal
```

---

## Solution

Verify:

- Route 53 Private Hosted Zone
- DNS Resolution
- DNS Hostnames

---

# ECS Tasks Not Running

Symptoms

```text
503

↓

No Healthy Targets
```

---

## Diagnose

Open:

```text
Amazon ECS

↓

Service

↓

Running Tasks
```

---

## Solution

Restart failed tasks.

Review container logs.

---

# Load Balancer Listener Missing

Symptoms

```text
502

↓

Connection Failed
```

---

## Diagnose

Verify:

```text
Listener

↓

Port 80

or

443
```

---

## Solution

Configure the correct listener.

---

# Incorrect VPC Link Integration

Example

API Gateway integrates with:

```text
Wrong ALB
```

---

## Diagnose

Review:

```text
Integration

↓

VPC Link

↓

Load Balancer
```

---

## Solution

Update the integration to the correct backend.

---

# Private API Returns 403

## Example

```http
HTTP/1.1 403 Forbidden
```

---

## Common Causes

- Wrong VPC Endpoint
- Resource Policy
- Private DNS disabled

---

## Diagnose

Verify:

```text
Interface Endpoint

↓

Status

↓

Available
```

---

## Solution

Review:

- Resource Policy
- SourceVpce
- Endpoint ID

---

# Private DNS Disabled

Symptoms

Applications cannot resolve:

```text
execute-api.amazonaws.com
```

inside the VPC.

---

## Solution

Enable:

```text
Private DNS

↓

Enabled
```

when creating the Interface Endpoint.

---

# Incorrect Resource Policy

Example

Allowed:

```json
aws:SourceVpce
```

does not match the actual endpoint.

---

## Symptoms

```http
403 Forbidden
```

---

## Solution

Update:

```json
aws:SourceVpce
```

with the correct Interface Endpoint ID.

---

# Backend Health Check Fails

Common causes:

- Wrong path
- Wrong HTTP method
- Wrong status code

---

## Recommended

```text
GET /health
```

Return:

```http
200 OK
```

without requiring authentication.

---

# Connection Refused

Symptoms

```text
Connection Refused
```

---

## Common Causes

- Backend stopped
- Wrong port
- Firewall
- Security Group

---

## Solution

Verify:

- Service running
- Listening port
- Security Groups

---

# Troubleshooting Workflow

```text
API Gateway

↓

VPC Link

↓

Load Balancer

↓

Target Group

↓

Backend

↓

Database
```

Check each layer independently.

---

# Useful AWS Services

Use:

- CloudWatch Logs
- CloudWatch Metrics
- AWS X-Ray
- ECS Console
- EC2 Console
- Target Groups
- VPC Console

---

# Production Checklist

Verify:

- VPC Link available
- Security Groups
- Route Tables
- DNS
- Private DNS
- Target Group healthy
- Load Balancer listeners
- ECS tasks running
- Health endpoint
- Resource Policy
- Interface Endpoint
- CloudWatch Logs

---

# Common Interview Questions

### What is a VPC Link?

A VPC Link is an API Gateway resource that provides private connectivity to resources inside a VPC, such as Application Load Balancers and Network Load Balancers, without exposing backend services to the public internet.

---

### Why would API Gateway return 502 when using a VPC Link?

Common causes include unhealthy backend targets, incorrect load balancer configuration, invalid backend responses, or integration misconfiguration between API Gateway and the load balancer.

---

### Why do Private APIs require an Interface VPC Endpoint?

Private APIs are accessible only through AWS PrivateLink. An Interface VPC Endpoint provides secure private connectivity between resources in a VPC and API Gateway.

---

### Why is Private DNS important for Private APIs?

Private DNS allows the standard `execute-api` hostname to resolve to private IP addresses inside the VPC, ensuring requests are routed through the Interface VPC Endpoint instead of the public internet.

---

### How do you troubleshoot VPC Link connectivity issues?

Verify the VPC Link status, load balancer listeners, target group health, ECS or EC2 backend status, security groups, route tables, DNS configuration, and review CloudWatch logs and metrics.

---

# Key Takeaways

- VPC Link enables API Gateway to securely communicate with private backend services inside a VPC.
- Most VPC Link issues stem from networking misconfigurations, unhealthy targets, or incorrect load balancer settings.
- Private APIs depend on Interface VPC Endpoints, Resource Policies, and Private DNS for secure access.
- Health checks, security groups, DNS resolution, and backend availability should be verified systematically during troubleshooting.
- A layer-by-layer debugging approach significantly reduces the time required to identify connectivity problems in production environments.