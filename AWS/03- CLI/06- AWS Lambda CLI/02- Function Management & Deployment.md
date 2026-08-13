# Function Management & Deployment

> Learn how to create, package, deploy, update, and manage AWS Lambda functions using the AWS CLI. This chapter covers deployment packages, runtimes, handlers, execution roles, code updates, configuration management, and production deployment workflows.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Create Lambda functions
- Deploy Lambda code using AWS CLI
- Understand deployment packages
- Configure runtimes and handlers
- Update function code
- Update function configuration
- Manage execution roles
- Build production deployment workflows

---

# Lambda Deployment Workflow

A Lambda deployment typically follows this process.

```text
Write Code

↓

Package Code

↓

Upload to Lambda

↓

Configure Function

↓

Invoke

↓

Monitor
```

---

# Lambda Function Components

Every Lambda function consists of:

```text
Lambda Function

│

├── Code

├── Runtime

├── Handler

├── Execution Role

├── Memory

├── Timeout

├── Environment Variables

└── Layers
```

Each component can be managed independently.

---

# Deployment Package

Lambda code is usually uploaded as a ZIP archive.

Example:

```text
project/

│

├── lambda_function.py

├── requirements.txt

└── package.zip
```

AWS extracts the ZIP and executes the configured handler.

---

# Create a Deployment Package

Python example:

```bash
zip function.zip lambda_function.py
```

Including dependencies:

```bash
pip install -r requirements.txt -t .

zip -r function.zip .
```

---

# Create a Lambda Function

```bash
aws lambda create-function \
--function-name payment-api \
--runtime python3.12 \
--role arn:aws:iam::123456789012:role/LambdaExecutionRole \
--handler lambda_function.lambda_handler \
--zip-file fileb://function.zip
```

---

# Required Parameters

When creating a function:

| Parameter | Description |
|-----------|-------------|
| `--function-name` | Function name |
| `--runtime` | Runtime environment |
| `--role` | IAM execution role |
| `--handler` | Entry point |
| `--zip-file` | Deployment package |

---

# Runtime

The runtime specifies which language executes your code.

Examples:

```text
python3.12

nodejs22.x

java21

dotnet8

provided.al2023
```

Choose the runtime that matches your application.

---

# Handler

The handler is the entry point.

Python example:

```python
def lambda_handler(event, context):
    return {
        "statusCode": 200
    }
```

Handler configuration:

```text
lambda_function.lambda_handler
```

Meaning:

```text
filename.function
```

---

# Execution Role

Every Lambda function assumes an IAM Role.

```text
Lambda

↓

IAM Role

↓

AWS Services
```

The role determines what the function is allowed to access.

Examples:

- DynamoDB
- S3
- CloudWatch Logs
- SQS
- SNS
- Secrets Manager

---

# List Functions

```bash
aws lambda list-functions
```

Returns all Lambda functions in the current Region.

---

# Get Function Details

```bash
aws lambda get-function \
--function-name payment-api
```

Returns:

- Runtime
- Handler
- Memory
- Timeout
- Environment Variables
- Last Modified
- Execution Role

---

# Get Function Configuration

```bash
aws lambda get-function-configuration \
--function-name payment-api
```

Useful for auditing deployed functions.

---

# Update Function Code

Deploy a new ZIP package.

```bash
aws lambda update-function-code \
--function-name payment-api \
--zip-file fileb://function.zip
```

Only the code changes.

Configuration remains unchanged.

---

# Update Function from Amazon S3

```bash
aws lambda update-function-code \
--function-name payment-api \
--s3-bucket deployment-artifacts \
--s3-key lambda/function.zip
```

Common in CI/CD pipelines.

---

# Update Function Configuration

```bash
aws lambda update-function-configuration \
--function-name payment-api \
--timeout 30 \
--memory-size 1024
```

Updates configuration without changing code.

---

# Memory Allocation

Lambda memory ranges from:

```text
128 MB

↓

10,240 MB
```

Increasing memory also increases available CPU.

---

# Timeout

Lambda timeout ranges from:

```text
1 Second

↓

900 Seconds (15 Minutes)
```

Choose the smallest timeout appropriate for the workload.

---

# Reserved Concurrency

Limit concurrent executions.

```bash
aws lambda put-function-concurrency \
--function-name payment-api \
--reserved-concurrent-executions 25
```

Useful for protecting downstream systems.

---

# Delete Reserved Concurrency

```bash
aws lambda delete-function-concurrency \
--function-name payment-api
```

---

# Delete a Function

```bash
aws lambda delete-function \
--function-name payment-api
```

Deletes the function permanently.

---

# Package Types

Lambda supports:

```text
ZIP Package

Container Image
```

ZIP packages are the most common deployment option.

Container images are useful for:

- Large dependencies
- Custom runtimes
- Machine Learning workloads

---

# Deploy Container Image

Container images are stored in Amazon ECR.

```text
Docker Image

↓

Amazon ECR

↓

Lambda
```

---

# Deployment Lifecycle

```text
Develop

↓

Build

↓

Package

↓

Deploy

↓

Invoke

↓

Monitor

↓

Update
```

---

# Common Errors

## ResourceConflictException

Example:

```text
The operation cannot be performed.
```

Another update is already in progress.

Wait until deployment completes.

---

## InvalidParameterValueException

Possible causes:

- Invalid handler
- Unsupported runtime
- Incorrect ZIP file

---

## AccessDeniedException

Verify:

- IAM execution role
- IAM user permissions
- Deployment permissions

---

## CodeStorageExceededException

Your Lambda code storage quota has been exceeded.

Remove unused functions or versions.

---

# Production Best Practices

- Keep deployment packages small.
- Store deployment artifacts in Amazon S3.
- Use CI/CD pipelines for deployments.
- Grant least-privilege IAM permissions.
- Configure appropriate memory and timeout values.
- Avoid hardcoding secrets.
- Use container images only when necessary.
- Test functions before production deployment.

---

# Real-World Workflow

```text
Developer

↓

Git Repository

↓

CI/CD Pipeline

↓

Build Package

↓

Upload to S3

↓

Update Lambda

↓

Smoke Test

↓

Production
```

---

# Architecture Note

```text
Source Code
      │
      ▼
ZIP Package / Container Image
      │
      ▼
AWS Lambda
      │
      ▼
IAM Role
      │
      ▼
AWS Services
```

The deployment package contains only the application code, while the execution role controls access to AWS resources.

---

# Interview Note

### Question

**What is required to create a Lambda function using the AWS CLI?**

### Answer

At minimum, you must provide a function name, runtime, handler, deployment package, and an IAM execution role. The deployment package contains the application code, the handler specifies the entry point, and the execution role grants the function permission to access AWS services such as CloudWatch Logs, S3, or DynamoDB.

---

# Key Takeaways

- Lambda functions are deployed as ZIP packages or container images.
- Every function requires a runtime, handler, and execution role.
- Function code and configuration can be updated independently.
- Memory allocation affects both RAM and CPU performance.
- Reserved concurrency limits the number of simultaneous executions.
- CI/CD pipelines typically automate Lambda deployments.
- Small deployment packages and least-privilege IAM roles are production best practices.