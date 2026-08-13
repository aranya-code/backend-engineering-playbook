# 08- Elastic Beanstalk Load Balancing

---

# Introduction

Modern applications must be able to handle:

* Increasing traffic
* Instance failures
* High availability requirements
* Zero-downtime deployments

If all user traffic is sent to a single server:

```text id="s3p4j8"
Users
  ↓
Server
```

the application becomes vulnerable to:

```text id="q7f8k1"
Server Failure
Traffic Overload
Maintenance Downtime
```

Load balancing solves these problems.

Elastic Beanstalk integrates directly with AWS Elastic Load Balancing (ELB) to distribute traffic across multiple instances.

---

# What Is Load Balancing?

Load Balancing is the process of distributing incoming traffic across multiple servers.

Instead of:

```text id="m5d7p2"
Users
  ↓
Server A
```

traffic is distributed:

```text id="v9t4q3"
Users
  ↓
Load Balancer
  ↓
Server A
Server B
Server C
```

This improves:

```text id="z1n8w5"
Availability
Scalability
Reliability
Performance
```

---

# Why Load Balancing Matters

Imagine a website receiving:

```text id="a6c2k9"
10,000 Requests Per Minute
```

A single server may struggle.

With a load balancer:

```text id="7b4f2m"
Server A -> 3,300 Requests
Server B -> 3,300 Requests
Server C -> 3,400 Requests
```

Workload is shared.

---

# Load Balancing Architecture

Typical Elastic Beanstalk architecture:

```text id="r4v9k8"
Users
  ↓
Application Load Balancer
  ↓
Auto Scaling Group
  ↓
EC2 Instances
```

---

# Elastic Load Balancing (ELB)

AWS provides:

```text id="n7j2p4"
Application Load Balancer (ALB)
Network Load Balancer (NLB)
Gateway Load Balancer (GWLB)
Classic Load Balancer (CLB)
```

Elastic Beanstalk primarily uses:

```text id="x3c5v7"
Application Load Balancer
```

---

# Why ALB Is Preferred

ALB provides:

```text id="d8m1q6"
Layer 7 Routing
HTTPS Support
Health Checks
Path-Based Routing
Host-Based Routing
```

These features make it ideal for web applications.

---

# Application Load Balancer Architecture

```text id="w5n3e8"
Users
  ↓
ALB
  ↓
Target Group
  ↓
EC2 Instances
```

---

# Target Groups

A Target Group contains backend servers.

Example:

```text id="y2t8q5"
Target Group
    ↓
EC2-A
EC2-B
EC2-C
```

ALB forwards traffic only to healthy targets.

---

# Request Lifecycle

When a user sends a request:

```text id="j7v6m4"
User
 ↓
DNS Resolution
 ↓
ALB
 ↓
Target Group
 ↓
EC2 Instance
 ↓
Application
```

Response follows the reverse path.

---

# Load Balancer Listeners

Listeners define how traffic enters the ALB.

Examples:

```text id="u1r9w3"
HTTP  : Port 80
HTTPS : Port 443
```

---

# Listener Architecture

```text id="f4p7n8"
Port 80
  ↓
Redirect
  ↓
Port 443
```

Production applications should always redirect HTTP to HTTPS.

---

# Listener Rules

ALB supports intelligent routing.

Example:

```text id="l8q3v5"
/api/*
```

Route to:

```text id="k1m7c2"
Backend Service
```

---

Another example:

```text id="g9r2d6"
/admin/*
```

Route to:

```text id="h5t8n4"
Admin Service
```

---

# Host-Based Routing

Example:

```text id="s4w1k7"
api.company.com
```

Route to:

```text id="m2c9v8"
API Service
```

---

```text id="t7n5e3"
admin.company.com
```

Route to:

```text id="b8q4r1"
Admin Service
```

---

# Health Checks

One of the most important ALB features.

Health checks determine whether instances can receive traffic.

---

# Health Check Flow

```text id="d6p8w2"
ALB
 ↓
Health Check
 ↓
EC2
 ↓
Healthy?
```

---

# Healthy Instance

```text id="z7m4k9"
HTTP 200
```

Result:

```text id="x1v6n8"
Receives Traffic
```

---

# Unhealthy Instance

```text id="q3r7t5"
HTTP 500
Timeout
Connection Failure
```

Result:

```text id="j8w2m6"
Removed From Traffic Pool
```

---

# Health Check Example

Common endpoint:

```text id="c4n9e7"
/health
```

or

```text id="r5k8t1"
/api/health
```

---

# Good Health Checks

Should verify:

```text id="u7d4p3"
Application
Database
Dependencies
```

---

# Bad Health Checks

Example:

```text id="v9c1k4"
Always Return 200
```

This can hide application failures.

---

# SSL/TLS Support

Production systems should always use HTTPS.

---

# HTTPS Architecture

```text id="y8m6q2"
User
 ↓
HTTPS
 ↓
ALB
 ↓
HTTP
 ↓
Application
```

---

# SSL Termination

Common practice:

```text id="t4k9w7"
SSL Ends At ALB
```

Benefits:

```text id="n3v7r8"
Reduced Server Load
Simplified Certificates
Centralized Security
```

