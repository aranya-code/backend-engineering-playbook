# Canary Deployments

## Overview

Deploying a new API version directly to all users is risky. A small bug can immediately impact every client and potentially cause outages.

Amazon API Gateway supports **Canary Deployments**, allowing you to release new API versions to a **small percentage of traffic** before rolling them out completely.

Instead of exposing all users to the new deployment:

- 90% of traffic can continue using the stable version.
- 10% of traffic is routed to the new version.

If the new deployment performs well, the percentage can gradually increase until all traffic uses the new version.

Canary deployments reduce deployment risk and enable safer production releases.

---

# Why Canary Deployments?

Traditional deployment:

```text
Users

↓

New Deployment

↓

100% Traffic

↓

Production
```

If the deployment contains a bug:

```text
100% Users

↓

Affected
```

With Canary Deployment:

```text
Users

↓

90% Stable

10% Canary

↓

Monitor

↓

Promote
```

Only a small percentage of users are initially affected.

---

# Architecture

```text
                 Users

                    │

                    ▼

          Amazon API Gateway

                    │

        ┌───────────┴───────────┐

        ▼                       ▼

 Stable Deployment      Canary Deployment

      90% Traffic           10% Traffic
```

Traffic is automatically split by API Gateway.

---

# Deployment Flow

```text
Current Version

↓

Deploy Canary

↓

Route Small Traffic

↓

Monitor

↓

Successful?

│

├── Yes

│      │

│      ▼

│ Increase Traffic

│

└── No

       │

       ▼

Rollback
```

---

# Traffic Distribution

Example configuration:

```text
Stable

90%

--------------------

Canary

10%
```

Incoming requests:

```text
100 Requests

↓

90 Stable

10 Canary
```

Users are automatically distributed.

---

# Gradual Rollout

A common rollout strategy:

```text
Version 1

↓

5%

↓

10%

↓

25%

↓

50%

↓

100%
```

Confidence increases with each stage.

---

# Rollback

If problems are detected:

```text
Errors

↓

Rollback

↓

100%

Stable Version
```

Rollback is immediate because the stable deployment remains active.

---

# Canary Settings

API Gateway supports configuring:

- Traffic percentage
- Stage variables
- Stage overrides

These allow the canary deployment to use different configuration values from the production deployment.

---

# Stage Variables

Canary deployments can override stage variables.

Example:

Stable:

```text
backend

↓

v1
```

Canary:

```text
backend

↓

v2
```

Both deployments share the same stage while using different backend configurations.

---

# Lambda Alias Example

Stable deployment:

```text
OrderService

↓

Alias

↓

prod
```

Canary deployment:

```text
OrderService

↓

Alias

↓

v2
```

Only canary traffic invokes the new Lambda alias.

---

# Backend Example

```text
API Gateway

│

├────────► ECS v1

│

└────────► ECS v2
```

Only a percentage of requests reach the new service.

---

# Monitoring Canary Deployments

Monitor:

- Error Rate
- Latency
- Integration Latency
- 4XX Errors
- 5XX Errors
- Backend Logs

CloudWatch dashboards are commonly used during rollout.

---

# CloudWatch Metrics

Useful metrics include:

- Count
- Latency
- IntegrationLatency
- 4XXError
- 5XXError
- CacheHitCount
- CacheMissCount

Compare stable and canary performance before increasing traffic.

---

# Canary vs Blue-Green Deployment

| Canary | Blue-Green |
|----------|------------|
| Gradual rollout | Complete environment switch |
| Small traffic percentage | Entire traffic moved |
| Lower deployment risk | Faster cutover |
| Easy monitoring | Easy rollback |

Canary minimizes risk, while Blue-Green minimizes downtime.

---

# Canary vs Rolling Deployment

| Canary | Rolling |
|----------|----------|
| Traffic-based | Instance-based |
| API Gateway controls routing | Infrastructure controls rollout |
| Ideal for APIs | Ideal for servers and containers |

---

# Advantages

## Reduced Risk

Only a small number of users experience the new deployment initially.

---

## Easy Rollback

The stable deployment remains active.

---

## Real Production Testing

Real users exercise the new version.

---

## Improved Reliability

Problems are detected before affecting all users.

---

## Gradual Confidence

Traffic increases only after verifying application health.

---

# Limitations

Canary deployments:

- Require monitoring
- Add operational complexity
- May require backend version compatibility
- Need careful testing of database changes

---

# Real-World Example

A payment API introduces a new fraud detection algorithm.

Deployment:

```text
95%

Old Version

----------------------

5%

New Version
```

Monitoring shows:

- Error rate unchanged
- Latency improved

Traffic gradually increases to:

```text
25%

↓

50%

↓

100%
```

The deployment completes without downtime.

---

# Best Practices

- Start with a small percentage (5–10%).
- Monitor CloudWatch metrics continuously.
- Keep stable and canary deployments backward compatible.
- Use Lambda aliases or versioned backends.
- Roll back immediately if error rates increase.
- Increase traffic gradually rather than jumping directly to 100%.
- Automate deployments using CI/CD pipelines.

---

# Common Interview Questions

### What is a Canary Deployment?

A Canary Deployment gradually releases a new API version to a small percentage of users while the remaining traffic continues using the stable version.

---

### Why use Canary Deployments?

They reduce deployment risk by exposing only a small portion of users to the new version before a full rollout.

---

### How does API Gateway split traffic?

API Gateway routes a configurable percentage of requests to the canary deployment while sending the remaining requests to the stable deployment.

---

### What should be monitored during a Canary Deployment?

Key metrics include:

- Error Rate
- Latency
- 4XX Errors
- 5XX Errors
- Backend Logs
- CloudWatch Metrics

---

### What happens if the Canary deployment fails?

Traffic can immediately be redirected back to the stable deployment by disabling the canary, minimizing user impact.

---

# Key Takeaways

- Canary Deployments allow gradual API releases by routing only a percentage of traffic to a new deployment.
- They significantly reduce deployment risk and enable rapid rollback.
- API Gateway supports traffic splitting, stage variable overrides, and canary-specific configuration.
- Continuous monitoring with CloudWatch is essential during rollout.
- Canary Deployments are a production best practice for safely releasing new API versions with minimal customer impact.