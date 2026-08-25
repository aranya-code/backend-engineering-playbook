# IAM Authorization

## Overview

AWS Identity and Access Management (IAM) is one of the authentication and authorization mechanisms supported by Amazon API Gateway.

With IAM Authorization, only AWS principals (users, roles, or services) that have the appropriate IAM permissions can invoke an API.

Unlike Cognito or JWT authentication, IAM is primarily designed for:

- Internal AWS applications
- Microservice-to-microservice communication
- Backend systems
- Automation scripts
- AWS SDK and CLI access

IAM Authorization is **not typically used for public-facing web or mobile applications** because end users generally do not possess AWS credentials.

---

# How IAM Authorization Works

When a client invokes an API protected by IAM Authorization, the request must be **cryptographically signed** using **AWS Signature Version 4 (SigV4).**

```text
Client

↓

Sign Request (SigV4)

↓

Amazon API Gateway

↓

IAM Authorization

↓

Backend
```

API Gateway verifies the signature before processing the request.

If the signature is invalid or missing, access is denied.

---

# Authentication Flow

```text
AWS User / Role

↓

AWS Credentials

↓

SigV4 Signed Request

↓

API Gateway

↓

IAM Policy Evaluation

↓

Allow or Deny

↓

Backend
```

Only authenticated AWS identities can invoke the API.

---

# AWS Signature Version 4 (SigV4)

SigV4 is AWS's request signing protocol.

Before sending a request, the client calculates a signature using:

- Access Key ID
- Secret Access Key
- Request Method
- URI
- Headers
- Request Body
- Timestamp

Example:

```text
GET /orders

↓

Sign Request

↓

Authorization Header

↓

API Gateway
```

API Gateway independently calculates the signature.

If both signatures match:

```text
Access Granted
```

Otherwise:

```http
403 Forbidden
```

---

# IAM Policy

API access is controlled using IAM policies.

Example policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "execute-api:Invoke",
            "Resource": "*"
        }
    ]
}
```

This grants permission to invoke API Gateway.

---

# Least Privilege

Rather than allowing access to every API:

Bad:

```json
"Resource":"*"
```

Use specific API ARNs.

Example:

```text
arn:aws:execute-api:
us-east-1:
123456789012:
abc123/prod/GET/orders
```

This limits access to one API method.

---

# API ARN Structure

An API Gateway ARN follows this pattern:

```text
arn:aws:execute-api:
region:
account-id:
api-id/stage/method/resource
```

Example:

```text
arn:aws:execute-api:
us-east-1:
123456789012:
abc123/prod/GET/products
```

Components:

- Region
- AWS Account
- API ID
- Stage
- HTTP Method
- Resource Path

---

# IAM Authorization Example

Suppose an EC2 instance needs to invoke an internal API.

```text
EC2 Instance

↓

IAM Role

↓

API Gateway

↓

Lambda
```

No usernames or passwords are required.

The EC2 instance signs requests using its IAM role credentials.

---

# Cross-Service Communication

A common use case:

```text
Lambda A

↓

IAM Role

↓

API Gateway

↓

Lambda B
```

Only Lambda A's IAM role can invoke the API.

---

# Cross-Account Access

IAM Authorization also supports cross-account access.

```text
AWS Account A

↓

IAM User

↓

API Gateway

↓

AWS Account B
```

This is commonly used in enterprise environments.

---

# Example Request

Using AWS CLI:

```bash
aws apigatewayv2 invoke-api \
    --api-id abc123
```

Using AWS SDK:

```python
import boto3
```

The SDK automatically signs requests using SigV4.

---

# IAM Authorization Architecture

```text
             EC2

              │

              ▼

          IAM Role

              │

              ▼

      Signed Request

              │

              ▼

      Amazon API Gateway

              │

              ▼

      Lambda / ECS / EC2
