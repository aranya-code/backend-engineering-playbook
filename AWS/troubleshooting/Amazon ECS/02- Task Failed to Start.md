# Task Failed to Start

One of the most common Amazon ECS issues is when a task never reaches the **RUNNING** state or immediately transitions from **PENDING** to **STOPPED**. This usually indicates that the container failed during initialization before the application became operational.

Task startup failures can result from application errors, incorrect Task Definition settings, missing dependencies, networking issues, or IAM permission problems.

---

# Typical Symptoms

You may observe one or more of the following:

- Task starts and immediately stops.
- ECS Service continuously launches replacement tasks.
- Deployment never completes.
- Application Load Balancer never registers healthy targets.
- Service remains unstable.

Example:

```
PENDING

↓

RUNNING

↓

STOPPED
```

---

# Troubleshooting Workflow

Always investigate startup failures using the following approach:

```
Task Failed

      │

      ▼

ECS Service Events

      │

      ▼

Task Details

      │

      ▼

CloudWatch Logs

      │

      ▼

Container Exit Code

      │

      ▼

Application Logs

      │

      ▼

Task Definition

      │

      ▼

Root Cause
```

---

# Step 1: Check ECS Service Events

The first place to investigate is the ECS Service Events.

Look for messages such as:

```
Essential container exited.
```

```
Task stopped unexpectedly.
```

```
CannotPullContainerError
```

```
ResourceInitializationError
```

```
Task failed ELB health checks.
```

These events usually indicate where the startup process failed.

---

# Step 2: Check Task Stop Reason

Open the failed task and review the **Stopped Reason**.

Examples:

```
Essential container exited
```

```
OutOfMemoryError
```

```
CannotPullContainerError
```

```
ResourceInitializationError
```

```
Task failed health checks
```

The stop reason provides valuable clues before examining application logs.

---

# Step 3: Review CloudWatch Logs

Most startup failures can be identified through container logs.

Look for:

- Python exceptions
- Java stack traces
- Node.js errors
- Missing configuration
- Database connection failures
- Port binding failures

Example:

```
django.db.utils.OperationalError

Could not connect to database
```

or

```
ModuleNotFoundError
```

or

```
Address already in use
```

---

# Step 4: Check Container Exit Code

Exit codes help identify why the container terminated.

| Exit Code | Meaning |
|-----------|----------|
| 0 | Process completed successfully |
| 1 | General application error |
| 125 | Docker runtime error |
| 126 | Command cannot execute |
| 127 | Command not found |
| 137 | Container killed (usually Out Of Memory) |
| 139 | Segmentation fault |
| 143 | Graceful termination (SIGTERM) |

---

### Interview Tip

Exit Code **137** almost always indicates:

- Memory limit exceeded
- Container killed by the Linux OOM Killer

---

# Step 5: Verify Task Definition

Incorrect Task Definitions are a frequent source of startup failures.

Review:

- Docker image
- CPU
- Memory
- Container port
- Environment variables
- Secrets
- EntryPoint
- Command
- IAM roles

Example:

```
Image

my-api:v5
```

Ensure the image exists and is accessible.

---

# Common Causes

## Incorrect Docker Image

Symptoms

```
CannotPullContainerError
```

Verify:

- Repository
- Image tag
- Image digest

---

## Missing Environment Variables

Example

```
DATABASE_URL

SECRET_KEY

REDIS_HOST
```

If these variables are missing, many applications fail during startup.

---

## Missing Secrets

Applications often retrieve credentials from:

- AWS Secrets Manager
- Systems Manager Parameter Store

If permissions are missing, initialization fails.

---

## Database Connection Failure

Example

```
OperationalError

Connection refused
```

Possible causes:

- Database offline
- Wrong credentials
- Incorrect endpoint
- Security Group
- Network routing

---

## Redis Connection Failure

Example

```
Cannot connect to Redis
```

Verify:

- Redis endpoint
- Security Groups
- Network connectivity
- Authentication

---

## Application Crash

Typical reasons include:

- Syntax error
- Runtime exception
- Missing dependency
- Invalid configuration
- Startup script failure

CloudWatch Logs usually reveal the root cause.

---

## Incorrect Port Configuration

Example

Application:

```
8000
```

Task Definition:

```
5000
```

The application starts, but ECS cannot communicate with it.

---

## Insufficient Memory

Symptoms

```
Exit Code 137
```

Container starts briefly and then terminates.

Solution:

Increase memory allocation or optimize application memory usage.

---

## Missing IAM Permissions

Typical errors:

```
AccessDeniedException
```

```
UnauthorizedOperation
```

Verify:

- Task Role
- Execution Role
- Resource policy

---

# Diagnostic Checklist

Before redeploying, verify:

- Docker image exists.
- Correct image tag.
- Environment variables configured.
- Secrets accessible.
- Database reachable.
- Redis reachable.
- Application starts locally.
- CloudWatch Logs enabled.
- IAM permissions correct.
- CPU and memory sufficient.
- Container port correct.
- Health check endpoint available.

---

# Best Practices

- Test containers locally before deployment.
- Store configuration outside the Docker image.
- Keep startup logic lightweight.
- Write logs to `stdout` and `stderr`.
- Use health checks to validate application readiness.
- Store secrets in AWS Secrets Manager.
- Allocate realistic CPU and memory limits.
- Monitor startup failures with CloudWatch alarms.

---

# Interview Questions

### Why would a task immediately stop after starting?

Possible reasons include:

- Application crash
- Missing configuration
- Database unavailable
- Invalid Docker image
- Out Of Memory
- Missing IAM permissions

---

### Where would you investigate first?

A good troubleshooting sequence is:

1. ECS Service Events
2. Task Stop Reason
3. CloudWatch Logs
4. Container Exit Code
5. Task Definition
6. Application configuration

---

### What does Exit Code 137 indicate?

The container was terminated because it exceeded its memory limit and was killed by the operating system.

---

# Key Takeaways

- Task startup failures are most commonly caused by application crashes, configuration issues, resource limitations, or missing dependencies.
- Begin troubleshooting with ECS Service Events, followed by the Task Stop Reason and CloudWatch Logs.
- Container exit codes provide valuable clues about why a task terminated.
- Verify the Task Definition carefully, including image, ports, CPU, memory, environment variables, secrets, and IAM roles.
- A structured troubleshooting approach significantly reduces the time required to identify and resolve startup failures.