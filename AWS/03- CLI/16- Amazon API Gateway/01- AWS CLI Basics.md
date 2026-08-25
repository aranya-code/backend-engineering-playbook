# AWS CLI Basics

## Overview

The AWS Command Line Interface (AWS CLI) allows you to create, configure, deploy, and manage Amazon API Gateway directly from your terminal.

Although Infrastructure as Code (CloudFormation, CDK, Terraform) is the preferred approach for production deployments, the AWS CLI is extremely useful for:

- Learning API Gateway
- Automation scripts
- CI/CD pipelines
- Troubleshooting
- Quickly testing configurations
- Managing multiple AWS environments

This chapter introduces the CLI commands you'll use throughout the API Gateway section.

---

# Installing AWS CLI

## Windows

Download and install:

```text
https://aws.amazon.com/cli/
```

Verify installation:

```bash
aws --version
```

Example:

```text
aws-cli/2.27.41 Python/3.13 Windows/11
```

---

## Linux

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip

unzip awscliv2.zip

sudo ./aws/install
```

---

## macOS

```bash
brew install awscli
```

Verify:

```bash
aws --version
```

---

# Configure AWS CLI

Run:

```bash
aws configure
```

Example:

```text
AWS Access Key ID

AWS Secret Access Key

Default Region

Default Output Format
```

Example:

```text
AWS Access Key ID: AKIA*************

AWS Secret Access Key: *************************

Default Region: us-east-1

Default Output: json
```

---

# Verify Configuration

Check identity:

```bash
aws sts get-caller-identity
```

Example:

```json
{
    "UserId": "...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/backend-user"
}
```

---

# Configure Multiple Profiles

Example:

```bash
aws configure --profile dev
```

```bash
aws configure --profile production
```

Use a profile:

```bash
aws apigateway get-rest-apis --profile dev
```

---

# Specify a Region

Temporarily:

```bash
aws apigateway get-rest-apis \
    --region us-east-1
```

Or configure permanently:

```bash
aws configure
```

---

# Output Formats

AWS CLI supports:

```text
json
```

```text
yaml
```

```text
table
```

```text
text
```

Example:

```bash
aws apigateway get-rest-apis \
    --output table
```

---

# API Gateway CLI Commands

Amazon API Gateway has **two CLI namespaces**.

## REST APIs

```bash
aws apigateway
```

Supports:

- REST APIs
- Resources
- Methods
- Deployments
- Usage Plans
- API Keys

---

## HTTP APIs & WebSocket APIs

```bash
aws apigatewayv2
```

Supports:

- HTTP APIs
- WebSocket APIs
- Routes
- Integrations
- JWT Authorizers

---

# Which Command Should You Use?

| API Type | CLI Command |
|-----------|-------------|
| REST API | `aws apigateway` |
| HTTP API | `aws apigatewayv2` |
| WebSocket API | `aws apigatewayv2` |

---

# Get CLI Help

General help:

```bash
aws help
```

API Gateway:

```bash
aws apigateway help
```

HTTP APIs:

```bash
aws apigatewayv2 help
```

Specific command:

```bash
aws apigateway create-rest-api help
```

---

# List REST APIs

```bash
aws apigateway get-rest-apis
```

Example:

```json
{
    "items": [
        {
            "id": "abc123",
            "name": "ProductAPI"
        }
    ]
}
```

---

# List HTTP APIs

```bash
aws apigatewayv2 get-apis
```

Example:

```json
{
    "Items": [
        {
            "ApiId": "xyz789",
            "Name": "OrdersAPI"
        }
    ]
}
```

---

# Filter Output

Using JMESPath:

```bash
aws apigateway get-rest-apis \
    --query "items[*].name"
```

Example:

```text
[
    "OrdersAPI",
    "UsersAPI"
]
```

---

# Save Output

```bash
aws apigateway get-rest-apis \
> apis.json
```

---

# Pretty Print JSON

Using jq:

```bash
aws apigateway get-rest-apis \
| jq
```

Example:

```json
{
  "items": [
    {
      "name": "OrdersAPI"
    }
  ]
}
```

---

# Use Environment Variables

Instead of hardcoding:

```bash
export AWS_REGION=us-east-1

export AWS_PROFILE=dev
```

Commands automatically use these values.

---

# Auto Prompt

AWS CLI v2 supports interactive prompts.

Example:

```bash
aws apigateway create-rest-api \
    --cli-auto-prompt
```

The CLI asks for required parameters interactively.

---

# Generate JSON Skeleton

Example:

```bash
aws apigateway create-rest-api \
    --generate-cli-skeleton
```

Output:

```json
{
    "name": "",
    "description": ""
}
```

Useful when writing automation scripts.

---

# Dry Run Equivalent

Many AWS services do not support a true dry run.

Instead:

- Generate CLI skeletons
- Validate IAM permissions
- Test in non-production accounts

---

# Common Global Options

```bash
--profile
```

```bash
--region
```

```bash
--output
```

```bash
--query
```

```bash
--debug
```

Example:

```bash
aws apigateway get-rest-apis \
    --profile dev \
    --region us-east-1 \
    --output table
```

---

# Enable Debug Mode

```bash
aws apigateway get-rest-apis \
    --debug
```

Useful for troubleshooting:

- Authentication
- IAM permissions
- HTTP requests
- AWS API responses

---

# Common Errors

## AccessDeniedException

Cause:

```text
Missing IAM Permission
```

Verify:

- IAM Policy
- AWS Profile
- AWS Credentials

---

## Unable to Locate Credentials

Run:

```bash
aws configure
```

or

```bash
aws sts get-caller-identity
```

---

## Expired Token

Common with:

- AWS SSO
- Temporary Credentials

Refresh credentials before retrying.

---

## Invalid Region

Verify:

```bash
aws configure get region
```

---

# CLI Best Practices

- Use named profiles for multiple AWS accounts.
- Store credentials securely.
- Avoid embedding secrets in scripts.
- Prefer JSON output for automation.
- Use `--query` to minimize output.
- Test commands in development before production.
- Use Infrastructure as Code for repeatable deployments.

---

# Common Interview Questions

### Why are there two API Gateway CLI commands?

Amazon API Gateway has separate APIs for REST APIs and HTTP/WebSocket APIs. The AWS CLI reflects this with:

- `aws apigateway` for REST APIs
- `aws apigatewayv2` for HTTP and WebSocket APIs

---

### Why use AWS CLI if Infrastructure as Code exists?

The AWS CLI is useful for quick testing, scripting, automation, troubleshooting, and CI/CD tasks. Infrastructure as Code remains the preferred approach for managing production environments.

---

### What does `aws configure` do?

It stores your AWS credentials, default region, and preferred output format, enabling authenticated CLI access to AWS services.

---

### What is the purpose of the `--query` option?

`--query` uses JMESPath expressions to filter and transform CLI output, making automation scripts more efficient and readable.

---

### Why use named profiles?

Named profiles allow engineers to switch easily between multiple AWS accounts or environments, such as development, staging, and production, without modifying credentials.

---

# Key Takeaways

- The AWS CLI is a powerful tool for interacting with Amazon API Gateway from the command line.
- REST APIs use the `aws apigateway` namespace, while HTTP and WebSocket APIs use `aws apigatewayv2`.
- Profiles, regions, output formats, and JMESPath queries make CLI workflows flexible and automation-friendly.
- The CLI complements Infrastructure as Code by supporting scripting, troubleshooting, and CI/CD pipelines.
- Understanding AWS CLI fundamentals provides the foundation for managing API Gateway resources programmatically.