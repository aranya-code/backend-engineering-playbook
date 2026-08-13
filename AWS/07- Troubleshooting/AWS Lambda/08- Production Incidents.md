# 08- Production Incidents

# Overview

Production incidents are inevitable in any distributed system. The difference between an average engineer and a senior engineer is not whether incidents occur, but **how quickly they are detected, investigated, mitigated, and prevented from happening again**.

AWS Lambda applications are highly distributed and interact with numerous AWS services including API Gateway, SQS, SNS, EventBridge, DynamoDB, Aurora, Redis, CloudWatch, and third-party APIs. As a result, production incidents often involve multiple services rather than Lambda itself.

This chapter presents a systematic approach to handling Lambda production incidents based on industry practices.

---

# Incident Response Lifecycle

Every production incident should follow a structured lifecycle.

```
Alert

↓

Incident Detection

↓

Impact Assessment

↓

Root Cause Analysis

↓

Mitigation

↓

Recovery

↓

Postmortem

↓

Preventive Actions
```

Never jump directly to code changes without understanding the failure.

---

# Severity Classification

| Severity | Description | Example |
|----------|-------------|---------|
| P0 | Complete outage affecting all users | API unavailable |
| P1 | Critical functionality unavailable | Payments failing |
| P2 | Partial degradation | Increased latency |
| P3 | Minor issue | Logging problem |
| P4 | Cosmetic issue | Dashboard formatting |

Prioritize response based on business impact.

---

# Example Incident

```
Alert

↓

API Error Rate

↓

85%

↓

Customers Unable to Place Orders
```

Immediate questions:

- When did the incident start?
- Which deployment occurred recently?
- Which service is failing?
- Is the issue regional?

---

# Step 1 — Confirm the Incident

Do not rely on a single alert.

Check:

- CloudWatch Metrics
- CloudWatch Alarms
- AWS Health Dashboard
- Application Dashboard
- Customer Reports

```
Alert

↓

Verify

↓

Incident Confirmed
```

---

# Step 2 — Assess Business Impact

Determine:

- Number of affected users
- Revenue impact
- Critical business functions
- Geographic scope

Example

```
Payment API

↓

Unavailable

↓

Revenue Impact

↓

Highest Priority
```

---

# Step 3 — Gather Evidence

Collect evidence before making changes.

Review:

- CloudWatch Logs
- CloudWatch Metrics
- AWS X-Ray
- CloudTrail
- Deployment History
- Recent Infrastructure Changes

---

# Step 4 — Identify the Failing Component

Architecture

```
Client

↓

CloudFront

↓

API Gateway

↓

Lambda

↓

Aurora

↓

External API
```

Determine exactly where requests begin failing.

---

# Step 5 — Immediate Mitigation

Examples

Rollback

```
Alias

↓

Previous Version
```

Disable Trigger

```
Reserved Concurrency

↓

0
```

Redirect Traffic

```
Route53

↓

Healthy Region
```

Immediate mitigation reduces customer impact while investigation continues.

---

# Incident 1 — API Returns 502

Architecture

```
Client

↓

API Gateway

↓

Lambda

↓

502
```

Possible causes

- Invalid Lambda response
- Runtime exception
- Missing handler

Investigation

- CloudWatch Logs
- Lambda response format
- API Gateway execution logs

---

# Incident 2 — Payment API Latency

Symptoms

```
Average

250 ms

↓

8 Seconds
```

X-Ray

```
API Gateway

↓

Lambda

↓

Stripe

↓

7800 ms
```

Root Cause

Third-party API slowdown.

Resolution

Move payment processing to asynchronous workers using Amazon SQS.

---

# Incident 3 — Database Outage

Symptoms

```
Lambda

↓

Aurora

↓

Timeout
```

Possible causes

- Database unavailable
- Too many connections
- Missing indexes

Resolution

```
Lambda

↓

RDS Proxy

↓

Aurora
```

---

# Incident 4 — Recursive Invocation

Architecture

```
S3

↓

Lambda

↓

S3

↓

Lambda

↓

Infinite Loop
```

Symptoms

- Millions of invocations
- Large AWS bill
- Increased concurrency

Immediate Action

```
Reserved Concurrency

↓

0
```

Fix architecture before re-enabling.

---

# Incident 5 — Throttling

Symptoms

