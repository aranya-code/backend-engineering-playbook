# 18- Lambda Environment Variables

# Introduction

Hardcoding configuration values directly into application code is considered a poor software engineering practice. It reduces flexibility, complicates deployments, and increases the risk of exposing sensitive information.

AWS Lambda provides **Environment Variables** to separate configuration from application logic. They allow developers to configure functions without modifying or redeploying the source code.

Environment variables are commonly used for:

- Database endpoints
- API URLs
- Feature flags
- Application settings
- Logging levels
- AWS resource names
- Third-party service endpoints

**Important:** Environment Variables are **not** a replacement for secrets management.

---

# Why Environment Variables?

Without environment variables:

```python
DATABASE_URL = "postgres://admin:password@prod-db.company.com"
```

Problems:

- Secrets in source code
- Different code for different environments
- Difficult deployments
- Security risks

With environment variables:

```python
DATABASE_URL = os.environ["DATABASE_URL"]
```

Configuration changes without changing application code.

---

# Architecture

```text
Developer

↓

Environment Variables

↓

Lambda Configuration

↓

Execution Environment

↓

Application Code
```

Lambda injects the variables into the runtime before executing your handler.

---

# How Environment Variables Work

When Lambda creates an execution environment:

```text
Create Environment

↓

Load Environment Variables

↓

Initialize Runtime

↓

Execute Handler
```

The variables become available through the operating system environment.

---

# Python Example

Configuration:

```
DATABASE_HOST = prod-db.amazonaws.com

LOG_LEVEL = INFO
```

Python:

```python
import os

host = os.environ["DATABASE_HOST"]

level = os.environ["LOG_LEVEL"]
```

---

# Accessing Variables Safely

Instead of:

```python
os.environ["API_URL"]
```

Use:

```python
os.getenv("API_URL")
```

Advantages:

- Avoids KeyError
- Allows default values

Example:

```python
url = os.getenv("API_URL", "https://localhost")
```

---

# Environment-Specific Configuration

Development

```text
DATABASE=db-dev

LOG_LEVEL=DEBUG
```

Production

```text
DATABASE=db-prod

LOG_LEVEL=ERROR
```

Same codebase.

Different configuration.

---

# Common Environment Variables

Examples include:

```text
DATABASE_HOST

DATABASE_PORT

REDIS_HOST

API_ENDPOINT

LOG_LEVEL

REGION

ENVIRONMENT

FEATURE_FLAG
```

---

# Feature Flags

Instead of deploying different versions:

```python
if os.getenv("NEW_PAYMENT_FLOW") == "true":
    use_new_payment()
else:
    use_old_payment()
```

Feature flags enable gradual rollouts.

---

# Logging Configuration

```python
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
```

Different environments can produce different logging verbosity.

---

# Database Configuration

Example:

```text
DB_HOST

DB_PORT

DB_NAME

DB_USER
```

Password should **not** be stored here.

Instead:

```
AWS Secrets Manager
```

---

# Environment Variables vs Secrets

Bad:

```text
DB_PASSWORD

API_SECRET

JWT_SECRET
```

Environment variables are encrypted at rest, but anyone with permission to view Lambda configuration can read them.

Sensitive credentials should be stored in:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store

---

# Encryption

AWS encrypts environment variables at rest using AWS KMS.

```text
Environment Variables

↓

KMS Encryption

↓

Stored Securely
```

During execution:

```text
Decrypt

↓

Inject into Runtime

↓

Application Access
```

---

# Customer Managed KMS Keys

Instead of using the default AWS-managed key:

```text
Lambda

↓

Customer Managed CMK

↓

Encrypted Variables
```

Benefits:

- Better auditing
- Key rotation
- Access control
- Compliance

---

# Secrets Manager Integration

Recommended architecture:

```text
Lambda

↓

Secrets Manager

↓

Retrieve Secret

↓

Cache

↓

Business Logic
```

This avoids storing sensitive credentials in configuration.

---

# Parameter Store Integration

AWS Systems Manager Parameter Store stores:

- Configuration
- Secure strings
- Feature flags
- Environment-specific settings

Example:

```text
Lambda

↓

Parameter Store

↓

Configuration

↓

Application
```

---

# Updating Environment Variables

Changing an environment variable updates the Lambda configuration.

However:

Existing warm execution environments may continue using the previous values until they are recycled.

New execution environments receive the updated configuration.

---

# Size Limits

AWS imposes a maximum combined size for all environment variables.

Current limit:

