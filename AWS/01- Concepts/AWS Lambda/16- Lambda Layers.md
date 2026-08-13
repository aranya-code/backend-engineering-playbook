# 16- Lambda Layers

# Introduction

As serverless applications grow, developers often find themselves copying the same dependencies into multiple Lambda functions.

For example:

- boto3 utilities
- Database drivers
- Logging libraries
- Authentication modules
- Shared business logic

This leads to:

- Larger deployment packages
- Duplicate code
- Difficult maintenance
- Longer deployment times

AWS Lambda Layers solve this problem by allowing common code and dependencies to be packaged separately and shared across multiple Lambda functions.

---

# What is a Lambda Layer?

A Lambda Layer is a ZIP archive that contains code, libraries, custom runtimes, or other dependencies that can be attached to one or more Lambda functions.

Instead of packaging dependencies with every function:

```text
Lambda A

├── Code
├── boto3
├── requests
└── psycopg2

Lambda B

├── Code
├── boto3
├── requests
└── psycopg2
```

You create one shared layer.

```text
Layer

├── boto3
├── requests
└── psycopg2

        │

────────┼────────

        │

Lambda A

Lambda B

Lambda C
```

---

# Why Use Layers?

Without Layers:

- Every Lambda package contains duplicate dependencies.
- Larger deployment artifacts.
- More storage consumption.
- Slower deployments.

With Layers:

- Shared dependencies
- Smaller deployment packages
- Easier maintenance
- Version management

---

# Architecture

```text
Application Code

        │

        ▼

Lambda Function

        │

        ▼

Attached Layers

        │

        ▼

Execution Environment
```

The Lambda runtime merges the function code and attached layers into a single execution environment.

---

# Layer Contents

A Lambda Layer can contain:

- Python packages
- Node.js modules
- Java JAR files
- Native libraries
- Shared utility code
- Custom runtimes
- Certificates
- Configuration files

---

# Typical Use Cases

## Shared Utilities

```text
Layer

↓

Logging Module

↓

Authentication Module

↓

Validation Utilities
```

---

## Database Drivers

Instead of packaging:

```
psycopg2
```

inside every Lambda,

Create:

```
Database Layer
```

---

## Machine Learning Libraries

Large libraries such as:

- NumPy
- Pandas
- SciPy

can be placed inside a dedicated layer.

---

## Organization-wide SDK

Many enterprises create a common layer containing:

```
Company Logger

↓

Monitoring SDK

↓

Error Handler

↓

Authentication Client
```

Every Lambda uses the same implementation.

---

# Layer Structure

Python Layers require a specific directory structure.

Example:

```text
python/

└── lib/

    └── python3.13/

        └── site-packages/

            ├── requests/

            ├── boto3/

            └── urllib3/
```

AWS automatically adds this path to `PYTHONPATH`.

---

# Multiple Layers

A Lambda function can attach multiple layers.

Example:

```text
Lambda

│

├── Monitoring Layer

├── Database Layer

├── Authentication Layer

└── Business Utilities
```

AWS combines all layers during execution.

---

# Maximum Number of Layers

Each Lambda function can have:

```
Maximum 5 Layers
```

Choose layers carefully to avoid unnecessary complexity.

---

# Layer Versions

Layers are immutable.

Every update creates a new version.

Example:

```text
Logging Layer

↓

Version 1

↓

Version 2

↓

Version 3
```

Lambda functions explicitly reference a version.

---

# Sharing Layers

Layers can be:

- Private
- Shared within an AWS account
- Shared across AWS accounts
- Public

Public layers are commonly used for open-source libraries.

---

# Permissions

Layer access is controlled using resource-based policies.

Example:

```
Account A

↓

Publishes Layer

↓

Allows Account B

↓

Account B Uses Layer
```

---

# Layer Size Limits

Current limits (subject to AWS updates):

- ZIP upload limits apply.
- Combined unzipped size of the function and all attached layers must remain within Lambda deployment limits.

Always check the latest AWS documentation for current limits.

---

# Execution Flow

