# 02- Elastic Beanstalk Core Components

---

# Introduction

Before you can effectively use Elastic Beanstalk, you must understand its core building blocks.

Most deployment problems, scaling issues, and configuration mistakes occur because engineers do not understand how Elastic Beanstalk organizes resources internally.

Every Elastic Beanstalk deployment revolves around a few key components:

```text
Application
Application Version
Environment
Environment Tier
Platform
Configuration
```

Understanding how these components relate to each other is the foundation of mastering Elastic Beanstalk.

---

# Component Relationship Overview

The easiest way to understand Elastic Beanstalk is through the hierarchy below.

```text
Application
    ↓
Application Version
    ↓
Environment
    ↓
Platform
    ↓
AWS Resources
```

A developer creates an application.

An application contains one or more versions.

A version is deployed to an environment.

The environment runs on a specific platform.

The platform provisions AWS resources.

---

# Application

An Application is the highest-level logical container in Elastic Beanstalk.

Think of it as a project.

Example:

```text
Inventory Management System
```

or

```text
E-Commerce Platform
```

An application does not run code directly.

Instead, it acts as a container for:

* Application Versions
* Environments
* Configurations

---

# Why Applications Exist

Applications help organize deployments.

Without applications:

```text
Version 1
Version 2
Version 3
Environment A
Environment B
```

would become difficult to manage.

Applications provide structure.

---

# Example

```text
Application:
Inventory System
```

Inside:

```text
Version 1.0
Version 1.1
Version 2.0
```

and

```text
Development Environment
Testing Environment
Production Environment
```

---

# Real World Example

A company might have:

```text
Customer Portal
Employee Portal
Admin Portal
```

Each would be a separate Elastic Beanstalk application.

---

# Application Version

An Application Version is a deployable version of your application.

Think of it as a snapshot of code.

---

# Why Versions Matter

Every deployment creates a new version.

Example:

```text
v1.0
v1.1
v1.2
v2.0
```

This allows:

* Rollbacks
* Auditing
* Controlled deployments

---

# Deployment Workflow

```text
Source Code
      ↓
ZIP Package
      ↓
Application Version
      ↓
Environment Deployment
```

---

# Version Storage

Application versions are stored in:

```text
Amazon S3
```

This is important because:

Elastic Beanstalk does not store code directly.

It stores references to version packages in S3.

---

# Version Lifecycle

```text
Create
 ↓
Upload
 ↓
Deploy
 ↓
Retain
 ↓
Delete
```

---

# Versioning Best Practices

Avoid:

```text
Version1
Version2
Version3
```

Use:

```text
v1.0.0
v1.1.0
v1.2.0
v2.0.0
```

or

```text
Build-2026-01-15
```

---

# Environment

An Environment is where your application actually runs.

Applications are logical.

Environments are operational.

---

# Simple Analogy

Application:

```text
Blueprint
```

Environment:

```text
Building
```

---

# Environment Examples

Most organizations create:

```text
Development
Testing
Staging
Production
```

environments.

---

# Environment Architecture

```text
Application
      ↓
Environment
      ↓
EC2
ALB
ASG
CloudWatch
```

---

# Multiple Environments

One application can have multiple environments.

Example:

```text
Inventory System
        ↓
Development
Testing
Production
```

All environments can run different versions.

---

# Why Multiple Environments Matter

Development:

```text
Experimentation
```

Testing:

```text
Validation
```

Production:

```text
Real Users
```

Separating environments reduces risk.

---

# Environment Lifecycle

Every environment follows:

```text
Create
 ↓
Deploy
 ↓
Operate
 ↓
Scale
 ↓
Update
 ↓
Terminate
```

Understanding this lifecycle is critical.

---

# Environment Tier

Elastic Beanstalk supports two environment types.

```text
Web Tier
Worker Tier
```

---

# Web Tier

Used for:

```text
Web Applications
REST APIs
Websites
```

Examples:

```text
Django
Flask
FastAPI
Spring Boot
Node.js
```

---

# Web Tier Architecture

```text
User
 ↓
Load Balancer
 ↓
EC2
 ↓
Application
```

This is the most common environment type.

---

# Worker Tier

Used for:

```text
Background Jobs
Email Processing
ETL
Scheduled Tasks
```

---

# Worker Tier Architecture

```text
SQS Queue
      ↓
Worker Environment
      ↓
Processing
```

