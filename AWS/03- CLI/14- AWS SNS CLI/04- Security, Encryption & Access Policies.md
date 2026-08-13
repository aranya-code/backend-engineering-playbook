# Security, Encryption & Access Policies

> Learn how to secure Amazon SNS Topics using IAM, Topic Policies, AWS KMS encryption, CloudTrail auditing, cross-account access, and production security best practices. This chapter covers authentication, authorization, encryption, private communication, and secure event distribution.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Secure Amazon SNS Topics
- Configure IAM permissions
- Configure Topic Policies
- Enable Server-Side Encryption
- Configure AWS KMS
- Configure cross-account publishing
- Secure event-driven architectures
- Apply production security best practices

---

# Security Architecture

Amazon SNS security consists of multiple layers.

```text
Publisher

↓

IAM

↓

Topic Policy

↓

Amazon SNS

↓

Encryption

↓

Subscribers
```

---

# Security Layers

Amazon SNS supports:

```text
Amazon SNS

│

├── IAM

├── Topic Policies

├── AWS KMS

├── Server-Side Encryption

├── CloudTrail

└── CloudWatch
```

---

# IAM Authentication

Every API request is authenticated using AWS IAM.

Example:

```text
IAM User

↓

IAM Role

↓

Amazon SNS
```

Applications should authenticate using IAM Roles instead of long-lived credentials.

---

# Least Privilege Principle

Avoid:

```text
sns:*
```

Grant only required permissions.

Example Publisher:

```text
sns:Publish
```

Example Administrator:

```text
sns:CreateTopic

sns:DeleteTopic
```

---

# Common IAM Permissions

| Permission | Purpose |
|------------|---------|
| sns:CreateTopic | Create Topics |
| sns:DeleteTopic | Delete Topics |
| sns:Publish | Publish messages |
| sns:Subscribe | Create subscriptions |
| sns:Unsubscribe | Remove subscriptions |
| sns:GetTopicAttributes | View Topic configuration |
| sns:SetTopicAttributes | Modify Topic configuration |
| sns:ListTopics | List Topics |

---

# Topic Policies

Topic Policies are resource-based policies attached directly to a Topic.

They define:

- Who can publish
- Who can subscribe
- Cross-account access
- AWS service integrations

---

# Topic Policy Workflow

```text
Publisher

↓

IAM Policy

↓

Topic Policy

↓

Amazon SNS
```

Both policies must allow access.

---

# View Topic Policy

```bash
aws sns get-topic-attributes \
--topic-arn TOPIC_ARN
```

Review:

```text
Policy
```

---

# Apply Topic Policy

```bash
aws sns set-topic-attributes \
--topic-arn TOPIC_ARN \
--attribute-name Policy \
--attribute-value file://policy.json
```

---

# Example Topic Policy

```json
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Effect":"Allow",
      "Principal":{
        "AWS":"arn:aws:iam::123456789012:root"
      },
      "Action":"sns:Publish",
      "Resource":"TOPIC_ARN"
    }
  ]
}
```

---

# Cross-Account Publishing

Organizations frequently publish events across AWS accounts.

```text
Account A

↓

Amazon SNS

↓

Account B

↓

Amazon SQS
```

Topic Policies enable secure cross-account communication.

---

# Cross-Service Publishing

AWS services can publish directly.

Examples:

```text
CloudWatch

↓

Amazon SNS
```

```text
EventBridge

↓

Amazon SNS
```

```text
Lambda

↓

Amazon SNS
```

Permissions are granted through Topic Policies.

---

# Server-Side Encryption

Amazon SNS supports encryption at rest.

```text
Publisher

↓

Encrypted Topic

↓

Subscribers
```

Message data is encrypted before being stored.

---

# Encryption Options

Amazon SNS supports:

```text
Server-Side Encryption

│

├── AWS Managed Key

└── Customer Managed KMS Key
```

---

# AWS Managed Key

AWS automatically manages:

- Key creation
- Rotation
- Availability

Suitable for most workloads.

---

# Customer Managed Key

AWS KMS provides:

