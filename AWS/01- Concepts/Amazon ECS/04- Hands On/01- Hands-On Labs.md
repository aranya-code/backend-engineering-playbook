# ECS Hands-On Labs

# Lab 01 - Deploy Nginx on ECS Fargate

## Objective

Deploy your first containerized application on ECS.

---

## Architecture

```text
Internet
 ↓
Public IP
 ↓
ECS Fargate Task
 ↓
Nginx Container
```

---

## Services Used

- ECS
- Fargate
- ECR
- CloudWatch Logs

---

## Steps

### Step 1

Create ECS Cluster

```text
Lab-ECS-Cluster
```

---

### Step 2

Create Task Definition

Container:

```text
nginx:latest
```

---

### Step 3

Assign:

```text
0.25 vCPU
512 MB RAM
```

---

### Step 4

Create Service

```text
Desired Count = 1
```

---

### Step 5

Assign Public IP

Enable:

```text
Auto Assign Public IP
```

---

## Validation

Open:

```text
http://PUBLIC-IP
```

---

Expected:

```text
Welcome to nginx!
```

---

# Lab 02 - Deploy Django API on ECS

## Objective

Deploy a containerized Django REST API.

---

## Architecture

```text
ALB
 ↓
ECS Service
 ↓
Django API
```

---

## Services Used

- ECS
- ALB
- ECR
- CloudWatch

---

## Steps

### Step 1

Dockerize Django Application

---

### Step 2

Push Image

```bash
docker push
```

to ECR.

---

### Step 3

Create Task Definition

Use ECR image URI.

---

### Step 4

Create ECS Service

Attach:

```text
Application Load Balancer
```

---

### Step 5

Configure Health Check

Example:

```text
/health/
```

---

## Validation

Call:

```text
/api/
```

---

Expected:

```json
200 OK
```

---

# Lab 03 - ECS + PostgreSQL

## Objective

Connect ECS workloads to PostgreSQL.

---

## Architecture

```text
ALB
 ↓
ECS
 ↓
PostgreSQL
```

---

## Services Used

- ECS
- RDS PostgreSQL
- Secrets Manager

---

## Steps

### Step 1

Create PostgreSQL Database.

---

### Step 2

Store credentials in:

```text
Secrets Manager
```

---

### Step 3

Inject secrets into ECS.

---

### Step 4

Run migrations.

---

## Validation

Verify:

```text
CRUD Operations
```

work successfully.

---

# Lab 04 - ECS + ALB

## Objective

Configure production traffic routing.

---

## Architecture

```text
Internet
 ↓
ALB
 ↓
ECS Tasks
```

---

## Tasks

Configure:

- Listener
- Target Group
- Health Check

---

## Validation

Verify:

```text
Healthy Targets
```

in Target Group.

---

# Lab 05 - ECS Auto Scaling

## Objective

Scale ECS automatically.

---

## Architecture

```text
CloudWatch
 ↓
Scaling Policy
 ↓
ECS Service
```

---

## Steps

### CPU Target

```text
60%
```

---

### Min Tasks

```text
2
```

---

### Max Tasks

```text
10
```

---

## Validation

Generate load.

Verify:

```text
Scale Out
```

occurs.

---

# Lab 06 - ECS + EFS

## Objective

Use shared persistent storage.

---

## Architecture

```text
Task A
Task B
 ↓
 EFS
```

---

## Steps

### Step 1

Create EFS.

---

### Step 2

Create Mount Targets.

---

### Step 3

Mount EFS in ECS Task Definition.

---

## Validation

Create file in Task A.

Verify visibility in Task B.

---

# Lab 07 - Blue/Green Deployment

## Objective

Perform zero-downtime deployments.

---

## Architecture

```text
Blue Environment
Green Environment
```

---

## Services Used

- ECS
- ALB
- CodeDeploy

---

## Steps

### Deploy Version 1

---

### Deploy Version 2

---

### Shift Traffic

Gradually.

---

## Validation

Rollback successfully.

---

# Lab 08 - ECS CI/CD with GitHub Actions

## Objective

Automate ECS deployments.

---

## Architecture

```text
GitHub
 ↓
GitHub Actions
 ↓
ECR
 ↓
ECS
```

---

## Pipeline

```text
Build
Test
Push
Deploy
```

---

## Validation

Push code.

Verify deployment automatically occurs.

---

# Lab 09 - ECS Monitoring Dashboard

## Objective

Build production monitoring.

---

## Services Used

- CloudWatch
- ECS
- Alarms

---

## Dashboard Metrics

```text
CPU
Memory
Task Count
Errors
```

---

## Validation

Trigger alarm intentionally.

Verify notification.

---

# Lab 10 - Production FastAPI Deployment

## Objective

Deploy a production-grade FastAPI application.

---

## Architecture

```text
CloudFront
 ↓
ALB
 ↓
ECS
 ↓
Redis
 ↓
PostgreSQL
```

---

## Services Used

- ECS
- ALB
- CloudFront
- RDS
- ElastiCache
- CloudWatch
- Secrets Manager

---

## Requirements

### Security

- Private Subnets
- IAM Roles
- Secrets Manager

---

### Reliability

- Multi-AZ
- Auto Scaling
- Health Checks

---

### Observability

- Logs
- Metrics
- Alarms

---

## Validation

Perform:

```text
Load Test
Deployment Test
Failover Test
```

---

# Bonus Lab 11 - Event-Driven ECS

## Objective

Trigger ECS workflows using EventBridge.

---

## Architecture

```text
EventBridge
 ↓
ECS Task
```

---

## Use Cases

- Scheduled Reports
- ETL Jobs
- Batch Processing

---

# Bonus Lab 12 - ECS Cost Optimization

## Objective

Reduce infrastructure cost.

---

## Tasks

Implement:

```text
Fargate Spot
Auto Scaling
Rightsizing
```

---

Measure:

```text
Before Cost
After Cost
```

---

# Suggested Learning Order

Beginner:

```text
Lab 01
Lab 02
Lab 03
Lab 04
```

---

Intermediate:

```text
Lab 05
Lab 06
Lab 07
Lab 08
```

---

Advanced:

```text
Lab 09
Lab 10
Lab 11
Lab 12
```

---

# Portfolio Projects

After completing labs:

Build:

```text
Django SaaS Platform
FastAPI Backend
Event-Driven Worker System
```

Deploy entirely on ECS.

---

# Interview Value

Labs demonstrate:

- Real deployment experience
- Cloud troubleshooting
- Production architecture knowledge

which are more valuable than memorizing definitions.

---

# Senior Engineer Perspective

Reading documentation creates awareness.

Building systems creates understanding.

These labs are designed to bridge the gap between:

```text
Knowing ECS
```

and

```text
Operating ECS
```

in real-world production environments.

---

# Key Takeaways

- Start with simple deployments.
- Add networking and databases.
- Learn scaling and monitoring.
- Automate deployments.
- Practice recovery and failover.
- Build complete production systems.