```text
Invoke Lambda

↓

Download Function

↓

Download Layers

↓

Merge File Systems

↓

Initialize Runtime

↓

Execute Handler
```

The function sees layer contents as part of its execution environment.

---

# Python Example

Suppose a layer contains:

```python
logger.py
```

Lambda code:

```python
from logger import log

def handler(event, context):

    log("Processing request")
```

No additional packaging is required.

---

# Common Layer Types

| Layer | Purpose |
|--------|----------|
| Logging | Centralized logging |
| Monitoring | Metrics & tracing |
| Database | Drivers |
| Security | Authentication |
| Utilities | Shared helper functions |
| ML | AI libraries |

---

# Benefits

✅ Smaller deployment packages

✅ Shared dependencies

✅ Easier maintenance

✅ Faster deployments

✅ Version management

✅ Code reuse

---

# Limitations

- Maximum five layers
- Version management required
- Additional initialization time if layers are very large
- Layer compatibility must match the runtime

---

# Common Mistakes

## Putting Business Logic in Layers

Layers should contain:

- Shared libraries
- Utilities
- Framework code

Avoid placing application-specific business logic inside a shared layer.

---

## Creating Too Many Layers

Bad:

```
Logger Layer

Validator Layer

String Layer

Math Layer

Date Layer
```

Better:

```
Common Utilities Layer
```

---

## Updating Existing Versions

Layer versions are immutable.

Updating code requires publishing a new version.

---

# Best Practices

✅ Group related dependencies into a single layer.

✅ Version layers carefully.

✅ Remove unused libraries.

✅ Keep layers as small as possible.

✅ Use layers for organization-wide utilities.

✅ Test compatibility before upgrading layer versions.

---

# Real-World Example

Microservices architecture:

```text
Common Logging Layer

        │

────────┼────────

        │

Order Lambda

Payment Lambda

User Lambda

Notification Lambda
```

Every service shares identical logging behavior.

---

# Layers vs Deployment Package

| Feature | Deployment Package | Layer |
|----------|-------------------|-------|
| Function Code | ✅ | ❌ |
| Shared Libraries | Optional | ✅ |
| Versioned Separately | ❌ | ✅ |
| Reusable | ❌ | ✅ |
| Shared Across Functions | ❌ | ✅ |

---

# Layers vs Container Images

| Feature | Layers | Container Images |
|----------|--------|------------------|
| Maximum Layers | 5 | Not Applicable |
| Dependency Sharing | Excellent | Built into Image |
| Package Size | Smaller | Can be much larger |
| Best For | Shared Libraries | Complex Applications |

---

# Senior Backend Engineering Perspective

Lambda Layers are a software engineering tool rather than merely an AWS feature.

They promote:

- Code reuse
- Standardization
- Maintainability
- Separation of concerns

In enterprise environments, common libraries for logging, monitoring, authentication, security, and database access are frequently distributed through versioned layers.

However, engineers should avoid overusing layers. Excessive layering increases operational complexity and can complicate version management. Layers should contain reusable infrastructure code—not business-specific logic.

---

# Interview Questions

### Beginner

- What is a Lambda Layer?
- Why are Lambda Layers used?
- How many layers can be attached to a Lambda function?

### Intermediate

- Can multiple Lambda functions share the same layer?
- Why are layer versions immutable?
- What types of content belong in a layer?

### Senior

- How would you structure layers for a microservices platform?
- When would you choose Layers instead of packaging dependencies with each function?
- What challenges arise when updating shared layers across hundreds of Lambda functions?
- Compare Lambda Layers with container images from an architectural perspective.

---

# Key Takeaways

- Lambda Layers allow dependencies and shared code to be packaged separately from application code.
- Layers improve code reuse, reduce deployment package size, and simplify maintenance across multiple Lambda functions.
- A Lambda function can attach up to five layers, and each layer is versioned independently.
- Layers are ideal for shared libraries, monitoring agents, authentication utilities, and database drivers—but not for application-specific business logic.
- Proper layer design improves maintainability while keeping serverless applications modular and consistent.