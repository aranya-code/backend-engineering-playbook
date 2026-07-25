# 07 - Security & IAM

## Overview

Security is a critical topic in senior DynamoDB interviews because databases often contain sensitive business and customer data.

Interviewers want to evaluate whether you understand:

- Authentication
- Authorization
- Encryption
- Least privilege
- IAM policies
- Network security
- Compliance
- Production security best practices

A common interview question is:

> "How would you secure a production DynamoDB table containing customer financial information?"

This chapter prepares you to answer that confidently.

---

# Learning Objectives

After completing this chapter, you'll be able to answer interview questions about:

- IAM authentication
- IAM authorization
- Resource-based permissions
- Encryption at rest
- Encryption in transit
- KMS
- VPC Endpoints
- Fine-grained access control
- Security best practices

---

# Question 1

## How is DynamoDB secured?

### Expected Answer

DynamoDB security consists of multiple layers:

```text
IAM Authentication

↓

IAM Authorization

↓

Encryption

↓

Network Security

↓

Monitoring

↓

Auditing
```

These layers work together to protect data from unauthorized access.

---

## Interview Tip

Always mention:

- IAM
- Encryption
- CloudTrail
- Least Privilege

---

# Question 2

## How does authentication work?

### Expected Answer

Applications authenticate using AWS credentials.

Examples:

- IAM User
- IAM Role
- EC2 Instance Profile
- ECS Task Role
- Lambda Execution Role

Example:

```text
Lambda

↓

IAM Role

↓

DynamoDB
```

No database username or password is required.

---

# Question 3

## How does authorization work?

### Expected Answer

Authorization is controlled through IAM policies.

Example:

```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:GetItem",
    "dynamodb:Query"
  ],
  "Resource": "arn:aws:dynamodb:region:account-id:table/Orders"
}
```

Only the specified operations are allowed.

---

# Question 4

## What is the Principle of Least Privilege?

### Expected Answer

Applications should receive only the permissions they require.

Bad example:

```text
dynamodb:*
```

Better example:

```text
GetItem

Query

UpdateItem
```

Only when necessary.

---

## Production Benefit

Reduces the impact of compromised credentials.

---

# Question 5

## What is Fine-Grained Access Control?

### Expected Answer

Fine-Grained Access Control (FGAC) restricts access to specific items or attributes.

Example:

Customer A

```text
Can Read

Customer A Records
```

Customer B

```text
Cannot Read

Customer A Records
```

This is commonly implemented using IAM policy conditions and partition-key based access.

---

# Question 6

## Is DynamoDB encrypted?

### Expected Answer

Yes.

DynamoDB encrypts data at rest by default.

Encryption options include:

- AWS owned keys
- AWS managed KMS keys
- Customer managed KMS keys (CMKs)

---

# Question 7

## What is KMS?

### Expected Answer

AWS Key Management Service (KMS) manages encryption keys used by AWS services.

Workflow:

```text
Application

↓

DynamoDB

↓

KMS

↓

Encrypted Storage
```

Customer-managed keys provide greater control over:

- Rotation
- Access policies
- Auditing

---

# Question 8

## Is data encrypted in transit?

### Expected Answer

Yes.

Communication with DynamoDB uses HTTPS/TLS.

Example:

```text
Application

↓

TLS

↓

DynamoDB
```

This protects data from interception during transmission.

---

# Question 9

## What is a VPC Endpoint for DynamoDB?

### Expected Answer

A VPC Gateway Endpoint allows private communication between resources in a VPC and DynamoDB without traversing the public internet.

Architecture:

```text
EC2

↓

VPC Endpoint

↓

DynamoDB
```

Benefits:

- Improved security
- Lower latency
- No NAT Gateway requirement for DynamoDB access

---

# Question 10

## Does DynamoDB live inside your VPC?

### Expected Answer

No.

DynamoDB is a regional AWS-managed service.

Applications inside a VPC access it through:

- Internet Gateway
- NAT Gateway
- VPC Gateway Endpoint

---

# Question 11

## What is CloudTrail?

### Expected Answer

CloudTrail records API activity.

Example:

```text
UpdateItem

↓

CloudTrail

↓

Audit Log
```

Useful for:

- Security investigations
- Compliance
- Change tracking

---

# Question 12

## How do you audit DynamoDB access?

### Expected Answer

Typically using:

- CloudTrail
- CloudWatch Logs
- AWS Config
- Security Hub
- GuardDuty

