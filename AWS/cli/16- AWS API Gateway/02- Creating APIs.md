# Creating APIs

## Overview

Amazon API Gateway supports multiple API types, each designed for different use cases.

Using the AWS CLI, you can create, configure, and automate API creation without using the AWS Management Console.

This chapter covers how to create:

- REST APIs
- HTTP APIs
- API Stages
- Basic Routes
- Lambda Integrations

These commands are commonly used in automation scripts and CI/CD pipelines.

---

# API Types

| API Type | CLI Command |
|----------|-------------|
| REST API | `aws apigateway` |
| HTTP API | `aws apigatewayv2` |
| WebSocket API | `aws apigatewayv2` |

---

# Create a REST API

Basic command:

```bash
aws apigateway create-rest-api \
    --name ProductAPI
```

Example output:

```json
{
    "id": "a1b2c3d4",
    "name": "ProductAPI"
}
```

Save the API ID.

---

# Create a REST API with Description

```bash
aws apigateway create-rest-api \
    --name ProductAPI \
    --description "Product Management REST API"
```

---

# Create a Regional REST API

```bash
aws apigateway create-rest-api \
    --name ProductAPI \
    --endpoint-configuration types=REGIONAL
```

Supported endpoint types:

- REGIONAL
- EDGE
- PRIVATE

---

# List REST APIs

```bash
aws apigateway get-rest-apis
```

Output:

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

# Get a Specific REST API

```bash
aws apigateway get-rest-api \
    --rest-api-id abc123
```

---

# Delete a REST API

```bash
aws apigateway delete-rest-api \
    --rest-api-id abc123
```

Deletion is permanent.

---

# Create an HTTP API

```bash
aws apigatewayv2 create-api \
    --name OrdersAPI \
    --protocol-type HTTP
```

Example output:

```json
{
    "ApiId": "xyz789",
    "Name": "OrdersAPI"
}
```

---

# Create a WebSocket API

```bash
aws apigatewayv2 create-api \
    --name ChatAPI \
    --protocol-type WEBSOCKET \
    --route-selection-expression '$request.body.action'
```

---

# List HTTP APIs

```bash
aws apigatewayv2 get-apis
```

---

# Get API Details

```bash
aws apigatewayv2 get-api \
    --api-id xyz789
```

---

# Delete an HTTP API

```bash
aws apigatewayv2 delete-api \
    --api-id xyz789
```

---

# Retrieve Root Resource (REST API)

Every REST API contains a root resource.

List resources:

```bash
aws apigateway get-resources \
    --rest-api-id abc123
```

Example:

```json
{
    "items": [
        {
            "id": "x1y2z3",
            "path": "/"
        }
    ]
}
```

The root resource ID is required when creating additional resources.

---

# Create a Resource

Example:

```bash
aws apigateway create-resource \
    --rest-api-id abc123 \
    --parent-id x1y2z3 \
    --path-part products
```

Result:

```text
/products
```

---

# Create Nested Resources

Example:

```bash
/products/{id}
```

CLI:

```bash
aws apigateway create-resource \
    --rest-api-id abc123 \
    --parent-id resource-id \
    --path-part "{id}"
```

---

# List Resources

```bash
aws apigateway get-resources \
    --rest-api-id abc123
```

Example:

```text
/

↓

/products

↓

/products/{id}
```

---

# Create an HTTP Route

Example:

```bash
aws apigatewayv2 create-route \
    --api-id xyz789 \
    --route-key "GET /products"
```

Example output:

```json
{
    "RouteId": "route123"
}
```

---

# List HTTP Routes

```bash
aws apigatewayv2 get-routes \
    --api-id xyz789
```

---

# Delete a Route

```bash
aws apigatewayv2 delete-route \
    --api-id xyz789 \
    --route-id route123
```

---

# Create Multiple Routes

Examples:

```text
GET /products

POST /products

PUT /products/{id}

DELETE /products/{id}
```

Each route maps an HTTP method to a backend integration.

---

# View API Endpoint

HTTP API:

```bash
aws apigatewayv2 get-api \
    --api-id xyz789 \
    --query "ApiEndpoint"
```

Example:

```text
https://xyz789.execute-api.us-east-1.amazonaws.com
```

---

# Use Variables

Instead of hardcoding:

```bash
API_ID=abc123
```

Then:

```bash
aws apigateway get-rest-api \
    --rest-api-id $API_ID
```

Improves script readability.

---

# Using Profiles

Example:

```bash
aws apigateway get-rest-apis \
    --profile production
```

---

# Output as Table

```bash
aws apigateway get-rest-apis \
    --output table
```

Example:

```text
---------------------------------

Name

ProductAPI

OrdersAPI

UsersAPI

---------------------------------
```

---

# Save API Information

```bash
aws apigateway get-rest-api \
    --rest-api-id abc123 \
> api.json
```

Useful for documentation and automation.

---

# Common Errors

## BadRequestException

Cause:

```text
Invalid Parameter
```

Verify:

- API ID
- Resource ID
- Endpoint Type

---

## NotFoundException

Cause:

```text
Incorrect API ID
```

List APIs:

```bash
aws apigateway get-rest-apis
```

---

## ConflictException

Occurs when:

```text
Duplicate Resource
```

Example:

```text
/products
```

already exists.

---

## AccessDeniedException

Verify:

- IAM Permissions
- AWS Profile
- Region

---

# CLI Best Practices

- Store API IDs in variables.
- Use named profiles.
- Prefer JSON output for scripting.
- Automate API creation through shell scripts or CI/CD pipelines.
- Use Infrastructure as Code for long-term resource management.
- Delete unused APIs to avoid unnecessary charges.

---

# Common Interview Questions

### What is the difference between `create-rest-api` and `create-api`?

`create-rest-api` is part of the `apigateway` CLI and creates REST APIs.

`create-api` belongs to `apigatewayv2` and creates HTTP or WebSocket APIs.

---

### Why does a REST API require resources?

REST APIs organize endpoints into a hierarchical resource tree (for example, `/products/{id}`), where each resource can have one or more HTTP methods.

---

### Why should API IDs be stored in variables?

Using variables makes scripts easier to maintain and reuse across different environments without repeatedly editing command arguments.

---

### Can API creation be automated?

Yes. AWS CLI commands are commonly embedded in shell scripts, CI/CD pipelines, or Infrastructure as Code workflows to provision APIs consistently.

---

### Should the AWS CLI replace Infrastructure as Code?

No. The AWS CLI is ideal for scripting, automation, and operational tasks, while Infrastructure as Code tools such as CloudFormation, CDK, and Terraform are preferred for provisioning and managing production infrastructure.

---

# Key Takeaways

- The AWS CLI supports creating and managing REST, HTTP, and WebSocket APIs.
- REST APIs use the `apigateway` namespace, while HTTP and WebSocket APIs use `apigatewayv2`.
- API creation involves defining APIs, resources, routes, and endpoint types.
- Variables, profiles, and structured output formats make CLI automation more maintainable.
- While the CLI is powerful for scripting and operational tasks, Infrastructure as Code remains the recommended approach for production deployments.