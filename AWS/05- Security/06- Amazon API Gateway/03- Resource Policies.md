# Resource Policies

## Overview

A **Resource Policy** is a resource-based IAM policy attached directly to an Amazon API Gateway API.

Unlike IAM Authorization, which determines **what an authenticated AWS principal is allowed to do**, a Resource Policy determines **who is allowed to access the API in the first place**.

Resource Policies are commonly used to:

- Allow specific AWS accounts
- Deny specific AWS accounts
- Restrict access by IP address
- Restrict access to specific VPC Endpoints
- Restrict access to specific VPCs
- Create private APIs
- Enable cross-account access

Think of a Resource Policy as the **front gate** of your API.

Even if a user has IAM permissions, the Resource Policy can still deny access.

---

# Where Does a Resource Policy Apply?

```text
               Internet
                   │
                   ▼
          Resource Policy
                   │
                   ▼
         Amazon API Gateway
                   │
          IAM Authorization
                   │
                   ▼
            Backend Service
```

A request must satisfy the Resource Policy **before** API Gateway invokes the backend.

---

# Why Resource Policies?

Imagine your API should only be accessible by applications running inside your AWS organization.

Without a Resource Policy:

```text
Internet

↓

API Gateway

↓

Backend
```

Anyone with valid credentials could potentially invoke the API.

With a Resource Policy:

```text
Internet

↓

Resource Policy

↓

API Gateway

↓

Backend
```

Only approved clients are allowed through.

---

# IAM Policy vs Resource Policy

This is one of the most common interview questions.

| IAM Policy | Resource Policy |
|------------|-----------------|
| Attached to a User, Role, or Group | Attached to an API |
| Defines what a principal can do | Defines who can access the API |
| Identity-based | Resource-based |
| Evaluated after authentication | Evaluated before backend invocation |

Think of them as answering different questions.

IAM Policy:

> **What can this user do?**

Resource Policy:

> **Who is allowed to access this API?**

---

# Resource Policy Evaluation

When a request arrives:

```text
Client

↓

Resource Policy

↓

Allowed?

↓

Yes

↓

IAM Authorization

↓

Backend
```

If denied:

```http
403 Forbidden
```

The backend is never invoked.

---

# Basic Resource Policy

Example:

```json
{
    "Version":"2012-10-17",
    "Statement":[
        {
            "Effect":"Allow",
            "Principal":"*",
            "Action":"execute-api:Invoke",
            "Resource":"execute-api:/*"
        }
    ]
}
```

This policy allows everyone.

This is suitable only for public APIs.

---

# Allow Specific AWS Account

Suppose only one AWS account should invoke the API.

```json
{
    "Effect":"Allow",
    "Principal":{
        "AWS":"arn:aws:iam::123456789012:root"
    },
    "Action":"execute-api:Invoke",
    "Resource":"execute-api:/*"
}
```

Only Account **123456789012** can invoke the API.

---

# Allow Specific IAM Role

Instead of allowing an entire AWS account:

```json
{
    "Effect":"Allow",
    "Principal":{
        "AWS":"arn:aws:iam::123456789012:role/InventoryServiceRole"
    },
    "Action":"execute-api:Invoke",
    "Resource":"execute-api:/*"
}
```

Only this IAM role gains access.

---

# Restrict by IP Address

A common security requirement is allowing only office networks.

Example:

```text
Office Network

203.0.113.0/24
```

Resource Policy:

```json
{
    "Condition":{
        "IpAddress":{
            "aws:SourceIp":[
                "203.0.113.0/24"
            ]
        }
    }
}
```

Only requests from that IP range are accepted.

---

# Deny Specific IP Addresses

Sometimes certain IPs should always be blocked.

```json
{
    "Effect":"Deny",
    "Condition":{
        "IpAddress":{
            "aws:SourceIp":[
                "198.51.100.0/24"
            ]
        }
    }
}
```

Requests from those addresses are rejected.

---

# Private API Restriction

Private APIs should only be accessed through Interface VPC Endpoints.

Architecture:

```text
EC2

↓

VPC Endpoint

↓

Private API

↓

Backend
```

Resource Policy:

```json
{
    "Condition":{
        "StringEquals":{
            "aws:SourceVpce":
                "vpce-123456789"
        }
    }
}
```

Only that VPC Endpoint can access the API.

