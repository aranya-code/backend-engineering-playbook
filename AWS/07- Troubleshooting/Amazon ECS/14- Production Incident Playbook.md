# Production Incident Playbook

Production incidents are inevitable in distributed systems. The goal is not to eliminate every incident, but to detect issues quickly, minimize customer impact, restore service efficiently, and prevent the same problem from occurring again.

This playbook provides a structured approach for handling production incidents involving Amazon ECS services.

---

# Incident Response Lifecycle

Every production incident should follow a repeatable process.

```
Alert

↓

Acknowledge

↓

Investigate

↓

Identify Root Cause

↓

Mitigate

↓

Recover

↓

Validate

↓

Postmortem

↓

Prevent Recurrence
```

Following the same process during every incident helps reduce downtime and avoids overlooking important diagnostic steps.

---

# Incident Severity Levels

| Severity | Description | Example |
|----------|-------------|----------|
| P1 | Complete outage affecting all users | Entire API unavailable |
| P2 | Major functionality degraded | Login service unavailable |
| P3 | Partial degradation | Increased latency |
| P4 | Minor issue | Dashboard metrics delayed |

---

# Phase 1: Incident Detection

Production incidents are usually detected through:

- CloudWatch Alarms
- Application monitoring
- Synthetic monitoring
- Customer reports
- PagerDuty
- Amazon SNS notifications
- Internal dashboards

Example

```
CPU > 90%

↓

CloudWatch Alarm

↓

SNS

↓

Engineer Notified
```

---

# Phase 2: Initial Assessment

Determine:

- Which service is affected?
- When did it start?
- How many users are impacted?
- Is the issue ongoing?
- Was a deployment recently completed?

Example questions

```
Is it only one ECS Service?

or

Entire Cluster?
```

---

# Phase 3: Verify Infrastructure

Before investigating application code, verify infrastructure health.

Review:

- ECS Cluster
- ECS Service
- Running Tasks
- Pending Tasks
- Target Group
- Load Balancer
- Auto Scaling
- Capacity Providers

---

## Infrastructure Checklist

Verify

- ECS Service healthy
- Desired count achieved
- Tasks running
- Cluster capacity available
- Load Balancer healthy
- Target Group healthy

---

# Phase 4: Review Recent Changes

Many production incidents occur shortly after a deployment.

Check for:

- New Task Definition
- New Docker Image
- Configuration changes
- IAM policy updates
- Security Group changes
- Database migrations

Timeline

```
Deployment

↓

5 Minutes Later

↓

Production Incident
```

Recent changes are often the fastest path to identifying the root cause.

---

# Phase 5: Analyze CloudWatch

Review:

Infrastructure

- CPU
- Memory
- Network
- Running Tasks

Application

- Response Time
- Error Rate
- Request Count

Business

- Orders
- Payments
- Transactions

Look for unusual spikes or sudden changes.

---

# Phase 6: Review ECS Service Events

ECS Service Events provide valuable deployment and scheduling information.

Common events

```
Task failed ELB health checks.
```

```
Unable to place task.
```

```
Deployment completed.
```

```
Task stopped unexpectedly.
```

---

# Phase 7: Review CloudWatch Logs

Search for:

- Exceptions
- Stack traces
- Connection failures
- Timeout errors
- AccessDeniedException
- OutOfMemoryError

Example

```
OperationalError

Connection refused
```

---

# Phase 8: Verify Dependencies

Modern applications depend on many external systems.

Verify

- Amazon RDS
- Amazon ElastiCache
- Amazon ECR
- Amazon SQS
- Amazon SNS
- Secrets Manager
- External APIs

One failed dependency may affect the entire application.

---

# Phase 9: Mitigation

The objective is to restore service quickly.

Possible mitigation strategies

- Roll back deployment
- Scale out ECS tasks
- Restart failed service
- Restore database connectivity
- Increase capacity
- Disable problematic feature
- Redirect traffic

Example

```
Deployment Failed

↓

Rollback

↓

Service Restored
```

---

# Phase 10: Validate Recovery

After mitigation, verify:

- Tasks healthy
- Load Balancer healthy
- Error rate normal
- Response time normal
- Customers can access the application
- Monitoring dashboards stable

