# Deployment & Stage Issues

## Overview

One of the most common reasons an API behaves unexpectedly is that the latest changes have **not been deployed** or are being served from the **wrong stage**.

Many engineers spend hours debugging Lambda functions or backend services when the real issue is simply that API Gateway is serving an older deployment.

This chapter covers the most common deployment and stage-related issues, explains why they occur, and demonstrates how to resolve them.

---

# Deployment Architecture

```text
API

↓

Deployment

↓

Stage

↓

Client
```

Clients always invoke a **Stage**, never the deployment directly.

---

# Common Deployment Problems

| Problem | Typical Error |
|----------|---------------|
| Changes Not Visible | Old Response |
| Stage Not Found | 404 |
| Missing Deployment | 500 |
| Wrong Stage URL | 404 |
| Stage Variables Incorrect | Backend Failure |
| Deployment Failed | Deployment Error |

---

# Changes Not Visible

## Symptoms

You updated:

- Routes
- Lambda
- Integrations

but clients still receive the old response.

---

## Common Cause

REST APIs require a new deployment.

Updating resources alone is **not enough**.

---

## Diagnose

Review:

```text
API

↓

Deployments

↓

Latest Deployment
```

---

## Solution

Create a new deployment.

```bash
aws apigateway create-deployment \
--rest-api-id abc123 \
--stage-name prod
```

---

# Wrong Stage URL

Example

Actual Stage:

```text
prod
```

Client uses:

```text
production
```

---

## Symptoms

```http
404 Not Found
```

or

```json
{
"message":"Missing Authentication Token"
}
```

---

## Solution

Verify the stage name.

Correct URL:

```text
https://api-id.execute-api.us-east-1.amazonaws.com/prod
```

---

# Stage Does Not Exist

## Symptoms

```http
404 Not Found
```

---

## Diagnose

```bash
aws apigateway get-stages \
--rest-api-id abc123
```

---

## Solution

Create the stage.

```bash
aws apigateway create-stage \
--rest-api-id abc123 \
--deployment-id deploy123 \
--stage-name prod
```

---

# Missing Deployment

## Symptoms

Stage exists

↓

Deployment missing

↓

Requests fail

---

## Diagnose

```bash
aws apigateway get-deployments \
--rest-api-id abc123
```

---

## Solution

Create a deployment.

---

# Deployment Deleted

Example

```text
Deployment

↓

Deleted

↓

Stage still references it
```

---

## Symptoms

Unexpected API behavior.

---

## Solution

Create a new deployment.

Update the stage.

---

# Stage Variables Incorrect

Example

Expected:

```text
Backend

↓

Production
```

Actual:

```text
Backend

↓

Development
```

---

## Symptoms

Requests reach the wrong backend.

---

## Diagnose

```bash
aws apigateway get-stage \
--rest-api-id abc123 \
--stage-name prod
```

Review:

```text
variables
```

---

## Solution

Update stage variables.

---

# Wrong Lambda Alias

Example

Configured:

```text
Lambda

↓

dev
```

Expected:

```text
Lambda

↓

prod
```

---

## Symptoms

Production API executes development code.

---

## Solution

Update:

- Stage Variables
- Lambda Alias
- Integration URI

---

# HTTP API Auto Deploy Disabled

Example

```text
Auto Deploy

↓

Disabled
```

---

## Symptoms

Recent route changes not visible.

---

## Diagnose

```bash
aws apigatewayv2 get-stage \
--api-id xyz789 \
--stage-name prod
```

Review:

```text
AutoDeploy
```

---

## Solution

Enable:

```bash
aws apigatewayv2 update-stage \
--api-id xyz789 \
--stage-name prod \
--auto-deploy
```

---

# Wrong Deployment Environment

Example

Developer deployed to:

```text
dev
```

Expected:

```text
prod
```

---

## Symptoms

Production unchanged.

---

## Solution

Verify deployment target before deployment.

---

# Custom Domain Points to Wrong Stage

