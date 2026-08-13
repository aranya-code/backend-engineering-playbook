# 06- Elastic Beanstalk Configuration

---

# Introduction

Deploying an application is only part of the journey.

A production application requires configuration for:

* Infrastructure
* Scaling
* Security
* Networking
* Monitoring
* Application Behavior

Elastic Beanstalk provides a centralized configuration system that allows engineers to control how environments operate without modifying application code.

A common misconception is:

```text id="7s1p0a"
Configuration
=
Application Settings Only
```

In reality, Elastic Beanstalk configuration controls nearly every aspect of the environment.

---

# What Is Configuration?

Configuration is the collection of settings that define how an Elastic Beanstalk environment behaves.

Examples:

```text id="f9x61z"
Instance Type
Auto Scaling Rules
Environment Variables
Health Checks
Deployment Strategy
Load Balancer Settings
```

---

# Why Configuration Matters

Poor configuration can cause:

```text id="gh4zv4"
Downtime
Security Issues
Performance Problems
Unexpected Costs
```

Good configuration enables:

```text id="jw6i0u"
Scalability
Reliability
Security
Operational Efficiency
```

---

# Configuration Architecture

```text id="ly7n5o"
Elastic Beanstalk
        ↓
Configuration
        ↓
Environment
        ↓
AWS Resources
```

Configuration drives infrastructure behavior.

---

# Configuration Categories

Elastic Beanstalk groups settings into categories.

```text id="a0bz6r"
Capacity
Deployment
Networking
Security
Monitoring
Software
Instances
Database
```

---

# Capacity Configuration

Capacity determines how many instances can run.

Example:

```text id="5v0j91"
Minimum Instances = 2
Maximum Instances = 10
```

---

# Why Capacity Matters

Too few instances:

```text id="x8r6mw"
Performance Issues
```

Too many instances:

```text id="tvmv1s"
Higher Costs
```

Capacity planning is one of the most important production tasks.

---

# Instance Configuration

Elastic Beanstalk allows selecting instance types.

Examples:

```text id="u4b5r0"
t3.micro
t3.small
t3.medium
m6i.large
c6i.large
```

---

# Instance Selection Strategy

Small workloads:

```text id="7skk9g"
t3.micro
t3.small
```

Medium workloads:

```text id="c31k4u"
t3.medium
t3.large
```

High-performance workloads:

```text id="z2e8uw"
c6i.large
m6i.large
```

---

# Environment Variables

Environment variables allow applications to receive configuration without hardcoding values.

---

# Why Environment Variables Matter

Avoid:

```python
DATABASE_PASSWORD = "password123"
```

Use:

```text id="vvr7zv"
DATABASE_PASSWORD
```

instead.

---

# Common Environment Variables

```text id="cs4vow"
DATABASE_URL
SECRET_KEY
REDIS_URL
API_KEY
DEBUG
```

---

# Example

Django:

```python
import os

SECRET_KEY = os.environ["SECRET_KEY"]
```

FastAPI:

```python
import os

db_url = os.getenv("DATABASE_URL")
```

---

# Benefits

* Security
* Flexibility
* Environment Separation

---

# Environment-Specific Configuration

Development:

```text id="p0r4ik"
DEBUG=True
```

Production:

```text id="1s7p7e"
DEBUG=False
```

Same codebase.

Different behavior.

---

# Deployment Configuration

Deployment configuration controls how new versions are deployed.

Examples:

```text id="ksbx4k"
All At Once
Rolling
Rolling With Additional Batch
Immutable
```

---

# Why Deployment Configuration Matters

Deployment strategy directly affects:

```text id="1mq5n8"
Downtime
Risk
Cost
```

---

# Networking Configuration

Elastic Beanstalk integrates with VPC networking.

---

# Components

```text id="9hkg1u"
VPC
Subnets
Route Tables
Security Groups
```

---

# Typical Architecture

```text id="lggvy6"
Internet
 ↓
Public Subnet
 ↓
ALB
 ↓
Private Subnet
 ↓
EC2
```

---

# Public vs Private Subnets

Public:

```text id="1ofw3d"
Internet Accessible
```

Private:

```text id="3n3qdf"
Internal Resources
```

Production workloads should prefer private subnets.

---

# Security Group Configuration

Security groups act as virtual firewalls.

---

# Example

ALB:

```text id="pw0h8i"
Allow:
80
443
```

EC2:

```text id="sk5v1e"
Allow:
Traffic From ALB Only
```

---

# Security Best Practice

Avoid:

```text id="2xjdlh"
0.0.0.0/0
```

whenever possible.

Follow least privilege principles.

---

# Load Balancer Configuration

Elastic Beanstalk commonly uses:

```text id="i4w4pm"
Application Load Balancer
```

---

# Configurable Settings

