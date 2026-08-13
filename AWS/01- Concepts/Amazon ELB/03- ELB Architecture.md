# 03- Elastic Beanstalk Architecture

---

# Introduction

Elastic Beanstalk is often perceived as a simple deployment service.

However, behind the scenes it orchestrates multiple AWS services to provide a complete application hosting platform.

A common mistake among beginners is believing:

```text
Elastic Beanstalk
=
Application Hosting Service
```

The reality is:

```text
Elastic Beanstalk
=
Infrastructure Orchestration Layer
```

Understanding the architecture is critical for:

* Troubleshooting
* Cost Optimization
* Security
* Scaling
* Production Operations

---

# High-Level Architecture

A typical Elastic Beanstalk deployment looks like:

```text
Users
  ↓
Route53
  ↓
Load Balancer
  ↓
Auto Scaling Group
  ↓
EC2 Instances
  ↓
Application
```

Managed by:

```text
Elastic Beanstalk
```

---

# Elastic Beanstalk Is Not A Compute Service

Elastic Beanstalk does not run applications directly.

Instead, it provisions AWS infrastructure.

Think of it as:

```text
Infrastructure Automation Engine
```

---

# Core AWS Services Used By Elastic Beanstalk

Behind every Elastic Beanstalk environment are multiple AWS services.

```text
Elastic Beanstalk
        ↓
CloudFormation
        ↓
EC2
Auto Scaling
ELB
CloudWatch
IAM
S3
SNS
```

---

# CloudFormation

CloudFormation is the foundation of Elastic Beanstalk.

Whenever an environment is created:

```text
Elastic Beanstalk
        ↓
CloudFormation Stack
        ↓
AWS Resources
```

are provisioned.

---

# Why CloudFormation Matters

Many troubleshooting scenarios require inspecting:

```text
CloudFormation Events
```

because failed environments often originate from failed stack operations.

---

# Amazon EC2

EC2 instances run the application.

Example:

```text
Python Application
       ↓
EC2 Instance
```

---

# EC2 Responsibilities

The EC2 instance hosts:

```text
Operating System
Runtime
Application Code
Logs
Processes
```

---

# Auto Scaling Group

Elastic Beanstalk automatically creates an Auto Scaling Group.

Purpose:

```text
Maintain Desired Capacity
```

---

# Auto Scaling Architecture

```text
Auto Scaling Group
          ↓
Launch EC2
          ↓
Terminate EC2
          ↓
Maintain Capacity
```

---

# Why Auto Scaling Matters

Without Auto Scaling:

```text
Instance Failure
        ↓
Downtime
```

With Auto Scaling:

```text
Instance Failure
        ↓
Replacement Instance
```

---

# Elastic Load Balancer

Most production environments use:

```text
Application Load Balancer (ALB)
```

---

# ALB Responsibilities

The load balancer:

* Distributes traffic
* Performs health checks
* Routes requests
* Terminates SSL

---

# Request Flow

```text
User
 ↓
ALB
 ↓
EC2
 ↓
Application
```

---

# Health Checks

The load balancer continuously verifies:

```text
Application Health
```

Example:

```text
/health
```

endpoint.

---

# Amazon S3

Elastic Beanstalk stores application versions in S3.

---

# Deployment Workflow

```text
Upload ZIP
      ↓
Store In S3
      ↓
Create Version
      ↓
Deploy
```

---

# Why S3 Matters

Application versions are:

```text
Persistent
```

and can be redeployed at any time.

---

# IAM

Elastic Beanstalk uses IAM roles extensively.

---

# Common Roles

```text
Service Role
Instance Profile
Application Role
```

---

# Service Role

Allows Elastic Beanstalk to manage AWS resources.

Example:

```text
Create Load Balancer
Create Auto Scaling Group
```

---

# Instance Profile

Attached to EC2 instances.

Provides access to:

```text
S3
CloudWatch
Secrets
```

---

# CloudWatch

CloudWatch provides:

```text
Metrics
Logs
Alarms
Events
```

---

# Common Metrics

```text
CPU Utilization
Memory Usage
Network Traffic
Request Count
Latency
```

---

# Monitoring Flow

```text
Application
      ↓
CloudWatch Metrics
      ↓
CloudWatch Alarm
      ↓
Scaling Action
```

---

# SNS Integration

Elastic Beanstalk can integrate with SNS.

Purpose:

```text
Notifications
```

Examples:

```text
Deployment Failed
Environment Degraded
Instance Failure
```

