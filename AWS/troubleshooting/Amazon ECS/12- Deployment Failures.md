# Deployment Failures

Deployments are one of the most critical operations in Amazon ECS. A failed deployment can prevent new application versions from becoming available, trigger automatic rollbacks, or even cause temporary service outages if not properly configured.

Deployment failures are commonly caused by unhealthy tasks, application startup errors, failed health checks, incorrect Task Definitions, networking problems, or insufficient cluster resources.

This guide explains how to systematically troubleshoot failed ECS deployments.

---

# Typical Symptoms

You may observe one or more of the following:

- Deployment remains **IN_PROGRESS** indefinitely.
- Deployment automatically rolls back.
- New tasks never become healthy.
- ECS continuously replaces tasks.
- Service never reaches the desired count.
- Users receive HTTP 502 or HTTP 503 errors.

Example

```
New Deployment

↓

New Tasks Started

↓

Health Check Failed

↓

Deployment Rollback
```

---

# ECS Deployment Workflow

Understanding the deployment lifecycle makes troubleshooting much easier.

```
Build Docker Image

        │

        ▼

Push to Amazon ECR

        │

        ▼

Create Task Definition Revision

        │

        ▼

Update ECS Service

        │

        ▼

Launch New Tasks

        │

        ▼

Health Checks

        │

        ▼

Register with ALB

        │

        ▼

Stop Old Tasks

        │

        ▼

Deployment Complete
```

A deployment can fail at any stage of this process.

---

# Troubleshooting Workflow

```
Deployment Failed

        │

        ▼

ECS Service Events

        │

        ▼

Deployment Status

        │

        ▼

Task Status

        │

        ▼

CloudWatch Logs

        │

        ▼

Health Checks

        │

        ▼

Task Definition

        │

        ▼

Infrastructure

        │

        ▼

Root Cause
```

---

# Step 1: Review ECS Service Events

Always begin with the Service Events.

Common messages include:

```
Service deployment failed.
```

```
Task failed ELB health checks.
```

```
Unable to place task.
```

```
Deployment completed.
```

These events usually identify where the deployment stopped.

---

# Step 2: Review Deployment Status

Open the ECS Service.

Review:

- Primary Deployment
- Active Deployment
- Failed Deployment
- Rollback status

Example

```
Deployment

FAILED
```

---

# Step 3: Verify New Tasks

Check whether new tasks:

- Started successfully
- Reached RUNNING state
- Passed health checks

Example

```
RUNNING

↓

UNHEALTHY

↓

STOPPED
```

---

# Step 4: Review CloudWatch Logs

Most deployment failures originate from the application itself.

Look for:

- Startup exceptions
- Missing configuration
- Database connection failures
- Missing dependencies
- Port binding failures

Example

```
OperationalError

Could not connect to PostgreSQL
```

---

# Step 5: Verify Task Definition

Ensure the new Task Definition is correct.

Review:

- Image
- Image tag
- CPU
- Memory
- Environment variables
- Secrets
- Ports
- Health checks
- IAM Roles

Many deployments fail because of incorrect Task Definition revisions.

---

# Step 6: Verify Health Checks

Health checks must succeed before ECS considers a task healthy.

Verify:

- Endpoint
- Port
- Timeout
- Success code
- Grace Period

Example

```
GET

/health

↓

HTTP 200
```

---

# Step 7: Verify Load Balancer

Review:

- Listener
- Target Group
- Target Registration
- Health Status

Tasks that never become healthy cannot receive production traffic.

---

# Step 8: Verify Image Version

Confirm that the new Task Definition references the correct image.

Example

Correct

```
backend-api:v2.1.0
```

Incorrect

```
backend-api:latest
```

Using immutable version tags simplifies deployments and rollbacks.

---

# Step 9: Verify Cluster Capacity

Deployments require additional capacity while replacing old tasks.

Example

```
Desired

4

Maximum Percent

200%

↓

Maximum Running Tasks

8
```

If the cluster lacks CPU or memory, deployment may stall.

---

# Step 10: Verify Deployment Configuration

Review deployment settings.

Important values:

- Desired Count
- Minimum Healthy Percent
- Maximum Percent

Example

```
Desired Count

4

Minimum Healthy

100%

Maximum

200%
```

Incorrect settings may delay deployments unnecessarily.

---

# Common Deployment Problems

## New Tasks Never Become Healthy

Possible causes

- Health endpoint failure
- Application startup error
- Database unavailable
- Wrong port
- Configuration issue

---

## Automatic Rollback

Occurs when ECS cannot establish healthy replacement tasks.

Typical reasons

- Failed health checks
- Application crash
- Container exits immediately

---

## Deployment Stuck

Possible causes

- Pending tasks
- Cluster capacity exhausted
- Placement constraints
- Capacity Provider issues

---

## Wrong Application Version

Symptoms

Users still access the previous version.

Possible causes

- Wrong image tag
- Deployment failed
- Load Balancer still routing to old tasks

---

# Common Root Causes

| Problem | Solution |
|----------|----------|
| Task crashes | Review CloudWatch Logs |
| Health checks fail | Fix endpoint or configuration |
| Wrong image | Deploy correct image |
| Database unavailable | Restore connectivity |
| Missing environment variables | Update Task Definition |
| Cluster lacks capacity | Add compute resources |
| Incorrect deployment configuration | Review deployment settings |
| IAM permission issues | Correct Task Role or Execution Role |

---

# Diagnostic Checklist

Before retrying the deployment, verify:

- ECS Service Events reviewed.
- Deployment status checked.
- New tasks running.
- CloudWatch Logs reviewed.
- Task Definition verified.
- Health checks passing.
- Target Group healthy.
- Correct image version deployed.
- Cluster has sufficient CPU and memory.
- IAM permissions verified.

---

# Best Practices

- Use immutable image tags.
- Test new Task Definitions before production deployment.
- Use Rolling or Blue/Green deployments.
- Configure proper health checks.
- Enable automatic rollback.
- Monitor deployments using CloudWatch.
- Keep applications stateless.
- Deploy gradually whenever possible.

---

# Interview Questions

### Why would an ECS deployment fail?

Common reasons include:

- Application startup failure
- Failed health checks
- Wrong Task Definition
- Database connectivity issues
- Missing configuration
- Cluster resource exhaustion

---

### Where would you investigate first?

Recommended order:

1. ECS Service Events
2. Deployment Status
3. CloudWatch Logs
4. Health Checks
5. Task Definition
6. Target Group
7. Infrastructure

---

### Why does ECS automatically roll back deployments?

If the newly deployed tasks never become healthy, ECS restores the previous stable version to maintain service availability.

---

### Why should immutable image tags be used?

Immutable tags provide:

- Predictable deployments
- Easier rollbacks
- Better version tracking
- Consistent environments

---

### What deployment strategy would you recommend for production?

For most production systems:

- **Rolling Deployment** for simple, low-risk updates.
- **Blue/Green Deployment** for zero-downtime releases and quick rollback capabilities.

---

# Key Takeaways

- Deployment failures are most commonly caused by unhealthy tasks, application startup errors, failed health checks, or infrastructure limitations.
- ECS Service Events and CloudWatch Logs should always be your starting point when diagnosing deployment issues.
- Verify the Task Definition, container image, health checks, and cluster capacity before attempting another deployment.
- Immutable image tags, proper deployment settings, and automated rollback mechanisms improve deployment reliability.
- A structured troubleshooting process helps identify deployment failures quickly while minimizing production downtime.