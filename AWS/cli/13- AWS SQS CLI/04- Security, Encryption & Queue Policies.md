# Security, Encryption & Queue Policies

> Learn how to secure Amazon SQS using IAM, Queue Policies, Server-Side Encryption (SSE), AWS KMS, VPC Endpoints, cross-account access, and production security best practices. This chapter covers how to protect message queues and ensure only authorized producers and consumers can access them.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Secure Amazon SQS queues
- Configure IAM permissions
- Configure Queue Policies
- Enable Server-Side Encryption
- Use AWS KMS
- Configure cross-account access
- Restrict network access
- Apply production security best practices

---

# Security Architecture

Amazon SQS security consists of multiple layers.

```text
Producer

↓

IAM

↓

Queue Policy

↓

Amazon SQS

↓

Encryption

↓

Consumer
```

---

# Security Layers

Amazon SQS supports:

```text
Amazon SQS

│

├── IAM

├── Queue Policies

├── AWS KMS

├── Server-Side Encryption

├── VPC Endpoints

└── CloudTrail
```

---

# IAM Authentication

Every request to Amazon SQS is authenticated through AWS IAM.

Example:

```text
IAM User

↓

IAM Role

↓

Amazon SQS
```

---

# Least Privilege Principle

Avoid:

```text
sqs:*
```

Prefer only required actions.

Example:

```text
Producer

↓

SendMessage
```

```text
Consumer

↓

ReceiveMessage

DeleteMessage
```

---

# Common IAM Permissions

| Permission | Purpose |
|------------|---------|
| sqs:CreateQueue | Create queues |
| sqs:DeleteQueue | Delete queues |
| sqs:SendMessage | Send messages |
| sqs:ReceiveMessage | Receive messages |
| sqs:DeleteMessage | Delete processed messages |
| sqs:GetQueueAttributes | View queue settings |
| sqs:SetQueueAttributes | Modify queue settings |
| sqs:ChangeMessageVisibility | Update visibility timeout |

---

# Queue Policies

Queue Policies are resource-based policies.

Architecture:

```text
AWS Account

↓

Queue Policy

↓

Amazon SQS
```

Queue Policies determine:

- Who can access the queue
- What actions are allowed
- Which AWS accounts are trusted

---

# View Queue Policy

```bash
aws sqs get-queue-attributes \
--queue-url QUEUE_URL \
--attribute-names Policy
```

---

# Apply Queue Policy

```bash
aws sqs set-queue-attributes \
--queue-url QUEUE_URL \
--attributes Policy=file://policy.json
```

---

# Example Queue Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:root"
      },
      "Action": "sqs:SendMessage",
      "Resource": "QUEUE_ARN"
    }
  ]
}
```

---

# Cross-Account Access

Organizations often centralize queues.

```text
Account A

↓

Amazon SQS

↓

Account B

↓

Consumer
```

Queue Policies make this possible.

---

# Cross-Service Access

AWS services can publish directly.

Examples:

```text
Amazon SNS

↓

Amazon SQS
```

```text
Amazon EventBridge

↓

Amazon SQS
```

```text
AWS Lambda

↓

Amazon SQS
```

Permissions are granted through Queue Policies.

---

# Server-Side Encryption (SSE)

Amazon SQS encrypts messages while stored.

Architecture:

```text
Producer

↓

Encrypted Queue

↓

Consumer
```

Encryption protects:

- Message body
- Queue storage

---

# Encryption Options

Amazon SQS supports:

```text
Server-Side Encryption

│

├── Amazon SQS Managed Keys (SSE-SQS)

└── AWS KMS Keys (SSE-KMS)
```

---

# SSE-SQS

AWS manages encryption automatically.

Benefits:

- No KMS management
- Easy setup
- No additional KMS charges

Suitable for most applications.

---

# SSE-KMS

Uses AWS Key Management Service.

Benefits:

- Customer-managed keys
- Auditability
- Key rotation
- Fine-grained permissions

Recommended for enterprise workloads.

---

# Create Encrypted Queue

Using Amazon-managed keys:

```bash
aws sqs create-queue \
--queue-name orders \
--attributes SqsManagedSseEnabled=true
```

---

# Create KMS Encrypted Queue

```bash
aws sqs create-queue \
--queue-name orders \
--attributes KmsMasterKeyId=alias/aws/sqs
```

---

# Verify Encryption

```bash
aws sqs get-queue-attributes \
--queue-url QUEUE_URL \
--attribute-names KmsMasterKeyId
```

---

# KMS Encryption Workflow

```text
Producer

