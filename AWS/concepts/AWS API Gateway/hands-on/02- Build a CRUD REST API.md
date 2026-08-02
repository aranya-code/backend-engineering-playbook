# Build a CRUD REST API

## Overview

In this hands-on project, you'll build a production-style **CRUD REST API** using:

- Amazon API Gateway
- AWS Lambda
- Amazon DynamoDB

The API will support the four fundamental database operations:

- Create
- Read
- Update
- Delete

Unlike the previous exercise, this project introduces a persistent data store and multiple API endpoints, closely resembling real-world backend services.

---

# What You'll Build

Architecture:

```text
                Client

                   │

                   ▼

          Amazon API Gateway

                   │

                   ▼

              AWS Lambda

                   │

                   ▼

          Amazon DynamoDB
```

API Endpoints:

| Method | Endpoint | Description |
|----------|----------|-------------|
| POST | /products | Create Product |
| GET | /products | List Products |
| GET | /products/{id} | Get Product |
| PUT | /products/{id} | Update Product |
| DELETE | /products/{id} | Delete Product |

---

# Project Architecture

```text
POST /products

        │

        ▼

API Gateway

        │

        ▼

Lambda Function

        │

        ▼

DynamoDB Table
```

Every request flows through API Gateway before reaching Lambda.

---

# Prerequisites

You should have:

- AWS Account
- Basic Lambda knowledge
- Completed the previous HTTP API project

---

# Step 1 — Create a DynamoDB Table

Open:

```text
AWS Console

↓

DynamoDB

↓

Create Table
```

Configuration:

| Setting | Value |
|----------|-------|
| Table Name | Products |
| Partition Key | productId (String) |

Choose:

```text
On-demand Capacity
```

Click:

```text
Create Table
```

---

# Step 2 — Create a Lambda Function

Create:

```text
product-api
```

Runtime:

```text
Python 3.12
```

---

# Step 3 — Grant DynamoDB Permissions

Attach IAM permissions allowing Lambda to:

- GetItem
- PutItem
- UpdateItem
- DeleteItem
- Scan

Example policy:

```text
Products Table

↓

CRUD Access
```

Always follow least privilege in production.

---

# Step 4 — Install boto3

The Lambda runtime already includes:

```python
import boto3
```

No additional installation is required.

---

# Step 5 — Create the DynamoDB Client

```python
import boto3

table = boto3.resource("dynamodb").Table("Products")
```

Lambda can now communicate with DynamoDB.

---

# Step 6 — Create Product

Request:

```http
POST /products
```

Body:

```json
{
    "productId":"101",
    "name":"Laptop",
    "price":85000
}
```

Lambda:

```python
table.put_item(
    Item=item
)
```

Response:

```http
201 Created
```

---

# Step 7 — Get Product

Endpoint:

```http
GET /products/101
```

Lambda:

```python
table.get_item(
    Key={
        "productId":"101"
    }
)
```

Response:

```json
{
    "productId":"101",
    "name":"Laptop",
    "price":85000
}
```

---

# Step 8 — List Products

Endpoint:

```http
GET /products
```

Lambda:

```python
table.scan()
```

Example response:

```json
[
    {
        "productId":"101",
        "name":"Laptop"
    },
    {
        "productId":"102",
        "name":"Keyboard"
    }
]
```

---

# Step 9 — Update Product

Endpoint:

```http
PUT /products/101
```

Body:

```json
{
    "price":90000
}
```

Lambda:

```python
UpdateItem()
```

Response:

```http
200 OK
```

---

# Step 10 — Delete Product

Endpoint:

```http
DELETE /products/101
```

Lambda:

```python
DeleteItem()
```

Response:

```http
204 No Content
```

---

# Configure API Gateway

Routes:

```text
POST /products

GET /products

GET /products/{id}

PUT /products/{id}

DELETE /products/{id}
```

Each route invokes the same Lambda function.

---