```
Throttles

↑
```

Investigation

```
ConcurrentExecutions

↓

Account Limit
```

Solutions

- Increase quota
- Optimize execution time
- Introduce SQS buffering

---

# Incident 6 — IAM Failure

Symptoms

```
AccessDeniedException
```

Review

- Execution Role
- Resource Policy
- CloudTrail

Fix only the missing permission.

---

# Incident 7 — VPC Connectivity Failure

Symptoms

```
Database Timeout

↓

External APIs Fail
```

Check

- Security Groups
- Route Tables
- NAT Gateway
- DNS
- VPC Endpoints

---

# Incident 8 — Cold Start Regression

Symptoms

```
Normal

150 ms

↓

After Deployment

2.5 Seconds
```

Possible causes

- Large package
- New dependency
- Runtime change

Resolution

- Optimize dependencies
- Provisioned Concurrency
- SnapStart (Java)

---

# Production Investigation Workflow

Always investigate in the following order.

```
CloudWatch Metrics

↓

CloudWatch Logs

↓

AWS X-Ray

↓

CloudTrail

↓

Deployment History

↓

Infrastructure

↓

Application Code
```

This avoids unnecessary assumptions.

---

# Monitoring Dashboard

Every production Lambda should monitor:

- Invocations
- Errors
- Duration
- Throttles
- Concurrent Executions
- Iterator Age
- Dead Letter Queue failures
- Memory utilization

---

# Incident Runbook

A simple runbook should contain:

```
Problem

↓

Possible Causes

↓

Verification Steps

↓

Immediate Mitigation

↓

Permanent Fix

↓

Owner
```

Maintain runbooks for recurring incidents.

---

# Communication During Incidents

Good communication is as important as technical resolution.

Typical flow

```
Incident Declared

↓

Engineering Team

↓

Stakeholders

↓

Management

↓

Customers (if required)
```

Avoid speculation. Share verified information.

---

# Post-Incident Review

Every production incident should conclude with a retrospective.

Questions

- What happened?
- Why did it happen?
- Why wasn't it detected earlier?
- How was it resolved?
- How can it be prevented?

---

# Example Postmortem

## Incident

```
Payment Service Downtime

15 Minutes
```

## Root Cause

Third-party API latency.

## Immediate Fix

Traffic redirected to asynchronous queue.

## Long-Term Action

- Circuit Breaker
- Retry Policy
- Timeout configuration
- Monitoring improvements

---

# Production Readiness Checklist

Before releasing any Lambda workload:

- [ ] CloudWatch Alarms configured
- [ ] AWS X-Ray enabled
- [ ] Structured logging implemented
- [ ] IAM follows least privilege
- [ ] Secrets stored securely
- [ ] RDS Proxy configured
- [ ] Retry policies reviewed
- [ ] Dead Letter Queue configured
- [ ] Rollback strategy tested
- [ ] Runbook documented

---

# Common Mistakes During Incidents

❌ Restarting deployments without investigation

❌ Making multiple changes simultaneously

❌ Ignoring logs

❌ Assuming Lambda is the root cause

❌ Disabling monitoring

❌ Forgetting rollback procedures

❌ Poor communication

---

# Best Practices

✅ Automate monitoring and alerting.

✅ Enable CloudWatch Logs and AWS X-Ray.

✅ Keep deployment rollbacks simple.

✅ Use canary deployments.

✅ Maintain incident runbooks.

✅ Perform regular disaster recovery drills.

✅ Conduct blameless postmortems.

---

# Senior Backend Engineering Perspective

Production incident management extends beyond fixing technical issues. Senior engineers focus on minimizing customer impact, coordinating communication, restoring service quickly, and implementing long-term improvements that reduce the likelihood of recurrence.

Successful incident response combines strong observability, disciplined investigation, automation, clear communication, and a culture of continuous learning.

---

# Key Takeaways

- A structured incident response process reduces downtime and improves reliability.
- Most Lambda production incidents involve integrations, networking, IAM, or downstream services rather than Lambda itself.
- CloudWatch, AWS X-Ray, CloudTrail, and deployment history are essential for root cause analysis.
- Runbooks, monitoring, gradual deployments, and rollback strategies significantly improve operational resilience.
- Every production incident should result in actionable improvements through a blameless postmortem and preventive engineering practices.