↓

Amazon SQS

↓

AWS KMS

↓

Encrypted Storage
```

---

# VPC Endpoints

Applications inside a VPC can access Amazon SQS without traversing the public internet.

Architecture:

```text
EC2

↓

VPC Endpoint

↓

Amazon SQS
```

Benefits:

- Private connectivity
- Improved security
- Reduced exposure

---

# CloudTrail Integration

Every API call is logged.

Examples:

- CreateQueue
- DeleteQueue
- SendMessage
- ReceiveMessage
- SetQueueAttributes

Useful for:

- Auditing
- Compliance
- Security investigations

---

# CloudWatch Monitoring

Monitor:

- Queue depth
- Messages sent
- Messages received
- Messages deleted
- DLQ growth
- Approximate age of oldest message

---

# Access Control Workflow

```text
Producer

↓

IAM Policy

↓

Queue Policy

↓

Amazon SQS
```

Both IAM and Queue Policies must allow access.

---

# Secure Architecture

```text
Application

↓

IAM Role

↓

Encrypted Amazon SQS

↓

Worker
```

Avoid using long-lived IAM user credentials in production.

---

# Secure Messaging Pattern

```text
Amazon SNS

↓

Encrypted SQS

↓

Lambda

↓

Database
```

Every service communicates using IAM roles.

---

# Common Errors

## AccessDenied

Verify:

- IAM Policy
- Queue Policy
- AWS Account

---

## KMSAccessDeniedException

Verify:

- KMS permissions
- Key policy
- IAM role

---

## InvalidAttributeValue

Verify:

- Queue attribute
- Attribute syntax

---

## Queue Policy Denied

Review:

- Principal
- Action
- Resource
- Condition

---

## Unable to Send Message

Verify:

- Queue exists
- Queue policy
- IAM permissions
- Region

---

# Production Best Practices

- Enable encryption for every production queue.
- Use AWS KMS for sensitive workloads.
- Apply least-privilege IAM permissions.
- Grant cross-account access using Queue Policies.
- Avoid using root credentials.
- Use IAM Roles for EC2, ECS, and Lambda.
- Enable CloudTrail auditing.
- Monitor queue metrics using CloudWatch.
- Use VPC Endpoints for private communication.
- Review Queue Policies regularly.

---

# Real-World Workflow

```text
Backend API

↓

IAM Role

↓

Encrypted Amazon SQS

↓

Worker

↓

Amazon RDS
```

---

# Architecture Note

```text
Producer
      │
      ▼
IAM Role
      │
      ▼
Queue Policy
      │
      ▼
Encrypted Amazon SQS
      │
      ▼
Consumer
```

A secure Amazon SQS deployment combines IAM authentication, Queue Policies, Server-Side Encryption, AWS KMS, and CloudTrail auditing to protect messages throughout their lifecycle.

---

# Interview Note

### Question

**What is the difference between IAM Policies and Queue Policies in Amazon SQS?**

### Answer

IAM Policies are **identity-based policies** attached to IAM users, groups, or roles that define what SQS actions a principal can perform. Queue Policies are **resource-based policies** attached directly to an SQS queue that define which AWS principals or services are allowed to access that specific queue. In many scenarios—such as cross-account access or allowing Amazon SNS to publish messages—both the IAM Policy and the Queue Policy must permit the requested action.

---

# Key Takeaways

- IAM authenticates users, roles, and services accessing Amazon SQS.
- Queue Policies provide resource-level access control.
- Server-Side Encryption protects messages at rest.
- AWS KMS enables customer-managed encryption keys.
- VPC Endpoints allow private access to Amazon SQS.
- CloudTrail records all Amazon SQS API operations for auditing.
- A secure production deployment combines IAM, Queue Policies, encryption, monitoring, and auditing.