# Deployments, Stages & Stage Variables

## Overview

Creating an API in Amazon API Gateway is only the first step. Changes made to an API are **not automatically available to users**.

Before clients can access new or updated APIs, you must:

1. Create or modify the API
2. Deploy the API
3. Deploy it to a Stage

Stages allow multiple versions of the same API (such as Development, Testing, and Production) to coexist independently.

---

# Deployment Workflow

The deployment process in API Gateway is straightforward.

```text
Create API

↓

Modify Resources

↓

Configure Methods

↓

Create Deployment

↓

Deploy to Stage

↓

Clients Access API
```

Every time you make changes to an API, you must create a **new deployment** for those changes to become available.

---

# What is a Deployment?

A deployment is a **snapshot** of your API configuration at a specific point in time.

It includes:

- Resources
- Methods
- Integrations
- Authorizers
- Request Validation
- Models
- Mapping Templates
- Configuration

Think of a deployment as taking a photograph of your API.

```text
API Configuration

↓

Take Snapshot

↓

Deployment Created
```

Future changes to the API do **not** affect existing deployments until a new deployment is created.

---

# Why Deployments Are Needed

Suppose you modify an API.

Before:

```http
GET /products
```

Returns:

```json
[
    {
        "id":1,
        "name":"Laptop"
    }
]
```

Now you add:

```http
POST /products
```

The POST endpoint is **not available** until you deploy the API again.

Without deployment:

```text
Changes Saved

❌ Not Live
```

After deployment:

```text
Changes Saved

↓

Deployment

↓

Users Can Access
```

---

# What is a Stage?

A **Stage** is a named environment that points to a deployment.

Common stages include:

```text
dev

test

staging

production
```

Each stage represents a different environment.

---

# Stage Architecture

```text
                 API
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
    dev         test       production
      │           │             │
      ▼           ▼             ▼
Deployment A Deployment B Deployment C
```

Each stage can reference a different deployment.

---

# Stage URLs

Every stage receives its own endpoint.

Example:

```text
Development

https://abc123.execute-api.us-east-1.amazonaws.com/dev
```

Testing

```text
https://abc123.execute-api.us-east-1.amazonaws.com/test
```

Production

```text
https://abc123.execute-api.us-east-1.amazonaws.com/prod
```

Although the API ID is the same, the stage determines which deployment serves requests.

---

# Why Use Multiple Stages?

Different environments serve different purposes.

| Stage | Purpose |
|---------|----------|
| dev | Development and debugging |
| test | Automated and manual testing |
| staging | Production-like validation |
| production | Live customer traffic |

This separation reduces the risk of deploying unfinished features directly to production.

---

# Example Deployment Lifecycle

```text
Developer

↓

Adds New Endpoint

↓

Deploy

↓

Development Stage

↓

Testing

↓

Deploy Again

↓

Production Stage
```

Each deployment can be promoted through environments after validation.

---

# Stage Variables

Stage Variables allow you to store configuration values that differ between environments.

Instead of hardcoding values into the API, you reference stage-specific variables.

---

# Example

Development stage:

```text
LambdaFunction

ProductService-Dev
```

Production stage:

```text
LambdaFunction

ProductService-Prod
```

The API configuration remains the same, while the stage determines which value is used.

---

# Stage Variable Syntax

Variables are referenced using:

```text
${stageVariables.variableName}
```

Example:

```text
${stageVariables.lambdaAlias}
```

or

```text
${stageVariables.backendUrl}
```

---

# Common Stage Variables

Examples include:

```text
backendUrl

lambdaAlias

environment

apiVersion

featureFlag

databaseEndpoint
```

---

# Stage Variable Example

Development

```text
backendUrl

https://dev-api.company.com
```

Production

```text
backendUrl

https://api.company.com
```

Integration:

```text
https://${stageVariables.backendUrl}
```

API Gateway automatically substitutes the correct value based on the active stage.

