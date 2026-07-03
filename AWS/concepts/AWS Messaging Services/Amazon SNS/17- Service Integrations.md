# 17- Service Integrations
# Introduction

Amazon SNS is designed to integrate seamlessly with many AWS services.

Instead of building custom notification systems, AWS services can publish events directly to an SNS Topic.

Amazon SNS then distributes these events to subscribers such as:

- Amazon SQS
- AWS Lambda
- Email
- SMS
- HTTP/HTTPS Endpoints
- Mobile Applications

This makes Amazon SNS a central component in event-driven architectures.

---

# Integration Overview

```
                AWS Services

       ┌─────────┼─────────┬─────────┐

       ▼         ▼         ▼         ▼

      S3   CloudWatch   EventBridge  EC2

                 │

                 ▼

           Amazon SNS Topic

      ┌──────────┼──────────┬──────────┐

      ▼          ▼          ▼          ▼

    SQS      Lambda      Email      HTTPS
```

---

# Amazon S3 Integration

Amazon S3 can publish object events to Amazon SNS.

Supported events include:

- Object Created
- Object Deleted
- Object Restore Completed
- Replication Events

---

## Architecture

```
Amazon S3

↓

Object Uploaded

↓

Amazon SNS

↓

Lambda

↓

Image Processing
```

---

## Common Use Cases

- Image processing
- Video transcoding
- File validation
- Backup notifications

---

# Amazon CloudWatch Integration

CloudWatch Alarms can publish alarm notifications to Amazon SNS.

```
CloudWatch Alarm

↓

Amazon SNS

↓

Email

↓

SMS

↓

Operations Team
```

---

## Example Use Cases

- High CPU utilization
- Low disk space
- Application failures
- Database alarms

---

# AWS Lambda Integration

Amazon SNS can invoke Lambda functions directly.

```
SNS Topic

↓

Lambda

↓

Business Logic
```

---

## Use Cases

- Data transformation
- API invocation
- Event enrichment
- Serverless automation

---

# Amazon SQS Integration

One of the most common integrations.

```
Publisher

↓

Amazon SNS

↓

Amazon SQS

↓

Consumers
```

Benefits

- Reliable processing
- Retry support
- Dead Letter Queues
- Independent scaling

---

# Amazon EventBridge Integration

Amazon EventBridge can route events to Amazon SNS.

```
Application

↓

EventBridge

↓

SNS

↓

Subscribers
```

---

## Use Cases

- Centralized event routing
- Cross-account events
- SaaS integrations

---

# Amazon EC2 Integration

Applications running on EC2 instances can publish operational events.

```
EC2 Application

↓

SNS

↓

Monitoring

↓

Email
```

---

## Common Events

- Application startup
- Deployment completed
- Error notifications
- Batch completion

---

# Amazon ECS Integration

Containerized applications can publish events to SNS.

```
Amazon ECS

↓

Application

↓

SNS

↓

SQS

↓

Workers
```

---

## Use Cases

- Order processing
- Payment events
- Inventory updates
- Microservices communication

---

# AWS Auto Scaling Integration

Auto Scaling can notify administrators about scaling events.

```
Auto Scaling

↓

SNS

↓

Email

↓

Operations Team
```

---

## Notifications

- Instance Launch
- Instance Termination
- Lifecycle Hooks
- Scaling Activities

---

# AWS Backup Integration

AWS Backup can send notifications for backup jobs.

```
AWS Backup

↓

SNS

↓

Email
```

---

## Events

- Backup Completed
- Backup Failed
- Restore Completed

---

# AWS Config Integration

AWS Config publishes compliance events.

```
AWS Config

↓

SNS

↓

Security Team
```

---

## Examples

- Resource drift
- Non-compliant resources
- Configuration changes

---

# AWS CodePipeline Integration

Deployment pipelines can notify teams.

```
CodePipeline

↓

SNS

↓

Email

↓

Slack

↓

Microsoft Teams
```

---

## Use Cases

- Deployment started
- Deployment succeeded
- Deployment failed

---

# Amazon RDS Integration

Amazon RDS publishes database events.

```
Amazon RDS

↓

SNS

↓

DBA Team
```

---

## Common Events

- Backup completed
- Failover occurred
- Maintenance started
- Storage nearing capacity

---

# Amazon DynamoDB Integration

DynamoDB Streams can trigger Lambda functions that publish events to SNS.

```
DynamoDB

↓

Streams

↓

Lambda

↓

SNS
```

---

# AWS Step Functions Integration

Step Functions can publish workflow status notifications.

```
Step Functions

↓

SNS

↓

Email

↓

Operations
```

---

## Events

- Workflow completed
- Workflow failed
- Timeout
- Manual approval

---

# CI/CD Notification Architecture

```
GitHub

↓

CodePipeline

↓

SNS

↓

Email

↓

Slack

↓

Teams
```

Development teams receive deployment notifications automatically.

---

# Monitoring Architecture

```
Application

↓

CloudWatch

↓

Alarm

↓

SNS

↓

Email

↓

SMS
```

---

# Event-Driven Microservices

```
Order Service

↓

SNS

↓

Inventory

↓

Billing

↓

Shipping

↓

Analytics
```

Each service processes events independently.

---

# Common Integration Patterns

| AWS Service | Typical SNS Usage |
|--------------|------------------|
| Amazon S3 | Object notifications |
| Amazon SQS | Reliable message processing |
| AWS Lambda | Serverless event handling |
| CloudWatch | Alarm notifications |
| EventBridge | Event routing |
| Amazon ECS | Microservice events |
| Amazon EC2 | Application notifications |
| CodePipeline | CI/CD notifications |
| AWS Backup | Backup alerts |
| AWS Config | Compliance alerts |
| Amazon RDS | Database notifications |
| Step Functions | Workflow notifications |

---

# Best Practices

- Use SNS as the central notification hub.
- Combine SNS with SQS for reliable processing.
- Use Lambda for lightweight event processing.
- Organize topics by business domain.
- Monitor integrations using CloudWatch.
- Secure topics using IAM Policies and Topic Policies.
- Enable Server-Side Encryption for production topics.
- Avoid embedding business logic directly into notification workflows.

---

# Common Mistakes

## Using One Topic for Every Service

Create topics based on business domains rather than individual AWS services.

---

## Ignoring Subscriber Health

Monitor downstream services such as SQS queues, Lambda functions, and HTTP endpoints.

---

## Not Using Message Filtering

Filtering reduces unnecessary message delivery and subscriber workload.

---

## Missing Permissions

Ensure IAM Policies, Topic Policies, and endpoint permissions are configured correctly.

---

# Summary

Amazon SNS integrates with a wide range of AWS services, making it a central communication layer for event-driven architectures. Whether processing Amazon S3 events, triggering AWS Lambda functions, delivering CloudWatch alarms, notifying deployment teams through CodePipeline, or distributing messages to Amazon SQS, Amazon SNS enables scalable, loosely coupled, and highly reliable application integration across the AWS ecosystem.