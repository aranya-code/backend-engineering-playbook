# Lambda Proxy Integration

## Overview

**Lambda Proxy Integration** is the most commonly used integration type in Amazon API Gateway.

In this integration, API Gateway forwards the **entire HTTP request** to an AWS Lambda function with minimal processing. The Lambda function is responsible for:

- Parsing the request
- Performing validation
- Executing business logic
- Calling databases or other services
- Constructing the HTTP response

Unlike Non-Proxy Integration, API Gateway does **not** perform request or response transformation using mapping templates.

For modern serverless applications, **Lambda Proxy Integration is the recommended approach**.

---

# Architecture

```text
                Client
                   │
                   ▼
          Amazon API Gateway
                   │
                   ▼
            AWS Lambda Function
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
    DynamoDB     Amazon S3   SNS/SQS
```

API Gateway acts only as the API layer, while Lambda handles all application logic.

---

# Request Flow

```text
Client

↓

API Gateway

↓

Entire HTTP Request

↓

Lambda Function

↓

Business Logic

↓

HTTP Response

↓

API Gateway

↓

Client
```

Notice that API Gateway forwards the request almost unchanged.

---

# What Gets Forwarded?

API Gateway sends the complete HTTP request to Lambda.

This includes:

- HTTP Method
- Resource Path
- Headers
- Query Parameters
- Path Parameters
- Request Body
- Stage Variables
- Identity Information
- Request Context

Example request:

```http
POST /users/101/orders?page=2

Authorization: Bearer xxxxx

Content-Type: application/json
```

Body:

```json
{
    "productId": 10,
    "quantity": 2
}
```

All of this information becomes part of the Lambda event object.

---

# Lambda Event Structure

A simplified Lambda event looks like:

```json
{
    "resource": "/users/{id}/orders",
    "path": "/users/101/orders",
    "httpMethod": "POST",
    "headers": {
        "Content-Type": "application/json"
    },
    "queryStringParameters": {
        "page": "2"
    },
    "pathParameters": {
        "id": "101"
    },
    "body": "{\"productId\":10,\"quantity\":2}",
    "isBase64Encoded": false
}
```

The Lambda function extracts whatever it needs from this event.

---

# Python Example

```python
import json

def lambda_handler(event, context):

    user_id = event["pathParameters"]["id"]

    page = event["queryStringParameters"]["page"]

    body = json.loads(event["body"])

    return {
        "statusCode": 200,
        "body": json.dumps({
            "user": user_id,
            "page": page,
            "product": body["productId"]
        })
    }
```

No mapping template is required.

---

# Response Format

Lambda must return a properly formatted response.

Example:

```json
{
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json"
    },
    "body": "{\"message\":\"Success\"}"
}
```

Required fields:

- statusCode
- body

Optional fields:

- headers
- multiValueHeaders
- cookies (HTTP APIs)
- isBase64Encoded

---

# Request Lifecycle

```text
Client

↓

POST /products

↓

API Gateway

↓

Lambda Event

↓

Lambda Business Logic

↓

Database

↓

Lambda Response

↓

API Gateway

↓

Client
```

Most business logic lives inside Lambda.

---

# Accessing Request Components

## Path Parameters

Request:

```http
GET /products/100
```

Event:

```python
event["pathParameters"]["id"]
```

---

## Query Parameters

Request:

```http
GET /products?page=2
```

Event:

```python
event["queryStringParameters"]["page"]
```

---

## Headers

Request:

```http
Authorization: Bearer abc
```

Event:

```python
event["headers"]["Authorization"]
```

---

## Request Body

Request:

```json
{
    "name":"Laptop"
}
```

Python:

```python
import json

body = json.loads(event["body"])
```

---

# Lambda Context Object

Lambda also receives a second parameter:

```python
context
```

The context object contains execution information.

Examples:

- Function Name
- Function Version
- AWS Request ID
- Remaining Execution Time
- Memory Limit

Example:

```python
context.function_name

context.aws_request_id

context.get_remaining_time_in_millis()
```

---

# Advantages

## Simple Configuration

No mapping templates are required.