Never assume recovery is complete without validation.

---

# Incident Investigation Checklist

During every incident, verify:

- ECS Service Events
- Running Tasks
- Pending Tasks
- CloudWatch Logs
- Target Group Health
- Load Balancer
- CPU utilization
- Memory utilization
- Auto Scaling
- IAM permissions
- Database connectivity
- Redis connectivity
- External services

---

# Common Production Incidents

## Deployment Failure

Symptoms

- Rollback
- Unhealthy tasks
- Failed health checks

Primary investigation

- ECS Service Events
- CloudWatch Logs
- Target Group

---

## High CPU

Symptoms

```
CPU

95%
```

Possible actions

- Scale out
- Profile application
- Optimize SQL
- Add caching

---

## Database Outage

Symptoms

```
Connection refused
```

Verify

- Database status
- Security Groups
- Credentials
- Route Tables

---

## Memory Leak

Symptoms

```
Exit Code

137
```

Actions

- Restart service
- Increase memory
- Fix application
- Profile memory usage

---

## Image Pull Failure

Symptoms

```
CannotPullContainerError
```

Verify

- Amazon ECR
- Execution Role
- Network connectivity

---

## Networking Failure

Symptoms

- Database unreachable
- Redis unreachable
- API timeout

Verify

- Security Groups
- Route Tables
- DNS
- NAT Gateway

---

# Incident Communication

During an incident:

Communicate

- Current status
- Business impact
- Mitigation steps
- Estimated recovery time
- Recovery confirmation

Avoid speculation.

Only communicate verified information.

---

# Post-Incident Review

Every production incident should end with a retrospective.

Questions to answer:

- What happened?
- Why did it happen?
- How was it detected?
- What restored service?
- What can prevent recurrence?

---

# Example Postmortem

## Incident

Deployment caused API failures.

---

## Root Cause

Incorrect database credentials.

---

## Resolution

Rolled back Task Definition.

---

## Preventive Actions

- Add deployment validation.
- Improve health checks.
- Add automated smoke tests.
- Validate secrets before deployment.

---

# Production Readiness Checklist

Before every deployment, verify:

- Infrastructure healthy.
- CloudWatch alarms configured.
- Health checks working.
- Rollback strategy tested.
- Monitoring dashboards available.
- Auto Scaling enabled.
- Database backups verified.
- Secrets configured.
- IAM policies reviewed.
- Load Balancer healthy.

---

# Best Practices

- Follow a documented incident response process.
- Investigate infrastructure before application code.
- Enable comprehensive monitoring and alerting.
- Automate rollback whenever possible.
- Conduct postmortems after every significant incident.
- Test disaster recovery procedures regularly.
- Keep runbooks updated.
- Use Infrastructure as Code to reproduce environments consistently.

---

# Interview Questions

### How would you handle a production incident?

A structured approach is:

1. Acknowledge the alert.
2. Assess the impact.
3. Verify infrastructure.
4. Review logs and metrics.
5. Identify the root cause.
6. Mitigate the issue.
7. Validate recovery.
8. Conduct a postmortem.

---

### What is the first thing you check during an ECS production incident?

Start with:

- CloudWatch Alarms
- ECS Service Events
- Running Tasks
- Target Group Health

These provide the fastest overview of system health.

---

### Why should you review recent deployments?

Because many production incidents are introduced by:

- New application versions
- Configuration changes
- Infrastructure modifications
- Database migrations

Recent changes often correlate directly with the start of an incident.

---

### Why are postmortems important?

Postmortems help teams:

- Identify root causes.
- Improve operational processes.
- Prevent recurring incidents.
- Share knowledge across the engineering team.

The focus should be on improving systems and processes rather than assigning blame.

---

# Key Takeaways

- A structured incident response process reduces recovery time and minimizes business impact.
- Always investigate infrastructure, logs, metrics, and recent changes before making corrective actions.
- CloudWatch, ECS Service Events, Target Groups, and application logs are the primary sources of information during an incident.
- Effective communication and post-incident reviews are as important as technical troubleshooting.
- Continuous improvement through automation, monitoring, testing, and documented runbooks increases the reliability of Amazon ECS workloads.