---

# Elastic Beanstalk Environment Architecture

A production environment usually contains:

```text
ALB
 ↓
Auto Scaling Group
 ↓
EC2 Instances
 ↓
Application
```

plus:

```text
CloudWatch
IAM
S3
```

---

# Single Instance Architecture

Development environments often use:

```text
Single EC2 Instance
```

Architecture:

```text
User
 ↓
EC2
 ↓
Application
```

---

# Advantages

* Cheap
* Simple
* Fast

---

# Disadvantages

* No High Availability
* No Fault Tolerance
* Not Production Ready

---

# Load Balanced Architecture

Production environments typically use:

```text
ALB
 ↓
Multiple EC2 Instances
```

---

# Architecture

```text
User
 ↓
ALB
 ↓
EC2-A

EC2-B

EC2-C
```

---

# Benefits

* High Availability
* Fault Tolerance
* Scaling

---

# Multi-AZ Architecture

Production systems should use:

```text
Multiple Availability Zones
```

---

# Example

```text
AZ-A
 ↓
EC2

AZ-B
 ↓
EC2
```

---

# Benefits

If one Availability Zone fails:

```text
Application Continues Running
```

---

# Environment Creation Workflow

When you create an environment:

```text
Create Environment
        ↓
CloudFormation
        ↓
Security Groups
        ↓
ALB
        ↓
Auto Scaling Group
        ↓
EC2
        ↓
Deploy Application
```

---

# Application Deployment Workflow

```text
Developer
     ↓
Upload ZIP
     ↓
S3
     ↓
Application Version
     ↓
Environment Update
     ↓
EC2 Deployment
```

---

# Request Lifecycle

Understanding request flow is important.

Example:

```text
User
 ↓
DNS
 ↓
Route53
 ↓
ALB
 ↓
EC2
 ↓
Nginx
 ↓
Gunicorn
 ↓
Django
```

---

# Response Lifecycle

```text
Django
 ↓
Gunicorn
 ↓
Nginx
 ↓
ALB
 ↓
User
```

---

# Deployment Architecture Example

Django Production:

```text
Users
 ↓
Route53
 ↓
ALB
 ↓
Elastic Beanstalk
 ↓
Django
 ↓
RDS PostgreSQL
```

---

# Enterprise Architecture Example

```text
Users
 ↓
CloudFront
 ↓
WAF
 ↓
ALB
 ↓
Elastic Beanstalk
 ↓
Aurora PostgreSQL
```

---

# Common Architectural Mistakes

## Single Instance Production

Risk:

```text
Single Point Of Failure
```

---

## No Load Balancer

Risk:

```text
Traffic Bottlenecks
```

---

## No Monitoring

Risk:

```text
Undetected Failures
```

---

## No Auto Scaling

Risk:

```text
Performance Issues
```

---

# Troubleshooting Architecture Problems

When troubleshooting:

Step 1

```text
CloudFormation
```

---

Step 2

```text
Elastic Beanstalk Events
```

---

Step 3

```text
Load Balancer Health
```

---

Step 4

```text
EC2 Logs
```

---

Step 5

```text
Application Logs
```

---

# Interview Questions

## What AWS Services Does Elastic Beanstalk Use?

* EC2
* Auto Scaling
* ELB
* CloudWatch
* IAM
* S3
* SNS
* CloudFormation

---

## Does Elastic Beanstalk Use CloudFormation?

Yes.

CloudFormation provisions resources behind the scenes.

---

## Where Are Application Versions Stored?

Amazon S3.

---

## Why Is Auto Scaling Important?

Maintains availability and handles traffic growth.

---

## Why Is ALB Used?

Traffic distribution and health checks.

---

# Senior Engineer Perspective

The biggest difference between a beginner and a senior engineer is understanding that:

```text
Elastic Beanstalk
Is Not The Architecture
```

The real architecture consists of:

```text
CloudFormation
ALB
Auto Scaling
EC2
CloudWatch
IAM
S3
```

Elastic Beanstalk simply orchestrates these services.

Senior engineers troubleshoot the underlying services rather than treating Elastic Beanstalk as a black box.

---

# Key Takeaways

* Elastic Beanstalk is an orchestration layer.
* CloudFormation provisions infrastructure.
* EC2 runs applications.
* Auto Scaling maintains capacity.
* ALB distributes traffic.
* S3 stores application versions.
* IAM controls permissions.
* CloudWatch provides monitoring.
* Understanding the architecture is essential for production operations.
