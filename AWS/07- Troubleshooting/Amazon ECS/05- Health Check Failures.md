# Health Check Failures

Health checks are one of the most important mechanisms in Amazon ECS for determining whether a container is healthy and capable of serving traffic. If health checks fail, ECS may stop the task and launch a replacement, while the Application Load Balancer (ALB) removes the task from its target group.

Health check failures are a common cause of deployment failures, continuous task replacements, and application downtime.

---

# Typical Symptoms

You may observe one or more of the following:

- Tasks repeatedly become unhealthy.
- ECS continuously replaces tasks.
- Deployment never completes.
- ALB Target Group shows unhealthy targets.
- Users receive HTTP 502 or 503 errors.

Example

```
Task Running

↓

Health Check Failed

↓

Task Marked Unhealthy

↓

Task Stopped

↓

Replacement Task Started
```

---

# Types of Health Checks

Amazon ECS commonly uses two types of health checks.

## Container Health Check

Executed inside the container.

Example

```
curl http://localhost:8000/health
```

Configured in the Task Definition.

---

## Load Balancer Health Check

Performed by the Application Load Balancer.

Example

```
GET /health
```

Configured in the Target Group.

---

# Troubleshooting Workflow

```
Health Check Failed

        │

        ▼

Target Group

        │

        ▼

Health Check Configuration

        │

        ▼

Container Status

        │

        ▼

Application Logs

        │

        ▼

Networking

        │

        ▼

Root Cause
```

---

# Step 1: Check ECS Service Events

Start by reviewing ECS Service Events.

Typical messages include:

```
Task failed ELB health checks.
```

```
Container health check failed.
```

```
Service reached steady state.
```

These events indicate whether ECS or the Load Balancer detected the failure.

---

# Step 2: Review Target Group Health

Open the Target Group in the AWS Console.

Review:

- Healthy targets
- Unhealthy targets
- Health status
- Failure reason

Typical status

```
Target

↓

Unhealthy
```

---

# Step 3: Verify Health Check Endpoint

The endpoint must return a successful HTTP response.

Example

```
GET

/health
```

Typical successful response

```
HTTP 200 OK
```

Common mistakes

- Wrong URL
- Typographical error
- Endpoint removed
- Authentication required

---

# Step 4: Verify Container Port

Example

Application listens on

```
8000
```

Task Definition exposes

```
5000
```

The Load Balancer cannot reach the application.

---

## Resolution

Ensure:

- Application port
- Container port
- Target Group port

all match.

---

# Step 5: Verify Security Groups

The Application Load Balancer must be allowed to communicate with ECS tasks.

Example

```
ALB

↓

Security Group

↓

ECS Task
```

Verify:

- Inbound rules
- Outbound rules
- Correct ports

---

# Step 6: Check Application Startup Time

Some applications require additional startup time.

Example

```
Container Starts

↓

Application Loading

↓

Health Check Begins

↓

Failure
```

The application is still initializing when health checks begin.

---

## Resolution

Increase:

- Health Check Grace Period
- Health Check Interval
- Healthy Threshold

---

# Step 7: Review Application Logs

CloudWatch Logs often identify the underlying issue.

Look for:

- Exceptions
- Database errors
- Redis errors
- Dependency failures
- Startup failures

Example

```
OperationalError

Database unavailable
```

---

# Step 8: Verify Database Connectivity

Applications often fail health checks because required services are unavailable.

Examples

- Amazon RDS
- Amazon ElastiCache
- Amazon OpenSearch
- Third-party APIs

---

## Investigation

Verify:

- Endpoint
- Credentials
- Security Groups
- Network routing

---

# Step 9: Verify Resource Utilization

High resource utilization may delay application responses.

Review:

- CPU utilization
- Memory utilization
- Disk usage

Applications under heavy load may fail health checks because responses exceed the configured timeout.

---

# Step 10: Verify Timeout Configuration

Example

```
Application Response

12 seconds

↓

Health Check Timeout

5 seconds
```

The target is marked unhealthy.

---

## Resolution

Increase:

- Timeout
- Interval
- Healthy Threshold

only after confirming the application is functioning correctly.

---

# Common Root Causes

| Problem | Typical Solution |
|----------|------------------|
| Wrong health endpoint | Correct endpoint path |
| Wrong port | Match application and target group ports |
| Slow startup | Increase health check grace period |
| Database unavailable | Restore connectivity |
| Redis unavailable | Restore connectivity |
| Security Group issue | Update security rules |
| Application exception | Fix application code |
| CPU saturation | Scale the service |
| Memory exhaustion | Increase memory allocation |

---

# Diagnostic Checklist

Before restarting the service, verify:

- ECS Service Events reviewed.
- Target Group health checked.
- Health endpoint returns HTTP 200.
- Container port matches Target Group.
- Security Groups configured correctly.
- Application fully starts before health checks begin.
- CloudWatch Logs reviewed.
- Database reachable.
- Redis reachable.
- CPU utilization normal.
- Memory utilization normal.

---

# Best Practices

- Create a lightweight `/health` endpoint.
- Do not perform expensive operations inside health checks.
- Return HTTP 200 only when the application is ready.
- Separate liveness and readiness checks when appropriate.
- Configure a Health Check Grace Period for slow-starting applications.
- Monitor unhealthy target counts using CloudWatch.
- Test health endpoints locally before deployment.

---

# Interview Questions

### Why do ECS tasks repeatedly fail health checks?

Common reasons include:

- Incorrect endpoint
- Wrong container port
- Application startup delay
- Database unavailable
- Security Group configuration
- Application exceptions

---

### Where would you investigate first?

Recommended order:

1. ECS Service Events
2. Target Group Health
3. Health Check Configuration
4. CloudWatch Logs
5. Application Logs
6. Networking
7. Database Connectivity

---

### What is the difference between a Container Health Check and an ALB Health Check?

| Container Health Check | ALB Health Check |
|-------------------------|------------------|
| Runs inside the container | Runs from the Load Balancer |
| Configured in Task Definition | Configured in Target Group |
| Verifies application process | Verifies external accessibility |
| Used by ECS | Used by ALB and ECS |

---

### Why shouldn't a health endpoint query the database?

Health checks should be lightweight and fast. Performing database queries or other expensive operations can increase response time, generate unnecessary load, and cause healthy services to be marked unhealthy during transient dependency issues.

---

# Key Takeaways

- Health checks determine whether ECS tasks are capable of serving traffic and directly affect deployments and service availability.
- Always begin troubleshooting by reviewing ECS Service Events and Target Group health status.
- Incorrect endpoint paths, port mismatches, slow application startup, networking issues, and dependency failures are the most common causes of health check failures.
- Design health endpoints to be lightweight, reliable, and focused on application readiness.
- Proper health check configuration is essential for stable deployments, automatic recovery, and high availability in production.