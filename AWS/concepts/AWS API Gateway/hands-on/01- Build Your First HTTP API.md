# Build Your First HTTP API

## Overview

The best way to learn Amazon API Gateway is by building a real API.

In this hands-on lab, you'll create your first **HTTP API** using:

- Amazon API Gateway
- AWS Lambda
- AWS Console

By the end of this exercise, you'll have a fully functional serverless API that returns JSON to clients over HTTPS.

Unlike REST APIs, HTTP APIs are simpler, cheaper, and provide lower latency, making them an excellent choice for modern web applications.

---

# What You'll Build

Architecture:

```text
Client

↓

Amazon API Gateway (HTTP API)

↓

AWS Lambda

↓

JSON Response
```

Example request:

```http
GET /hello
```

Example response:

```json
{
    "message": "Hello from API Gateway!"
}
```

---

# Prerequisites

Before starting, ensure you have:

- AWS Account
- IAM User with AdministratorAccess (for learning)
- AWS Console access
- Basic knowledge of Lambda

---

# Step 1 — Create a Lambda Function

Open:

```text
AWS Console

↓

Lambda

↓

Create Function
```

Choose:

```text
Author From Scratch
```

Configuration:

| Setting | Value |
|----------|-------|
| Function Name | hello-api |
| Runtime | Python 3.12 |
| Architecture | x86_64 |

Click:

```text
Create Function
```

---

# Step 2 — Replace the Default Code

Replace the generated Lambda code with:

```python
import json

def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "message": "Hello from API Gateway!"
        })
    }
```

Click:

```text
Deploy
```

---

# Step 3 — Test the Lambda Function

Click:

```text
Test

↓

Create New Test Event
```

Example event:

```json
{}
```

Run:

```text
Test
```

Expected response:

```json
{
    "statusCode": 200,
    "body": "{\"message\":\"Hello from API Gateway!\"}"
}
```

The Lambda function is ready.

---

# Step 4 — Create an HTTP API

Navigate to:

```text
AWS Console

↓

API Gateway

↓

Create API
```

Choose:

```text
HTTP API
```

Click:

```text
Build
```

---

# Step 5 — Add Integration

Select:

```text
Lambda
```

Choose:

```text
hello-api
```

Click:

```text
Next
```

API Gateway now invokes your Lambda function.

---

# Step 6 — Configure Routes

Create a route.

Method:

```text
GET
```

Path:

```text
/hello
```

Result:

```text
GET /hello
```

Click:

```text
Next
```

---

# Step 7 — Configure Stage

Stage name:

```text
prod
```

Leave remaining settings as default.

Click:

```text
Next
```

---

# Step 8 — Review

Configuration:

```text
HTTP API

↓

Lambda Integration

↓

GET /hello

↓

prod Stage
```

Click:

```text
Create
```

---

# Step 9 — Copy the Invoke URL

Example:

```text
https://abc123.execute-api.us-east-1.amazonaws.com
```

Your URL will be different.

---

# Step 10 — Test the API

Open:

```text
https://your-api-url/hello
```

Expected response:

```json
{
    "message": "Hello from API Gateway!"
}
```

Congratulations!

You have built your first HTTP API.

---

# Understanding the Request Flow

```text
Browser

↓

HTTPS Request

↓

API Gateway

↓

Lambda

↓

JSON Response

↓

Browser
```

API Gateway automatically invokes Lambda.

---

# What Happens Behind the Scenes?

When the client calls:

```http
GET /hello
```

API Gateway creates an event similar to:

```json
{
    "version": "2.0",
    "routeKey": "GET /hello",
    "rawPath": "/hello",
    "requestContext": {
        "http": {
            "method": "GET"
        }
    }
}
```

This event is passed to Lambda.

---

# Lambda Response Format

HTTP APIs expect:

```python
{
    "statusCode": 200,
    "headers": {},
    "body": "..."
}
```

API Gateway converts this into a proper HTTP response.

---

# API Endpoint

Your endpoint looks like:

```text
https://xxxxx.execute-api.<region>.amazonaws.com/hello
```

Components:

```text
Protocol

↓

Domain

↓

Stage

↓

Route
```

---

# Test Using Browser

Simply visit:

```http
GET /hello
```

Response:

```json
{
    "message":"Hello from API Gateway!"
}
```

---

# Test Using curl

```bash
curl https://your-api-url/hello
```

Expected output:

```json
{
    "message":"Hello from API Gateway!"
}
```

---

# Test Using Postman

Method:

```text
GET
```

URL:

```text
https://your-api-url/hello
```

Response:

```json
{
    "message":"Hello from API Gateway!"
}
```

---

# Modify the Response

Update Lambda:

```python
import json

def lambda_handler(event, context):

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Backend Engineering Playbook",
            "service": "HTTP API",
            "status": "Running"
        })
    }
```

Deploy again.

Response:

```json
{
    "message":"Backend Engineering Playbook",
    "service":"HTTP API",
    "status":"Running"
}
```

---

# Add Query Parameters

Example URL:

```text
/hello?name=John
```

Lambda:

```python
import json

def lambda_handler(event, context):

    name = event.get("queryStringParameters", {}).get("name", "Guest")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"Hello {name}"
        })
    }
```

Calling:

```text
/hello?name=Alice
```

Returns:

```json
{
    "message":"Hello Alice"
}
```

---

# Common Errors

### 404 Not Found

Cause:

```text
Incorrect Route
```

Solution:

Verify:

```text
GET /hello
```

---

### 500 Internal Server Error

Cause:

```text
Lambda Exception
```

Solution:

Check:

```text
CloudWatch Logs
```

---

### 403 Forbidden

Cause:

```text
Permission Issue
```

Solution:

Verify API Gateway has permission to invoke Lambda.

---

### 502 Bad Gateway

Cause:

```text
Invalid Lambda Response
```

Ensure the response contains:

```python
statusCode

headers

body
```

---

# Cleanup

Delete resources after completing the lab.

Delete:

- HTTP API
- Lambda Function

This avoids unnecessary AWS charges.

---

# What You Learned

In this hands-on exercise, you learned how to:

- Create an HTTP API.
- Create a Lambda function.
- Integrate API Gateway with Lambda.
- Create routes.
- Deploy an API stage.
- Invoke APIs using a browser, curl, and Postman.
- Return JSON responses.
- Read query parameters.
- Troubleshoot common issues.

---

# Common Interview Questions

### Why use HTTP API instead of REST API?

HTTP APIs are simpler, cheaper, and provide lower latency. They are ideal when advanced REST API features such as Usage Plans or request transformations are not required.

---

### How does API Gateway invoke Lambda?

API Gateway converts the incoming HTTP request into an event object and passes it to the Lambda function. Lambda processes the event and returns a structured response that API Gateway converts into an HTTP response.

---

### What response format does Lambda return for HTTP APIs?

Lambda should return a response containing:

- `statusCode`
- `headers` (optional)
- `body`

The `body` should be a string, typically JSON-encoded.

---

### Why is CloudWatch useful in this project?

CloudWatch Logs capture Lambda execution details, making it easier to diagnose runtime errors, inspect request handling, and troubleshoot integration issues.

---

# Key Takeaways

- HTTP APIs provide a simple and cost-effective way to expose serverless applications.
- API Gateway acts as the HTTPS endpoint while Lambda executes the application logic.
- A Lambda response must follow the expected structure for API Gateway to generate a valid HTTP response.
- Query parameters and other request details are passed to Lambda through the event object.
- This project establishes the foundation for building more advanced APIs with authentication, databases, and production-grade features.