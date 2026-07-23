# 22- Lambda Deployment Strategies

# Introduction

Deploying a Lambda function directly into production is risky. Even a small bug can cause widespread failures because serverless applications often scale instantly.

Production-grade systems use **deployment strategies** that gradually introduce new code while minimizing risk and enabling quick rollbacks.

AWS Lambda supports several deployment strategies through:

- Lambda Versions
- Lambda Aliases
- AWS CodeDeploy
- Weighted Routing
- Canary Deployments
- Linear Deployments
- Blue/Green Deployments

A senior backend engineer should understand when each strategy is appropriate and how to implement it.

---

# Why Deployment Strategies Matter

Imagine a payment service.

```
Users

↓

Lambda v1
```

You deploy a new version.

```
Users

↓

Lambda v2
```

If v2 contains a bug:

- Payments fail
- Revenue is lost
- Rollback becomes urgent

Instead of replacing the function immediately, production systems deploy gradually.

---

# Lambda Versions

Every published Lambda version is immutable.

```
$LATEST

↓

Publish

↓

Version 1

↓

Publish

↓

Version 2

↓

Publish

↓

Version 3
```

Once published:

- Code cannot change
- Configuration cannot change
- Safe for production

---

# Lambda Aliases

Aliases provide stable names that point to versions.

```
Production

↓

Version 15
```

Example aliases:

```
dev

qa

staging

production
```

Applications invoke the alias rather than a version number.

---

# Deployment Flow

```
Developer

↓

Upload Code

↓

$LATEST

↓

Publish Version

↓

Move Alias

↓

Production
```

---

# Why Aliases Matter

Without aliases:

```
Client

↓

Version 18
```

Every deployment changes the client configuration.

With aliases:

```
Client

↓

production

↓

Version 18
```

Future deployments only update the alias.

---

# Weighted Routing

Aliases support traffic splitting.

Example:

```
Production Alias

│

├── Version 10

90%

└── Version 11

10%
```

Only a small percentage of users receive the new version.

---

# Canary Deployment

A Canary deployment releases the new version to a small percentage of users first.

```
Users

↓

90%

↓

Version 1

-------------

10%

↓

Version 2
```

If monitoring shows no issues:

```
100%

↓

Version 2
```

---

# Benefits of Canary Deployments

- Reduced deployment risk
- Early bug detection
- Easy rollback
- Production testing

---

# Linear Deployment

Traffic increases gradually.

Example:

```
10%

↓

30%

↓

50%

↓

75%

↓

100%
```

Useful when additional confidence is required.

---

# All-at-Once Deployment

```
100%

↓

New Version
```

Advantages:

- Fast deployment

Disadvantages:

- Highest risk

Suitable only for:

- Development
- Low-risk applications

---

# Blue/Green Deployment

Two production environments exist simultaneously.

```
Blue

↓

Version 10

-----------------

Green

↓

Version 11
```

Traffic shifts from Blue to Green after validation.

---

# Blue/Green Workflow

```
Deploy Green

↓

Run Tests

↓

Shift Traffic

↓

Monitor

↓

Remove Blue
```

Rollback simply redirects traffic back to Blue.

---

# AWS CodeDeploy

AWS CodeDeploy automates Lambda deployments.

```
Developer

↓

CodeDeploy

↓

Traffic Shift

↓

Monitor

↓

Complete
```

It integrates with CloudWatch Alarms for automatic rollback.

---

# Deployment Configurations

Common CodeDeploy configurations:

| Strategy | Description |
|-----------|-------------|
| AllAtOnce | Immediate deployment |
| Canary | Small percentage first |
| Linear | Gradual traffic increase |

---

# Canary Example

```
Version 8

↓

90%

Version 9

↓

10%

↓

5 Minutes Later

↓

100%

Version 9
```

If alarms trigger during the canary period:

```
Automatic Rollback
```

---

# Linear Example

```
10%

↓

20%

↓

30%

↓

50%

↓

75%

↓

100%
```

Each step is monitored before continuing.

---

# CloudWatch Integration

```
Deployment

↓

CloudWatch Metrics

↓

Alarm?

↓

Yes

↓

Rollback
```

