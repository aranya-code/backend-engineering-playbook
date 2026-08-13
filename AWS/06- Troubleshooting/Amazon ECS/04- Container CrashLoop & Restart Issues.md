# Container CrashLoop & Restart Issues

A container crash loop occurs when an ECS task repeatedly starts, crashes, and is restarted by the ECS Service Scheduler. Since an ECS Service maintains the desired number of running tasks, it continuously launches replacement tasks whenever a container exits unexpectedly.

Crash loops are among the most common production issues because they often indicate problems within the application rather than the ECS infrastructure.

---

# Typical Symptoms

You may observe one or more of the following:

- Tasks continuously restart.
- Deployment never completes.
- High task replacement count.
- Load Balancer targets repeatedly become unhealthy.
- Service never reaches a stable state.

Example

```
Task Started

↓

Application Crashed

↓

Task Stopped

↓

ECS Starts New Task

↓

Application Crashed Again

↓

Infinite Loop
```

---

# Troubleshooting Workflow

Always investigate restart issues using a structured approach.

```
Task Restarting

        │

        ▼

Service Events

        │

        ▼

Task Stop Reason

        │

        ▼

Container Exit Code

        │

        ▼

CloudWatch Logs

        │

        ▼

Application Logs

        │

        ▼

Configuration

        │

        ▼

Infrastructure

        │

        ▼

Root Cause
```

---

# Step 1: Check ECS Service Events

The ECS Service Events often indicate why tasks are being replaced.

Common messages include:

```
Essential container exited.
```

```
Task failed ELB health checks.
```

```
Container health check failed.
```

```
Task stopped unexpectedly.
```

---

# Step 2: Review the Stop Reason

Open the failed task and examine the **Stopped Reason**.

Common examples:

```
Essential container exited
```

```
OutOfMemoryError
```

```
Container health check failed
```

```
Task failed ELB health checks
```

---

# Step 3: Check Container Exit Code

Exit codes provide valuable diagnostic information.

| Exit Code | Meaning |
|-----------|----------|
| 0 | Application completed normally |
| 1 | General application error |
| 125 | Docker runtime failure |
| 126 | Command cannot execute |
| 127 | Command not found |
| 137 | Out Of Memory (OOM Kill) |
| 139 | Segmentation fault |
| 143 | Graceful termination (SIGTERM) |

---

### Most Important Exit Code

```
137
```

Usually indicates:

- Memory exhausted
- Linux OOM Killer terminated the container

---

# Step 4: Review CloudWatch Logs

CloudWatch Logs usually reveal why the application exited.

Look for:

- Python exceptions
- Java exceptions
- Node.js errors
- Missing modules
- Database errors
- Configuration problems
- Stack traces

Example

```
ModuleNotFoundError
```

```
OperationalError

Database unavailable
```

---

# Common Root Causes

---

# Application Crash

The application itself throws an exception during startup or runtime.

Examples

```
SyntaxError
```

```
ImportError
```

```
NullPointerException
```

```
Unhandled Exception
```

---

## Resolution

Fix the application before redeploying.

---

# Out Of Memory (OOM)

One of the most common production problems.

Symptoms

```
Exit Code

137
```

Possible causes

- Memory leak
- Large cache
- Huge file processing
- Large database query
- Insufficient memory allocation

---

## Investigation

Review

- Memory utilization
- CloudWatch metrics
- Application memory profile

---

## Resolution

- Increase task memory.
- Optimize application memory usage.
- Process data in smaller batches.

---

# Incorrect Startup Command

Example

Dockerfile

```
CMD ["python"]
```

instead of

```
CMD ["gunicorn","config.wsgi"]
```

The container immediately exits because the main process terminates.

---

## Resolution

Verify

- ENTRYPOINT
- CMD
- Startup script

---

# Missing Environment Variables

Example

```
DATABASE_URL
```

```
SECRET_KEY
```

```
REDIS_HOST
```

Applications frequently terminate if required configuration is unavailable.

---

## Resolution

Verify all required environment variables and Secrets Manager configuration.

---

# Database Connection Failure

Example

```
Connection refused
```

Possible reasons

- Database offline
- Wrong endpoint
- Security Groups
- Invalid credentials

---

## Resolution

Verify

- Database endpoint
- Credentials
- Security Groups
- Route tables
- Network connectivity

---

# Redis Connection Failure

Applications depending on Redis may fail during startup.

Example

```
Unable to connect to Redis
```

---

## Resolution

Verify

- Redis endpoint
- Security Groups
- Authentication
- Network connectivity

---

# Health Check Failure

The application starts successfully but fails health checks.

Result

```
RUNNING

↓

UNHEALTHY

↓

STOPPED
```

---

## Investigation

Review

- Health endpoint
- Response code
- Startup time
- ALB configuration

---

## Resolution

Correct the health check configuration or application endpoint.

---

# Missing IAM Permissions

Applications accessing AWS resources may terminate if permissions are missing.

Example

```
AccessDeniedException
```

---

## Resolution

Review

- Task Role
- IAM policy
- Resource policy

---

# Resource Exhaustion

Applications may terminate because of insufficient:

- CPU
- Memory
- Disk
- File descriptors

---

## Investigation

Review CloudWatch metrics.

Check

- CPU utilization
- Memory utilization
- Storage usage

---

# Container Dependency Failure

Some applications depend on external services.

Examples

- Database
- Redis
- Amazon SQS
- Amazon SNS
- Third-party APIs

If these services are unavailable during startup, the container may terminate.

---

# Diagnostic Checklist

Before restarting the service, verify:

- ECS Service Events reviewed.
- Task Stop Reason identified.
- Container Exit Code examined.
- CloudWatch Logs reviewed.
- Application logs analyzed.
- Database reachable.
- Redis reachable.
- Environment variables configured.
- Secrets available.
- IAM permissions correct.
- CPU sufficient.
- Memory sufficient.
- Health checks configured correctly.

---

# Best Practices

- Keep containers stateless.
- Handle transient failures gracefully.
- Implement retry logic for external dependencies.
- Configure readiness and health checks.
- Monitor restart counts using CloudWatch.
- Allocate sufficient CPU and memory.
- Write logs to stdout and stderr.
- Test startup locally before deployment.

---

# Interview Questions

### Why do ECS containers repeatedly restart?

Common causes include:

- Application crash
- Health check failures
- Out Of Memory
- Missing configuration
- Missing dependencies
- Database unavailable
- IAM permission errors

---

### What would you investigate first?

A recommended troubleshooting order is:

1. ECS Service Events
2. Task Stop Reason
3. Exit Code
4. CloudWatch Logs
5. Application Logs
6. Resource utilization
7. Configuration

---

### What is the difference between a CrashLoop and a PENDING task?

| CrashLoop | Pending |
|------------|----------|
| Application starts | Application never starts |
| Container exits | Scheduler cannot place task |
| Usually application issue | Usually infrastructure or scheduling issue |
| Logs available | Often no application logs |

---

# Key Takeaways

- Crash loops occur when ECS repeatedly replaces containers that terminate unexpectedly.
- ECS Service Events, Task Stop Reasons, Exit Codes, and CloudWatch Logs provide the fastest path to identifying the root cause.
- Application exceptions, memory exhaustion, failed health checks, missing configuration, and dependency failures are the most common causes.
- Exit Code **137** is a strong indicator of an Out Of Memory condition.
- Implementing proper health checks, retry logic, monitoring, and resource sizing helps prevent recurring crash loops in production.