---

# Restrict by VPC

Another option is restricting requests to a specific VPC.

```json
{
    "Condition":{
        "StringEquals":{
            "aws:SourceVpc":
                "vpc-12345678"
        }
    }
}
```

Only resources inside the specified VPC are allowed.

---

# Cross-Account Access

Suppose:

```text
AWS Account A

↓

API Gateway

↓

AWS Account B
```

A Resource Policy allows Account B to invoke APIs hosted in Account A.

This is common in enterprise environments.

---

# Evaluation Logic

API Gateway evaluates policies using AWS's standard authorization model.

```text
Explicit Deny

↓

Overrides Everything

---------------------

Explicit Allow

↓

Access Granted

---------------------

No Matching Policy

↓

Implicit Deny
```

An explicit **Deny** always wins.

---

# Common Conditions

| Condition | Purpose |
|------------|----------|
| aws:SourceIp | Restrict by client IP |
| aws:SourceVpc | Restrict by VPC |
| aws:SourceVpce | Restrict by Interface VPC Endpoint |
| aws:PrincipalArn | Restrict specific IAM principals |
| aws:PrincipalAccount | Restrict AWS accounts |

Conditions make Resource Policies very flexible.

---

# Real-World Example

An internal HR API.

Requirements:

- Only EC2 instances inside the production VPC
- Only Company AWS Account
- No Internet access

Architecture:

```text
EC2

↓

Production VPC

↓

VPC Endpoint

↓

API Gateway

↓

Lambda
```

Resource Policy ensures:

- External traffic denied
- Other AWS accounts denied
- Internet access denied

---

# Resource Policy vs API Key

These are often confused.

| Resource Policy | API Key |
|-----------------|----------|
| Security Control | Consumer Identification |
| Blocks Access | Tracks Usage |
| IAM-Based | Application-Based |
| Controls Who Can Access | Controls Consumption |

API Keys should **never** replace Resource Policies.

---

# Resource Policy vs Security Groups

| Resource Policy | Security Group |
|-----------------|----------------|
| API Gateway | EC2, ALB, ENIs |
| Application Layer | Network Layer |
| Controls API Access | Controls Network Traffic |

They protect different parts of the architecture.

---

# Common Use Cases

Resource Policies are ideal for:

- Internal APIs
- Cross-account APIs
- Private APIs
- Enterprise systems
- Banking applications
- Healthcare applications
- Government workloads
- IP-based access control

---

# Best Practices

- Follow the Principle of Least Privilege.
- Avoid using `"Principal": "*"` unless the API is intentionally public.
- Prefer allowing specific IAM roles instead of entire AWS accounts.
- Restrict private APIs using Interface VPC Endpoints.
- Use IP restrictions for corporate or partner networks.
- Explicitly deny known malicious IP ranges when appropriate.
- Combine Resource Policies with IAM, Cognito, or Lambda Authorizers for layered security.

---

# Common Interview Questions

### What is a Resource Policy?

A Resource Policy is a resource-based IAM policy attached directly to an API Gateway API that controls **who can invoke the API**.

---

### What is the difference between an IAM Policy and a Resource Policy?

IAM Policies are attached to identities and define **what actions they can perform**, while Resource Policies are attached to APIs and define **who is allowed to access them**.

---

### Can a Resource Policy restrict access by IP address?

Yes.

Using the `aws:SourceIp` condition, API Gateway can allow or deny requests based on the client's IP address.

---

### How do Private APIs use Resource Policies?

Private APIs commonly use the `aws:SourceVpce` condition to allow requests only through approved Interface VPC Endpoints (AWS PrivateLink).

---

### What happens if a Resource Policy explicitly denies access?

An explicit **Deny** overrides all Allow statements. API Gateway returns **403 Forbidden**, and the request never reaches the backend.

---

# Key Takeaways

- Resource Policies are **resource-based IAM policies** attached directly to API Gateway APIs.
- They determine **who can access an API**, complementing IAM policies that determine **what an authenticated principal can do**.
- Resource Policies support restrictions based on AWS accounts, IAM roles, IP addresses, VPCs, and Interface VPC Endpoints.
- They are essential for securing internal, cross-account, and private APIs.
- Resource Policies should be combined with authentication mechanisms such as IAM, Cognito, or Lambda Authorizers to implement defense-in-depth.