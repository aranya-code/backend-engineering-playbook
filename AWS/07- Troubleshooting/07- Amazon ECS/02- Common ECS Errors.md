# Common ECS Errors

This guide covers the most frequently encountered Amazon Elastic Container Service (ECS) errors, explains why they occur, and provides a structured approach to diagnosing and resolving them. Rather than memorizing individual error messages, the goal is to understand where the failure is occurring and how to systematically identify the root cause.

Many ECS issues fall into one of a few categories:

- Container startup failures
- Deployment failures
- Networking issues
- IAM permission errors
- Resource limitations
- Health check failures
- Load balancer configuration
- Image pull failures
- Auto Scaling problems

Understanding these categories significantly reduces troubleshooting time in production.

---

# ECS Troubleshooting Workflow

When an ECS issue occurs, always follow a structured troubleshooting process.

```
Application Error
        │
        ▼
CloudWatch Alarm
        │
        ▼
ECS Service Events
        │
        ▼
Task Status
        │
        ▼
Container Logs
        │
        ▼
Application Logs
        │
        ▼
AWS Resource Configuration
        │
        ▼
Root Cause
```

Avoid making configuration changes before identifying the actual cause of the problem.

---

# Common ECS Error Categories

| Category | Typical Symptoms |
|----------|------------------|
| Container Startup | Task stops immediately after starting |
| Deployment | Service update fails or rolls back |
| Image Pull | Container image cannot be downloaded |
| Networking | Service cannot communicate with other resources |
| Load Balancer | Targets remain unhealthy |
| IAM | Access denied to AWS resources |
| Resource Constraints | Tasks remain in PENDING state |
| Monitoring | Logs or metrics are missing |
| Scaling | Tasks do not scale up or down |

---

# Error 1: CannotPullContainerError

## Example

```
CannotPullContainerError:
pull image manifest has been retried multiple times
```

or

```
CannotPullContainerError:
Error response from daemon
```

---

## Possible Causes

- Incorrect image name
- Invalid image tag
- Image does not exist
- Amazon ECR permissions missing
- Execution Role missing permissions
- Network connectivity issue
- NAT Gateway unavailable
- VPC Endpoint misconfigured

---

## How to Investigate

Verify:

- Image exists in Amazon ECR.
- Image tag is correct.
- Task Execution Role has ECR permissions.
- Internet access or VPC Endpoint is available.
- Repository policy allows access.

---

## Resolution

- Push the correct Docker image.
- Update the Task Definition.
- Fix IAM permissions.
- Verify networking configuration.

---

# Error 2: Task Failed to Start

## Symptoms

Task immediately changes to:

```
RUNNING

↓

STOPPED
```

---

## Common Causes

- Incorrect startup command
- Missing environment variables
- Database connection failure
- Missing dependencies
- Invalid application configuration
- Application crash during startup

---

## Investigation

Check:

- CloudWatch Logs
- Container logs
- Task Definition
- Environment variables
- Secrets Manager
- Startup command

---

## Resolution

Fix the application startup issue before redeploying.

---

# Error 3: Tasks Stuck in PENDING

## Symptoms

```
PENDING

PENDING

PENDING
```

Tasks never become RUNNING.

---

## Possible Causes

- Insufficient CPU
- Insufficient memory
- No available EC2 capacity
- Incorrect Capacity Provider
- ENI exhaustion
- Subnet IP exhaustion
- Placement constraints
- Service quota limits

---

## Investigation

Review:

- ECS Service Events
- Cluster capacity
- Available CPU
- Available memory
- Networking configuration

---

## Resolution

- Add compute capacity.
- Increase cluster size.
- Free unused resources.
- Review task resource requests.

---

# Error 4: Health Check Failed

## Symptoms

Task starts successfully but becomes unhealthy.

```
RUNNING

↓

UNHEALTHY

↓

STOPPED
```

---

## Possible Causes

- Incorrect health check path
- Wrong container port
- Slow application startup
- HTTP 500 responses
- Security Group restrictions
- Application not listening

---

## Investigation

Verify:

- Health check endpoint
- Target Group configuration
- Container port mapping
- Application logs

---

## Resolution

Fix the health endpoint or application startup.

---

