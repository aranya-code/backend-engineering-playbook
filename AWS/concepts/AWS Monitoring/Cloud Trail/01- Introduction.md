# What is AWS CloudTrail?

AWS CloudTrail is a **fully managed governance, compliance, auditing, and operational logging service** provided by AWS that records API activity across your AWS account.

CloudTrail captures actions performed by users, applications, AWS services, and the AWS Management Console, allowing organizations to monitor, audit, and troubleshoot activity within their AWS environments.

Every supported AWS API call is recorded as an **event**, making CloudTrail one of the most important security and auditing services in AWS.

------------------------------------------------------------------------

# Why Do We Need CloudTrail?

As cloud environments grow, it becomes increasingly difficult to determine:

- Who created a resource?
- Who deleted an EC2 instance?
- When was an IAM policy modified?
- Which application accessed an S3 bucket?
- Who launched a Lambda function?

CloudTrail provides a complete audit trail that answers these questions by recording AWS API activity.

------------------------------------------------------------------------

# Core Capabilities

AWS CloudTrail provides several important capabilities:

- **API Activity Logging** — Records supported AWS API calls.
- **Governance** — Helps organizations maintain operational governance.
- **Security Auditing** — Tracks user and service activity.
- **Compliance** — Supports regulatory compliance requirements.
- **Operational Troubleshooting** — Helps investigate unexpected resource changes.
- **Automation** — Integrates with EventBridge to trigger automated workflows.
- **Long-Term Storage** — Stores logs in Amazon S3 for retention and analysis.

------------------------------------------------------------------------

# What Does CloudTrail Record?

CloudTrail records activities performed by:

- IAM Users
- IAM Roles
- AWS Services
- Applications using AWS SDKs
- AWS CLI
- AWS Management Console
- AWS CloudFormation
- AWS Lambda
- Third-party applications using AWS APIs

------------------------------------------------------------------------

# Types of Events

CloudTrail records several categories of events.

## 1. Management Events

Management Events (Control Plane Events) record operations that create, modify, or delete AWS resources.

**Examples**

- Launch EC2 Instance
- Create IAM User
- Delete Security Group
- Modify Route Table
- Create VPC

------------------------------------------------------------------------

## 2. Data Events

Data Events (Data Plane Events) record operations performed on the data stored inside AWS resources.

**Examples**

- Upload S3 Object
- Download S3 Object
- Delete S3 Object
- Invoke Lambda Function
- DynamoDB Item Operations

------------------------------------------------------------------------

## 3. Network Activity Events

Network Activity Events provide visibility into supported network-related API activity, including operations performed through supported VPC endpoints and private connectivity.

------------------------------------------------------------------------

# CloudTrail Architecture Overview

A typical CloudTrail workflow looks like this:

```text
User / Application

↓

AWS API Call

↓

AWS CloudTrail

├── Event History (90 Days)

├── Amazon S3

├── CloudWatch Logs

└── Amazon EventBridge
```

CloudTrail captures API activity and can store it, monitor it, or trigger automated workflows.

------------------------------------------------------------------------

# Benefits of AWS CloudTrail

- Fully managed AWS service
- Continuous API activity logging
- Improves security and governance
- Supports compliance requirements
- Long-term log storage
- Detects unauthorized changes
- Tracks user activity
- Integrates with CloudWatch
- Integrates with EventBridge
- Supports multi-account environments using AWS Organizations

------------------------------------------------------------------------

# Common Use Cases

CloudTrail is commonly used for:

- Security auditing
- Compliance reporting
- Investigating unauthorized access
- Monitoring IAM changes
- Tracking infrastructure modifications
- Detecting accidental resource deletion
- Triggering automated remediation
- Incident response
- Operational troubleshooting

------------------------------------------------------------------------

# Real-World Example

An administrator accidentally deletes an Amazon S3 bucket.

CloudTrail records:

1. User identity
2. API name (`DeleteBucket`)
3. Timestamp
4. Source IP address
5. AWS Region
6. Request parameters
7. Response details

Using this information, administrators can determine who performed the action, when it occurred, and investigate the cause.

------------------------------------------------------------------------

# Key Features

- Continuous AWS API logging
- Event History
- Trails
- Management Events
- Data Events
- Network Activity Events
- CloudTrail Insights
- Log file integrity validation
- Multi-Region Trails
- Organization Trails
- Amazon S3 integration
- CloudWatch Logs integration
- EventBridge integration
- SNS and Lambda integration
- IAM integration

------------------------------------------------------------------------

# Advantages

- Easy to enable
- Highly scalable
- Improves security visibility
- Enables compliance auditing
- Centralized logging
- Supports long-term log retention
- Integrates with AWS monitoring services
- Simplifies incident investigations
- Enables automated security responses

------------------------------------------------------------------------

# Key Takeaways

- AWS CloudTrail is AWS's auditing and governance service.
- It records supported AWS API activity across your AWS account.
- CloudTrail captures Management Events, Data Events, and Network Activity Events.
- Event History stores Management Events for the last 90 days without requiring a Trail.
- Trails archive events to Amazon S3 and integrate with CloudWatch Logs and EventBridge.
- CloudTrail is essential for security auditing, compliance, troubleshooting, and operational governance.