---

## Less Maintenance

The backend controls request parsing and response generation.

---

## Flexible

Any HTTP request can be processed.

---

## Easier Development

Developers only work with Lambda code.

No VTL knowledge is required.

---

## Faster Development

Most serverless frameworks generate Lambda Proxy integrations by default.

Examples:

- AWS SAM
- Serverless Framework
- AWS CDK
- Terraform

---

# Disadvantages

## Larger Lambda Event

Entire request is forwarded.

Very large HTTP requests produce larger event objects.

---

## Backend Handles Everything

Validation.

Parsing.

Error handling.

Response formatting.

All become Lambda's responsibility.

---

## Tight Coupling

Lambda must understand API Gateway's event structure.

---

# Common Use Cases

Lambda Proxy Integration is ideal for:

- Serverless APIs
- CRUD Applications
- REST APIs
- Mobile Backends
- Microservices
- Event-driven systems

---

# Lambda Proxy vs Lambda Non-Proxy

| Feature | Lambda Proxy | Lambda Non-Proxy |
|----------|--------------|------------------|
| Mapping Templates | ❌ | ✅ |
| Request Transformation | ❌ | ✅ |
| Response Transformation | ❌ | ✅ |
| Configuration | Simple | Complex |
| Business Logic | Lambda | Shared |
| Recommended | ✅ | Only when needed |

For new applications, Lambda Proxy Integration should generally be the default choice.

---

# Error Handling

Lambda should return appropriate HTTP status codes.

Example:

```python
return {
    "statusCode":404,
    "body":"Product not found"
}
```

Server Error:

```python
return {
    "statusCode":500,
    "body":"Internal Server Error"
}
```

Avoid always returning:

```text
200 OK
```

for failed operations.

---

# Best Practices

### Keep API Gateway Simple

API Gateway should manage:

- Authentication
- Authorization
- Routing
- Throttling
- Monitoring

Lambda should manage:

- Validation
- Business Logic
- Database Operations
- Response Generation

---

### Validate Input

Never trust incoming requests.

Always validate:

- Path parameters
- Query parameters
- Headers
- Request body

---

### Return Proper Status Codes

Examples:

```text
200 OK

201 Created

204 No Content

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

409 Conflict

422 Unprocessable Entity

500 Internal Server Error
```

---

### Keep Functions Focused

Instead of one Lambda handling every endpoint:

Bad:

```text
AppLambda

Handles Everything
```

Better:

```text
CreateProduct

GetProduct

UpdateProduct

DeleteProduct
```

Smaller functions are easier to maintain and deploy.

---

# Real-World Example

An online shopping application.

```text
Client

↓

POST /orders

↓

API Gateway

↓

CreateOrder Lambda

↓

Validate Inventory

↓

Store Order

↓

Publish SNS Event

↓

Return Order ID
```

API Gateway simply forwards the request.

The Lambda function performs all business logic.

---

# Common Interview Questions

### What is Lambda Proxy Integration?

Lambda Proxy Integration forwards the complete HTTP request to a Lambda function with minimal transformation. The Lambda function processes the request and returns a properly formatted HTTP response.

---

### Does Lambda Proxy Integration require Mapping Templates?

No.

API Gateway forwards the request directly, so Mapping Templates are generally unnecessary.

---

### What is contained in the Lambda event?

The event contains:

- HTTP Method
- Path
- Headers
- Query Parameters
- Path Parameters
- Request Body
- Stage Variables
- Request Context
- Identity Information

---

### Why is Lambda Proxy Integration recommended?

Because it is:

- Simpler
- Easier to maintain
- Less configuration-intensive
- More flexible
- Better suited for modern serverless applications

---

# Key Takeaways

- Lambda Proxy Integration is the recommended integration type for most serverless APIs.
- API Gateway forwards the complete HTTP request directly to Lambda with minimal processing.
- The Lambda function is responsible for request parsing, validation, business logic, and response generation.
- No mapping templates are required, simplifying configuration and maintenance.
- Proper input validation, error handling, and HTTP status codes should be implemented within the Lambda function.