# Error 5: AccessDeniedException

## Example

```
AccessDeniedException
```

---

## Possible Causes

- Missing Task Role permissions
- Missing Execution Role permissions
- Incorrect IAM policy
- Incorrect Resource ARN
- Cross-account permission issue

---

## Investigation

Identify:

Which IAM role generated the error?

- Task Role
- Execution Role

Then review:

- IAM policy
- Resource policy
- CloudTrail logs

---

## Resolution

Grant only the required permissions following the Principle of Least Privilege.

---

# Error 6: ResourceInitializationError

## Example

```
ResourceInitializationError
```

---

## Common Causes

- Secrets Manager unavailable
- Systems Manager Parameter Store issue
- IAM permission problem
- Network issue
- Missing VPC Endpoint

---

## Investigation

Check:

- Task Execution Role
- Secrets Manager access
- Network connectivity
- Region configuration

---

## Resolution

Correct IAM permissions and ensure the required AWS services are reachable.

---

# Error 7: Deployment Failed

## Symptoms

Deployment starts but eventually rolls back.

---

## Possible Causes

- New tasks unhealthy
- Health check failures
- Incorrect Task Definition
- Startup errors
- Database unavailable
- Configuration changes

---

## Investigation

Review:

- Deployment events
- CloudWatch Logs
- Target Group health
- ECS Service events

---

## Resolution

Identify why new tasks failed before attempting another deployment.

---

# Error 8: Service Not Scaling

## Symptoms

Traffic increases but task count remains unchanged.

---

## Possible Causes

- Auto Scaling disabled
- CloudWatch alarms missing
- Scaling policy incorrect
- Maximum capacity reached
- Capacity Provider unavailable

---

## Investigation

Check:

- Scaling policies
- CloudWatch alarms
- Maximum task count
- Cluster capacity

---

## Resolution

Correct scaling policies and ensure sufficient infrastructure exists to launch additional tasks.

---

# Error 9: Container Exits Immediately

## Symptoms

```
RUNNING

↓

STOPPED
```

within a few seconds.

---

## Possible Causes

- Main process exits
- Startup script completes
- Application crash
- Missing configuration
- Runtime exception

---

## Investigation

Review:

- Dockerfile
- ENTRYPOINT
- CMD
- Application logs
- Exit code

---

## Resolution

Ensure the container's main application process remains running.

---

# Error 10: No Logs in CloudWatch

## Symptoms

Application is running but CloudWatch contains no logs.

---

## Possible Causes

- awslogs driver missing
- Incorrect log group
- Execution Role lacks permissions
- Application writes logs to local files
- Incorrect logging configuration

---

## Investigation

Verify:

- Task Definition logging
- CloudWatch Log Group
- IAM permissions
- Application logging configuration

---

## Resolution

Configure the `awslogs` log driver and write logs to `stdout` and `stderr`.

---

# ECS Troubleshooting Checklist

Before making changes, verify the following:

- Is the task running?
- Is the container healthy?
- Are CloudWatch logs available?
- Are health checks passing?
- Does the image exist in Amazon ECR?
- Are IAM roles configured correctly?
- Is networking configured properly?
- Is the database reachable?
- Is Auto Scaling configured correctly?
- Are enough CPU and memory resources available?

---

# Best Practices

- Always investigate ECS Service Events first.
- Review CloudWatch Logs before modifying infrastructure.
- Use health checks to detect application failures early.
- Store secrets in AWS Secrets Manager instead of environment variables.
- Keep containers stateless whenever possible.
- Configure CloudWatch alarms for critical metrics.
- Use Infrastructure as Code for consistent deployments.
- Follow the Principle of Least Privilege for IAM roles.
- Test container images locally before deploying to ECS.

---

# Key Takeaways

- Most ECS issues fall into a small number of categories, including startup failures, networking, IAM permissions, deployments, and resource constraints.
- Begin troubleshooting with ECS Service Events and CloudWatch Logs before making configuration changes.
- Many deployment failures are caused by unhealthy tasks, incorrect Task Definitions, or failed health checks.
- Understanding common ECS error patterns enables faster root cause analysis and reduces production downtime.
- A structured troubleshooting methodology is more effective than investigating individual error messages in isolation.