# Lambda Proxy Event

Example:

```json
{
    "requestContext": {
        "http": {
            "method": "POST"
        }
    },
    "rawPath": "/products"
}
```

The Lambda function determines which operation to execute.

---

# Routing Logic

Typical pattern:

```text
Method

↓

POST

↓

Create

---------------------

GET

↓

Read

---------------------

PUT

↓

Update

---------------------

DELETE

↓

Delete
```

---

# Testing Using Postman

### Create

```http
POST /products
```

### Read

```http
GET /products/101
```

### Update

```http
PUT /products/101
```

### Delete

```http
DELETE /products/101
```

Verify every endpoint.

---

# Error Handling

If the product doesn't exist:

```http
404 Not Found
```

Invalid request:

```http
400 Bad Request
```

Unexpected failure:

```http
500 Internal Server Error
```

Never return generic success responses for failures.

---

# Validation

Validate:

- productId
- name
- price

Reject invalid requests before accessing DynamoDB.

---

# Logging

Log:

```text
Request ID

↓

Method

↓

Path

↓

Status Code
```

Avoid logging sensitive information.

---

# Monitoring

Monitor:

- Request Count
- Latency
- 4XX Errors
- 5XX Errors
- Lambda Duration
- DynamoDB Consumed Capacity

Use CloudWatch dashboards to observe application health.

---

# Production Improvements

A production version should additionally include:

- JWT Authentication
- Request Validation
- API Keys
- Usage Plans
- CloudFront
- AWS WAF
- Structured Logging
- Correlation IDs
- CI/CD
- Infrastructure as Code

---

# Production Architecture

```text
                   Client

                      │

                      ▼

               Amazon API Gateway

                      │

                      ▼

                 AWS Lambda

                      │

                      ▼

              Amazon DynamoDB

                      │

                      ▼

          CloudWatch Metrics & Logs
```

This architecture forms the foundation of many serverless CRUD applications.

---

# Cleanup

Delete:

- API Gateway
- Lambda Function
- DynamoDB Table

to avoid ongoing AWS charges.

---

# What You Learned

In this project, you learned how to:

- Create a DynamoDB table.
- Build a CRUD API using API Gateway and Lambda.
- Store and retrieve data from DynamoDB.
- Configure multiple API routes.
- Handle common HTTP methods.
- Return appropriate HTTP status codes.
- Monitor API performance using CloudWatch.

---

# Common Interview Questions

### Why use DynamoDB for this project?

DynamoDB is a fully managed NoSQL database that integrates seamlessly with Lambda, offers low-latency performance, and scales automatically without server management.

---

### Why is a single Lambda function often used for CRUD APIs?

A single Lambda function can inspect the HTTP method and route to perform Create, Read, Update, or Delete operations. While suitable for small applications, larger systems often split operations into separate Lambda functions for better maintainability.

---

### Why should POST return 201 Created?

HTTP 201 indicates that a new resource has been successfully created, making it the appropriate status code for successful create operations.

---

### Why shouldn't Scan be used for large DynamoDB tables?

`Scan` reads every item in the table, making it expensive and slow for large datasets. Production applications should prefer `Query` operations using well-designed partition and sort keys.

---

### What production improvements would you make?

Typical enhancements include:

- JWT authentication with Cognito
- Request validation
- API Gateway throttling
- CloudFront
- AWS WAF
- Structured logging
- Monitoring and alarms
- Infrastructure as Code
- CI/CD pipelines

---

# Key Takeaways

- API Gateway, Lambda, and DynamoDB provide a powerful serverless architecture for building CRUD APIs.
- REST endpoints map naturally to Create, Read, Update, and Delete operations.
- Proper validation, error handling, logging, and monitoring are essential for production-quality APIs.
- DynamoDB offers scalable, fully managed storage that integrates efficiently with Lambda.
- This project serves as the foundation for building secure, authenticated, and production-ready serverless applications.