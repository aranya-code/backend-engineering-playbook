# Managing Resources

## Overview

After creating an API, the next step is managing its resources, methods, integrations, models, and configurations.

For **REST APIs**, API Gateway organizes endpoints as a hierarchical resource tree.

Example:

```text
/

├── products
│      ├── GET
│      ├── POST
│      └── {id}
│             ├── GET
│             ├── PUT
│             └── DELETE
│
└── users
       ├── GET
       └── POST
```

Using the AWS CLI, you can automate the creation and management of these resources, making it ideal for scripting and CI/CD pipelines.

---

# REST API Resource Hierarchy

Example:

```text
/

↓

products

↓

{id}

↓

reviews
```

Each resource can have one or more HTTP methods attached.

---

# List Resources

Retrieve all resources for an API.

```bash
aws apigateway get-resources \
    --rest-api-id abc123
```

Example output:

```json
{
    "items": [
        {
            "id": "root123",
            "path": "/"
        },
        {
            "id": "prod123",
            "path": "/products"
        }
    ]
}
```

---

# Create a Resource

Create:

```text
/products
```

```bash
aws apigateway create-resource \
    --rest-api-id abc123 \
    --parent-id root123 \
    --path-part products
```

---

# Create Nested Resources

Example:

```text
/products/{id}
```

```bash
aws apigateway create-resource \
    --rest-api-id abc123 \
    --parent-id prod123 \
    --path-part "{id}"
```

Result:

```text
/products/{id}
```

---

# Create Multiple Levels

Example:

```text
/products/{id}/reviews
```

CLI:

```bash
aws apigateway create-resource \
    --rest-api-id abc123 \
    --parent-id resource-id \
    --path-part reviews
```

---

# Get a Specific Resource

```bash
aws apigateway get-resource \
    --rest-api-id abc123 \
    --resource-id prod123
```

---

# Delete a Resource

```bash
aws apigateway delete-resource \
    --rest-api-id abc123 \
    --resource-id prod123
```

Deleting a parent resource removes all child resources.

---

# Create a GET Method

```bash
aws apigateway put-method \
    --rest-api-id abc123 \
    --resource-id prod123 \
    --http-method GET \
    --authorization-type NONE
```

---

# Create a POST Method

```bash
aws apigateway put-method \
    --rest-api-id abc123 \
    --resource-id prod123 \
    --http-method POST \
    --authorization-type NONE
```

---

# Create PUT Method

```bash
aws apigateway put-method \
    --rest-api-id abc123 \
    --resource-id id123 \
    --http-method PUT \
    --authorization-type NONE
```

---

# Create DELETE Method

```bash
aws apigateway put-method \
    --rest-api-id abc123 \
    --resource-id id123 \
    --http-method DELETE \
    --authorization-type NONE
```

---

# View Methods

```bash
aws apigateway get-resource \
    --rest-api-id abc123 \
    --resource-id prod123
```

Output includes:

```text
GET

POST
```

---

# Delete a Method

```bash
aws apigateway delete-method \
    --rest-api-id abc123 \
    --resource-id prod123 \
    --http-method POST
```

---

# Configure Lambda Integration

Example:

```bash
aws apigateway put-integration \
    --rest-api-id abc123 \
    --resource-id prod123 \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:ProductAPI/invocations
```

This enables Lambda Proxy Integration.

---

# HTTP Integration

Connect to an external HTTP endpoint.

```bash
aws apigateway put-integration \
    --rest-api-id abc123 \
    --resource-id prod123 \
    --http-method GET \
    --type HTTP_PROXY \
    --integration-http-method GET \
    --uri https://api.example.com/products
```

---

# View Integration

```bash
aws apigateway get-integration \
    --rest-api-id abc123 \
    --resource-id prod123 \
    --http-method GET
```

---

# Delete Integration

```bash
aws apigateway delete-integration \
    --rest-api-id abc123 \
    --resource-id prod123 \
    --http-method GET
```

---

# Configure Method Response

Example:

```bash
aws apigateway put-method-response \
    --rest-api-id abc123 \
    --resource-id prod123 \
    --http-method GET \
    --status-code 200
```

---

# Configure Integration Response

```bash
aws apigateway put-integration-response \
    --rest-api-id abc123 \
    --resource-id prod123 \
    --http-method GET \
    --status-code 200
```

---

# Create Request Model

```bash
aws apigateway create-model \
    --rest-api-id abc123 \
    --name ProductModel \
    --content-type application/json \
    --schema file://product-schema.json
```

Models help validate request payloads.

---

# List Models

```bash
aws apigateway get-models \
    --rest-api-id abc123
```

---

# Delete Model

```bash
aws apigateway delete-model \
    --rest-api-id abc123 \
    --model-name ProductModel
```

---

# Enable Request Validation

Create validator:

```bash
aws apigateway create-request-validator \
    --rest-api-id abc123 \
    --name ValidateBody \
    --validate-request-body
```

---

# List Validators

```bash
aws apigateway get-request-validators \
    --rest-api-id abc123
```

---

# Resource Tree Example

```text
/

├── products
│      ├── GET
│      ├── POST
│      │
│      └── {id}
│             ├── GET
│             ├── PUT
│             └── DELETE
│
└── users
       ├── GET
       └── POST
```

---

# Automation Example

```bash
API_ID=abc123

ROOT_ID=root123

RESOURCE=$(aws apigateway create-resource \
--rest-api-id $API_ID \
--parent-id $ROOT_ID \
--path-part products \
--query id \
--output text)
```

Scripts like this are commonly used in deployment automation.

---

# Common Errors

## Resource Already Exists

Cause:

```text
Duplicate Resource
```

Example:

```text
/products
```

already exists.

---

## Invalid Resource ID

Verify:

```bash
aws apigateway get-resources \
--rest-api-id abc123
```

---

## Missing Integration

API methods without integrations return:

```text
500 Internal Server Error
```

Configure an integration before deployment.

---

## AccessDeniedException

Verify:

- IAM permissions
- AWS credentials
- Active AWS profile

---

# CLI Best Practices

- Use variables for API IDs and resource IDs.
- Prefer Lambda Proxy Integration for modern applications.
- Validate requests before invoking backend services.
- Use JSON schemas for request models.
- Automate resource creation using shell scripts.
- Use Infrastructure as Code for long-term management.

---

# Common Interview Questions

### What is a resource in API Gateway?

A resource represents a path in a REST API, such as `/products` or `/products/{id}`. Resources form a hierarchical structure and contain one or more HTTP methods.

---

### What is the difference between a resource and a method?

A resource defines the URL path, while a method defines the HTTP operation (GET, POST, PUT, DELETE) that can be performed on that resource.

---

### Why use Lambda Proxy Integration?

Lambda Proxy Integration forwards the complete HTTP request to Lambda, simplifying backend development by allowing the application to handle routing, headers, query parameters, and request bodies directly.

---

### What are request models used for?

Request models define the expected JSON schema for incoming payloads and enable request validation before traffic reaches backend services.

---

### Why automate resource creation using the CLI?

CLI automation reduces manual effort, improves consistency, supports CI/CD pipelines, and enables repeatable deployments across multiple environments.

---

# Key Takeaways

- REST APIs are organized as hierarchical resources with one or more HTTP methods.
- The AWS CLI allows complete management of resources, methods, integrations, models, and request validators.
- Lambda Proxy Integration is the preferred integration type for most modern serverless applications.
- Request validation improves API reliability by rejecting malformed requests early.
- CLI automation complements Infrastructure as Code by simplifying operational tasks and deployment workflows.