```

No custom authentication code is required.

---

# Advantages

## Native AWS Security

Uses AWS Identity and Access Management.

---

## No Password Storage

AWS credentials handle authentication.

---

## Fine-Grained Permissions

Access can be controlled down to:

- API
- Stage
- HTTP Method
- Resource

---

## Automatic Credential Rotation

IAM Roles provide temporary credentials.

---

## SDK Support

AWS SDKs automatically generate SigV4 signatures.

---

# Disadvantages

## AWS-Specific

Clients must possess AWS credentials.

---

## Not Suitable for Public Users

Web browsers and mobile apps typically cannot securely store AWS credentials.

---

## More Complex Than JWT

Request signing adds complexity compared to bearer tokens.

---

# Typical Use Cases

IAM Authorization is commonly used for:

- Internal APIs
- Lambda-to-Lambda communication
- EC2 applications
- ECS services
- Automation scripts
- AWS CLI
- CI/CD pipelines
- Cross-account integrations

---

# IAM vs Cognito

| Feature | IAM | Cognito |
|----------|-----|----------|
| Intended Users | AWS Identities | Application Users |
| Uses AWS Credentials | ✅ | ❌ |
| Uses JWT | ❌ | ✅ |
| Mobile Apps | ❌ | ✅ |
| Internal APIs | ✅ | Limited |
| Service-to-Service | ✅ | ❌ |

---

# IAM vs Lambda Authorizer

| Feature | IAM | Lambda Authorizer |
|----------|-----|-------------------|
| Custom Logic | ❌ | ✅ |
| AWS Credentials | Required | Optional |
| Performance | Higher | Slightly Lower |
| External Identity Providers | ❌ | ✅ |

---

# Real-World Example

A company has multiple internal microservices.

```text
Order Service

↓

API Gateway

↓

Inventory Service
```

Only services running with approved IAM roles can invoke the API.

No external client can access it.

---

# Common Mistakes

### Using IAM for Public APIs

Bad choice.

Public users do not have AWS credentials.

Instead:

- Amazon Cognito
- JWT Authorizers
- OAuth

are better choices.

---

### Granting Excessive Permissions

Avoid:

```json
"Resource":"*"
```

Grant only the required API resources.

---

### Hardcoding AWS Credentials

Never store:

- Access Keys
- Secret Keys

inside applications.

Use:

- IAM Roles
- AWS STS
- Temporary Credentials

---

# Common Interview Questions

### What is IAM Authorization?

IAM Authorization allows API Gateway to authenticate AWS users and services using AWS Signature Version 4 (SigV4) and IAM policies.

---

### When should IAM Authorization be used?

It is best suited for internal AWS workloads such as EC2, Lambda, ECS, AWS CLI, SDKs, and service-to-service communication.

---

### Why is IAM not recommended for mobile applications?

Because mobile applications should not store long-term AWS credentials. User authentication is better handled using Amazon Cognito or another OAuth/OIDC provider.

---

### What permission allows invoking an API Gateway API?

```text
execute-api:Invoke
```

This permission is granted through an IAM policy.

---

# Best Practices

- Use IAM Authorization for internal AWS workloads.
- Follow the Principle of Least Privilege.
- Prefer IAM Roles over long-term access keys.
- Restrict permissions to specific API ARNs.
- Never embed AWS credentials in source code.
- Use temporary credentials through IAM Roles or AWS STS.
- Use Cognito or JWT Authorizers for customer-facing APIs instead of IAM.

---

# Key Takeaways

- IAM Authorization authenticates AWS identities using **AWS Signature Version 4 (SigV4)**.
- Access is controlled using IAM policies with the **execute-api:Invoke** permission.
- IAM Authorization is ideal for internal AWS applications, automation, and service-to-service communication.
- It provides fine-grained access control and integrates seamlessly with AWS SDKs and IAM Roles.
- Public-facing applications should generally use Cognito or JWT-based authentication instead of IAM Authorization.