- Customer control
- Key rotation
- Audit logging
- Fine-grained IAM permissions

Recommended for enterprise environments.

---

# Enable Encryption

```bash
aws sns set-topic-attributes \
--topic-arn TOPIC_ARN \
--attribute-name KmsMasterKeyId \
--attribute-value alias/aws/sns
```

---

# Verify Encryption

```bash
aws sns get-topic-attributes \
--topic-arn TOPIC_ARN
```

Review:

```text
KmsMasterKeyId
```

---

# Encryption Workflow

```text
Publisher

↓

Amazon SNS

↓

AWS KMS

↓

Encrypted Topic
```

---

# CloudTrail Integration

Every Amazon SNS API call is logged.

Examples:

- CreateTopic
- DeleteTopic
- Publish
- Subscribe
- SetTopicAttributes

Useful for:

- Auditing
- Compliance
- Security investigations

---

# CloudWatch Integration

Monitor:

- Published messages
- Delivered notifications
- Failed deliveries
- Topic activity

---

# Secure Publishing Architecture

```text
Application

↓

IAM Role

↓

Encrypted SNS Topic

↓

Subscribers
```

Applications should never use embedded AWS credentials.

---

# Secure SNS → SQS Architecture

```text
Application

↓

Amazon SNS

↓

Encrypted Amazon SQS

↓

Workers
```

Both services should use encryption.

---

# Secure Lambda Integration

```text
Application

↓

Amazon SNS

↓

Lambda

↓

Amazon RDS
```

Communication is authenticated through IAM Roles.

---

# Common Errors

## AuthorizationError

Verify:

- IAM Policy
- Topic Policy
- AWS Account

---

## InvalidParameter

Verify:

- Topic ARN
- KMS Key
- Attribute name

---

## KMSAccessDeniedException

Verify:

- IAM permissions
- KMS Key Policy
- KMS Region

---

## AccessDenied

Review:

- IAM Role
- Topic Policy
- SCPs (if using AWS Organizations)

---

## Publish Failed

Verify:

- Topic exists
- Publisher permissions
- Topic Policy
- KMS configuration

---

# Production Best Practices

- Enable encryption for every production Topic.
- Use customer-managed KMS keys for sensitive workloads.
- Apply least-privilege IAM permissions.
- Use Topic Policies for cross-account communication.
- Prefer IAM Roles over IAM Users.
- Enable CloudTrail logging.
- Monitor CloudWatch metrics.
- Review Topic Policies regularly.
- Restrict publishing to trusted applications.
- Encrypt both SNS Topics and SQS queues.

---

# Real-World Workflow

```text
Backend API

↓

IAM Role

↓

Encrypted SNS Topic

↓

Amazon SQS

↓

Workers
```

---

# Architecture Note

```text
Publisher
      │
      ▼
IAM Role
      │
      ▼
Topic Policy
      │
      ▼
Encrypted Amazon SNS
      │
      ▼
Subscribers
```

A production Amazon SNS deployment combines IAM authentication, Topic Policies, AWS KMS encryption, CloudTrail auditing, and CloudWatch monitoring to securely distribute business events across multiple applications and AWS accounts.

---

# Interview Note

### Question

**What is the difference between an IAM Policy and an Amazon SNS Topic Policy?**

### Answer

An IAM Policy is an **identity-based policy** attached to IAM users, groups, or roles that defines which Amazon SNS actions a principal can perform. A Topic Policy is a **resource-based policy** attached directly to an SNS Topic that defines which AWS principals, AWS accounts, or AWS services are allowed to publish to or subscribe to that Topic. Cross-account publishing and service integrations commonly require both IAM Policies and Topic Policies to allow the requested action.

---

# Key Takeaways

- IAM authenticates users, roles, and AWS services.
- Topic Policies provide resource-level access control.
- AWS KMS encrypts SNS Topics at rest.
- CloudTrail records every Amazon SNS API operation.
- CloudWatch monitors Topic activity and delivery metrics.
- Cross-account publishing is implemented through Topic Policies.
- Production deployments combine IAM, Topic Policies, encryption, monitoring, and auditing to secure event-driven architectures.