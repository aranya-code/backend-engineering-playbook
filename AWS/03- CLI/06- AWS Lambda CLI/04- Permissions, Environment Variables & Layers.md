# Permissions, Environment Variables & Layers

> Learn how AWS Lambda securely accesses AWS services using IAM permissions, manages configuration through environment variables, shares code using Lambda Layers, and protects sensitive data. This chapter covers Execution Roles, Resource-based Policies, Environment Variables, Layers, Secrets Manager integration, and production security best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Lambda permissions
- Configure IAM Execution Roles
- Configure Resource-based Policies
- Manage Environment Variables
- Use Lambda Layers
- Store secrets securely
- Share code across functions
- Apply production security practices

---

# Lambda Security Architecture

Every Lambda function operates under an IAM Role.

```text
Lambda Function

↓

Execution Role

↓

AWS Services
```

The function can only perform actions allowed by its IAM Role.

---

# Types of Permissions

Lambda uses two permission models.

```text
Permissions

│

├── Execution Role

└── Resource-based Policy
```

Both are important but serve different purposes.

---

# Execution Role

The Execution Role defines **what the Lambda function can access**.

Example:

```text
Lambda

↓

IAM Role

↓

S3

↓

DynamoDB

↓

CloudWatch Logs
```

Without an execution role, the function cannot access AWS services.

---

# View Function Configuration

```bash
aws lambda get-function-configuration \
--function-name payment-api
```

Returns:

- Runtime
- Memory
- Timeout
- Role ARN
- Environment Variables

---

# Update Execution Role

```bash
aws lambda update-function-configuration \
--function-name payment-api \
--role arn:aws:iam::123456789012:role/LambdaExecutionRole
```

---

# Least Privilege Principle

Avoid:

```text
Lambda

↓

AdministratorAccess
```

Prefer:

```text
Lambda

↓

Read S3

↓

Write DynamoDB

↓

Write CloudWatch Logs
```

Grant only the permissions required.

---

# Resource-based Policies

Execution Roles define:

> What Lambda can do.

Resource Policies define:

> Who can invoke Lambda.

Example:

```text
API Gateway

↓

Invoke Lambda
```

This permission is granted through a resource-based policy.

---

# View Resource Policy

```bash
aws lambda get-policy \
--function-name payment-api
```

---

# Add Permission

Allow API Gateway to invoke the function.

```bash
aws lambda add-permission \
--function-name payment-api \
--statement-id apigateway \
--action lambda:InvokeFunction \
--principal apigateway.amazonaws.com
```

---

# Remove Permission

```bash
aws lambda remove-permission \
--function-name payment-api \
--statement-id apigateway
```

---

# Environment Variables

Environment Variables store configuration outside the application code.

Instead of:

```python
DATABASE = "production-db"
```

Use:

```text
DATABASE_NAME

↓

Environment Variable
```

---

# Typical Environment Variables

Examples:

- Database Host
- API Endpoint
- Log Level
- Queue Name
- Bucket Name
- Feature Flags

---

# View Environment Variables

```bash
aws lambda get-function-configuration \
--function-name payment-api
```

---

# Configure Environment Variables

```bash
aws lambda update-function-configuration \
--function-name payment-api \
--environment "Variables={ENV=Production,LOG_LEVEL=INFO}"
```

---

# Updating Existing Variables

Updating replaces the entire set.

Recommended workflow:

```text
Read Existing Variables

↓

Merge Changes

↓

Update Configuration
```

Avoid overwriting variables unintentionally.

---

# Should Secrets Be Stored Here?

Avoid storing:

- Database Passwords
- API Keys
- Tokens
- Private Keys

Even though Lambda encrypts environment variables, Secrets Manager provides stronger operational controls.

---

# AWS Secrets Manager

Preferred workflow:

```text
Lambda

↓

Secrets Manager

↓

Retrieve Secret

↓

Application
```

Benefits:

- Automatic rotation
- Encryption
- Centralized management
- Auditing

---

# Parameter Store

