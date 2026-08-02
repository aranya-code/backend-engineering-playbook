# Deploy a Private API

## Overview

Not every API should be accessible from the public internet.

Enterprise applications commonly expose APIs that are intended only for internal services, corporate networks, or workloads running inside an AWS Virtual Private Cloud (VPC).

Examples include:

- Internal microservices
- HR systems
- Payment services
- Inventory APIs
- Internal admin APIs
- Database management APIs

Amazon API Gateway supports **Private APIs**, allowing API access only through **AWS PrivateLink (Interface VPC Endpoints)**.

In this hands-on project, you'll deploy a Private API and access it securely from within your VPC.

---

# What You'll Build

```text
             EC2 Instance

                  │

                  ▼

          VPC Interface Endpoint

                  │

                  ▼

      Amazon API Gateway (Private)

                  │

                  ▼

             AWS Lambda

                  │

                  ▼

             DynamoDB
```

The API is completely inaccessible from the public internet.

---

# Prerequisites

Complete:

- Build Your First HTTP API
- Build a CRUD REST API
- Secure API with Cognito

You should also have:

- One VPC
- One private subnet
- One EC2 instance inside the VPC

---

# Architecture

```text
             Internet

                 │

                 ▼

            No Access

-------------------------------

            Private VPC

                 │

                 ▼

         Interface Endpoint

                 │

                 ▼

          Private API Gateway

                 │

                 ▼

             Lambda Function
```

Only resources inside the VPC can access the API.

---

# Step 1 — Create a Lambda Function

Create:

```text
private-api
```

Runtime:

```text
Python 3.12
```

Example code:

```python
import json

def lambda_handler(event, context):

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Private API Working"
        })
    }
```

Deploy the function.

---

# Step 2 — Create a REST API

Navigate:

```text
AWS Console

↓

API Gateway

↓

Create API

↓

REST API
```

Private APIs are currently supported only with **REST APIs**, not HTTP APIs.

---

# Step 3 — Choose Private Endpoint Type

Endpoint Type:

```text
Private
```

Instead of:

```text
Regional

Edge Optimized
```

Click:

```text
Create API
```

---

# Step 4 — Create Resource

Example:

```text
/private
```

Method:

```text
GET
```

---

# Step 5 — Configure Lambda Integration

Integration:

```text
Lambda

↓

private-api
```

Deploy the API.

---

# Step 6 — Create a VPC Endpoint

Navigate:

```text
AWS Console

↓

VPC

↓

Endpoints

↓

Create Endpoint
```

Service:

```text
com.amazonaws.<region>.execute-api
```

Type:

```text
Interface Endpoint
```

---

# Step 7 — Select the VPC

Choose:

- Your VPC
- Private subnet(s)
- Security Group

Example:

```text
Production VPC

↓

Private Subnet

↓

Security Group
```

Create the endpoint.

---

# Step 8 — Enable Private DNS

Enable:

```text
Private DNS

✓ Enabled
```

This allows applications to use the standard API Gateway hostname inside the VPC.

---

# Step 9 — Attach Resource Policy

Open:

```text
API Gateway

↓

Resource Policy
```

Example:

```text
Allow

↓

Specific VPC Endpoint
```

Instead of allowing everyone.

---

# Example Resource Policy

Restrict access to one Interface Endpoint.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "execute-api:Invoke",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:SourceVpce": "vpce-xxxxxxxx"
        }
      }
    }
  ]
}
```

Only requests coming through this endpoint are permitted.

---

# Step 10 — Deploy API

Deploy to stage:

```text
prod
```

Copy the Invoke URL.

---

# Test from EC2

SSH into the EC2 instance.

Run:

```bash
curl https://<api-id>.execute-api.<region>.amazonaws.com/prod/private
```

Expected:

```json
{
    "message":"Private API Working"
}
```

---

# Test from Your Laptop

Run the same command outside AWS.

Expected:

```text
403 Forbidden
```

or

```text
Connection Failed
```

This confirms the API is private.

---

# Request Flow

```text
EC2

