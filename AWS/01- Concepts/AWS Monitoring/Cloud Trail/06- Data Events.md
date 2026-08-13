# Data Events

Data Events record operations performed on the **data stored inside AWS resources** rather than changes made to the resources themselves.

These events are also called **Data Plane Events** because they capture actions performed on objects, records, and functions.

Unlike Management Events, **Data Events are disabled by default** because they can generate a very large number of log entries.

------------------------------------------------------------------------

# What are Data Events?

Data Events capture operations performed on resource contents.

Examples include:

- Uploading an object to Amazon S3
- Downloading an object from Amazon S3
- Deleting an object from Amazon S3
- Invoking an AWS Lambda function
- Reading or writing data in supported services

------------------------------------------------------------------------

# Characteristics

- Disabled by default
- Capture data access operations
- Can generate millions of events
- Additional charges may apply
- Useful for security auditing and compliance

------------------------------------------------------------------------

# Common Data Event Sources

CloudTrail supports Data Events for several AWS services.

Examples include:

- Amazon S3 Object-level API activity
- AWS Lambda Invoke API
- Amazon DynamoDB (supported data operations)
- Amazon SNS (selected operations)
- Amazon SQS (selected operations)

*Supported services may expand over time.*

------------------------------------------------------------------------

# Amazon S3 Data Events

Object-level operations include:

- GetObject
- PutObject
- DeleteObject
- CopyObject
- RestoreObject

Example:

```text
User

↓

Upload File

↓

PutObject

↓

CloudTrail Records Data Event
```

------------------------------------------------------------------------

# AWS Lambda Data Events

CloudTrail records Lambda function invocations.

Example:

```text
Application

↓

Invoke Lambda

↓

CloudTrail Records Invoke Event
```

This helps monitor serverless workloads.

------------------------------------------------------------------------

# Event Flow

```text
Application

↓

Access Resource Data

↓

AWS Service

↓

CloudTrail

↓

Data Event

↓

Amazon S3 Trail
```

------------------------------------------------------------------------

# Management Events vs Data Events

| Feature | Management Events | Data Events |
|----------|-------------------|-------------|
| Records | Resource changes | Resource data access |
| Default | Enabled | Disabled |
| Cost | Included | Additional charges may apply |
| Example | CreateBucket | PutObject |

------------------------------------------------------------------------

# Why Enable Data Events?

Data Events are useful when you need to answer questions such as:

- Who downloaded this file?
- Who deleted an S3 object?
- Which application invoked this Lambda function?
- Who accessed sensitive business data?

------------------------------------------------------------------------

# Cost Considerations

Because object-level operations occur frequently, Data Events can generate a large number of log entries.

Recommendations:

- Enable Data Events only for critical resources.
- Monitor high-value S3 buckets.
- Trace sensitive Lambda functions.
- Regularly review CloudTrail costs.

------------------------------------------------------------------------

# Real-World Example

A confidential document is accidentally deleted from an Amazon S3 bucket.

CloudTrail Data Events reveal:

```text
DeleteObject

↓

IAM User

↓

Object Name

↓

Timestamp

↓

Source IP
```

This information helps identify who deleted the object and supports recovery and auditing efforts.

------------------------------------------------------------------------

# Best Practices

- Enable Data Events only where necessary.
- Monitor sensitive S3 buckets.
- Audit Lambda invocations for critical applications.
- Archive logs using Amazon S3 Lifecycle policies.
- Combine Data Events with CloudWatch Alarms and EventBridge automation.

------------------------------------------------------------------------

# Key Takeaways

- Data Events record operations performed on the data inside AWS resources.
- They are disabled by default.
- Common examples include S3 object operations and Lambda invocations.
- Data Events provide detailed auditing but can increase CloudTrail costs.
- Enable them selectively for critical workloads and compliance requirements.