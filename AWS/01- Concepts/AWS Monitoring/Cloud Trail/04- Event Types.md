# AWS CloudTrail Event Types

AWS CloudTrail records different categories of events depending on the AWS resource and the type of operation being performed.

Understanding these event types is important for AWS certifications and production environments.

------------------------------------------------------------------------

# Types of CloudTrail Events

CloudTrail supports three primary event types:

1. Management Events
2. Data Events
3. Network Activity Events

------------------------------------------------------------------------

# 1. Management Events

Management Events record operations performed on AWS resources.

These are also called **Control Plane Events**.

Examples:

- Launch EC2 Instance
- Create IAM User
- Modify Security Group
- Create VPC
- Delete RDS Instance

Management Events are enabled by default.

------------------------------------------------------------------------

# 2. Data Events

Data Events record operations performed on the data inside AWS resources.

These are also called **Data Plane Events**.

Examples:

- Upload S3 Object
- Download S3 Object
- Delete S3 Object
- Invoke Lambda Function
- DynamoDB Item Operations

Data Events are disabled by default because they can generate a large number of records.

------------------------------------------------------------------------

# 3. Network Activity Events

Network Activity Events record API activity associated with supported VPC endpoints and network-based access to AWS services.

These events provide additional visibility into network-level operations and private connectivity.

------------------------------------------------------------------------

# Read Events vs Write Events

CloudTrail also classifies Management Events as:

## Read Events

These do not modify resources.

Examples:

- DescribeInstances
- ListBuckets
- GetRole

------------------------------------------------------------------------

## Write Events

These modify AWS resources.

Examples:

- RunInstances
- DeleteBucket
- CreateUser
- UpdateFunctionCode

------------------------------------------------------------------------

# Event Comparison

| Event Type | Records | Default |
|------------|---------|---------|
| Management Events | Resource configuration changes | Enabled |
| Data Events | Operations on resource data | Disabled |
| Network Activity Events | Supported network/API activity | Optional |

------------------------------------------------------------------------

# Real-World Example

A developer uploads a file to Amazon S3.

```text
Create Bucket

↓

Management Event

↓

Upload Object

↓

Data Event

↓

Access through VPC Endpoint

↓

Network Activity Event
```

Each action generates a different CloudTrail event type.

------------------------------------------------------------------------

# Best Practices

- Always enable Management Events.
- Enable Data Events only for critical resources.
- Review Network Activity Events when using VPC endpoints.
- Monitor Write Events closely for security.
- Archive logs in Amazon S3.

------------------------------------------------------------------------

# Key Takeaways

- CloudTrail records Management, Data, and Network Activity Events.
- Management Events are enabled by default.
- Data Events capture operations performed on resource data.
- Network Activity Events provide visibility into supported network access.
- Understanding event types is essential for auditing and security.