Example

```text
api.company.com

↓

staging
```

instead of

```text
prod
```

---

## Symptoms

Unexpected responses.

Wrong API version.

---

## Diagnose

Review:

API Mapping

↓

Stage

---

## Solution

Update API Mapping.

---

# Stage Cache Not Refreshed

Symptoms

Old responses continue after deployment.

---

## Common Cause

Cached response.

---

## Solution

Flush cache.

Or disable caching temporarily.

---

# Canary Deployment Misconfigured

Traffic split:

```text
90%

↓

Production

10%

↓

New Version
```

---

## Symptoms

Some users receive different responses.

---

## Diagnose

Review:

Stage

↓

Canary Settings

---

## Solution

Update traffic percentage.

Or disable Canary Deployment.

---

# Stage Logging Disabled

Symptoms

Unable to troubleshoot.

---

## Diagnose

Stage Configuration

↓

CloudWatch Logs

↓

Disabled

---

## Solution

Enable:

- Execution Logs
- Access Logs
- Metrics

---

# X-Ray Disabled

Symptoms

Cannot trace requests.

---

## Solution

Enable:

```text
Stage

↓

Tracing

↓

Enabled
```

---

# Incorrect Stage Permissions

Example

IAM policy allows:

```text
dev
```

Client accesses:

```text
prod
```

---

## Symptoms

```http
403 Forbidden
```

---

## Solution

Update IAM permissions.

---

# API Mapping Missing

Custom domain:

```text
api.company.com
```

↓

No mapping

↓

404

---

## Diagnose

Review:

Custom Domain

↓

API Mapping

---

## Solution

Create the API Mapping.

---

# Deployment Automation Failure

CI/CD pipeline:

```text
Build

↓

Success

↓

Deployment

↓

Skipped
```

---

## Symptoms

Old API remains active.

---

## Solution

Verify pipeline:

- Deployment Step
- AWS Credentials
- Region
- API ID

---

# Debugging Workflow

```text
Client

↓

Correct URL?

↓

Correct Stage?

↓

Latest Deployment?

↓

Stage Variables?

↓

API Mapping?

↓

Backend

↓

Fixed
```

---

# Useful AWS Services

Use:

- CloudWatch Logs
- CloudWatch Metrics
- CloudTrail
- API Gateway Console
- AWS CLI

---

# Production Checklist

Verify:

- Latest deployment created
- Correct stage
- Correct deployment
- Stage variables
- Lambda alias
- Auto Deploy
- API Mapping
- Custom Domain
- CloudWatch Logs
- X-Ray
- Cache status
- Canary settings

---

# Common Interview Questions

### Why are API changes not visible after updating resources?

For REST APIs, configuration changes are not automatically published. A new deployment must be created and associated with the stage before clients can access the updated API.

---

### What is the difference between a deployment and a stage?

A deployment is an immutable snapshot of the API configuration, while a stage is an environment (such as `dev`, `staging`, or `prod`) that points to a specific deployment.

---

### Why does a custom domain return the wrong API version?

The custom domain may be mapped to the wrong stage or API. Reviewing API Mappings usually identifies the issue.

---

### What problems can stage variables cause?

Incorrect stage variables can route requests to the wrong backend, Lambda alias, or environment, leading to unexpected behavior even though the API itself is functioning correctly.

---

### How do HTTP APIs differ from REST APIs regarding deployments?

HTTP APIs support **Auto Deploy**, allowing configuration changes to be published automatically. REST APIs require an explicit deployment after every configuration change.

---

# Key Takeaways

- REST APIs require explicit deployments before configuration changes become available.
- Stages determine which deployment clients access and can have independent settings such as variables, logging, and caching.
- Incorrect stage names, stale deployments, or misconfigured stage variables are common causes of production issues.
- Custom domains and API mappings should always be verified when troubleshooting unexpected responses.
- Automating deployments and validating stage configuration in CI/CD pipelines reduces deployment-related production incidents.