↓

VPC Endpoint

↓

Private API Gateway

↓

Lambda

↓

Response
```

No traffic leaves the AWS network.

---

# Understanding AWS PrivateLink

PrivateLink provides private connectivity.

Instead of:

```text
Internet

↓

API Gateway
```

Traffic flows through:

```text
AWS Network

↓

Private Endpoint

↓

API Gateway
```

Benefits:

- Lower attack surface
- No public internet
- Private routing

---

# Security Groups

Ensure the VPC Endpoint Security Group allows:

```text
HTTPS

↓

TCP 443
```

Without this rule, requests will fail.

---

# DNS Resolution

With Private DNS enabled:

```text
execute-api.amazonaws.com

↓

Private IP
```

DNS resolves to the Interface Endpoint instead of the public endpoint.

---

# Logging

Enable:

```text
Access Logs

Execution Logs
```

CloudWatch records:

- Requests
- Errors
- Latency

---

# Monitoring

Monitor:

- Request Count
- Latency
- 4XX Errors
- 5XX Errors

CloudWatch metrics work exactly like public APIs.

---

# Common Errors

### 403 Forbidden

Cause:

```text
Incorrect Resource Policy
```

Verify:

```text
aws:SourceVpce
```

matches the endpoint ID.

---

### Timeout

Cause:

```text
Security Group

↓

Port 443 Blocked
```

Allow HTTPS traffic.

---

### DNS Resolution Failure

Cause:

```text
Private DNS Disabled
```

Enable:

```text
Private DNS
```

for the Interface Endpoint.

---

### API Not Reachable

Verify:

- Correct VPC
- Correct subnet
- Interface Endpoint status
- API deployment stage

---

# Production Improvements

A production deployment should also include:

- AWS WAF (for public APIs)
- IAM Authentication
- Cognito Authentication
- CloudWatch Alarms
- X-Ray Tracing
- Infrastructure as Code
- CI/CD
- Multi-AZ Interface Endpoints

---

# Production Architecture

```text
                 EC2

                  │

                  ▼

         Interface Endpoint

                  │

                  ▼

       Private API Gateway

                  │

          IAM Authentication

                  │

                  ▼

             AWS Lambda

                  │

                  ▼

              DynamoDB
```

---

# Cleanup

Delete:

- REST API
- Interface Endpoint
- Lambda Function

if no longer required.

---

# What You Learned

In this hands-on project, you learned how to:

- Create a Private REST API.
- Configure a Lambda integration.
- Create an Interface VPC Endpoint.
- Enable Private DNS.
- Restrict API access using Resource Policies.
- Test private connectivity from within a VPC.
- Prevent public internet access to sensitive APIs.

---

# Common Interview Questions

### What is a Private API in API Gateway?

A Private API is accessible only through Interface VPC Endpoints (AWS PrivateLink), preventing direct access from the public internet.

---

### Why are Private APIs useful?

They reduce the attack surface by allowing only trusted resources inside a VPC to invoke sensitive APIs.

---

### Why is an Interface VPC Endpoint required?

Private APIs are reachable only through Interface VPC Endpoints, which provide private network connectivity between the VPC and API Gateway.

---

### Can HTTP APIs be Private APIs?

No.

Currently, Private APIs are supported only for **REST APIs**.

---

### How do Resource Policies improve security?

Resource Policies restrict which AWS accounts, VPCs, or VPC Endpoints are allowed to invoke the API, adding an additional layer of access control.

---

# Key Takeaways

- Private APIs are designed for internal applications and are not exposed to the public internet.
- AWS PrivateLink enables secure, private connectivity to API Gateway using Interface VPC Endpoints.
- Resource Policies ensure that only approved VPC Endpoints can invoke the API.
- Private APIs reduce the attack surface while maintaining all the monitoring and operational capabilities of API Gateway.
- This architecture is commonly used for enterprise microservices, internal platforms, and highly secure backend systems.