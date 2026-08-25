# Production Serverless API

## Overview

In the previous hands-on projects, you learned how to:

- Build an HTTP API
- Create a CRUD API
- Secure APIs using Amazon Cognito

This project combines those concepts into a **production-ready serverless architecture**.

Instead of focusing on a single AWS service, you'll build an API that incorporates authentication, monitoring, security, scalability, and Infrastructure as Code principles.

This architecture represents a common production deployment for modern serverless applications.

---

# What You'll Build

```text
                    Users

                       │

                       ▼

                 CloudFront

                       │

                       ▼

                   AWS WAF

                       │

                       ▼

              Amazon API Gateway

                       │

             JWT Authorizer

                       │

                       ▼

                 AWS Lambda

                       │

                       ▼

             Amazon DynamoDB
```

The API supports secure CRUD operations while remaining fully serverless.

---

# Features

The application includes:

- REST API
- JWT Authentication
- CRUD Operations
- DynamoDB Storage
- CloudWatch Logging
- CloudWatch Metrics
- AWS X-Ray Tracing
- CloudFront
- AWS WAF
- HTTPS
- Auto Scaling

---

# Project Architecture

```text
Client

↓

CloudFront

↓

AWS WAF

↓

API Gateway

↓

JWT Validation

↓

Lambda

↓

DynamoDB
```

Each service performs a dedicated responsibility.

---

# Step 1 — Create DynamoDB

Table:

```text
Products
```

Partition Key:

```text
productId
```

Capacity Mode:

```text
On-Demand
```

---

# Step 2 — Create Lambda

Runtime:

```text
Python 3.12
```

Function:

```text
product-service
```

Grant:

```text
CRUD

↓

Products Table
```

permissions.

---

# Step 3 — Implement CRUD Logic

Support:

```text
POST

GET

PUT

DELETE
```

Return appropriate:

```http
200

201

204

400

404

500
```

status codes.

---

# Step 4 — Create HTTP API

Create:

```text
HTTP API
```

Integrate:

```text
Lambda
```

---

# Step 5 — Configure Routes

Example:

```text
POST /products

GET /products

GET /products/{id}

PUT /products/{id}

DELETE /products/{id}
```

---

# Step 6 — Create Cognito User Pool

Create:

```text
ProductUsers
```

Enable:

- Email Login
- Password Policy
- App Client

---

# Step 7 — Configure JWT Authorizer

Attach:

```text
JWT Authorizer
```

to every protected route.

Unauthenticated requests should return:

```http
401 Unauthorized
```

---

# Step 8 — Configure CORS

Allow:

```text
https://app.company.com
```

Methods:

```text
GET

POST

PUT

DELETE
```

Headers:

```text
Authorization

Content-Type
```

---

# Step 9 — Enable CloudWatch Logs

Enable:

```text
Access Logs

↓

Execution Logs
```

Include:

- Request ID
- Method
- Status
- Latency

---

# Step 10 — Enable AWS X-Ray

Enable tracing for:

```text
API Gateway

↓

Lambda
```

This allows end-to-end request tracing.

---

# Step 11 — Configure CloudFront

Place CloudFront before API Gateway.

```text
Client

↓

CloudFront

↓

API Gateway
```

Benefits:

- Lower latency
- Edge caching
- HTTPS optimization

---

# Step 12 — Attach AWS WAF

Associate a Web ACL with CloudFront.

Enable managed rules for:

- SQL Injection
- XSS
- IP Reputation
- Rate Limiting

---

# Step 13 — Configure Custom Domain

Example:

```text
api.company.com
```

Using:

- ACM Certificate
- Route 53 Alias Record

Clients no longer use the default execute-api URL.

---

# Step 14 — Enable Monitoring

Create CloudWatch Alarms for:

- 5XX Errors
- High Latency
- Lambda Errors
- DynamoDB Throttling

Notifications:

```text
CloudWatch

↓

SNS

↓

Email
```

---

# Step 15 — Configure CI/CD

Pipeline:

```text
GitHub

↓

GitHub Actions

↓

Tests

↓

Deploy

↓

API Gateway

↓

Lambda
```

Infrastructure should be deployed using:

- CloudFormation
- AWS CDK
- Terraform

---

# Request Flow

```text
Browser

↓

CloudFront

↓

AWS WAF

↓

API Gateway

↓

JWT Validation

↓

Lambda

↓

DynamoDB

↓

Response
```

---

