# Management Events

Management Events are the most common type of events recorded by AWS CloudTrail. They capture operations performed on AWS resources that create, modify, or delete infrastructure.

These events are also known as **Control Plane Events** because they involve managing AWS resources rather than accessing the data stored within them.

Management Events are **enabled by default** for every CloudTrail trail.

------------------------------------------------------------------------

# What are Management Events?

Management Events record API calls that affect the configuration of AWS resources.

They help answer questions such as:

- Who launched an EC2 instance?
- Who created an IAM user?
- Who modified a Security Group?
- Who deleted an S3 bucket?
- Who changed an IAM policy?

------------------------------------------------------------------------

# Characteristics

- Enabled by default
- Capture control plane operations
- Record both successful and failed API calls
- Support security auditing
- Available in Event History for 90 days
- Can be stored indefinitely using Trails

------------------------------------------------------------------------

# Read Events vs Write Events

Management Events are divided into two categories.

## Read Events

Read events retrieve information without modifying resources.

Examples:

- DescribeInstances
- ListBuckets
- GetRole
- DescribeVpcs
- ListUsers

Example:

```text
AWS CLI

↓

DescribeInstances

↓

CloudTrail Records Read Event
```

------------------------------------------------------------------------

## Write Events

Write events create, modify, or delete AWS resources.

Examples:

- RunInstances
- TerminateInstances
- CreateBucket
- DeleteBucket
- CreateUser
- DeleteRole
- CreateVpc

Example:

```text
Administrator

↓

DeleteSecurityGroup

↓

CloudTrail Records Write Event
```

------------------------------------------------------------------------

# Common Management Events

| AWS Service | Example API |
|-------------|-------------|
| Amazon EC2 | RunInstances |
| Amazon EC2 | StopInstances |
| Amazon EC2 | TerminateInstances |
| Amazon S3 | CreateBucket |
| Amazon S3 | DeleteBucket |
| IAM | CreateUser |
| IAM | AttachRolePolicy |
| VPC | CreateVpc |
| Lambda | CreateFunction |
| RDS | CreateDBInstance |

------------------------------------------------------------------------

# Event Flow

```text
User

↓

AWS Console / CLI / SDK

↓

AWS API

↓

CloudTrail

↓

Management Event

↓

Event History / Trail
```

------------------------------------------------------------------------

# Example Event

Suppose an administrator launches a new EC2 instance.

CloudTrail records:

- Event Name: RunInstances
- Event Time
- AWS Region
- IAM User
- Source IP
- Request Parameters
- Response Elements

This information is available for auditing and troubleshooting.

------------------------------------------------------------------------

# Security Benefits

Management Events help detect:

- Unauthorized IAM changes
- Resource deletion
- Security Group modifications
- VPC configuration changes
- Administrative activity

They are essential for compliance and forensic investigations.

------------------------------------------------------------------------

# Best Practices

- Always enable Management Events.
- Record both Read and Write events for production environments.
- Store logs in an encrypted Amazon S3 bucket.
- Enable Multi-Region Trails.
- Monitor sensitive API calls using CloudWatch Alarms.
- Trigger automated responses using EventBridge.

------------------------------------------------------------------------

# Real-World Example

A developer accidentally deletes an Amazon RDS instance.

CloudTrail records:

```text
DeleteDBInstance

↓

IAM User

↓

Timestamp

↓

Source IP

↓

AWS Region

↓

Request Parameters
```

The operations team can quickly identify who performed the action, when it occurred, and begin recovery procedures.

------------------------------------------------------------------------

# Key Takeaways

- Management Events record Control Plane API operations.
- They are enabled by default in CloudTrail.
- Events are categorized as Read or Write operations.
- They are essential for auditing, governance, and compliance.
- Management Events form the foundation of AWS security monitoring.