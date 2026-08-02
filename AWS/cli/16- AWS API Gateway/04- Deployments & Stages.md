# Deployments & Stages

## Overview

Creating an API is only the first step. Before clients can invoke it, the API must be **deployed** to a **Stage**.

A deployment is a snapshot of the API configuration at a specific point in time.

A stage is an environment that points to a deployment.

Typical environments include:

- Development
- Testing
- Staging
- Production

Using the AWS CLI, deployments and stages can be fully automated, making them ideal for CI/CD pipelines.

---

# Deployment Lifecycle

```text
API Changes

↓

Deployment

↓

Stage

↓

Invoke URL
```

Users always access a **Stage**, never the deployment directly.

---

# REST API Deployment Model

```text
REST API

↓

Deployment

↓

Stage

↓

Production Traffic
```

Each deployment represents a fixed version of the API.

---

# HTTP API Deployment Model

```text
HTTP API

↓

Stage

↓

Auto Deployment (Optional)
```

HTTP APIs support automatic deployment whenever changes are made.

---

# Create a Deployment (REST API)

```bash
aws apigateway create-deployment \
    --rest-api-id abc123
```

Example output:

```json
{
    "id": "deploy123",
    "createdDate": "2025-07-01T12:30:00Z"
}
```

Save the deployment ID.

---

# Create Deployment with Description

```bash
aws apigateway create-deployment \
    --rest-api-id abc123 \
    --description "Initial Production Deployment"
```

---

# Create Deployment for a Stage

```bash
aws apigateway create-deployment \
    --rest-api-id abc123 \
    --stage-name prod
```

If the stage doesn't exist, API Gateway creates it automatically.

---

# List Deployments

```bash
aws apigateway get-deployments \
    --rest-api-id abc123
```

Example:

```json
{
    "items": [
        {
            "id": "deploy123"
        }
    ]
}
```

---

# View Deployment Details

```bash
aws apigateway get-deployment \
    --rest-api-id abc123 \
    --deployment-id deploy123
```

---

# Delete Deployment

```bash
aws apigateway delete-deployment \
    --rest-api-id abc123 \
    --deployment-id deploy123
```

A deployment cannot be deleted if an active stage references it.

---

# Create a Stage

```bash
aws apigateway create-stage \
    --rest-api-id abc123 \
    --deployment-id deploy123 \
    --stage-name dev
```

Example:

```text
Stage

↓

dev
```

---

# List Stages

```bash
aws apigateway get-stages \
    --rest-api-id abc123
```

---

# View Stage

```bash
aws apigateway get-stage \
    --rest-api-id abc123 \
    --stage-name prod
```

---

# Delete Stage

```bash
aws apigateway delete-stage \
    --rest-api-id abc123 \
    --stage-name dev
```

---

# Stage Architecture

```text
REST API

│

├── dev

├── test

├── staging

└── prod
```

Each stage can point to a different deployment.

---

# Update a Stage

```bash
aws apigateway update-stage \
    --rest-api-id abc123 \
    --stage-name prod \
    --patch-operations op=replace,path=/description,value="Production"
```

---

# Configure Stage Variables

Example:

```bash
aws apigateway update-stage \
    --rest-api-id abc123 \
    --stage-name prod \
    --patch-operations op=replace,path=/variables/backend,value=production
```

Retrieve stage:

```bash
aws apigateway get-stage \
    --rest-api-id abc123 \
    --stage-name prod
```

---

# Enable CloudWatch Logging

```bash
aws apigateway update-stage \
    --rest-api-id abc123 \
    --stage-name prod \
    --patch-operations \
    op=replace,path=/*/*/logging/loglevel,value=INFO
```

---

# Enable Metrics

```bash
aws apigateway update-stage \
    --rest-api-id abc123 \
    --stage-name prod \
    --patch-operations \
    op=replace,path=/*/*/metrics/enabled,value=true
```

CloudWatch metrics become available immediately.

---

# Enable X-Ray Tracing