Metrics commonly monitored:

- Error Rate
- Duration
- Throttles
- 5XX Errors

---

# Automatic Rollback

If deployment health deteriorates:

```
Alarm

↓

Rollback

↓

Previous Version
```

No manual intervention required.

---

# Deployment Validation

Before increasing traffic:

Validate:

- API responses
- Error rates
- Memory usage
- Duration
- Business metrics

---

# AppSpec File

CodeDeploy uses an AppSpec file.

Example structure:

```yaml
version: 0.0

Resources:

- MyLambdaFunction:

    Type: AWS::Lambda::Function

    Properties:

      Name: payment-service

      Alias: production

      CurrentVersion: 14

      TargetVersion: 15
```

The AppSpec file tells CodeDeploy:

- Current version
- Target version
- Alias

---

# Pre-Traffic Validation

Optional validation Lambda:

```
Deploy

↓

Validation Function

↓

Pass?

↓

Yes

↓

Traffic Shift
```

Useful for:

- Smoke tests
- Health checks
- Database connectivity

---

# Post-Traffic Validation

After deployment:

```
Traffic Shift

↓

Monitor

↓

Health Check

↓

Complete
```

---

# Rollback Strategy

Good deployments always define rollback criteria.

Example:

```
Error Rate > 2%

↓

Rollback
```

Or:

```
Latency > 500 ms

↓

Rollback
```

---

# Deployment Pipeline

```
Developer

↓

GitHub

↓

GitHub Actions

↓

Build

↓

Test

↓

Deploy

↓

CodeDeploy

↓

Lambda

↓

CloudWatch

↓

Production
```

---

# Common Mistakes

## Deploying $LATEST to Production

Never invoke:

```
$LATEST
```

Always publish immutable versions.

---

## Skipping Monitoring

Deployment without monitoring is dangerous.

Always monitor:

- Errors
- Latency
- Memory
- Throttles

---

## No Rollback Plan

Every deployment should have:

```
Deployment

↓

Failure

↓

Automatic Rollback
```

---

# Best Practices

✅ Always publish versions.

✅ Use aliases instead of version numbers.

✅ Prefer Canary or Linear deployments.

✅ Integrate CloudWatch Alarms.

✅ Enable automatic rollback.

✅ Validate deployments before shifting all traffic.

✅ Never deploy directly to production.

---

# Real-World Architecture

```
Developer

↓

GitHub

↓

GitHub Actions

↓

AWS CodeDeploy

↓

Lambda Alias

↓

90% → Version 24

10% → Version 25

↓

CloudWatch

↓

Healthy?

↓

100% Version 25

↓

Production
```

---

# Senior Backend Engineering Perspective

Production deployments should prioritize reliability over speed.

Modern Lambda deployments rely on immutable versions, aliases, and progressive traffic shifting to minimize operational risk. Canary and Linear deployments provide opportunities to detect defects with a subset of production traffic before affecting all users.

For mission-critical workloads, deployment automation should integrate with CI/CD pipelines, CloudWatch alarms, and automated rollback mechanisms. This enables rapid releases while maintaining high availability and minimizing customer impact.

---

# Interview Questions

### Beginner

- What is a Lambda Version?
- What is a Lambda Alias?
- Why shouldn't `$LATEST` be used in production?

### Intermediate

- What is Weighted Routing?
- What is a Canary deployment?
- How does CodeDeploy automate Lambda deployments?

### Senior

- Design a zero-downtime deployment strategy for a payment API.
- How would you configure automatic rollback using CloudWatch?
- Compare Canary, Linear, and Blue/Green deployments.
- How would you safely deploy hundreds of Lambda functions across multiple AWS Regions?

---

# Key Takeaways

- Lambda Versions are immutable snapshots of function code and configuration.
- Aliases provide stable endpoints that can be redirected to different versions.
- Canary, Linear, and Blue/Green deployments reduce deployment risk by shifting traffic gradually.
- AWS CodeDeploy automates deployments, health monitoring, and rollback.
- A production-ready deployment strategy combines immutable versions, progressive traffic shifting, monitoring, and automated rollback to achieve safe, zero-downtime releases.