AWS Systems Manager Parameter Store is another option.

Suitable for:

- Configuration values
- Non-sensitive parameters
- Small secrets

---

# Lambda Layers

Layers allow multiple functions to share code.

Example:

```text
Lambda A

↓

Shared Layer

↓

Common Library
```

Instead of packaging dependencies repeatedly.

---

# Layer Architecture

```text
Lambda Function

│

├── Function Code

└── Layer

        │

        ├── Libraries

        ├── SDKs

        └── Shared Code
```

---

# Common Layer Use Cases

Examples:

- Python packages
- Node modules
- Shared utilities
- Logging libraries
- Monitoring SDKs
- Security libraries

---

# Publish a Layer

```bash
aws lambda publish-layer-version \
--layer-name shared-utils \
--zip-file fileb://layer.zip \
--compatible-runtimes python3.12
```

---

# List Layers

```bash
aws lambda list-layers
```

---

# List Layer Versions

```bash
aws lambda list-layer-versions \
--layer-name shared-utils
```

---

# Attach a Layer

```bash
aws lambda update-function-configuration \
--function-name payment-api \
--layers arn:aws:lambda:ap-south-1:123456789012:layer:shared-utils:1
```

---

# Remove a Layer

Update the function without specifying the layer.

Lambda removes the previous attachment.

---

# Layer Benefits

Using Layers:

```text
Without Layer

↓

Every Function

↓

Duplicate Dependencies
```

With Layers:

```text
Shared Layer

↓

Many Functions

↓

One Dependency Package
```

---

# Environment-specific Configuration

Recommended approach:

```text
Development

↓

Alias

↓

Environment Variables

↓

Development Database
```

```text
Production

↓

Alias

↓

Environment Variables

↓

Production Database
```

Avoid maintaining separate source code for each environment.

---

# Common Errors

## AccessDeniedException

Possible causes:

- Missing IAM permissions
- Incorrect Execution Role
- Resource Policy missing

---

## InvalidParameterValueException

Possible causes:

- Invalid Layer ARN
- Unsupported Runtime
- Incorrect Environment Variable syntax

---

## ResourceNotFoundException

Verify:

- Function Name
- Layer ARN
- IAM Role
- Secret Name

---

# Production Best Practices

- Follow the Principle of Least Privilege.
- Never hardcode credentials.
- Store secrets in AWS Secrets Manager.
- Use Parameter Store for configuration values.
- Share dependencies using Layers.
- Keep Layers small and versioned.
- Separate environments using aliases and environment variables.
- Audit IAM permissions regularly.

---

# Real-World Workflow

```text
Developer

↓

Deploy Lambda

↓

Execution Role Assigned

↓

Environment Variables Loaded

↓

Layer Attached

↓

Secrets Retrieved

↓

Lambda Executes
```

---

# Architecture Note

```text
Lambda
      │
      ├── Execution Role
      ├── Resource Policy
      ├── Environment Variables
      ├── Lambda Layer
      └── Secrets Manager
              │
              ▼
      AWS Resources
```

Security, configuration, and dependency management work together to create secure, maintainable Lambda applications.

---

# Interview Note

### Question

**What is the difference between an Execution Role and a Resource-based Policy in AWS Lambda?**

### Answer

An **Execution Role** defines what a Lambda function is allowed to do after it starts running, such as reading from Amazon S3 or writing to DynamoDB. A **Resource-based Policy** defines who or what is allowed to invoke the Lambda function, such as API Gateway, EventBridge, SNS, or another AWS account. In simple terms, the Execution Role controls outbound access from Lambda, while the Resource-based Policy controls inbound access to Lambda.

---

# Key Takeaways

- Every Lambda function requires an IAM Execution Role.
- Resource-based Policies control who can invoke a Lambda function.
- Environment Variables separate configuration from application code.
- AWS Secrets Manager is preferred for sensitive information.
- Lambda Layers allow dependency sharing across multiple functions.
- Apply least-privilege IAM permissions.
- Keep configuration, security, and shared code separate from business logic.