---

# AWS Certificate Manager (ACM)

Certificates are typically managed using:

```text id="m8q4j6"
AWS Certificate Manager
```

Benefits:

```text id="w6k2v9"
Free Certificates
Automatic Renewal
Easy Integration
```

---

# Load Balancing Algorithms

ALB distributes traffic automatically.

Typical behavior:

```text id="h1n8c4"
Round Robin
```

Traffic is distributed evenly across targets.

---

# Sticky Sessions

Sometimes applications require:

```text id="q7m3v2"
Session Persistence
```

---

# Architecture

Without Sticky Sessions:

```text id="a9t4w7"
Request 1 → Server A
Request 2 → Server B
```

---

With Sticky Sessions:

```text id="r6c8n1"
Request 1 → Server A
Request 2 → Server A
```

---

# When To Use Sticky Sessions

Examples:

```text id="k2m9p6"
Legacy Applications
Session-Based Applications
```

Modern applications should prefer:

```text id="b5v7q3"
Stateless Design
```

---

# Cross-Zone Load Balancing

ALB distributes traffic across Availability Zones.

---

# Example

```text id="d1r8w4"
AZ-A
 ↓
EC2-A

AZ-B
 ↓
EC2-B
```

Traffic is balanced automatically.

---

# Benefits

```text id="v4m7c9"
High Availability
Fault Tolerance
Better Resource Utilization
```

---

# Load Balancer And Auto Scaling

ALB works closely with Auto Scaling.

---

# Workflow

```text id="t8n5q7"
Auto Scaling
      ↓
Launch Instance
      ↓
Register With ALB
      ↓
Receive Traffic
```

---

# Scale In Workflow

```text id="p7k3m8"
Instance Removal
      ↓
Deregister From ALB
      ↓
Stop Traffic
```

---

# Load Balancer During Deployments

Deployments rely heavily on health checks.

---

# Workflow

```text id="g4w8r2"
Deploy New Version
        ↓
Health Check
        ↓
Healthy?
        ↓
Receive Traffic
```

---

# Benefits

```text id="u5m9n3"
Reduced Deployment Risk
Improved Reliability
```

---

# Single Instance Environment

Development environments often use:

```text id="j9v2k5"
No Load Balancer
```

Architecture:

```text id="x4t7m1"
User
 ↓
EC2
 ↓
Application
```

---

# Limitations

```text id="w8q5r4"
No High Availability
No Fault Tolerance
No Traffic Distribution
```

---

# Load Balanced Environment

Production environments should use:

```text id="y6m3k9"
ALB
```

Architecture:

```text id="z2t8v4"
User
 ↓
ALB
 ↓
EC2-A
EC2-B
EC2-C
```

---

# Common Load Balancer Issues

## Health Check Failure

Symptoms:

```text id="p4v9m2"
503 Errors
Instance Out Of Service
```

---

## SSL Errors

Symptoms:

```text id="q5k8n6"
Certificate Invalid
HTTPS Failure
```

---

## Security Group Problems

Symptoms:

```text id="t9v3m1"
ALB Cannot Reach EC2
```

---

## Incorrect Listener Rules

Symptoms:

```text id="u8m6r2"
Requests Routed Incorrectly
```

---

# Troubleshooting Load Balancer Problems

Step 1:

```text id="s7n2v5"
Check Target Group Health
```

---

Step 2:

```text id="d5m8q1"
Check Security Groups
```

---

Step 3:

```text id="k1v9r4"
Check Health Check Endpoint
```

---

Step 4:

```text id="w3q8m6"
Review ALB Access Logs
```

---

Step 5:

```text id="r4n7t2"
Review Application Logs
```

---

# Interview Questions

## What Load Balancer Does Elastic Beanstalk Typically Use?

```text id="b8q5m2"
Application Load Balancer
```

---

## What Is A Target Group?

A collection of backend resources that receive traffic from a load balancer.

---

## What Is SSL Termination?

The process of decrypting HTTPS traffic at the load balancer.

---

## Why Are Health Checks Important?

They ensure traffic is routed only to healthy instances.

---

## What Is Cross-Zone Load Balancing?

Traffic distribution across multiple Availability Zones.

---

## Should Production Use HTTPS?

```text id="v7m2k8"
Always
```

---

# Senior Engineer Perspective

Many engineers think of a load balancer as:

```text id="t5n4r7"
Traffic Distributor
```

In reality, it is also:

```text id="j8q6m3"
Security Layer
Availability Layer
Deployment Layer
Monitoring Layer
```

The ALB plays a critical role in:

* Scaling
* Availability
* Deployments
* Security

Understanding load balancing is therefore essential for operating production-grade Elastic Beanstalk environments.

---

# Key Takeaways

* Elastic Beanstalk primarily uses Application Load Balancers.
* Load balancers distribute traffic across multiple instances.
* Target Groups contain backend resources.
* Health checks determine instance availability.
* HTTPS should be enabled in production.
* SSL is commonly terminated at the ALB.
* Cross-zone load balancing improves resilience.
* Load balancers integrate closely with Auto Scaling.
* Proper ALB configuration is critical for production reliability.
