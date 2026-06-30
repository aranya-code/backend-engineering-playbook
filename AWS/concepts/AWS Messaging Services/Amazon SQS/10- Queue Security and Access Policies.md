# Introduction

Amazon SQS often stores critical business messages such as payment requests, order events, customer notifications, and financial transactions.

Protecting these messages is essential to ensure confidentiality, integrity, and controlled access.

Amazon SQS provides multiple security mechanisms to protect queues and messages, including:

- AWS Identity and Access Management (IAM)
- Queue Resource Policies
- Server-Side Encryption (SSE)
- AWS Key Management Service (AWS KMS)
- HTTPS (TLS) Encryption
- Cross-Account Access Control

These features help organizations implement secure, compliant, and least-privilege messaging architectures.

---

# SQS Security Overview

Amazon SQS security consists of multiple layers.

```
                    Amazon SQS

                        │

      ┌─────────────────┼─────────────────┐

      ▼                 ▼                 ▼

    IAM Policies    Queue Policies     Encryption

                                            │

                             ┌──────────────┴──────────────┐

                             ▼                             ▼

                     HTTPS (TLS)                  AWS KMS Encryption
```

Each layer protects a different aspect of the queue.

---

# IAM Policies

IAM policies control **who can perform actions on Amazon SQS**.

These policies are attached to:

- IAM Users
- IAM Roles
- IAM Groups

IAM policies define permissions such as:

- Create queues
- Delete queues
- Send messages
- Receive messages
- Delete messages
- Change queue attributes

---

## Example IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage"
      ],
      "Resource": "arn:aws:sqs:us-east-1:123456789012:OrderQueue"
    }
  ]
}
```

This policy allows users to:

- Send messages
- Receive messages
- Delete processed messages

from the specified queue.

---

# Principle of Least Privilege

Always grant only the permissions required.

Good example

```
Application

↓

Only SendMessage()
```

Bad example

```
Application

↓

sqs:*
```

Granting unnecessary permissions increases security risks.

---

# Queue Policies

Queue Policies are **resource-based policies** attached directly to an SQS queue.

Unlike IAM policies, Queue Policies specify **who is allowed to access the queue**.

Queue Policies are commonly used for:

- Cross-account access
- AWS service integrations
- Public access restrictions

---

## Queue Policy Architecture

```
AWS Account A

      │

      ▼

 Queue Policy

      │

      ▼

Amazon SQS Queue

      ▲

      │

AWS Account B
```

The queue owner controls access through the Queue Policy.

---

# Example Queue Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowAccountB",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::222222222222:root"
      },
      "Action": "sqs:SendMessage",
      "Resource": "arn:aws:sqs:us-east-1:111111111111:OrderQueue"
    }
  ]
}
```

This policy allows another AWS account to send messages to the queue.

---

# IAM Policy vs Queue Policy

| IAM Policy | Queue Policy |
|------------|--------------|
| Attached to IAM identities | Attached to the SQS queue |
| Controls what an identity can do | Controls who can access the queue |
| Used within an AWS account | Commonly used for cross-account access |
| Identity-based | Resource-based |

---

# Cross-Account Access

Applications in different AWS accounts often need to communicate.

Example:

```
AWS Account A

↓

Amazon SQS Queue

↑

AWS Account B
```

Instead of creating IAM users in another account, use a Queue Policy to grant access.

---

# Server-Side Encryption (SSE)

Amazon SQS supports encryption of messages while they are stored in the queue.

Encryption happens automatically.

```
Producer

↓

Encrypt

↓

Amazon SQS

↓

Encrypted Storage

↓

Decrypt

↓

Consumer
```

Applications do not need to manually encrypt or decrypt messages.

---

# AWS KMS

Amazon SQS integrates with **AWS Key Management Service (KMS)**.

Supported options:

- AWS Managed Key (`alias/aws/sqs`)
- Customer Managed Key (CMK)

---

## AWS Managed Key

AWS automatically manages:

- Key creation
- Rotation
- Maintenance

Suitable for most applications.

---

## Customer Managed Key (CMK)

Organizations manage:

- Key rotation
- Key policies
- Access permissions
- Auditing

Useful when:

- Regulatory compliance is required.
- Different teams require separate encryption keys.
- Fine-grained access control is needed.