Together these provide visibility into access and configuration changes.

---

# Question 13

## How do you protect against accidental deletion?

### Expected Answer

Recommended features:

- Point-in-Time Recovery (PITR)
- On-Demand Backups
- IAM restrictions
- Infrastructure as Code
- Change approval processes

---

# Question 14

## How would you secure Lambda access to DynamoDB?

### Expected Answer

Best practice:

```text
Lambda

↓

Execution Role

↓

Least Privilege Policy

↓

DynamoDB
```

Never embed AWS credentials in source code.

---

# Question 15

## Should applications use long-term IAM user credentials?

### Expected Answer

No.

Production applications should use temporary credentials provided by IAM roles.

Examples:

- EC2 Instance Profiles
- ECS Task Roles
- EKS IAM Roles for Service Accounts (IRSA)
- Lambda Execution Roles

---

# Question 16

## What are common IAM mistakes?

### Expected Answer

Examples:

- Using `AdministratorAccess`
- Hardcoding credentials
- Wildcard permissions
- No key rotation
- Shared IAM users
- Missing CloudTrail logging

---

# Question 17

## How do you restrict access to one table?

### Expected Answer

Specify the table ARN in the IAM policy.

Example:

```text
Resource

↓

Orders Table ARN
```

This prevents access to other DynamoDB tables.

---

# Question 18

## Can IAM restrict specific DynamoDB actions?

### Expected Answer

Yes.

Example:

Allow:

- GetItem
- Query

Deny:

- DeleteItem
- DeleteTable

Permissions are action-specific.

---

# Question 19

## How would you secure customer data in DynamoDB?

### Expected Answer

A production approach includes:

- IAM roles
- Least privilege
- KMS encryption
- HTTPS
- VPC Endpoint
- CloudTrail auditing
- PITR
- Regular security reviews
- Fine-grained access control where appropriate

---

# Question 20

## Explain DynamoDB security in one minute.

### Sample Answer

> DynamoDB security relies primarily on IAM for authentication and authorization, KMS for encryption at rest, and TLS for encryption in transit. Applications should use IAM roles with least-privilege permissions rather than long-term credentials. Additional security controls such as VPC Gateway Endpoints, CloudTrail, AWS Config, and Point-in-Time Recovery help secure production environments, support compliance, and simplify incident response.

---

# Rapid Fire Questions

| Question | Short Answer |
|-----------|--------------|
| Authentication | IAM |
| Authorization | IAM Policies |
| Encryption at Rest | Yes |
| Encryption in Transit | TLS |
| Default Encryption | Yes |
| KMS Supported | Yes |
| VPC Endpoint | Yes |
| CloudTrail Support | Yes |
| Least Privilege | Recommended |
| Long-term Credentials | Avoid |

---

# Senior Interview Tips

Strong candidates discuss:

- Defense in depth
- IAM roles instead of access keys
- Encryption with customer-managed KMS keys when required
- Auditing using CloudTrail
- Compliance considerations
- Disaster recovery
- Operational security

Avoid saying:

> "The database is secure because AWS manages it."

Instead explain:

> "AWS secures the infrastructure, while customers are responsible for identity management, permissions, encryption configuration, monitoring, and secure application design under the AWS Shared Responsibility Model."

---

# Common Mistakes

## Using Wildcard Permissions

Avoid:

```text
dynamodb:*
```

Grant only the actions your application requires.

---

## Hardcoding AWS Credentials

Use IAM roles instead of storing access keys in:

- Source code
- Configuration files
- Docker images

---

## Ignoring Encryption

For highly regulated workloads, use customer-managed KMS keys with appropriate key policies and rotation strategies.

---

## No Audit Logging

Enable CloudTrail and regularly review logs for suspicious activity.

---

# Interview Cheat Sheet

```text
IAM

↓

Least Privilege

↓

IAM Roles

↓

KMS

↓

TLS

↓

VPC Endpoint

↓

CloudTrail

↓

AWS Config

↓

PITR

↓

Secure Production
```

---

# Key Takeaways

- DynamoDB security is built on IAM, encryption, monitoring, and least-privilege access.
- Use IAM roles with temporary credentials instead of long-term access keys.
- Encrypt data at rest with KMS and in transit with TLS.
- Leverage VPC Gateway Endpoints, CloudTrail, AWS Config, and PITR to strengthen production security.
- Senior interviewers expect candidates to understand the AWS Shared Responsibility Model and explain how multiple security controls work together in a production environment.