---

# Lambda Alias Example

Suppose you have Lambda aliases.

```text
ProductService

├── DEV
├── TEST
└── PROD
```

Stage Variables

Development

```text
lambdaAlias = DEV
```

Testing

```text
lambdaAlias = TEST
```

Production

```text
lambdaAlias = PROD
```

API Gateway invokes the correct Lambda alias without changing the API configuration.

---

# Stage-Level Configuration

Each stage can have independent settings.

Examples include:

- Logging
- CloudWatch Metrics
- X-Ray Tracing
- Throttling
- Caching
- Stage Variables
- Canary Deployment
- Access Logs

This allows production and development environments to behave differently.

---

# Stage-Level Logging

Development

```text
Detailed Logs

Enabled
```

Production

```text
Error Logs Only

Enabled
```

This reduces logging costs while preserving useful debugging information in development.

---

# Stage-Level Throttling

Development

```text
50 Requests/Second
```

Production

```text
5000 Requests/Second
```

Each environment can enforce different traffic limits.

---

# Stage-Level Caching

Development

```text
Disabled
```

Production

```text
Enabled
```

Caching is commonly enabled only in production to improve performance and reduce backend load.

---

# Stage-Level Canary Deployments

Stages support canary releases.

Example:

```text
90%

↓

Version 1

10%

↓

Version 2
```

Only a small percentage of users receive the new deployment.

If problems occur, rollback is simple.

---

# Deployment vs Stage

| Deployment | Stage |
|------------|-------|
| Snapshot of API configuration | Named environment |
| Immutable | Mutable |
| Created after API changes | References a deployment |
| Multiple deployments possible | Multiple stages possible |

Think of it this way:

```text
Deployment

↓

"What version?"

---------------------

Stage

↓

"Where is it running?"
```

---

# Real-World Example

An online shopping platform has three environments.

```text
Developer

↓

Development Stage

↓

QA Testing

↓

Staging Stage

↓

Production Approval

↓

Production Stage
```

Each environment points to a different deployment.

Production remains stable while developers continue making changes.

---

# Common Mistakes

### Forgetting to Deploy

Making API changes without creating a new deployment.

Result:

```text
Changes Saved

↓

Users Cannot See Them
```

---

### Using One Stage for Everything

Bad:

```text
production
```

Only one stage exists.

Any deployment immediately affects customers.

---

### Hardcoding Environment Values

Bad:

```text
Lambda ARN

Database URL

API Endpoint
```

Instead, use Stage Variables whenever possible.

---

# Interview Questions

### What is the difference between a Deployment and a Stage?

**Answer:**

A Deployment is a snapshot of an API configuration. A Stage is a named environment (such as `dev`, `test`, or `prod`) that points to a specific deployment.

---

### Do API changes become live immediately?

**Answer:**

No. API changes become available only after creating a new deployment and associating it with a stage.

---

### Why are Stage Variables useful?

**Answer:**

They allow environment-specific configuration without changing the API itself. The same API can behave differently in development, testing, and production.

---

### Can multiple stages point to different deployments?

**Answer:**

Yes. This enables different versions of an API to exist simultaneously across environments.

---

# Best Practices

- Create separate stages for development, testing, staging, and production.
- Never test new features directly in production.
- Use Stage Variables instead of hardcoded values.
- Enable detailed logging only in non-production environments when practical.
- Enable caching and higher throttling limits primarily in production.
- Use canary deployments to reduce deployment risk.
- Always create a new deployment after modifying API resources or methods.

---

# Key Takeaways

- A **Deployment** is an immutable snapshot of an API configuration.
- A **Stage** is a named environment that points to a deployment.
- API changes are not visible until a new deployment is created.
- Stage Variables enable environment-specific configuration without modifying the API.
- Each stage can have independent settings for logging, caching, throttling, tracing, and canary deployments.
- Using separate stages is essential for safe and reliable API delivery.