```
4 KB
```

Do not store:

- Certificates
- Large JSON documents
- Files

Instead use:

- S3
- Parameter Store
- Secrets Manager

---

# Configuration Example

```text
Production

↓

API_ENDPOINT

↓

https://api.company.com

↓

Lambda
```

Development

```text
API_ENDPOINT

↓

http://localhost:8000
```

Same application.

Different configuration.

---

# Reserved Variables

Lambda automatically provides several environment variables.

Examples include:

```text
AWS_REGION

AWS_EXECUTION_ENV

AWS_LAMBDA_FUNCTION_NAME

AWS_LAMBDA_FUNCTION_VERSION

AWS_LAMBDA_RUNTIME_API
```

Applications can use these to determine runtime information.

---

# Access Example

```python
import os

print(os.environ["AWS_REGION"])
```

Returns the Region where the function is running.

---

# Best Practices for Secrets

Bad:

```text
Environment Variable

↓

Database Password
```

Good:

```text
Environment Variable

↓

Secret Name

↓

Secrets Manager

↓

Retrieve Password
```

---

# Caching Secrets

Instead of requesting Secrets Manager every invocation:

```text
Lambda Starts

↓

Retrieve Secret

↓

Memory Cache

↓

Reuse
```

Reduces latency and API costs.

---

# Common Mistakes

## Hardcoding Configuration

Bad:

```python
BASE_URL = "https://prod.company.com"
```

Always externalize configuration.

---

## Storing Secrets

Avoid storing:

- Passwords
- API keys
- OAuth secrets
- Certificates

Use dedicated secret management services.

---

## Large Configuration

Environment variables should contain small configuration values.

Do not use them as configuration files.

---

# Best Practices

✅ Keep configuration outside application code.

✅ Store secrets in Secrets Manager.

✅ Use Parameter Store for application configuration.

✅ Use `os.getenv()` instead of direct indexing.

✅ Encrypt sensitive values with KMS.

✅ Keep environment variables small.

✅ Use feature flags for gradual deployments.

---

# Real-World Architecture

```text
Developer

↓

CI/CD Pipeline

↓

Lambda Configuration

↓

Environment Variables

↓

Business Logic

↓

Secrets Manager

↓

Amazon RDS
```

Configuration remains separate from credentials, improving security and maintainability.

---

# Environment Variables vs Parameter Store vs Secrets Manager

| Feature | Environment Variables | Parameter Store | Secrets Manager |
|----------|----------------------|-----------------|-----------------|
| Configuration | ✅ | ✅ | Limited |
| Password Storage | ❌ | ✅ (SecureString) | ✅ |
| Automatic Rotation | ❌ | ❌ | ✅ |
| KMS Encryption | ✅ | ✅ | ✅ |
| Runtime Retrieval | No | Yes | Yes |

---

# Senior Backend Engineering Perspective

Environment Variables follow one of the core principles of the **Twelve-Factor App**: **Store configuration in the environment**.

In production systems, environment variables should be limited to lightweight, non-sensitive configuration. Secrets belong in dedicated secret management services such as AWS Secrets Manager.

A common enterprise pattern is:

- Environment variables hold resource identifiers (e.g., Secret ARN, Parameter names).
- Secrets Manager stores credentials.
- Parameter Store stores application configuration.
- Lambda caches retrieved values during warm executions to reduce latency.

This approach provides security, flexibility, and operational simplicity while supporting multi-environment deployments.

---

# Interview Questions

### Beginner

- What are Lambda Environment Variables?
- How do you access them in Python?
- Why should configuration be externalized?

### Intermediate

- Are environment variables encrypted?
- Why shouldn't passwords be stored in environment variables?
- What is the size limit for Lambda environment variables?

### Senior

- How would you manage configuration across Development, QA, and Production?
- Compare Environment Variables, Parameter Store, and Secrets Manager.
- How would you securely rotate database credentials used by Lambda?
- How would you design configuration management for hundreds of Lambda functions?

---

# Key Takeaways

- Environment Variables separate configuration from application code, improving portability and maintainability.
- They are loaded into the Lambda execution environment during initialization and are available through the operating system environment.
- While encrypted at rest with AWS KMS, they are not intended for storing highly sensitive secrets.
- AWS Secrets Manager and Systems Manager Parameter Store provide more secure and scalable options for credentials and centralized configuration.
- Following the Twelve-Factor App principle and combining environment variables with dedicated secret management services results in secure, flexible, and production-ready serverless applications.