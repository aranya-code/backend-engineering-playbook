# 06- Lambda with API Gateway.md

# Lambda with API Gateway

One of the most common production use cases for AWS Lambda is building **REST APIs** using **Amazon API Gateway**.

Instead of running web servers on EC2 or containers, API Gateway receives HTTP requests and invokes Lambda functions to execute business logic.

This architecture eliminates the need to manage web servers while providing automatic scaling, authentication, rate limiting, monitoring, and security.

---

# High-Level Architecture

```text
                Internet

                    │

                    ▼

            Amazon API Gateway

                    │

                    ▼

              AWS Lambda

                    │

                    ▼

        Database / S3 / DynamoDB
```

API Gateway acts as the HTTP frontend, while Lambda serves as the backend compute layer.

---

# Why Use API Gateway?

Without API Gateway:

```text
Client

↓

EC2

↓

Nginx

↓

Application

↓

Database
```

With Lambda:

```text
Client

↓

API Gateway

↓

Lambda

↓

Database
```

AWS manages:

- HTTPS endpoints
- SSL certificates
- Scaling
- Authentication
- Authorization
- Rate limiting
- Monitoring
- Logging

---

# Request Flow

Consider an API:

```
GET /users/101
```

Request flow:

```text
Client

↓

HTTPS Request

↓

API Gateway

↓

Lambda

↓

DynamoDB

↓

API Gateway

↓

HTTP Response

↓

Client
```

---

# How API Gateway Invokes Lambda

API Gateway converts the HTTP request into a JSON event.

Example:

```http
GET /users/101?active=true
```

Becomes:

```json
{
    "resource": "/users/{id}",
    "path": "/users/101",
    "httpMethod": "GET",
    "headers": {},
    "queryStringParameters": {
        "active": "true"
    },
    "pathParameters": {
        "id": "101"
    }
}
```

Lambda receives this event as the first parameter.

---

# Lambda Function

Python example:

```python
def handler(event, context):

    user_id = event["pathParameters"]["id"]

    return {
        "statusCode": 200,
        "body": f"User ID = {user_id}"
    }
```

Response:

```text
User ID = 101
```

---

# Request Components

API Gateway extracts:

- HTTP Method
- Headers
- Cookies
- Query Parameters
- Path Parameters
- Body
- Request Context

Example:

```http
POST /orders
```

Body:

```json
{
    "product":"Laptop",
    "quantity":2
}
```

Lambda receives:

```python
event["body"]
```

---

# HTTP Methods

API Gateway supports:

```
GET
POST
PUT
PATCH
DELETE
OPTIONS
HEAD
```

Example:

```text
GET /products

↓

Lambda

↓

Read Products
```

```text
POST /products

↓

Lambda

↓

Create Product
```

---

# Path Parameters

Endpoint:

```
GET /users/{id}
```

Request:

```
GET /users/500
```

Event:

```json
{
    "pathParameters": {
        "id":"500"
    }
}
```

Access:

```python
user_id = event["pathParameters"]["id"]
```

---

# Query Parameters

Request:

```
GET /users?page=2&limit=20
```

Event:

```json
{
    "queryStringParameters":{
        "page":"2",
        "limit":"20"
    }
}
```

Python:

```python
page = event["queryStringParameters"]["page"]
```

---

# Headers

Example:

```
Authorization: Bearer TOKEN
```

Lambda:

```python
token = event["headers"]["Authorization"]
```

Useful for:

- JWT
- API Keys
- OAuth

---

# Request Body

POST Request:

```json
{
    "name":"John",
    "age":28
}
```

Python:

```python
import json

body = json.loads(event["body"])
```

Now:

```python
body["name"]
```

Returns:

```
John
```

---

# Response Format

Lambda must return:

```python
return {

    "statusCode":200,

    "headers":{

        "Content-Type":"application/json"

    },

    "body":"..."
}
```

Example:

```python
return {

    "statusCode":200,

    "body":"Hello"
}
```

---

# Returning JSON

```python
import json

return {

    "statusCode":200,

    "body":json.dumps({

        "id":100,

        "name":"Alice"

    })
}
```

---

# Error Response

```python
return {

    "statusCode":404,

    "body":"User Not Found"
}
```

Or:

```python
raise Exception("Database Error")
```

API Gateway converts this into an HTTP error response.

---

# Authentication

API Gateway supports multiple authentication mechanisms.

```text
Client

↓

JWT

↓

API Gateway

↓

Lambda
```

Supported methods:

- IAM Authentication
- Cognito User Pools
- Lambda Authorizers
- JWT Authorizers
- API Keys

---

# Lambda Authorizer

Flow:

```text
Client

↓

Authorization Header

↓

Lambda Authorizer

↓

Allow

↓

Backend Lambda
```

Authorizers execute **before** the backend Lambda.

---

# API Keys

API Gateway supports API Keys.

```text
Client

↓

API Key

↓

API Gateway

↓

Lambda
```

Useful for:

- Partner APIs
- Internal APIs
- Usage plans

---

# Rate Limiting

API Gateway provides throttling.

Example:

```
100 Requests/Second
```

Requests above this limit receive:

```
HTTP 429
```

Benefits:

- Prevent abuse
- Protect Lambda
- Protect database

---

# Request Validation

API Gateway can validate:

- JSON Schema
- Required parameters
- Required headers
- Path parameters

Invalid requests never reach Lambda.

---

# CORS

For browser applications:

```text
Browser

↓

OPTIONS Request

↓

API Gateway

↓

CORS Headers

↓

Browser Allows Request
```

Example headers:

```
Access-Control-Allow-Origin
```

---

# Binary Support

API Gateway supports binary data.

Examples:

- Images
- PDFs
- ZIP files
- Audio

---

# Timeout

API Gateway maximum timeout:

```
29 Seconds
```

Lambda maximum timeout:

```
15 Minutes
```

Therefore:

If Lambda exceeds:

```
29 Seconds
```

The client receives a timeout.

---

# API Gateway Logging

Logs:

```text
Client

↓

API Gateway Logs

↓

CloudWatch
```

Useful information:

- Latency
- Request IDs
- Status codes
- Errors

---

# Lambda Logging

```python
print(event)
```

Appears in:

```
CloudWatch Logs
```

Useful for debugging.

---

# Monitoring

Monitor:

- Request Count
- 4XX Errors
- 5XX Errors
- Integration Latency
- Lambda Duration
- Cold Starts
- Throttles

---

# Production Architecture

```text
Internet

↓

Route53

↓

CloudFront

↓

WAF

↓

API Gateway

↓

Lambda

↓

DynamoDB
```

Optional:

```text
↓

SQS

↓

Lambda Workers

↓

RDS
```

---

# REST API Example

```
GET /users

↓

Lambda

↓

List Users
```

```
GET /users/10

↓

Lambda

↓

Get User
```

```
POST /users

↓

Lambda

↓

Create User
```

```
PUT /users/10

↓

Lambda

↓

Update User
```

```
DELETE /users/10

↓

Lambda

↓

Delete User
```

---

# Advantages

- No web server
- Automatic scaling
- HTTPS built-in
- Authentication support
- Rate limiting
- Monitoring
- Versioning
- Easy deployment

---

# Limitations

- API Gateway timeout (29 sec)
- Payload size limits
- Cold starts
- Higher latency than direct servers
- Request transformation overhead

---

# Common Mistakes

## Heavy Processing

Bad:

```text
Client

↓

API Gateway

↓

Lambda

↓

Generate Report

↓

Send Email

↓

Resize Images

↓

Return
```

The client waits.

Better:

```text
API Gateway

↓

Lambda

↓

EventBridge

↓

Background Workers
```

---

## Returning Invalid Response

Bad:

```python
return "Hello"
```

Correct:

```python
return {

    "statusCode":200,

    "body":"Hello"
}
```

---

## Not Parsing JSON

Incorrect:

```python
event["body"]["name"]
```

Correct:

```python
import json

body = json.loads(event["body"])
```

---

# Best Practices

✅ Keep API Lambdas lightweight.

✅ Validate input.

✅ Use structured JSON responses.

✅ Return proper HTTP status codes.

✅ Offload long-running tasks to SQS or EventBridge.

✅ Enable API Gateway logging.

✅ Use Lambda Authorizers or Cognito for authentication.

✅ Implement idempotency for POST requests.

---

# Senior Backend Engineering Perspective

A senior backend engineer views API Gateway as much more than an HTTP proxy. It is the **front door** to serverless applications and is responsible for request validation, authentication, authorization, throttling, observability, and traffic management.

The Lambda function should focus solely on business logic, while API Gateway handles concerns related to HTTP. For latency-sensitive APIs, engineers should minimize cold starts, keep handlers lightweight, and move expensive operations to asynchronous workflows using services like SQS or EventBridge.

---

# Interview Questions

### Beginner

- How does API Gateway invoke Lambda?
- What does the Lambda event contain?
- What response format should Lambda return?

### Intermediate

- How are path parameters accessed?
- What is the difference between path parameters and query parameters?
- How does API Gateway handle authentication?
- What happens if Lambda throws an exception?

### Senior

- Why would you choose API Gateway over an Application Load Balancer?
- How would you design a high-throughput serverless REST API?
- How would you implement authentication, rate limiting, and request validation?
- How would you reduce latency caused by cold starts?
- How would you design an API that processes long-running requests without blocking the client?

---

# Key Takeaways

- API Gateway is the most common synchronous trigger for AWS Lambda.
- It transforms HTTP requests into structured JSON events for Lambda functions.
- Lambda responses must follow the API Gateway response format.
- API Gateway provides authentication, authorization, throttling, validation, monitoring, and HTTPS out of the box.
- Production-grade serverless APIs separate HTTP concerns (API Gateway) from business logic (Lambda) and offload long-running tasks to asynchronous services.