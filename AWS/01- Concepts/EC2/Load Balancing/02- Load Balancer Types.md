# Types of AWS Load Balancers

AWS currently provides four major types of load balancers.

---

# 1. Classic Load Balancer (CLB)

## Released
- 2009

## Supported Protocols
- HTTP
- HTTPS
- TCP
- SSL

## Characteristics
- Legacy load balancer
- Basic Layer 4 and Layer 7 functionality
- Limited routing capabilities

## Use Cases
- Older AWS applications
- Legacy architectures

## Important Note
AWS recommends using ALB or NLB instead of CLB for modern applications.

---

# 2. Application Load Balancer (ALB)

## Released
- 2016

## Operates At
- Layer 7 (Application Layer)

## Supported Protocols
- HTTP
- HTTPS
- WebSocket

## Best For
- Microservices
- Container-based applications
- ECS and Kubernetes workloads

## Key Features

### Path-Based Routing
Example:
- `/users` → User Service
- `/orders` → Order Service

### Host-Based Routing
Example:
- `api.example.com`
- `admin.example.com`

### Routing Based on:
- Query strings
- Headers

### Dynamic Port Mapping
Very useful for ECS containers.

---

# ALB Good to Know

## Fixed DNS Name
ALB provides a fixed DNS hostname such as:

`my-alb.region.elb.amazonaws.com`

## Client IP Behavior

Backend servers do not directly see the original client IP.

The original IP is forwarded through:

- `X-Forwarded-For`
- `X-Forwarded-Port`
- `X-Forwarded-Proto`

## SSL Termination

ALB can terminate HTTPS traffic and forward plain HTTP internally.

This reduces backend server workload.

---

# Target Groups

ALB routes traffic to target groups.

## Supported Targets

- EC2 instances
- ECS tasks
- Lambda functions
- Private IP addresses

## Important Notes

- Health checks are configured at target group level.
- One ALB can route traffic to multiple target groups.

---

# Interview Notes

## Common Interview Questions

### Why is ALB preferred for microservices?

Because ALB supports:
- Path-based routing
- Host-based routing
- Dynamic port mapping
- Multiple target groups

### Which OSI layer does ALB operate on?
- Layer 7

---

# 3. Network Load Balancer (NLB)

## Released
- 2017

## Operates At
- Layer 4 (Transport Layer)

## Supported Protocols
- TCP
- TLS
- UDP

## Key Features

- Ultra-low latency
- Handles millions of requests per second
- High performance
- Static IP support
- Elastic IP support

## Use Cases

- Gaming applications
- Financial systems
- Real-time applications
- High-throughput workloads

## Important Notes

NLB forwards traffic very efficiently with minimal processing overhead.

---

# 4. Gateway Load Balancer (GWLB)

## Released
- 2020

## Operates At
- Layer 3 (Network Layer)

## Purpose

Used for:
- Security appliances
- Firewalls
- Packet inspection
- Intrusion detection systems

## Common Use Cases

- Centralized security architecture
- Traffic inspection pipelines

---

# Quick Comparison Table

| Load Balancer | Layer | Protocols | Best Use Case |
|---|---|---|---|
| CLB | Layer 4/7 | HTTP, HTTPS, TCP, SSL | Legacy apps |
| ALB | Layer 7 | HTTP, HTTPS, WebSocket | Web apps & microservices |
| NLB | Layer 4 | TCP, TLS, UDP | High performance traffic |
| GWLB | Layer 3 | IP | Security appliances |