```text id="s6h1u9"
Listeners
SSL
Health Checks
Timeouts
```

---

# HTTPS Configuration

Production applications should always use:

```text id="xw9mhz"
HTTPS
```

instead of:

```text id="0mhv4s"
HTTP
```

---

# SSL Configuration

Typical architecture:

```text id="4q9md8"
User
 ↓
HTTPS
 ↓
ALB
 ↓
EC2
```

SSL termination usually occurs at the load balancer.

---

# Health Check Configuration

Health checks determine application availability.

---

# Example

```text id="x5eqdn"
/health
```

or

```text id="w0qkmq"
/api/health
```

---

# Good Health Checks

Verify:

```text id="q4kz4g"
Application
Database
Dependencies
```

---

# Bad Health Checks

Avoid:

```text id="vzgkpy"
Always Returning 200
```

because they provide false confidence.

---

# Monitoring Configuration

Elastic Beanstalk integrates with CloudWatch.

---

# Metrics

```text id="z1t94j"
CPU
Memory
Network
Latency
Request Count
```

---

# Alarm Configuration

Example:

```text id="31ebzb"
CPU > 80%
```

Trigger:

```text id="jk3r7f"
Scale Out
```

---

# Log Configuration

Logs are critical for troubleshooting.

---

# Common Logs

```text id="z4kj3k"
Application Logs
Web Server Logs
Deployment Logs
System Logs
```

---

# Log Retention

Define retention policies.

Example:

```text id="0o5n2u"
7 Days
30 Days
90 Days
```

---

# Saved Configurations

Elastic Beanstalk supports exporting configuration.

---

# Why Save Configurations?

Benefits:

```text id="6db9qm"
Reusability
Consistency
Disaster Recovery
```

---

# Example

Production Configuration:

```text id="z0mc0v"
Instance Type
Scaling Rules
Networking
Security
```

can be saved and reused.

---

# Configuration Templates

Think of templates as:

```text id="eb0sz0"
Environment Blueprints
```

---

# Example Workflow

```text id="xj4r7k"
Create Template
       ↓
Save Configuration
       ↓
Create New Environment
       ↓
Apply Template
```

---

# Configuration Drift

One of the biggest operational challenges.

---

# Example

Development:

```text id="rrks3i"
t3.small
```

Production:

```text id="t7n8k2"
t3.large
```

Over time environments become inconsistent.

---

# Risks

```text id="s9h2qg"
Unexpected Behavior
Difficult Troubleshooting
Failed Deployments
```

---

# Preventing Configuration Drift

Use:

```text id="bvmxk5"
Saved Configurations
Version Control
Infrastructure As Code
```

---

# Common Configuration Mistakes

---

## Hardcoding Secrets

Bad:

```python
SECRET_KEY = "my-secret"
```

Good:

```python
SECRET_KEY = os.environ["SECRET_KEY"]
```

---

## Single Instance Production

Risk:

```text id="lmw7g6"
No High Availability
```

---

## No Auto Scaling

Risk:

```text id="h5ecvf"
Performance Bottlenecks
```

---

## Public Database Access

Risk:

```text id="j7nuvx"
Security Vulnerabilities
```

---

## Missing HTTPS

Risk:

```text id="bnxcnl"
Data Exposure
```

---

# Production Configuration Example

```text id="v6v1hf"
Environment:
Production

Instance Type:
t3.medium

Min Instances:
2

Max Instances:
6

Deployment:
Immutable

HTTPS:
Enabled

Monitoring:
CloudWatch

Logs:
30 Days Retention
```

---

# Interview Questions

## What Are Environment Variables?

Configuration values provided to applications at runtime.

---

## Why Use Environment Variables?

Security and flexibility.

---

## What Is Configuration Drift?

Differences between environments over time.

---

## Why Save Configurations?

To ensure consistency and reusability.

---

## What Is The Recommended Deployment Configuration For Production?

Typically:

```text id="dbylbx"
Immutable
Blue/Green
```

---

## Why Use Private Subnets?

Improved security.

---

# Senior Engineer Perspective

Many production outages are caused by:

```text id="p2wqqr"
Bad Configuration
```

rather than bad code.

Configuration management is therefore a critical engineering discipline.

A mature team treats configuration as:

```text id="0r8g3e"
Versioned
Reviewed
Documented
Audited
```

just like application code.

The goal is simple:

```text id="mxy7a0"
Predictable Infrastructure
Predictable Deployments
Predictable Operations
```

---

# Key Takeaways

* Configuration controls environment behavior.
* Environment variables should be used for secrets and runtime settings.
* Networking, security, scaling, monitoring, and deployment are all configurable.
* Saved configurations improve consistency.
* Configuration drift is a major operational risk.
* Production environments should use HTTPS, monitoring, auto scaling, and private networking.
* Configuration management is as important as application development.