# Authentication Flow

```text
User

↓

Amazon Cognito

↓

JWT

↓

API Gateway

↓

Lambda
```

JWT validation occurs before Lambda execution.

---

# Logging Strategy

Capture:

- Request ID
- User ID
- Endpoint
- Status Code
- Execution Time

Use structured JSON logs for easier analysis.

---

# Monitoring Dashboard

Monitor:

- Request Count
- Latency
- Integration Latency
- 4XX Errors
- 5XX Errors
- Lambda Duration
- DynamoDB Read Capacity
- DynamoDB Write Capacity

---

# Scaling

```text
Traffic

↓

API Gateway

↓

Lambda

↓

DynamoDB
```

All three services scale automatically based on demand.

---

# Security Layers

```text
CloudFront

↓

AWS WAF

↓

API Gateway

↓

JWT

↓

IAM

↓

Lambda
```

Multiple layers protect the API.

---

# Production Checklist

Verify:

- HTTPS enabled
- JWT authentication
- CORS configured
- CloudWatch enabled
- X-Ray enabled
- WAF enabled
- CloudFront enabled
- Custom domain configured
- IAM least privilege applied
- Infrastructure as Code used
- CI/CD automated

---

# Expected Folder Structure

```text
serverless-api/

├── template.yaml
├── lambda/
│   ├── app.py
│   ├── requirements.txt
│   └── handlers.py
│
├── infrastructure/
│   ├── api.yaml
│   ├── dynamodb.yaml
│   └── iam.yaml
│
├── tests/
│
└── README.md
```

This structure separates application code from infrastructure.

---

# Production Architecture

```text
                   Users

                      │

                      ▼

                 Route 53

                      │

                      ▼

                CloudFront

                      │

                      ▼

                  AWS WAF

                      │

                      ▼

             Amazon API Gateway

                      │

              JWT Authorizer

                      │

                      ▼

                AWS Lambda

                      │

                      ▼

               DynamoDB Table

                      │

                      ▼

     CloudWatch • X-Ray • SNS
```

This architecture is widely used for production-grade serverless APIs.

---

# Common Issues

### 401 Unauthorized

Verify:

- JWT Token
- Cognito Configuration
- JWT Authorizer

---

### 403 Forbidden

Verify:

- IAM Permissions
- Resource Policies
- WAF Rules

---

### 500 Internal Server Error

Check:

- Lambda Logs
- CloudWatch
- X-Ray Traces

---

### High Latency

Investigate:

- Cold Starts
- DynamoDB Queries
- Lambda Duration
- External Dependencies

---

# What You Learned

In this project, you learned how to:

- Build a complete production-style serverless API.
- Protect endpoints using Cognito JWT authentication.
- Store application data in DynamoDB.
- Improve performance with CloudFront.
- Secure APIs using AWS WAF.
- Monitor applications using CloudWatch and X-Ray.
- Automate deployments with CI/CD and Infrastructure as Code.

---

# Common Interview Questions

### Why is this architecture considered production-ready?

It combines security, scalability, monitoring, authentication, logging, and automated deployment while using fully managed AWS services that scale automatically.

---

### Why place CloudFront in front of API Gateway?

CloudFront reduces latency by serving requests from edge locations, improves TLS performance, and integrates with AWS WAF for edge security.

---

### Why use Cognito instead of implementing authentication inside Lambda?

Centralizing authentication in API Gateway prevents unauthorized requests from reaching Lambda, reduces duplicated code, and improves security.

---

### How does this architecture scale?

API Gateway, Lambda, and DynamoDB all scale automatically. Combined with CloudFront caching, the architecture can handle significant traffic without manual provisioning.

---

### Why use Infrastructure as Code?

Infrastructure as Code ensures API Gateway, Lambda, DynamoDB, IAM, and other AWS resources are version-controlled, reproducible, reviewable, and easy to deploy consistently across environments.

---

# Key Takeaways

- A production serverless API combines API Gateway, Lambda, DynamoDB, Cognito, CloudFront, and AWS WAF into a secure, scalable architecture.
- Authentication, monitoring, logging, and automated deployments are as important as the application code itself.
- CloudWatch, X-Ray, and CloudFront provide visibility and performance improvements without additional server management.
- Infrastructure as Code and CI/CD enable repeatable, reliable deployments suitable for enterprise environments.
- This architecture demonstrates how multiple AWS managed services work together to build highly available, production-ready APIs.