```bash
aws apigateway update-stage \
    --rest-api-id abc123 \
    --stage-name prod \
    --patch-operations \
    op=replace,path=/tracingEnabled,value=true
```

---

# Configure Throttling

Example:

```bash
aws apigateway update-stage \
    --rest-api-id abc123 \
    --stage-name prod \
    --patch-operations \
    op=replace,path=/*/*/throttling/rateLimit,value=100
```

---

# Enable Caching

```bash
aws apigateway update-stage \
    --rest-api-id abc123 \
    --stage-name prod \
    --cache-cluster-enabled
```

Caching is supported only for REST APIs.

---

# HTTP API Stages

Create:

```bash
aws apigatewayv2 create-stage \
    --api-id xyz789 \
    --stage-name prod \
    --auto-deploy
```

Example output:

```json
{
    "StageName": "prod",
    "AutoDeploy": true
}
```

---

# List HTTP API Stages

```bash
aws apigatewayv2 get-stages \
    --api-id xyz789
```

---

# Update HTTP API Stage

```bash
aws apigatewayv2 update-stage \
    --api-id xyz789 \
    --stage-name prod \
    --auto-deploy
```

---

# Disable Auto Deploy

```bash
aws apigatewayv2 update-stage \
    --api-id xyz789 \
    --stage-name prod \
    --no-auto-deploy
```

---

# Invoke URL

REST API:

```text
https://abc123.execute-api.us-east-1.amazonaws.com/prod
```

HTTP API:

```text
https://xyz789.execute-api.us-east-1.amazonaws.com
```

Routes are appended to the stage URL.

---

# Deployment Pipeline

```text
Developer

↓

Git Push

↓

Build

↓

Deploy API

↓

Update Stage

↓

Production
```

This process is typically automated using CI/CD.

---

# Automation Example

```bash
API_ID=abc123

aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod
```

---

# Common Errors

## Stage Not Found

Verify:

```bash
aws apigateway get-stages \
    --rest-api-id abc123
```

---

## Deployment Not Found

List deployments:

```bash
aws apigateway get-deployments \
    --rest-api-id abc123
```

---

## Changes Not Visible

REST APIs require a new deployment after modifying resources or methods.

Redeploy:

```bash
aws apigateway create-deployment \
    --rest-api-id abc123 \
    --stage-name prod
```

---

## AccessDeniedException

Verify:

- IAM permissions
- AWS credentials
- AWS profile
- Region

---

# CLI Best Practices

- Use separate stages for development, testing, and production.
- Enable CloudWatch Logs and Metrics for production stages.
- Enable X-Ray tracing for distributed debugging.
- Use stage variables sparingly and prefer environment variables where appropriate.
- Automate deployments using CI/CD.
- Never make manual production changes without version control.

---

# Common Interview Questions

### What is the difference between a deployment and a stage?

A deployment is an immutable snapshot of the API configuration. A stage is an environment (such as `dev` or `prod`) that points to a specific deployment.

---

### Why are stages useful?

Stages allow the same API to have multiple environments with independent configurations, enabling safe testing before production releases.

---

### Why do REST APIs require deployments after changes?

REST APIs do not automatically publish configuration changes. Creating a new deployment captures the latest API configuration and makes it available through a stage.

---

### What is Auto Deploy in HTTP APIs?

Auto Deploy automatically publishes configuration changes to a stage, eliminating the need to manually create deployments after every update.

---

### Why enable CloudWatch Logs and X-Ray on stages?

CloudWatch Logs provide visibility into requests and errors, while AWS X-Ray enables distributed tracing to diagnose latency and backend issues.

---

# Key Takeaways

- Deployments capture immutable snapshots of REST API configurations.
- Stages provide environment-specific access to deployments and support independent settings.
- HTTP APIs support automatic deployments, while REST APIs require manual deployment after changes.
- CloudWatch logging, metrics, X-Ray tracing, caching, and throttling are configured at the stage level.
- Automating deployments and stage management is essential for reliable CI/CD pipelines and production operations.