---

# Encryption in Transit

Messages sent between applications and Amazon SQS are encrypted using HTTPS.

```
Producer

↓

HTTPS (TLS)

↓

Amazon SQS

↓

HTTPS (TLS)

↓

Consumer
```

This protects messages from network interception.

---

# Encryption at Rest

Messages stored in Amazon SQS are encrypted using AWS KMS.

```
Message

↓

Encrypt

↓

Storage

↓

Decrypt

↓

Receive
```

Encryption at rest protects stored data from unauthorized access.

---

# Configuring Server-Side Encryption

## AWS Management Console

1. Open **Amazon SQS**.
2. Select the queue.
3. Choose **Edit**.
4. Enable **Server-side encryption**.
5. Select the KMS key.
6. Save the changes.

---

## AWS CLI

```bash
aws sqs set-queue-attributes \
  --queue-url QUEUE_URL \
  --attributes KmsMasterKeyId=alias/aws/sqs
```

---

## Boto3

```python
import boto3

sqs = boto3.client("sqs")

sqs.set_queue_attributes(
    QueueUrl=QUEUE_URL,
    Attributes={
        "KmsMasterKeyId": "alias/aws/sqs"
    }
)
```

---

## CloudFormation

```yaml
Resources:
  OrderQueue:
    Type: AWS::SQS::Queue
    Properties:
      KmsMasterKeyId: alias/aws/sqs
```

---

## Terraform

```terraform
resource "aws_sqs_queue" "order_queue" {

  name = "order-queue"

  kms_master_key_id = "alias/aws/sqs"

}
```

---

# Amazon S3 to Amazon SQS

One of the most common integrations is Amazon S3 sending event notifications to an SQS queue.

To allow this, the queue must have an appropriate Queue Policy.

```
Amazon S3

↓

Object Created

↓

Queue Policy

↓

Amazon SQS
```

Example events include:

- Object Created
- Object Deleted
- Restore Completed

---

# AWS Lambda and Amazon SQS

Lambda functions frequently consume messages from Amazon SQS.

```
Amazon SQS

↓

AWS Lambda

↓

Business Logic
```

Lambda requires appropriate IAM permissions to:

- Receive messages
- Delete messages
- Change Visibility Timeout

---

# Monitoring Security

Security-related activities can be monitored using:

- AWS CloudTrail
- AWS CloudWatch
- AWS Config
- Amazon GuardDuty

CloudTrail records API actions such as:

- CreateQueue
- DeleteQueue
- SendMessage
- ReceiveMessage
- SetQueueAttributes

---

# Best Practices

- Follow the Principle of Least Privilege.
- Use IAM Roles instead of long-term IAM user credentials.
- Enable Server-Side Encryption for production queues.
- Use Customer Managed Keys when regulatory requirements demand greater control.
- Require HTTPS for all communication with Amazon SQS.
- Use Queue Policies for cross-account access.
- Regularly review IAM and Queue Policies.
- Monitor API activity using AWS CloudTrail.
- Rotate Customer Managed KMS keys according to organizational policies.

---

# Common Mistakes

## Granting Full SQS Permissions

Avoid policies such as:

```json
"Action": "sqs:*"
```

Grant only the required actions.

---

## Disabling Encryption

Sensitive business data should never be stored in unencrypted queues.

---

## Using IAM Users for Applications

Prefer IAM Roles attached to EC2 instances, ECS tasks, Lambda functions, or EKS service accounts.

---

## Confusing IAM Policies with Queue Policies

IAM Policies define **what an identity can do**.

Queue Policies define **who can access the queue**.

---

## Forgetting Queue Policies for AWS Services

Services such as Amazon S3 require an appropriate Queue Policy before they can publish messages to Amazon SQS.

---

# Summary

Amazon SQS provides multiple layers of security to protect queues and messages. IAM Policies control permissions for users and roles, while Queue Policies manage access to the queue itself, particularly for cross-account and AWS service integrations. Encryption in transit using HTTPS and encryption at rest using AWS KMS safeguard message confidentiality. By combining least-privilege IAM policies, secure Queue Policies, server-side encryption, and continuous monitoring with CloudTrail and CloudWatch, organizations can build secure and compliant messaging systems on AWS.