# 01 - IAM Authentication & Authorization

## Overview

Security is one of the most important aspects of any DynamoDB deployment. Unlike traditional databases that manage users and passwords internally, **Amazon DynamoDB relies entirely on AWS Identity and Access Management (IAM)** for authentication and authorization.

There are:

- No database users
- No database passwords
- No GRANT or REVOKE statements
- No database login accounts

Instead, every request to DynamoDB is authenticated using AWS credentials and authorized using IAM policies.

Understanding IAM is essential because it determines **who can access DynamoDB, what actions they can perform, and which resources they can access.**

---

# Learning Objectives

After completing this chapter, you will understand:

- How DynamoDB authentication works
- IAM users, groups, and roles
- Identity-based and resource-based permissions
- Least privilege access
- Temporary credentials
- Cross-account access
- Production security architecture
- Common IAM mistakes

---

# Authentication vs Authorization

These two concepts are often confused.

## Authentication

Authentication answers:

> **Who are you?**

Examples:

- IAM User
- IAM Role
- AWS Lambda Role
- ECS Task Role
- EC2 Instance Profile

Authentication occurs before any DynamoDB request is processed.

---

## Authorization

Authorization answers:

> **What are you allowed to do?**

Examples:

- Read items
- Write items
- Delete items
- Query a table
- Create tables

IAM evaluates permissions before DynamoDB executes the request.

---

# Authentication Flow

```text
Application

↓

AWS Credentials

↓

AWS Signature Version 4

↓

IAM Authentication

↓

IAM Policy Evaluation

↓

DynamoDB
```

Every request must be signed using AWS Signature Version 4 (SigV4).

---

# Internal Request Flow

```text
Client

↓

AWS SDK

↓

Request Signing

↓

IAM

↓

Permission Evaluation

↓

DynamoDB

↓

Response
```

If authentication or authorization fails, DynamoDB rejects the request.

---

# IAM Components

## IAM User

Represents an individual person.

Example:

```text
Alice

↓

IAM User

↓

Access Key
```

Generally used for administrators or developers—not applications.

---

## IAM Group

Groups multiple users together.

```text
Developers

↓

Read Access

────────────

Operations

↓

Admin Access
```

Policies are attached to the group instead of each individual user.

---

## IAM Role

Roles provide temporary credentials.

Examples:

- AWS Lambda
- ECS Tasks
- EC2
- Step Functions
- AWS Glue

Production applications should almost always use IAM Roles instead of long-lived access keys.

---

# Example Architecture

```text
API Gateway

↓

Lambda

↓

IAM Role

↓

DynamoDB
```

No passwords or API keys are stored in the application.

---

# Identity-Based Policies

Identity-based policies are attached to:

- Users
- Groups
- Roles

Example:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/Orders"
    }
  ]
}
```

This policy allows only read operations.

---

# Resource-Level Permissions

IAM policies can restrict access to specific resources.

Example:

```text
Orders Table

↓

Allowed

────────────

Payments Table

↓

Denied
```

Applications receive access only to the tables they require.

---

# Fine-Grained Actions

Common DynamoDB IAM actions include:

```text
GetItem

PutItem

UpdateItem

DeleteItem

BatchGetItem

BatchWriteItem

Query

Scan

DescribeTable

CreateTable

DeleteTable
```

Avoid using wildcard permissions whenever possible.

---

# Least Privilege Principle

Poor policy:

```text
Allow

↓

dynamodb:*
```

Better:

```text
Allow

↓

GetItem

Query

UpdateItem
```

Grant only the permissions required for the workload.

---

# Temporary Credentials

Modern AWS services use temporary credentials.

```text
Lambda

↓

IAM Role

↓

STS

↓

Temporary Credentials

↓

DynamoDB
```

Benefits:

- Automatic rotation
- No hardcoded secrets
- Reduced attack surface

---

# Cross-Account Access

Sometimes an application in one AWS account accesses a table in another.

Architecture:

```text
Account A

↓

IAM Role

↓

AssumeRole

↓

Account B

↓

DynamoDB
```

AWS Security Token Service (STS) enables this securely.

---

# Production Architecture

```text
             Users

                │

                ▼

         API Gateway

                │

                ▼

             Lambda

                │

          IAM Execution Role

                │

                ▼

           DynamoDB Table
```

The application never stores AWS credentials.

---

# IAM Best Practices

- Use IAM Roles instead of access keys.
- Apply the principle of least privilege.
- Separate development and production permissions.
- Rotate long-lived credentials when they are unavoidable.
- Enable CloudTrail for auditing.
- Review IAM policies regularly.
- Restrict access to specific tables whenever possible.

---

# Common Mistakes

## Using AdministratorAccess

Poor:

```text
Application

↓

AdministratorAccess
```

Applications rarely require full AWS permissions.

---

## Hardcoding AWS Keys

Avoid:

```python
ACCESS_KEY = "AKIA..."
SECRET_KEY = "..."
```

Instead:

```text
IAM Role

↓

Automatic Credentials
```

---

## Wildcard Resources

Avoid:

```text
Resource

↓

*
```

Instead:

```text
Orders Table ARN
```

Grant access only to required resources.

---

## Ignoring CloudTrail

Without logging:

- Unauthorized access is harder to detect.
- Security investigations become difficult.
- Compliance requirements may not be met.

---

# Production Considerations

Enterprise environments commonly implement:

```text
Developer

↓

GitHub Actions

↓

IAM Role

↓

Deploy

↓

Lambda

↓

IAM Role

↓

DynamoDB
```

Every workload has a dedicated IAM role with only the permissions it requires.

Additional security controls often include:

- AWS Organizations SCPs
- Permission Boundaries
- IAM Access Analyzer
- CloudTrail auditing
- AWS Config compliance rules

---

# Interview Notes

A common interview question is:

> **How does DynamoDB authenticate requests?**

DynamoDB relies on AWS Identity and Access Management (IAM). Requests are signed using AWS Signature Version 4 (SigV4), authenticated by IAM, and then evaluated against IAM policies before being executed.

Another common question is:

> **Why are IAM Roles preferred over IAM Users for applications?**

IAM Roles provide temporary credentials that rotate automatically, eliminating the need to store long-lived access keys and improving security.

Another common question is:

> **What is the principle of least privilege?**

Grant only the minimum permissions required for a user or application to perform its tasks, reducing the impact of compromised credentials.

Another common question is:

> **Can you restrict an application to a single DynamoDB table?**

Yes. IAM policies can specify the ARN of a particular table, allowing access only to that resource and only for approved actions.

---

# Key Takeaways

- DynamoDB uses IAM for both authentication and authorization.
- Every request is authenticated using AWS credentials and authorized using IAM policies.
- IAM Roles are the preferred authentication mechanism for production workloads.
- Apply least privilege by granting only the required actions on specific DynamoDB resources.
- Avoid hardcoded credentials, wildcard permissions, and unnecessary administrator access.
- IAM, combined with CloudTrail and other AWS security services, forms the foundation of a secure DynamoDB deployment.