Unlike Web Tier, Worker Tier processes messages instead of HTTP requests.

---

# When To Use Worker Tier

Examples:

```text
Send Emails
Generate Reports
Image Processing
Video Processing
PDF Generation
```

These tasks should not block user requests.

---

# Platform

A Platform defines the runtime environment.

It determines:

```text
Operating System
Runtime
Web Server
Deployment Configuration
```

---

# Platform Examples

Elastic Beanstalk supports:

```text
Python
Node.js
Java
Go
Ruby
PHP
.NET
Docker
```

---

# Python Platform Example

```text
Amazon Linux
      ↓
Python Runtime
      ↓
Web Server
      ↓
Application
```

---

# Docker Platform Example

```text
Amazon Linux
      ↓
Docker Engine
      ↓
Containers
```

---

# Why Platforms Matter

Platforms define:

```text
Application Runtime
```

Changing platforms can affect:

* Compatibility
* Deployment
* Performance

---

# Platform Versions

Example:

```text
Python 3.10
Python 3.11
Python 3.12
```

or

```text
Node 18
Node 20
```

Platform updates should be tested before production deployment.

---

# Configuration

Configuration controls environment behavior.

Examples:

```text
Instance Type
Scaling Rules
Environment Variables
Health Checks
Load Balancer Settings
```

---

# Configuration Categories

Common configuration areas:

```text
Capacity
Networking
Security
Scaling
Monitoring
Deployment
```

---

# Example Configuration

```text
Instance Type:
t3.medium

Minimum Instances:
2

Maximum Instances:
6
```

---

# Environment Variables

Applications often require:

```text
Database URL
API Keys
Secrets
```

These are stored as environment variables.

Example:

```text
DATABASE_URL
SECRET_KEY
REDIS_URL
```

---

# Configuration Templates

Configuration Templates store reusable environment settings.

Think of them as:

```text
Environment Blueprints
```

---

# Why Templates Matter

Without templates:

Every environment requires manual configuration.

With templates:

```text
Create Once
Reuse Many Times
```

---

# Saved Configurations

Elastic Beanstalk allows saving environment configurations.

Example:

```text
Production Configuration
```

can be exported and reused.

---

# Benefits

* Consistency
* Faster Environment Creation
* Reduced Human Error

---

# Putting Everything Together

A complete Elastic Beanstalk deployment looks like:

```text
Application
      ↓
Application Version
      ↓
Environment
      ↓
Platform
      ↓
AWS Resources
```

This relationship is the foundation of Elastic Beanstalk.

---

# Common Beginner Mistakes

## Confusing Applications and Environments

Application:

```text
Logical Container
```

Environment:

```text
Running Deployment
```

---

## Deploying Directly To Production

Always use:

```text
Development
Testing
Production
```

---

## Poor Versioning

Avoid:

```text
latest
latest-final
latest-final-final
```

Use proper semantic versioning.

---

## Ignoring Saved Configurations

Configurations should be reusable and documented.

---

# Interview Questions

## What is an Application?

A logical container for environments and application versions.

---

## What is an Application Version?

A deployable snapshot of code.

---

## What is an Environment?

A running deployment of an application version.

---

## What are the two Environment Tiers?

Web Tier and Worker Tier.

---

## What is a Platform?

A runtime environment used by Elastic Beanstalk.

---

## What is the difference between Application and Environment?

Application is logical.

Environment is operational.

---

## Where are Application Versions stored?

Amazon S3.

---

# Senior Engineer Perspective

Most Elastic Beanstalk troubleshooting comes down to understanding component relationships.

A senior engineer should immediately understand:

```text
Application
     ↓
Version
     ↓
Environment
     ↓
Platform
     ↓
Infrastructure
```

because every deployment, scaling event, rollback, migration, and troubleshooting workflow ultimately traces back to these components.

Teams that understand these relationships deploy faster, troubleshoot faster, and operate Elastic Beanstalk more effectively.

---

# Key Takeaways

* Applications are logical containers.
* Application Versions are deployable snapshots.
* Environments run applications.
* Environment Tiers define workload types.
* Platforms define runtimes.
* Configurations control behavior.
* Application Versions are stored in S3.
* Understanding component relationships is essential for mastering Elastic Beanstalk.
* Most production operations revolve around these core building blocks.
