# API Gateway + Lambda

## Overview

Amazon API Gateway and AWS Lambda form one of the most common serverless architectures on AWS.

In this architecture:

- API Gateway exposes HTTPS endpoints.
- Lambda contains the business logic.
- API Gateway invokes Lambda whenever an API request is received.

This combination enables developers to build scalable APIs without provisioning or managing servers.

It is widely used for:

- REST APIs
- Mobile backends
- Web applications
- SaaS platforms
- Event-driven applications
- Microservices

---

# Why API Gateway + Lambda?

Without API Gateway:

```text
Client

↓

Lambda Function URL
```

Problems:

- Limited API management
- No API Keys
- No Usage Plans
- Limited authentication options
- No request validation
- Limited monitoring

With API Gateway:

```text
Client

↓

API Gateway

↓

Lambda
```

Benefits:

- Authentication
- Authorization
- Throttling
- Request validation
- Monitoring
- API versioning
- Custom domains

---

# Architecture

```text
              Client

                 │

                 ▼

         Amazon API Gateway

                 │

        Authentication

                 │

        Request Validation

                 │

                 ▼

           AWS Lambda

                 │

                 ▼

      DynamoDB / RDS / S3
```

API Gateway acts as the frontend while Lambda executes business logic.

---

# Request Flow

```text
Client

↓

HTTPS Request

↓

API Gateway

↓

Authentication

↓

Request Validation

↓

Lambda Invocation

↓

Business Logic

↓

Response

↓

API Gateway

↓

Client
```

---

# Example API

```http
GET /products/101
```

API Gateway invokes:

```text
Product Lambda
```

Lambda returns:

```json
{
    "id":101,
    "name":"Laptop"
}
```

API Gateway sends the response back to the client.

---

# Lambda Proxy Integration

The most commonly used integration is **Lambda Proxy Integration**.

Flow:

```text
Client

↓

API Gateway

↓

Entire HTTP Request

↓

Lambda
```

Lambda receives:

- Headers
- Query parameters
- Path parameters
- Request body
- Context information

Lambda generates the complete HTTP response.

---

# Lambda Event

Example event received by Lambda:

```json
{
  "resource": "/products/{id}",
  "path": "/products/101",
  "httpMethod": "GET",
  "headers": {
    "Authorization": "Bearer token"
  },
  "queryStringParameters": {
    "sort": "price"
  },
  "pathParameters": {
    "id": "101"
  },
  "body": null
}
```

API Gateway automatically creates this event.

---

# Lambda Response

Lambda returns:

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"id\":101,\"name\":\"Laptop\"}"
}
```

API Gateway converts this into an HTTP response.

---

# Authentication Flow

```text
Client

↓

JWT Token

↓

API Gateway

↓

JWT Validation

↓

Lambda

↓

Response
```

Lambda only executes after successful authentication.

---

# Authorization

API Gateway can authorize requests using:

- IAM
- Amazon Cognito
- JWT Authorizers
- Lambda Authorizers

Unauthorized requests never invoke Lambda.

---

# Request Validation

Example:

```json
{}
```

Expected:

```json
{
  "email":"john@example.com"
}
```

API Gateway returns:

```http
400 Bad Request
```

Lambda is not invoked.

---

# Error Handling

Lambda throws an exception:

```text
Database Connection Failed
```

API Gateway returns:

```http
500 Internal Server Error
```

Custom error responses can also be configured.

---

# Monitoring

API Gateway publishes:

- Request Count
- Latency
- 4XX Errors
- 5XX Errors

Lambda publishes:

- Duration
- Errors
- Invocations
- Concurrent Executions

Together they provide complete visibility.

---

# Logging

Logs are available in:

```text
API Gateway

↓

CloudWatch Logs

----------------------

Lambda

↓

CloudWatch Logs
```

Request tracing becomes easier using Request IDs.

---

# X-Ray Integration

```text
Client

↓

API Gateway

↓

Lambda

↓

DynamoDB
```

AWS X-Ray shows:

- Complete request flow
- Latency
- Errors
- Service map

---

# Scalability

Both services scale automatically.

```text
10 Requests

↓

100 Requests

↓

10,000 Requests

↓

1 Million Requests
```

No infrastructure management is required.

---

# High Availability

```text
API Gateway

↓

Multi-AZ

↓

Lambda

↓

Multi-AZ
```

The architecture is highly available by default.

---

# Cold Starts

The first Lambda invocation after inactivity may experience a cold start.

```text
Request

↓

Cold Start

↓

Lambda Initialization

↓

Execution
```

Mitigation:

- Provisioned Concurrency
- Smaller deployment packages
- Efficient initialization code

---

# Common Use Cases

API Gateway + Lambda is commonly used for:

- User authentication
- CRUD APIs
- Payment APIs
- Inventory systems
- Notification services
- Mobile backends
- SaaS platforms
- Internal APIs

---

# Advantages

- Fully serverless
- Automatic scaling
- High availability
- Pay-per-use pricing
- Built-in security
- Easy monitoring
- Minimal operational overhead

---

# Limitations

- Lambda cold starts
- Maximum Lambda execution time
- Payload size limits
- Stateless execution model
- Backend concurrency limits

Applications with long-running workloads may be better suited to ECS or EC2.

---

# Production Architecture

```text
                    Client

                       │

                       ▼

                 Amazon Route 53

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

       Authentication & Validation

                       │

                       ▼

                 AWS Lambda

                       │

        ┌──────────────┼──────────────┐

        ▼              ▼              ▼

   DynamoDB         Amazon S3      Amazon SQS
```

This is a common production architecture for modern serverless applications.

---

# Best Practices

- Use Lambda Proxy Integration unless request transformation is required.
- Keep Lambda functions small and focused on a single responsibility.
- Validate requests in API Gateway before invoking Lambda.
- Use Provisioned Concurrency for latency-sensitive APIs.
- Enable CloudWatch Logs, Metrics, and X-Ray.
- Return proper HTTP status codes from Lambda.
- Store configuration in environment variables or AWS Systems Manager Parameter Store.
- Follow the principle of least privilege for Lambda IAM roles.
- Design Lambda functions to be stateless.

---

# Common Interview Questions

### Why use API Gateway with Lambda instead of Lambda Function URLs?

API Gateway provides advanced features such as authentication, authorization, request validation, throttling, API Keys, monitoring, custom domains, and caching that Lambda Function URLs do not offer.

---

### What is Lambda Proxy Integration?

Lambda Proxy Integration forwards the complete HTTP request to Lambda, allowing the function to handle request parsing and generate the full HTTP response.

---

### Does API Gateway scale automatically with Lambda?

Yes.

Both API Gateway and Lambda automatically scale based on incoming traffic.

---

### What causes Lambda cold starts?

A cold start occurs when AWS creates a new execution environment for a Lambda function after inactivity or during scaling events.

---

### Where should request validation occur?

Whenever possible, request validation should occur in API Gateway so invalid requests are rejected before Lambda is invoked, reducing execution cost and backend load.

---

# Key Takeaways

- API Gateway and Lambda together form the foundation of modern serverless API architectures.
- API Gateway handles API management concerns such as authentication, authorization, validation, throttling, and monitoring, while Lambda executes business logic.
- Lambda Proxy Integration is the preferred integration pattern for most production workloads because it forwards the complete HTTP request to Lambda.
- The architecture automatically scales, is highly available, and integrates seamlessly with CloudWatch, X-Ray, DynamoDB, S3, and other AWS services.
- Following best practices such as request validation, least-privilege IAM, observability, and stateless function design results in secure, scalable, and maintainable production APIs.