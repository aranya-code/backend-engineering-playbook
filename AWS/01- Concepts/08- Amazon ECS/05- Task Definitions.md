# ECS Task Definitions

# What is a Task Definition?

A Task Definition is a blueprint that tells ECS how to run your containers.

Think of it as:

```text
Dockerfile
    ↓
How To Build

Task Definition
    ↓
How To Run
```

Without a Task Definition, ECS does not know:

- Which image to run
- How much CPU to allocate
- How much memory to allocate
- Which ports to expose
- Which secrets to inject

---

# ECS Task Definition Architecture

```text
Task Definition
      ↓
Container Definitions
      ↓
Task
      ↓
Running Containers
```

The Task Definition acts as a deployment template.

---

# Core Components

A Task Definition usually contains:

- Family Name
- Container Definitions
- CPU
- Memory
- IAM Roles
- Networking
- Volumes
- Environment Variables
- Secrets
- Logging Configuration

---

# Family Name

A family groups multiple revisions together.

Example:

```text
user-service
```

Revisions:

```text
user-service:1
user-service:2
user-service:3
```

Benefits:

- Version control
- Rollback support
- Deployment tracking

---

# Container Definitions

A Task Definition can contain one or more containers.

Example:

```text
Task
 ├── Application Container
 └── Sidecar Container
```

---

# Single Container Example

```text
FastAPI Container
```

Simple deployment.

Most common pattern.

---

# Multi-Container Example

```text
Application
      +
Log Collector
      +
Monitoring Agent
```

Examples:

- Fluent Bit
- Datadog Agent
- OpenTelemetry Collector

---

# Docker Image

Every container requires an image.

Example:

```text
123456789.dkr.ecr.amazonaws.com/user-service:v1
```

Best Practice:

Use versioned tags.

Good:

```text
v1.0.0
v1.2.3
```

Avoid:

```text
latest
```

---

# CPU Configuration

CPU controls processing power available to tasks.

Example:

```text
256 CPU Units
```

Equivalent:

```text
0.25 vCPU
```

---

Common Values

| CPU Units | vCPU |
|------------|------|
| 256 | 0.25 |
| 512 | 0.5 |
| 1024 | 1 |
| 2048 | 2 |
| 4096 | 4 |

---

# Memory Configuration

Memory defines available RAM.

Example:

```text
512 MB
1024 MB
2048 MB
```

If memory is exhausted:

```text
OOM Kill
```

Task stops.

---

# CPU vs Memory

CPU Bottleneck:

```text
High CPU Usage
Low Memory Usage
```

Memory Bottleneck:

```text
Low CPU Usage
High Memory Usage
```

Monitor both metrics.

---

# Environment Variables

Used to pass configuration.

Example:

```text
ENV=production
DEBUG=False
```

Benefits:

- Environment separation
- Dynamic configuration

---

# Environment Variable Example

```json
{
  "name": "ENV",
  "value": "production"
}
```

---

# Secrets Management

Never store secrets directly in Task Definitions.

Bad:

```text
DATABASE_PASSWORD=mysecret
```

---

# Use AWS Secrets Manager

Store:

- Database passwords
- API keys
- Tokens

Retrieve securely at runtime.

---

# Parameter Store

Alternative option.

Good for:

- Configuration values
- Non-sensitive settings

Examples:

```text
/api/base-url
/application/environment
```

---

# Port Mappings

Maps container ports.

Example:

```text
Container Port: 8000
```

FastAPI Example:

```text
uvicorn app:app --port 8000
```

---

# Networking Example

```text
ALB
 ↓
8000
 ↓
Container
```

Traffic reaches application.

---

# Logging Configuration

Applications should write logs to:

```text
stdout
stderr
```

ECS forwards logs.

---

# CloudWatch Logs

Architecture:

```text
Container
     ↓
CloudWatch Logs
```

Benefits:

- Centralized logging
- Monitoring
- Alerting

---

# Log Stream Example

```text
/ecs/user-service
```

Each task receives:

```text
Unique Log Stream
```

---

# Volumes

Volumes provide persistent storage.

Without volumes:

```text
Task Stops
     ↓
Data Lost
```

---

# EFS Integration

Example:

```text
Container A
      ↓
      EFS
      ↑
Container B
```

Shared storage.

Useful for:

- User uploads
- Reports
- Shared assets

---

# IAM Roles

Task Definitions can define:

## Execution Role

Used by ECS.

Examples:

- Pull image from ECR
- Send logs to CloudWatch

---

## Task Role

Used by application.

Examples:

```python
boto3.client("s3")
```

Permissions:

```text
s3:GetObject
s3:PutObject
```

---

# Task Definition Revisions

Every update creates a new revision.

Example:

```text
v1
v2
v3
```

Benefits:

- Rollback capability
- Deployment history

---

# Deployment Example

Version 1:

```text
user-service:1
```

Deploy.

Version 2:

```text
user-service:2
```

Deploy.

Rollback:

```text
user-service:1
```

---

# Production Best Practices

## Use Versioned Images

Good:

```text
v1.0.0
```

Bad:

```text
latest
```

---

## Store Secrets Securely

Use:

- Secrets Manager
- Parameter Store

---

## Define Resource Limits

Always specify:

- CPU
- Memory

Avoid unlimited resources.

---

## Centralize Logs

Use CloudWatch Logs.

---

## Use IAM Roles

Avoid static AWS credentials.

---

# Common Mistakes

## Using latest Tag

Problem:

Unpredictable deployments.

---

## Hardcoding Secrets

Problem:

Security vulnerability.

---

## No Memory Limits

Problem:

Container crashes.

---

## No Logging Configuration

Problem:

Difficult troubleshooting.

---

# Common Interview Questions

## What is a Task Definition?

Blueprint for running containers.

---

## Difference Between Task Definition and Task?

Task Definition:

Configuration template.

Task:

Running instance.

---

## Why Use Revisions?

Supports:

- Rollbacks
- Deployment history

---

## How Are Secrets Managed?

Use:

- Secrets Manager
- Parameter Store

---

## Why Avoid latest Tags?

Can cause:

- Unpredictable deployments
- Rollback difficulties

---

# Senior Engineer Perspective

Task Definitions are the heart of ECS deployments.

Most production incidents occur because of:

- Incorrect resource allocation
- Poor secrets management
- Bad image versioning
- Missing logging

A senior engineer treats Task Definitions as version-controlled infrastructure artifacts.

---

# Key Takeaways

- Task Definitions are deployment blueprints.
- Container Definitions specify how containers run.
- CPU and Memory limits protect workloads.
- Secrets should be managed securely.
- Logging must be centralized.
- Revisions enable safe deployments and rollbacks.
- Task Definitions should follow infrastructure-as-code principles.
